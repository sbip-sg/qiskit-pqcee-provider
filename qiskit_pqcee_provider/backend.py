from qiskit.providers import BackendV2 as Backend
from qiskit.providers import ProviderV1 as Provider
from qiskit.transpiler import Target
from qiskit.providers import Options
from qiskit.circuit import Measure
from qiskit.circuit.library import PhaseGate, CXGate, IGate
from qiskit.circuit.library import XGate, HGate, CCXGate, TGate, YGate
from qiskit.circuit.library import ZGate, CPhaseGate
import numpy as np
import logging
import qiskit

import web3
import pathlib
from solcx import compile_source

from .job import BlockcahinJob

logger = logging.getLogger(__name__)


class BlockchainBackend(Backend):
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
    ):
        r"""
        Args:
            provider: The qiskit provider of the backend.
            web3_provider: The web3 provider for the blockchain.
            backend_address: The address of the backend smart contract.
            is_local: If the backend is local or not.
            backend_seed: The seed for the backend.
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
            provider=provider,
            name=name,
            description='qunatum backend on blockchain',
            # simulator=is_simulator,
            # local=is_local,
        )

        # self._configuration.simulator = is_simulator

        # create the random seed
        self.state_seed = np.random.RandomState(
            np.random.MT19937(
                np.random.SeedSequence(backend_seed)
            )
        )

        # Create Target
        self._target = Target(
            description="Target for quantum backend on blockchain",
            num_qubits=num_qubits
        )

        for gate_name in gates_names:
            match gate_name:
                case "I":
                    self._target.add_instruction(
                        IGate(),
                        {(qubit,): None for qubit in range(num_qubits)}
                    )
                case "X":
                    self._target.add_instruction(
                        XGate(),
                        {(qubit,): None for qubit in range(num_qubits)}
                    )
                case "H":
                    self._target.add_instruction(
                        HGate(),
                        {(qubit,): None for qubit in range(num_qubits)}
                    )
                case "CN":
                    self._target.add_instruction(
                        CXGate(),
                        {
                            edge: None for edge in [
                                (x, y)
                                for x in range(num_qubits)
                                for y in range(num_qubits)
                                if x != y
                            ]
                        }
                    )
                case "CCN":
                    self._target.add_instruction(
                        CCXGate(),
                        {edge: None for edge in [
                            (x, y, z)
                            for x in range(num_qubits)
                            for y in range(num_qubits)
                            for z in range(num_qubits)
                            if x != y and x != z and y != z
                        ]}
                    )
                case "P45":
                    self._target.add_instruction(
                        PhaseGate(np.pi/4),
                        {(qubit,): None for qubit in range(num_qubits)},
                        name='p45'
                    )
                case "T":
                    self._target.add_instruction(
                        TGate(),
                        {(qubit,): None for qubit in range(num_qubits)}
                    )
                case "Y":
                    self._target.add_instruction(
                        YGate(),
                        {(qubit,): None for qubit in range(num_qubits)}
                    )
                case "Z":
                    self._target.add_instruction(
                        ZGate(),
                        {(qubit,): None for qubit in range(num_qubits)}
                    )
                case "CP45":
                    self._target.add_instruction(
                        CPhaseGate(np.pi/4),
                        {(qubit,): None for qubit in range(num_qubits)},
                        name='cp45'
                    )
                case "m":
                    self._target.add_instruction(
                        Measure(),
                        {(qubit,): None for qubit in range(num_qubits)}
                    )

        # Set option validators
        self.options.set_validator("shots", (1, 4096))

    @property
    def target(self):
        return self._target

    @property
    def max_circuits(self):
        return 1

    @classmethod
    def _default_options(cls):
        return Options(shots=4)

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
        job_json = dict(
            circuit_str=self.convert_circuit_to_string(circuits[0]),
            shots=options['shots'],
            num_qubits=self.num_qubits,
            random_seed=self.state_seed.randint(low=0, high=65535)
        )
        job_handle = self.web3_contract
        return BlockcahinJob(self, job_handle, job_json, circuits)

    def convert_circuit_to_string(
            self,
            circuit: qiskit.QuantumCircuit,
    ) -> str:
        r"""
        Convert a circuit to a string.

        Args:
            circuit: The circuit to convert.

        Returns:
            The circuit as a string.
        """
        # convert circuit to json
        # return json
        # Transpile the circuit to the target
        transpiled_circuit = qiskit.transpile(
            circuit,
            backend=self
        )
        circuit_string: str = ""
        for gate in transpiled_circuit.data:
            # get gate name
            gate_name = gate.operation.name
            # get the number of qubits
            gate_num_qubits = gate.operation.num_qubits
            # get gate qubits
            gate_qubits = gate.qubits
            # string to add
            # initialise with identity gates
            gate_string = "I" * self.num_qubits

            if gate_name == "barrier":
                continue
            # if only 1 qubit gate
            match gate_num_qubits:
                case 1:
                    if gate_name == "p45":
                        gate_name = "P"
                    gate_name = gate_name.upper()
                    if gate_name == "MEASURE":
                        gate_name = "m"
                    index = transpiled_circuit.find_bit(gate_qubits[0]).index
                    # print(index)
                    gate_string = string_replact_at(
                        gate_string,
                        index,
                        gate_name
                    )
                case 2:
                    if gate_name == "cx":
                        gate_name = "CN"
                    elif gate_name == "cp45":
                        gate_name = "CP"
                    else:
                        raise NotImplementedError("Gate not supported")
                    c_index = transpiled_circuit.find_bit(gate_qubits[0]).index
                    t_index = transpiled_circuit.find_bit(gate_qubits[1]).index
                    gate_string = string_replact_at(
                        gate_string,
                        c_index,
                        "C"
                    )
                    if gate_name == "CP":
                        gate_string = string_replact_at(
                            gate_string,
                            t_index,
                            "P"
                        )
                    if gate_name == "CN":
                        gate_string = string_replact_at(
                            gate_string,
                            t_index,
                            "N"
                        )
                case 3:
                    if gate_name == "ccx":
                        gate_name = "CCN"
                    else:
                        raise NotImplementedError("Gate not supported")
                    c1_index = (
                        transpiled_circuit.find_bit(gate_qubits[0]).index
                    )
                    c2_index = (
                        transpiled_circuit.find_bit(gate_qubits[1]).index
                    )
                    t_index = transpiled_circuit.find_bit(gate_qubits[2]).index
                    gate_string = string_replact_at(
                        gate_string,
                        c1_index,
                        "C"
                    )
                    gate_string = string_replact_at(
                        gate_string,
                        c2_index,
                        "C"
                    )
                    if gate_name == "CCN":
                        gate_string = string_replact_at(
                            gate_string,
                            t_index,
                            "N"
                        )
                    else:
                        raise NotImplementedError("Gate not supported")
                case _:
                    raise NotImplementedError("Gate not supported")
            circuit_string += gate_string + ','
        # finish the circuit string
        circuit_string = string_replact_at(
            circuit_string,
            len(circuit_string)-1,
            "."
        )
        return circuit_string


def string_replact_at(source: str, index: int, value: str) -> str:
    r"""
    Replace a character at a given index in a string.

    Args:
        source: The source string.
        index: The index to replace.
        value: The value to replace with.

    Returns:
        The string with the character replaced.
    """
    return source[:index] + value + source[(index+1):]
