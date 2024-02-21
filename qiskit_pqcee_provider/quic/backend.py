# future annotations
from __future__ import annotations
from qiskit.providers import BackendV2 as Backend
from qiskit.providers import ProviderV1 as Provider
from qiskit.providers import Options
from qiskit.synthesis import generate_basic_approximations
from qiskit.transpiler.passes.synthesis import SolovayKitaev
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit.transpiler import PassManager
from qiskit_aer import AerProvider
# aer simulator for emulation
from qiskit_aer import AerSimulator
import logging
import qiskit

from .gate import QuiCGate
from .target import QuiCTarget

logger = logging.getLogger(__name__)

def get_SolovayKitaev_pass_manager(
    basis_gates: list[str] = None,
    depth: int = 3,
    recursion_degree: int = 4
) -> PassManager:
    basic_approximations = generate_basic_approximations(
        basis_gates=basis_gates,
        depth=depth
    )
    return PassManager([SolovayKitaev(
        basic_approximations=basic_approximations,
        recursion_degree=recursion_degree
    )])


class QuiCBackend(Backend):
    def __init__(
        self,
        quic_basis_gates: list[str],
        num_qubits: int = 32,
        approximation_depth: int = 0,
        approximation_recursion_degree: int = 0,
        provider: Provider = None,
        name: str = "aer_quic_simulator",
        description: str = 'QuiC AER Backend'
    ) -> None:
        if provider is None:
            provider = AerProvider()

        super().__init__(
            provider=provider,
            name=name,
            description=description
        )
        basis_gates = list(
            map(
                QuiCGate.from_quic_name,
                quic_basis_gates
            )
        )
        self._target = QuiCTarget(
            basis_gates=basis_gates,
            num_qubits=num_qubits
        )

        # Set option validators
        self.options.set_validator("shots", (1, 4096))

        # if approximation depth and recursion degree are set
        # generate the pass manager
        if approximation_depth > 0 and approximation_recursion_degree > 0:
            self._approximation_pass_manager = get_SolovayKitaev_pass_manager(
                basis_gates=self._target.get_approximation_basis_gates(),
                depth=approximation_depth,
                recursion_degree=approximation_recursion_degree
            )
        else:
            self._approximation_pass_manager = None
    
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
        # maybe only use the basis gates and make an emulator
        # use a fake aer simulator to run the circuits
        fake_simulator = AerSimulator.from_backend(self)
        # run the circuits
        return fake_simulator.run(circuits, **options)
    
    def run_aer_simulator(self, circuits, **kwargs):
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
        # use a fake aer simulator to run the circuits
        fake_simulator = AerProvider().get_backend('aer_simulator')
        # run the circuits
        return fake_simulator.run(circuits, **options)

    def transpile_circuit(
            self,
            circuit: qiskit.QuantumCircuit
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
        # TODO hard problem to add back the measurements at
        # the right time and the right qubits
        circuit.data = [
            gate for gate in circuit.data
            if gate.operation.name != "measure"]
        # get the pass manager no optimisations
        pass_manager = generate_preset_pass_manager(0, self)
        if self._approximation_pass_manager is not None:
            pass_manager.pre_layout = self._approximation_pass_manager
        circuit = pass_manager.run(circuit)
        return circuit

    def get_quic_circuit_string(
        self,
        circuit: qiskit.QuantumCircuit
    ) -> str:
        r"""
        Convert a circuit to a string.

        Args:
            circuit: The circuit to convert.

        Returns:
            The circuit as a string.
        """
        circuit = self.transpile_circuit(circuit)

        # compute the maximum num qubits
        circuit_num_qubits = max(
            [
                circuit.find_bit(qubit).index
                for gate in circuit.data
                for qubit in gate.qubits
            ] + [0]) + 1
        circuit_string: str = ""
        circuit_string_list: list[str] = []
        for gate in circuit.data:
            # get gate name
            gate_name = gate.operation.name
            # get the number of qubits
            gate_num_qubits = gate.operation.num_qubits
            # get gate qubits
            gate_qubits = gate.qubits
            # string to add
            # initialise with identity gates
            gate_string_list = ["I" for _ in range(circuit_num_qubits)]

            if gate_name == "barrier":
                continue

            quic_gate = QuiCGate.from_qiskit_name(gate_name)
            # get the quic representation
            quic_representation = quic_gate.get_quic_representation()
            # modify the gate string list
            for qubit_no in range(gate_num_qubits):
                index = circuit.find_bit(gate_qubits[qubit_no]).index
                gate_string_list[index] = quic_representation[qubit_no]
            # join the list to get the gate string
            gate_string = "".join(gate_string_list)
            # add the gate string to the circuit string list
            circuit_string_list.append(gate_string)
        # join the circuit string list to get the circuit string
        circuit_string = ",".join(circuit_string_list)
        logger.debug(circuit_string)
        return circuit_string + "."

    def get_quantum_circuit_from_quic_string(
        self,
        quic_string: str,
        add_measurements: bool = False
    ) -> qiskit.QuantumCircuit:
        r"""
        Convert a string to a circuit.

        Args:
            quic_string: The string to convert.
            add_measurements: Add measurements to the circuit.

        Returns:
            The qiskit Quantum circuit.
        """
        if quic_string[-1] != ".":
            raise ValueError("QuIC string must end with a period.")
        # remove the period
        quic_string = quic_string.strip()[:-1]
        # split the string by the comma
        quic_string_list = quic_string.split(",")
        # num qubits
        num_qubits = len(quic_string_list[0])
        # Create Quantum Registers
        qr = qiskit.QuantumRegister(num_qubits, 'q')
        # Create Classical Registers
        cr = qiskit.ClassicalRegister(num_qubits, 'c')
        # Create a Quantum Circuit
        circuit = qiskit.QuantumCircuit(
            qr,
            cr,
            name="QuIC Circuit"
        )
        # iterate over the gates
        for quic_gate in quic_string_list:
            # create a quantum gate
            if 'C' in quic_gate:
                # we have control qubits
                control_qubits = [
                    index
                    for index, qubit in enumerate(quic_gate)
                    if qubit == 'C'
                ]
                target_qubits = [
                    index
                    for index, qubit in enumerate(quic_gate)
                    if (qubit != 'C') and (qubit != 'I')
                ]
                # verify the correctness of the quic string
                if len(target_qubits) != 1:
                    raise ValueError(f"{quic_gate}: QuIC gate string is not correct.")
                target_qubit = target_qubits[0]
                # create the quic gate string
                quic_gate_string = "C" * len(control_qubits) + quic_gate[target_qubit]
                # get the qiskit gate
                qiskit_gate = QuiCGate.from_quic_name(quic_gate_string).get_qiskit_instruction()
                # add the gate to the circuit
                circuit.append(
                    qiskit_gate,
                    [qr[index] for index in control_qubits] + [qr[target_qubit]]
                )
            else:
                # we have no control qubits
                # get the target qubits
                target_qubits = [
                    index
                    for index, qubit in enumerate(quic_gate)
                    #if qubit != 'I'
                ]
                # append the gates to the circuit
                for target_qubit in target_qubits:
                    # get the qiskit gate
                    qiskit_gate = QuiCGate.from_quic_name(quic_gate[target_qubit]).get_qiskit_instruction()
                    if qiskit_gate.name == "measure":
                        circuit.append(
                            qiskit_gate,
                            [qr[target_qubit]],
                            [cr[target_qubit]]
                        )
                    else:
                        # add the gate to the circuit
                        circuit.append(
                            qiskit_gate,
                            [qr[target_qubit]]
                        )
        # add the measurements
        if add_measurements:
            circuit.measure(qr, cr)
        return circuit


    def run_quic_script(
        self,
        circuit_string: str,
        **kwargs
    ):
        r"""
        Run a circuit string on the QuiC backend.

        Args:
            circuit_string: The circuit string to run.

        Returns:
            The Job.
        """
        qc = self.get_quantum_circuit_from_quic_string(
            quic_string=circuit_string,
            add_measurements=kwargs.get('add_measurements', False)
        )
        kwargs.pop('add_measurements', None)
        return self.run(qc, **kwargs)
        