import pytest

from qiskit_pqcee_provider.quic import QuiCGate

def test_init_quic_gate(quic_gates_name):
    for gate in quic_gates_name:
        assert QuiCGate.from_quic_name(gate).quicRepresentation is gate

def test_quic_gate_list(quic_gates_name):
    assert QuiCGate.get_gates_quic_name() == quic_gates_name

def test_special_custom_pqcee_gates(special_pqcee_gates_quic_name):
    for gate in special_pqcee_gates_quic_name:
        assert QuiCGate.from_quic_name(gate).is_special() is True

def test_special_qiskit_gates(special_qiskit_gates):
    for gate in special_qiskit_gates:
        assert gate.is_special() is True

def test_getitem_by_name(quic_gates_name):
    for gate in quic_gates_name:
        assert QuiCGate(QuiCGate.from_quic_name(gate).name) is QuiCGate.from_quic_name(gate)

def test_getitem_by_qiskit_name(quic_gates_name):
    for gate in quic_gates_name:
        assert QuiCGate.from_qiskit_name(QuiCGate.from_quic_name(gate).get_qiskit_instruction().name) is QuiCGate.from_quic_name(gate)

def test_get_gates():
    gates_name = QuiCGate.get_gates_name()
    gates_quic_name = QuiCGate.get_gates_quic_name()
    gates_qiskit_name = QuiCGate.get_gates_qiskit_name()
    for index in range(len(gates_name)):
        assert QuiCGate(gates_name[index]) is QuiCGate.from_quic_name(gates_quic_name[index])
        assert QuiCGate.from_quic_name(gates_quic_name[index]) is QuiCGate.from_qiskit_name(gates_qiskit_name[index])

def test_missing_gate():
    with pytest.raises(KeyError):
        QuiCGate("MISSING_GATE")

def test_missing_quic_gate():
    with pytest.raises(KeyError):
        QuiCGate.from_quic_name("XYZ")

def test_missing_qiskit_gate():
    with pytest.raises(KeyError):
        QuiCGate.from_qiskit_name("missing")