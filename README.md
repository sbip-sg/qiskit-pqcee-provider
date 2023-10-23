# qiskit-pqcee-provider
The Qiskit provider for pQCee blockchain quantum simulator

# Install
```
pip install qiskit-pqcee-provider
```

# Usage
```python
import qiskit
from qiskit_pqcee_provider import PqceeProvider

provider = PqceeProvider()
backend = provider.get_backend('pqcee_simulator')

qc = qiskit.QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()

job = backend.run(qc, shots=10)
result = job.result()
print(result.get_counts())
```
