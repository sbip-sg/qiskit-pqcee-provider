from typing_extensions import override
from qiskit.providers import ProviderV1 as Provider
from qiskit.providers import Options
# from qiskit.circuit.gate import Gate
import numpy as np
import logging

import web3
import pathlib
from solcx import compile_source

from .job import BlockcahinJob
from .quic import QuiCBackend

logger = logging.getLogger(__name__)


class BlockchainBackend(QuiCBackend):
    r"""
    The quantum backend on the blockchain.
    """

    web3_contract: web3.contract.Contract = None
    r"""
    The backend smart contract.
    """
    state_seed: np.random.RandomState = None
    r"""
    The seed random state
    """

    def __init__(
            self,
            provider: Provider,
            web3_provider: web3.Web3,
            backend_address: str,
            is_local: bool = False,
            backend_seed: int = 0,
            approximation_depth: int = 3,
            approximation_recursion_degree: int = 3,
    ):
        r"""
        Args:
            provider: The qiskit provider of the backend.
            web3_provider: The web3 provider for the blockchain.
            backend_address: The address of the backend smart contract.
            is_local: If the backend is local or not.
            backend_seed: The seed for the backend.
            approximation_depth: The depth of the basic approximation.
            approximation_recursion_degree: The recursion degree for the Solovay-Kitaev
        """
        # get the backend interface for the abi
        mod_path = pathlib.Path(__file__).parent.absolute()
        absolute_path = (
            mod_path / "contracts" / "QuantumBackendInterface.sol"
        ).resolve()
        sc_interface_code = absolute_path.read_text()
        compiled_sol = compile_source(sc_interface_code, output_values=['abi'])
        contract_id, contract_interface = compiled_sol.popitem()
        abi = contract_interface['abi']
        # connect to backend contract
        self.web3_contract = web3_provider.eth.contract(
            address=backend_address,
            abi=abi
        )
        # getting the backend information from the backend contract
        name = self.web3_contract.functions.getName().call()
        num_qubits = self.web3_contract.functions.getNumberOfQubits().call()
        # is_simulator = self.web3_contract.functions.isSimulator().call()
        gates_names = self.web3_contract.functions.getGatesNames().call()

        super().__init__(
            basis_gates=gates_names,
            num_qubits=num_qubits,
            approximation_depth=approximation_depth,
            approximation_recursion_degree=approximation_recursion_degree,
            provider=provider,
            name=name,
            description='quantum backend on blockchain'
        )

        # self._configuration.simulator = is_simulator

        # create the random seed
        self.state_seed = np.random.RandomState(
            np.random.MT19937(
                np.random.SeedSequence(backend_seed)
            )
        )

    @property
    def target(self):
        return self._target

    @property
    def max_circuits(self):
        return 1

    @classmethod
    def _default_options(cls):
        return Options(shots=10)

    @override
    def run(self, circuits, **kwargs):
        # serialize circuits submit to backend and create a job
        for kwarg in kwargs:
            if not hasattr(self.options, kwarg):
                logger.warn(
                    "Option %s is not used by this backend" % kwarg,
                    UserWarning, stacklevel=2)
        options = {
            'shots': kwargs.get('shots', self.options.shots)
        }
        # make a list of circuits
        if type(circuits) is not list:
            circuits = [circuits]
        # job_json = convert_to_wire_format(circuits, options)
        # job_handle = submit_to_backend(job_jsonb)
        circuit_str: str = self.get_quic_circuit_string(circuits[0])
        first_index = circuit_str.find(",")
        if first_index == -1:
            first_index = circuit_str.find(".")
        if first_index <= 0:
            raise ValueError("Invalid circuit string")
        num_qubits: int = first_index
        job_json = dict(
            circuit_str=circuit_str,
            shots=options['shots'],
            num_qubits=num_qubits,
            random_seed=self.state_seed.randint(low=0, high=65535)
        )
        job_handle = self.web3_contract
        return BlockcahinJob(self, job_handle, job_json, circuits)
