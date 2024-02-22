import pytest

from qiskit_pqcee_provider.quic import QuiCTarget, QuiCGate


def init_quic_target(test_quic_gates):
    minimum_qubits = max(
        map(
            lambda x: x.get_qiskit_instruction().num_qubits,
            test_quic_gates
        )
    )
    quic_target = QuiCTarget(test_quic_gates, minimum_qubits)
    assert quic_target.num_qubits == minimum_qubits
    for quic_gate in test_quic_gates:
        assert quic_gate.get_qiskit_instruction() in quic_target.operations
    return quic_target

def test_init_quic_target(quic_gates, quic_target):
    init_quic_target(quic_gates)
    with pytest.raises(ValueError):
        QuiCTarget(quic_gates, quic_target.num_qubits - 1)

def init_quic_target_approximation_basis_gates(test_quic_gates):
    quic_target = init_quic_target(test_quic_gates)
    approximation_basis_gates = list(
        map(
            lambda x: x.get_qiskit_instruction().name,
            filter(
                lambda x: not(x.is_special()) and x.get_qiskit_instruction().num_qubits == 1,
                test_quic_gates
            )
        )
    )
    if QuiCGate.P_GATE in test_quic_gates and QuiCGate.S_GATE not in test_quic_gates:
        approximation_basis_gates.append(QuiCGate.S_GATE.get_qiskit_instruction().name)
        assert QuiCGate.S_GATE.get_qiskit_instruction().name in quic_target.get_approximation_basis_gates()
    if QuiCGate.PDG_GATE in test_quic_gates and QuiCGate.SDG_GATE not in test_quic_gates:
        approximation_basis_gates.append(QuiCGate.SDG_GATE.get_qiskit_instruction().name)
        assert QuiCGate.SDG_GATE.get_qiskit_instruction().name in quic_target.get_approximation_basis_gates()
    
    assert quic_target.get_approximation_basis_gates() == approximation_basis_gates

    return quic_target


#def test_init_quic_target_all(complete_combinations_quic_gates):
#    for test_quic_gates in complete_combinations_quic_gates:
#        init_quic_target(test_quic_gates)

#def test_init_quic_target_all(complete_combinations_quic_gates):
#    for test_quic_gates in complete_combinations_quic_gates:
#       init_quic_target_approximation_basis_gates(test_quic_gates)

def test_get_approximation_basis_gates(quic_target, approximation_basis_gates):
    assert len(quic_target.get_approximation_basis_gates()) == len(approximation_basis_gates)
    assert quic_target.get_approximation_basis_gates() == approximation_basis_gates


    