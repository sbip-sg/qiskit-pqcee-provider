import pytest

import qiskit_pqcee_provider.quic

import itertools
import functools

# Add new gates in the list
@pytest.fixture
def quic_gates_name():
    return ["I", "X", "Y", "Z", "H", "S", "s", "T", "t", "CN", "CCN", "CS", "Cs", "m", "P", "p", "CP", "Cp", "CT", "Ct"]

@pytest.fixture
def quic_gates(quic_gates_name):
    return list(
        map(
            lambda x: qiskit_pqcee_provider.quic.QuiCGate.from_quic_name(x),
            quic_gates_name
        )
    )

@pytest.fixture
def special_pqcee_gates_quic_name():
    return ["P", "p", "CP", "Cp"]

# Speacial gates from qiskit
# Identity gate and Measurement gate
@pytest.fixture
def special_qiskit_gates():
    return [
        qiskit_pqcee_provider.quic.QuiCGate.IDENTITY_GATE,
        qiskit_pqcee_provider.quic.QuiCGate.MEASUREMENT_GATE
    ]

@pytest.fixture
def speacial_qiskit_gates_quic_name(special_qiskit_gates):
    return list(map(lambda x: x.quicRepresentation, special_qiskit_gates))

@pytest.fixture
def quic_basic_gates(
    quic_gates_name,
    special_qiskit_gates_quic_name,
    special_pqcee_gates_quic_name
):
    return [
        x
        for x in quic_gates_name
        if x not in special_qiskit_gates_quic_name and
        x not in special_pqcee_gates_quic_name
    ]

@pytest.fixture
def quic_target(quic_gates):
    minimum_qubits = max(
        map(
            lambda x: x.get_qiskit_instruction().num_qubits,
            quic_gates
        )
    )
    return qiskit_pqcee_provider.quic.QuiCTarget(quic_gates, minimum_qubits)

@pytest.fixture
def approximation_basis_gates(quic_gates):
    return list(
        map(
            lambda x: x.get_qiskit_instruction().name,
            filter(
                lambda x: not(x.is_special()) and x.get_qiskit_instruction().num_qubits == 1,
                quic_gates
            )
        )
    )

@pytest.fixture
def complete_combinations_quic_gates(quic_gates):
    return functools.reduce(
        lambda x, y: x + y,
        [
            list(
                map(
                    lambda x: list(x),
                    itertools.combinations(quic_gates, k)
                )
            )
            for k in range(1, len(quic_gates) + 1)
        ]
    )


@pytest.fixture
def complete_combinations_quic_gates_name(quic_gates_name):
    return functools.reduce(
        lambda x, y: x + y,
        [
            list(
                map(
                    lambda x: list(x),
                    itertools.combinations(quic_gates_name, k)
                )
            )
            for k in range(1, len(quic_gates_name) + 1)
        ]
    )

@pytest.fixture
def simple_quic_backend(quic_gates_name):
    return qiskit_pqcee_provider.quic.QuiCBackend(
        quic_gates_name
    )
