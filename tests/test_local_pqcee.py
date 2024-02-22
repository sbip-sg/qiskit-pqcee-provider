import pytest

import qiskit_pqcee_provider as qpp

import qiskit

@pytest.fixture
def local_pqcee_backend():
    return qpp.LocalPqceeProvider(
        approximation_depth=0,
        approximation_recursion_degree=0
    ).get_backend('pqcee_simulator')

def test_run_local_pqcee_backend(local_pqcee_backend):
    qc = qiskit.QuantumCircuit(2, 2)
    qc.x(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])
    job = local_pqcee_backend.run(qc, shots=10)
    result = job.result()
    assert result.get_counts() == {'11': 10}