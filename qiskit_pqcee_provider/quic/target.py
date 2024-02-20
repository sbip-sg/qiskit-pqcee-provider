# future annotations
from __future__ import annotations
import numpy as np
import logging
import qiskit
import qiskit.circuit.equivalence_library 
import enum
import itertools

from .gate import QuiCGate

logger = logging.getLogger(__name__)

class QuiCTarget(qiskit.transpiler.Target):
    quic_sel: qiskit.circuit.equivalence_library.EquivalenceLibrary = qiskit.circuit.equivalence_library.SessionEquivalenceLibrary
    approximation_basis_gates: list[str] = []

    def __init__(
        self,
        basis_gates: list[QuiCGate],
        num_qubits: int
    ) -> None:
        super().__init__(num_qubits=num_qubits)

        # add all the instructions to the target
        for gate in basis_gates:
            instruction: qiskit.circuit.Instruction = gate.get_qiskit_instruction()

            if instruction.num_qubits > num_qubits:
                raise ValueError(f"Gate {gate.name} requires more qubits than the target.")
            
            # generate all coupling maps for the instruction
            # by taking all permutations of the qubits of
            # length instruction.num_qubits wihtout repetition
            # of the same qubit
            self.add_instruction(
                instruction,
                {edge: None for edge in list(
                        itertools.permutations(
                            range(num_qubits), instruction.num_qubits
                        )
                    )
                }
            )
            # if is not a special case and is a single qubit gate
            # add it to the approximation basis gates
            if (not(gate.is_special())) and (instruction.num_qubits == 1):
                self.approximation_basis_gates.append(instruction.name)
        
        # add equivalences if necessary
        
        # add 2 x P45 -> s
        if ((QuiCGate.P_GATE in basis_gates) and
            (QuiCGate.S_GATE not in basis_gates)):
            qc = qiskit.QuantumCircuit(1)
            qc.append(
                QuiCGate.P_GATE.get_qiskit_instruction(),
                [0],
                []
            )
            qc.append(
                QuiCGate.P_GATE.get_qiskit_instruction(),
                [0],
                []
            )
            self.quic_sel.add_equivalence(
                QuiCGate.S_GATE.get_qiskit_instruction(),
                qc
            )
            self.approximation_basis_gates.append(
                QuiCGate.S_GATE.get_qiskit_instruction().name
            )
        
        # add 2 x PDG45 -> sdg
        if ((QuiCGate.PDG_GATE in basis_gates) and
            (QuiCGate.SDG_GATE not in basis_gates)):
            qc = qiskit.QuantumCircuit(1)
            qc.append(
                QuiCGate.PDG_GATE.get_qiskit_instruction(),
                [0],
                []
            )
            qc.append(
                QuiCGate.PDG_GATE.get_qiskit_instruction(),
                [0],
                []
            )
            self.quic_sel.add_equivalence(
                QuiCGate.SDG_GATE.get_qiskit_instruction(),
                qc
            )
            self.approximation_basis_gates.append(
                QuiCGate.SDG_GATE.get_qiskit_instruction().name
            )
        
        # if any other equivalences are needed, add them here
    
    def get_approximation_basis_gates(self) -> list[str]:
        return self.approximation_basis_gates
    
    def get_quic_equivalence_library(self) -> qiskit.circuit.equivalence_library.EquivalenceLibrary:
        return self.quic_sel
