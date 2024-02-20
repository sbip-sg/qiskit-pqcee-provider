import qiskit_pqcee_provider as qpp
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerProvider

# Create a Quantum Register with 2 qubits.
qr = QuantumRegister(2, 'q')
# Create a Classical Register with 2 bits.
cr = ClassicalRegister(2, 'c')
# Create a Quantum Circuit
circuit = QuantumCircuit(qr, cr)
# Add a H gate on qubit 0, putting this qubit in superposition.
circuit.h(qr[0])
# Add a CX (CNOT) gate on control qubit 0 and target qubit 1, putting
# the qubits in a Bell state.
# circuit.cx(qr[0], qr[1])
# add a rx gate on qubit 0
# circuit.rx(0.5, qr[0])
# add x gate on qubit 1
# circuit.x(qr[1])
# add y gate on qubit 1
# circuit.y(qr[1])
# circuit.y(qr[0])
# add z gate on qubit 1
# circuit.z(qr[1])
# add s gate on qubit 1
# circuit.s(qr[1])
# add sdg gate on qubit 1
# circuit.sdg(qr[1])
# add t gate on qubit 1
# circuit.t(qr[1])
# add tdg gate on qubit 1
# circuit.tdg(qr[1])
# add a ry gate on qubit 0
# circuit.ry(0.5, qr[0])
# add a rz gate on qubit 0
# circuit.rz(0.5, qr[0])
# Add a Measure gate to see the state.
circuit.measure(qr, cr)
# Draw the circuit
print(circuit.draw())

# initi the qpp provider
a = qpp.LocalPqceeProvider()
# get the backend
backend = a.get_backend('pqcee_simulator')

# run on the simulator
simulator = AerProvider().get_backend('aer_simulator')
result = simulator.run(circuit).result()
print(result.get_counts())

# to test on the pqcee_simulator
# import tqpp
# job = tqpp.backend.run(tqpp.circuit)
# result = job.result()
# print(result.get_counts())
