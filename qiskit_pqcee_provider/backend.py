from qiskit.providers import BackendV2 as Backend
from qiskit.providers import ProviderV1 as Provider
from qiskit.transpiler import Target
from qiskit.providers import Options
from qiskit.circuit import Measure
from qiskit.circuit.library import CXGate, IGate, ZGate
from qiskit.circuit.library import XGate, HGate, CCXGate, YGate
from qiskit.circuit.library import SGate, SdgGate, TGate, TdgGate
from qiskit.circuit.library import CSGate, CSdgGate
# from qiskit.circuit.library import PhaseGate, RXGate
# from qiskit.circuit.library import ZGate, CPhaseGate, RGate, CRXGate
from qiskit.circuit.equivalence_library import SessionEquivalenceLibrary
from qiskit.synthesis import generate_basic_approximations
from qiskit.transpiler.passes.synthesis import SolovayKitaev
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit.transpiler import PassManager
# from qiskit.circuit.gate import Gate
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
    skd_pass_manager: PassManager = None
    r"""
    The pass manager for the Solovay-Kitaev algorithm.
    """

    def __init__(
            self,
            provider: Provider,
            web3_provider: web3.Web3,
            backend_address: str,
            is_local: bool = False,
            backend_seed: int = 0,
            basic_approx_depth: int = 3,
            skd_recursion_degree: int = 3,
    ):
        r"""
        Args:
            provider: The qiskit provider of the backend.
            web3_provider: The web3 provider for the blockchain.
            backend_address: The address of the backend smart contract.
            is_local: If the backend is local or not.
            backend_seed: The seed for the backend.
            basic_approx_depth: The depth of the basic approximation.
            skd_recursion_degree: The recursion degree for the Solovay-Kitaev
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

        aprox_basis_gates = []

        # depending on the gates names, add the gates to the target
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
                    aprox_basis_gates.append("x")
                case "H":
                    self._target.add_instruction(
                        HGate(),
                        {(qubit,): None for qubit in range(num_qubits)}
                    )
                    aprox_basis_gates.append("h")
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
                    # p45 = PhaseGate(np.pi/4, label='p45')
                    qc = qiskit.QuantumCircuit(1, name='p45')
                    qc.p(np.pi/4, 0)
                    p45_instruction = qc.to_instruction()
                    self._target.add_instruction(
                        p45_instruction,
                        {(qubit,): None for qubit in range(num_qubits)}
                    )
                case "p45":
                    # p45 = PhaseGate(np.pi/4, label='p45')
                    qc = qiskit.QuantumCircuit(1, name='pdg45')
                    qc.p(-np.pi/4, 0)
                    pdg45_instruction = qc.to_instruction()
                    self._target.add_instruction(
                        pdg45_instruction,
                        {(qubit,): None for qubit in range(num_qubits)}
                    )
                case "S":
                    self._target.add_instruction(
                        SGate(),
                        {(qubit,): None for qubit in range(num_qubits)}
                    )
                    aprox_basis_gates.append("s")
                case "s":
                    self._target.add_instruction(
                        SdgGate(),
                        {(qubit,): None for qubit in range(num_qubits)}
                    )
                    aprox_basis_gates.append("sdg")
                case "T":
                    self._target.add_instruction(
                        TGate(),
                        {(qubit,): None for qubit in range(num_qubits)}
                    )
                    aprox_basis_gates.append("t")
                case "t":
                    self._target.add_instruction(
                        TdgGate(),
                        {(qubit,): None for qubit in range(num_qubits)}
                    )
                    aprox_basis_gates.append("tdg")
                case "Y":
                    self._target.add_instruction(
                        YGate(),
                        {(qubit,): None for qubit in range(num_qubits)}
                    )
                    aprox_basis_gates.append("y")
                case "Z":
                    self._target.add_instruction(
                        ZGate(),
                        {(qubit,): None for qubit in range(num_qubits)}
                    )
                    aprox_basis_gates.append("z")
                case "CS":
                    self._target.add_instruction(
                        CSGate(),
                        {edge: None for edge in [
                            (x, y)
                            for x in range(num_qubits)
                            for y in range(num_qubits)
                            if x != y
                        ]}
                    )
                case "Cs":
                    self._target.add_instruction(
                        CSdgGate(),
                        {edge: None for edge in [
                            (x, y)
                            for x in range(num_qubits)
                            for y in range(num_qubits)
                            if x != y
                        ]}
                    )
                case "CP45":
                    qc = qiskit.QuantumCircuit(2, name='cp45')
                    qc.cp(np.pi/4, 0, 1)
                    cp45_instruction = qc.to_instruction()
                    self._target.add_instruction(
                        cp45_instruction,
                        {
                            edge: None for edge in [
                                (x, y)
                                for x in range(num_qubits)
                                for y in range(num_qubits)
                                if x != y
                            ]
                        }
                    )
                case "Cp45":
                    qc = qiskit.QuantumCircuit(2, name='cpdg45')
                    qc.cp(-np.pi/4, 0, 1)
                    cp45_instruction = qc.to_instruction()
                    self._target.add_instruction(
                        cp45_instruction,
                        {
                            edge: None for edge in [
                                (x, y)
                                for x in range(num_qubits)
                                for y in range(num_qubits)
                                if x != y
                            ]
                        }
                    )
                case "m":
                    self._target.add_instruction(
                        Measure(),
                        {(qubit,): None for qubit in range(num_qubits)}
                    )

        if ("P45" in gates_names) and ("S" not in gates_names):
            q = qiskit.QuantumRegister(1, "q")
            def_p_s = qiskit.QuantumCircuit(q)
            def_p_s.append(p45_instruction, [q[0]], [])
            def_p_s.append(p45_instruction, [q[0]], [])
            SessionEquivalenceLibrary.add_equivalence(
                SGate(), def_p_s)
            aprox_basis_gates.append("s")
        if ("p45" in gates_names) and ("s" not in gates_names):
            q = qiskit.QuantumRegister(1, "q")
            def_p_sdg = qiskit.QuantumCircuit(q)
            def_p_sdg.append(pdg45_instruction, [q[0]], [])
            def_p_sdg.append(pdg45_instruction, [q[0]], [])
            SessionEquivalenceLibrary.add_equivalence(
                SdgGate(), def_p_sdg)
            aprox_basis_gates.append("sdg")
        # Set option validators
        self.options.set_validator("shots", (1, 4096))

        # make the basic aproximation given the depth
        # for the given 1-qubit gates, except identity and
        # measure.
        aprox = generate_basic_approximations(
            basis_gates=aprox_basis_gates, depth=basic_approx_depth
        )
        # generate the pass manager for the Solovay-Kitaev algorithm
        skd = SolovayKitaev(
            recursion_degree=skd_recursion_degree,
            basic_approximations=aprox
        )
        self.skd_pass_manager = PassManager([skd])

    @property
    def target(self):
        return self._target

    @property
    def max_circuits(self):
        return 1

    @classmethod
    def _default_options(cls):
        return Options(shots=10)

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
        circuit_str: str = self.convert_circuit_to_string(circuits[0])
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

    def get_transpiled_circuit(
            self,
            circuit: qiskit.QuantumCircuit,
    ) -> qiskit.QuantumCircuit:
        r"""
        Transpile a circuit.

        Args:
            circuit: The circuit to transpile.

        Returns:
            The transpiled circuit.
        """
        # delete measure gates
        circuit = circuit.copy()
        circuit.data = [
            gate for gate in circuit.data
            if gate.operation.name != "measure"]
        # get the pass manager
        pass_manager = generate_preset_pass_manager(0, self)
        pass_manager.pre_layout = self.skd_pass_manager
        circuit = pass_manager.run(circuit)
        return circuit

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
        circuit = self.get_transpiled_circuit(circuit)

        # compute the maximum num qubits
        circuit_num_qubits = max(
            [
                circuit.find_bit(qubit).index
                for gate in circuit.data
                for qubit in gate.qubits
            ]) + 1
        # convert circuit to json
        # return json
        circuit_string: str = ""
        for gate in circuit.data:
            # get gate name
            gate_name = gate.operation.name
            # get the number of qubits
            gate_num_qubits = gate.operation.num_qubits
            # get gate qubits
            gate_qubits = gate.qubits
            # string to add
            # initialise with identity gates
            gate_string = "I" * circuit_num_qubits

            if gate_name == "barrier":
                continue
            # if only 1 qubit gate
            match gate_num_qubits:
                case 1:
                    if gate_name == "S":
                        gate_name = "S"
                    elif gate_name == "sdg":
                        gate_name = "s"
                    elif gate_name == "T":
                        gate_name = "T"
                    elif gate_name == "tdg":
                        gate_name = "t"
                    elif gate_name == "p45":
                        gate_name = "P"
                    elif gate_name == "pdg45":
                        gate_name = "p"
                    else:
                        gate_name = gate_name.upper()
                    if gate_name == "MEASURE":
                        gate_name = "m"
                    index = circuit.find_bit(gate_qubits[0]).index
                    # print(index)
                    gate_string = string_replact_at(
                        gate_string,
                        index,
                        gate_name
                    )
                case 2:
                    if gate_name == "cx":
                        gate_name = "CN"
                    elif gate_name == "cs":
                        gate_name = "CS"
                    elif gate_name == "csdg":
                        gate_name = "Cs"
                    elif gate_name == "cp45":
                        gate_name = "CP"
                    elif gate_name == "cpdg45":
                        gate_name = "Cp"
                    else:
                        raise NotImplementedError("Gate not supported")
                    c_index = circuit.find_bit(gate_qubits[0]).index
                    t_index = circuit.find_bit(gate_qubits[1]).index
                    gate_string = string_replact_at(
                        gate_string,
                        c_index,
                        "C"
                    )
                    if gate_name == "CS":
                        gate_string = string_replact_at(
                            gate_string,
                            t_index,
                            "S"
                        )
                    elif gate_name == "Cs":
                        gate_string = string_replact_at(
                            gate_string,
                            t_index,
                            "s"
                        )
                    elif gate_name == "CP":
                        gate_string = string_replact_at(
                            gate_string,
                            t_index,
                            "P"
                        )
                    elif gate_name == "Cp":
                        gate_string = string_replact_at(
                            gate_string,
                            t_index,
                            "p"
                        )
                    elif gate_name == "CN":
                        gate_string = string_replact_at(
                            gate_string,
                            t_index,
                            "N"
                        )
                    else:
                        raise NotImplementedError("Gate not supported")
                case 3:
                    if gate_name == "ccx":
                        gate_name = "CCN"
                    else:
                        raise NotImplementedError("Gate not supported")
                    c1_index = (
                        circuit.find_bit(gate_qubits[0]).index
                    )
                    c2_index = (
                        circuit.find_bit(gate_qubits[1]).index
                    )
                    t_index = circuit.find_bit(gate_qubits[2]).index
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

        logger.debug(circuit_string)
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
