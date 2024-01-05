from qiskit.providers import JobV1 as Job
from qiskit.providers import JobError
from qiskit.providers import JobTimeoutError
from qiskit.providers.jobstatus import JobStatus
from qiskit.result import Result
from qiskit.result.models import ExperimentResult, ExperimentResultData
import time

import numpy as np
import threading


class BlockcahinJob(Job):
    r"""
    A job that runs on the blockchain.
    """
    def __init__(self, backend, job_handle, job_json, circuits):
        r"""
        Args:
            backend: The backend the job is running on.
            job_handle: The handle for the job.
            job_json: The job json.
            circuits: The circuits to run.
        """
        # create the job id as the concatenation of the address of the
        # contract and the random seed
        job_id = (
            str(job_handle.address) +
            "_" +
            str(job_json['random_seed']) +
            "_" +
            str(job_json['shots'])
        )
        super().__init__(backend, job_id)
        self._backend = backend
        self.job_json = job_json
        self.job_handle = job_handle
        self.circuits = circuits
        self.job_status = JobStatus.INITIALIZING
        # the results of the experiment in order of the shots
        self.experiment_results = list()
        # the result counts of the experiemnt
        self.experiment_counts = dict()
        # start the job on a different thread
        threading.Thread(target=self.submit).start()

    def _wait_for_result(self, timeout=None, wait=5):
        start_time = time.time()
        result = None
        # verify is the timeout is met or the job is done
        while True:
            elapsed = time.time() - start_time
            if timeout and elapsed >= timeout:
                raise JobTimeoutError('Timed out waiting for result')
            result = self.status()
            if result is JobStatus.DONE:
                break
            if result is JobStatus.ERROR:
                raise JobError('Job error')
            time.sleep(wait)
        return result

    def result(self, timeout=None, wait=5):
        result = self._wait_for_result(timeout, wait)
        return Result(
            backend_name=self._backend.name,
            backend_version=self._backend.backend_version,
            job_id=self._job_id,
            qobj_id=', '.join(x.name for x in self.circuits),
            success=result is JobStatus.DONE,
            results=[
                ExperimentResult(
                    shots=self.job_json['shots'],
                    success=result is JobStatus.DONE,
                    data=ExperimentResultData(
                        # memory=self.experiment_results
                        counts=self.experiment_counts
                    ),
                    seed=self.job_json['random_seed'],
                )
            ]
        )

    def status(self):
        return self.job_status

    def submit(self):
        experiment_results = list()
        experiment_counts = dict()
        # get a random generator from the random seed given
        # the random generator will generate seed for our
        # function
        random_seed = np.random.RandomState(
            np.random.MT19937(
                np.random.SeedSequence(self.job_json['random_seed'])
            )
        )
        self.job_status = JobStatus.RUNNING
        # run every shot
        for shot in range(self.job_json['shots']):
            # TODO: find a way to to run without gas
            call_options = {'gas': 900000000}
            # run the circuit with the contract implementation
            # of the simulator. The parameters are the number
            # of qubits, the circuit as a string and the random
            # seed
            shot_result = self.job_handle.functions.runQScript(
                self.job_json['num_qubits'],
                self.job_json['circuit_str'],
                random_seed.randint(low=0, high=65535)
            ).call(call_options)
            # The result is an unsigned integer that represents
            # the measurement result of the circuit. We need to
            # convert it to binary and then pad it with zeros
            # to the number of qubits. Also revers the order of
            # the bits to match the qiskit convention
            shot_result = format(shot_result, 'b').zfill(
                self.job_json['num_qubits']
            )[::-1]
            # append the result to the experiment results
            experiment_results.append(shot_result)
            # add the result to the experiment counts
            if shot_result in experiment_counts:
                experiment_counts[shot_result] += 1
            else:
                experiment_counts[shot_result] = 1
        self.experiment_counts = experiment_counts
        self.experiment_results = experiment_results
        # set the job status to done
        # after all the shots are done
        self.job_status = JobStatus.DONE
