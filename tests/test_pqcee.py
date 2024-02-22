import pytest

import qiskit_pqcee_provider as qpp

import qiskit

@pytest.fixture
def pqcee_backend():
    return qpp.PqceeProvider(
        approximation_depth=0,
        approximation_recursion_degree=0
    ).get_backend('pqcee_simulator')

def test_run_pqcee_backend(pqcee_backend):
    qc = qiskit.QuantumCircuit(2, 2)
    qc.x(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])
    job = pqcee_backend.run(qc, shots=10)
    result = job.result()
    assert result.get_counts() == {'11': 10}