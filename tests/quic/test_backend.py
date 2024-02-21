import pytest

import functools
import itertools

from qiskit_pqcee_provider.quic import QuiCTarget, QuiCGate, QuiCBackend
import qiskit

from qiskit.quantum_info import Operator


def one_gate_qiskit_circuit(target_gate_quic_name) -> qiskit.QuantumCircuit:
    target_quic_gate = QuiCGate.from_quic_name(target_gate_quic_name)
    qc = qiskit.QuantumCircuit(
        target_quic_gate.get_qiskit_instruction().num_qubits,
        target_quic_gate.get_qiskit_instruction().num_qubits
    )
    qc.append(
        target_quic_gate.get_qiskit_instruction(),
        list(range(target_quic_gate.get_qiskit_instruction().num_qubits))
    )
    #qc.measure_all()
    return qc

def qiskit_circuit_from_gates(
    target_gates_quic_name,
    speacial_qiskit_gates_quic_name
) -> qiskit.QuantumCircuit:
    target_quic_gates = [
        QuiCGate.from_quic_name(gate)
        for gate in target_gates_quic_name
    ]
    num_qubits = max(
        map(
            lambda x: x.get_qiskit_instruction().num_qubits,
            target_quic_gates
        )
    )
    speacial_qiskit_gates_quic = [
        QuiCGate.from_quic_name(gate)
        for gate in speacial_qiskit_gates_quic_name
    ]
    qc = qiskit.QuantumCircuit(num_qubits, num_qubits)
    for gate in target_quic_gates:
        if gate not in speacial_qiskit_gates_quic:
            qc.append(
                gate.get_qiskit_instruction(),
                list(range(gate.get_qiskit_instruction().num_qubits))
            )
        #else:
        #    qc.append(
        #        instruction=gate.get_qiskit_instruction(),
        #        qargs=list(range(gate.get_qiskit_instruction().num_qubits)),
        #        cargs=list(range(gate.get_qiskit_instruction().num_clbits))
        #    )
    #qc.measure_all()
    return qc

def init_quic_simple_backend(
    target_gates_quic_name,
    speacial_qiskit_gates_quic_name
):
    target_backend = QuiCBackend(target_gates_quic_name)

    for gate in target_gates_quic_name:
        if gate not in speacial_qiskit_gates_quic_name:
            qc = one_gate_qiskit_circuit(gate)
            quic_string = target_backend.get_quic_circuit_string(qc)
            assert quic_string[:-1] == gate
            b_qc = target_backend.get_quantum_circuit_from_quic_string(
                quic_string=quic_string#,
                #add_measurements=True
            )
            assert Operator(qc).equiv(Operator(b_qc))

def test_quic_complete_simple_backend(
    quic_gates_name,
    speacial_qiskit_gates_quic_name
):
    init_quic_simple_backend(
        quic_gates_name,
        speacial_qiskit_gates_quic_name
    )

def init_quic_backend(
    target_gates_quic_name,
    speacial_qiskit_gates_quic_name
):
    target_backend = QuiCBackend(
        target_gates_quic_name
    )
    qc = qiskit_circuit_from_gates(
        target_gates_quic_name,
        speacial_qiskit_gates_quic_name
    )
    quic_string = target_backend.get_quic_circuit_string(qc)
    b_qc = target_backend.get_quantum_circuit_from_quic_string(
        quic_string=quic_string#,
        #add_measurements=True
    )
    assert Operator(qc).equiv(Operator(b_qc))
    return target_backend

def test_quic_complete_backend(
    complete_combinations_quic_gates_name,
    speacial_qiskit_gates_quic_name
):
    # eliminate special combinations
    # that only use measurements and identity gates
    # which don't have any effect on the quantum state
    special_combinations = functools.reduce(
        lambda x, y: x + y,
        [
            list(
                map(
                    lambda x: list(x),
                    itertools.combinations(speacial_qiskit_gates_quic_name, k)
                )
            )
            for k in range(1, len(speacial_qiskit_gates_quic_name) + 1)
        ]
    )
    for target_gates_quic_name in complete_combinations_quic_gates_name:
        if target_gates_quic_name not in special_combinations:
            init_quic_backend(
                target_gates_quic_name,
                speacial_qiskit_gates_quic_name
            )