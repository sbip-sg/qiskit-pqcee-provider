// SPDX-License-Identifier: MIT with Commons Clause 
/*

Name: QuantumContract
Description: An on-chain quantum emulator running in an EVM smart contract
Author: Teik Guan Tan
Date: Feb 2023

MIT License

Copyright (c) 2023 pQCee Pte Ltd 

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

 * “Commons Clause” License Condition v1.0
 *
 * The Software is provided to you by the Licensor under the License, as defined below, subject to the following
 * condition.
 *
 * Without limiting other conditions in the License, the grant of rights under the License will not include, and
 * the License does not grant to you, the right to Sell the Software.
 *
 * For purposes of the foregoing, “Sell” means practicing any or all of the rights granted to you under the License
 * to provide to third parties, for a fee or other consideration (including without limitation fees for hosting or
 * consulting/ support services related to the Software), a product or service whose value derives, entirely or
 * substantially, from the functionality of the Software. Any license notice or attribution required by the License
 * must also include this Commons Clause License Condition notice.
 *
 * Software: QuantumContract
 *
 * License: MIT 1.0
 *
 * Licensor: pQCee Pte Ltd

modified by Stefan-Dan Ciocirlan (sdcioc) Date: 18.10.2023
*/

pragma solidity ^0.8.17;

import "./QuantumBackendInterface.sol";

contract QuantumBackend is IQuantumBackend
{
	address public owner;
	mapping(address => uint256) public balances;
	uint256 feePerBlock = 10**8;
	uint256 evalPeriod = 1;
	
	uint8 constant MAX_QUBITS=8;
	uint8 constant SUBSCRIPTION_QUBITS=5;
	uint256 constant MAX_IDX=2**MAX_QUBITS;
	bytes1 constant GATE_H      = 'H';
	bytes1 constant GATE_I      = 'I';
	bytes1 constant GATE_C      = 'C';
	bytes1 constant GATE_N      = 'N';
	bytes1 constant GATE_X      = 'X';
	bytes1 constant GATE_Y      = 'Y';
	bytes1 constant GATE_Z      = 'Z';
	bytes1 constant GATE_P      = 'P';
	bytes1 constant GATE_p      = 'p'; // conjugate P gate
	bytes1 constant GATE_T      = 'T';
	bytes1 constant GATE_t      = 't'; // conjugate T gate
	bytes1 constant GATE_m      = 'm';
	bytes1 constant DELIM_NEXT  = ',';
	bytes1 constant DELIM_END   = '.';

	string[] public gatesNames = ["H","I","CN","CCN","X","Y","Z","P45","T","CP","m"];
	
	struct Qubit
	{
		int256[2][MAX_IDX] rQubits;  // instance count in real 
		int256[2][MAX_IDX] iQubits;  // instance count in imaginary 
	}

	constructor() 
	{
		owner = msg.sender;
	}

	function getRandom(uint256 range, uint256 randomSeed) private view returns (uint) 
	{
		uint randomHash = uint(keccak256(abi.encode(block.prevrandao, block.timestamp, randomSeed)));
		return randomHash % range;
	}

	function qc_H(uint256 mask, uint256 currState, Qubit memory q, uint8 Qidx) internal pure 
	{
		uint8 nQidx = (Qidx == 0)?1:0;
		if ((mask & currState) != 0)
		{
			q.rQubits[currState-mask][nQidx] += q.rQubits[currState][Qidx];
			q.iQubits[currState-mask][nQidx] += q.iQubits[currState][Qidx];

			q.rQubits[currState][nQidx] += 0-q.rQubits[currState][Qidx];
			q.iQubits[currState][nQidx] += q.iQubits[currState][Qidx];
		}				
		else
		{
			q.rQubits[currState+mask][nQidx] += q.rQubits[currState][Qidx];
			q.iQubits[currState+mask][nQidx] += q.iQubits[currState][Qidx];

			q.rQubits[currState][nQidx] += q.rQubits[currState][Qidx];
			q.iQubits[currState][nQidx] += q.iQubits[currState][Qidx];
		}

	}

	function qc_0(uint256 mask, uint256 currState, Qubit memory q, uint8 Qidx) internal pure 
	{
		uint8 nQidx = (Qidx == 0)?1:0;

		if ((mask & currState) == 0)
		{
			q.rQubits[currState][nQidx] += q.rQubits[currState][Qidx];
			q.iQubits[currState][nQidx] += q.iQubits[currState][Qidx];
		}
	}

	function qc_1(uint256 mask, uint256 currState, Qubit memory q, uint8 Qidx) internal pure 
	{
		uint8 nQidx = (Qidx == 0)?1:0;

		if ((mask & currState) == mask)
		{
			q.rQubits[currState][nQidx] += q.rQubits[currState][Qidx];
			q.iQubits[currState][nQidx] += q.iQubits[currState][Qidx];
		}
	}

	function qc_X(uint256 mask, uint256 currState, Qubit memory q, uint8 Qidx) internal pure 
	{
		uint8 nQidx = (Qidx == 0)?1:0;

		if ((mask & currState) != 0)
		{
			q.rQubits[currState-mask][nQidx] += q.rQubits[currState][Qidx];
			q.iQubits[currState-mask][nQidx] += q.iQubits[currState][Qidx];
		}
		else
		{
			q.rQubits[currState+mask][nQidx] += q.rQubits[currState][Qidx];
			q.iQubits[currState+mask][nQidx] += q.iQubits[currState][Qidx];
		}
	}

	function qc_Y(uint256 mask, uint256 currState, Qubit memory q, uint8 Qidx) internal pure 
	{
		uint8 nQidx = (Qidx == 0)?1:0;

		if ((mask & currState) != 0)
		{
			q.rQubits[currState-mask][nQidx] += q.iQubits[currState][Qidx];
			q.iQubits[currState-mask][nQidx] += 0-q.rQubits[currState][Qidx];
		}
		else
		{
			q.rQubits[currState+mask][nQidx] += 0-q.iQubits[currState][Qidx];
			q.iQubits[currState+mask][nQidx] += q.rQubits[currState][Qidx];
		}
	}

	function qc_Z(uint256 mask, uint256 currState, Qubit memory q, uint8 Qidx) internal pure 
	{
		uint8 nQidx = (Qidx == 0)?1:0;

		if ((mask & currState) != 0)
		{
			q.rQubits[currState][nQidx] += 0-q.rQubits[currState][Qidx];
			q.iQubits[currState][nQidx] += 0-q.iQubits[currState][Qidx];
		}
		else
		{
			q.rQubits[currState][nQidx] += q.rQubits[currState][Qidx];
			q.iQubits[currState][nQidx] += q.iQubits[currState][Qidx];
		}
	}

	function qc_I(uint256 currState, Qubit memory q, uint8 Qidx) internal pure 
	{
		uint8 nQidx = (Qidx == 0)?1:0;
		q.rQubits[currState][nQidx] += q.rQubits[currState][Qidx];
		q.iQubits[currState][nQidx] += q.iQubits[currState][Qidx];
	}

	function qc_CN(uint256 cMask, uint256 mask, uint256 currState, Qubit memory q, uint8 Qidx) internal pure 
	{
		uint8 nQidx = (Qidx == 0)?1:0;
		if (((cMask & currState) == cMask) && (cMask != 0))
		{
			if ((mask & currState) != 0)
			{
				q.rQubits[currState-mask][nQidx] += q.rQubits[currState][Qidx];
				q.iQubits[currState-mask][nQidx] += q.iQubits[currState][Qidx];
			}
			else
			{
				q.rQubits[currState+mask][nQidx] += q.rQubits[currState][Qidx];
				q.iQubits[currState+mask][nQidx] += q.iQubits[currState][Qidx];
			}
		}
		else
		{
			q.rQubits[currState][nQidx] += q.rQubits[currState][Qidx];
			q.iQubits[currState][nQidx] += q.iQubits[currState][Qidx];
		}

	}

	function qc_CP(uint256 cMask, uint256 mask, uint256 currState, Qubit memory q, uint8 Qidx) internal pure 
	{
		uint8 nQidx = (Qidx == 0)?1:0;
		if ((cMask & currState) == cMask) // allow cMask == 0 ==> just P, not CP
		{
			if ((mask & currState) != 0)
			{
				q.rQubits[currState][nQidx] += 0-q.iQubits[currState][Qidx];
				q.iQubits[currState][nQidx] += q.rQubits[currState][Qidx];
			}
			else
			{
				q.rQubits[currState][nQidx] += q.rQubits[currState][Qidx];
				q.iQubits[currState][nQidx] += q.iQubits[currState][Qidx];
			}
		}
		else
		{
			q.rQubits[currState][nQidx] += q.rQubits[currState][Qidx];
			q.iQubits[currState][nQidx] += q.iQubits[currState][Qidx];
		}

	}

	function qc_Cp(uint256 cMask, uint256 mask, uint256 currState, Qubit memory q, uint8 Qidx) internal pure 
	{
		uint8 nQidx = (Qidx == 0)?1:0;
		if ((cMask & currState) == cMask) // allow cMask == 0 ==> just p, not Cp
		{
			if ((mask & currState) != 0)
			{
				q.rQubits[currState][nQidx] += q.iQubits[currState][Qidx];
				q.iQubits[currState][nQidx] += 0-q.rQubits[currState][Qidx];
			}
			else
			{
				q.rQubits[currState][nQidx] += q.rQubits[currState][Qidx];
				q.iQubits[currState][nQidx] += q.iQubits[currState][Qidx];
			}
		}
		else
		{
			q.rQubits[currState][nQidx] += q.rQubits[currState][Qidx];
			q.iQubits[currState][nQidx] += q.iQubits[currState][Qidx];
		}

	}

	function qc_CT(uint256 cMask, uint256 mask, uint256 currState, Qubit memory q, uint8 Qidx) internal pure returns (uint8) 
	{
		// e^{i*pi/4} = ((1+i)/sqrt(2))
		uint8 nQidx = (Qidx == 0)?1:0;
		uint8 ret = 0;
		if ((cMask & currState) == cMask) // allow cMask == 0 ==> just T, not CT
		{
			if ((mask & currState) != 0)
			{
				q.rQubits[currState][nQidx] += (q.rQubits[currState][Qidx]-q.iQubits[currState][Qidx]);
				q.iQubits[currState][nQidx] += (q.rQubits[currState][Qidx]+q.iQubits[currState][Qidx]);
				ret = 1;
			}
			else
			{
				q.rQubits[currState][nQidx] += q.rQubits[currState][Qidx];
				q.iQubits[currState][nQidx] += q.iQubits[currState][Qidx];
			}
		}
		else
		{
			q.rQubits[currState][nQidx] += q.rQubits[currState][Qidx];
			q.iQubits[currState][nQidx] += q.iQubits[currState][Qidx];
		}

		return ret;
	}

	function qc_Ct(uint256 cMask, uint256 mask, uint256 currState, Qubit memory q, uint8 Qidx) internal pure returns (uint8) 
	{
		// e^{-i*pi/4} = ((1-i)/sqrt(2))
		uint8 nQidx = (Qidx == 0)?1:0;
		uint8 ret = 0;
		if ((cMask & currState) == cMask) // allow cMask == 0 ==> just t, not Ct
		{
			if ((mask & currState) != 0)
			{
				q.rQubits[currState][nQidx] += (q.rQubits[currState][Qidx]+q.iQubits[currState][Qidx]);
				q.iQubits[currState][nQidx] += (0-q.rQubits[currState][Qidx]+q.iQubits[currState][Qidx]);
				ret = 1;
			}
			else
			{
				q.rQubits[currState][nQidx] += q.rQubits[currState][Qidx];
				q.iQubits[currState][nQidx] += q.iQubits[currState][Qidx];
			}
		}
		else
		{
			q.rQubits[currState][nQidx] += q.rQubits[currState][Qidx];
			q.iQubits[currState][nQidx] += q.iQubits[currState][Qidx];
		}

		return ret;
	}

	function qc_exec(uint8 numQubits, bytes1[] memory qAlgo, Qubit memory q, uint256 randomSeed) internal view returns (uint8)
	{
		uint256 mask;
		uint256 i;
		uint256 j;
		uint8 Qidx = 0;

		uint256 maxj=(2**numQubits);
		mask = 1;
		mask <<= numQubits - 1;
		for (i=0;i<numQubits;i++)
		{
			uint8 nQidx;

			nQidx = (Qidx == 0)?1:0;
			for (j=0;j<maxj;j++)
			{
				q.rQubits[j][nQidx] = q.iQubits[j][nQidx] = 0;
			}
			if (qAlgo[i] == GATE_H)
			{
				for(j=0;j<maxj;j++)
				{
					if ((q.rQubits[j][Qidx]!=0) || (q.iQubits[j][Qidx] != 0))
						qc_H(mask,j,q,Qidx);
				}
			}
			else if ((qAlgo[i] == GATE_I) || (qAlgo[i] == GATE_C))
			{
				for(j=0;j<maxj;j++)
				{
					if ((q.rQubits[j][Qidx]!=0) || (q.iQubits[j][Qidx] != 0))
						qc_I(j,q,Qidx);
				}
			}
			else if (qAlgo[i] == GATE_X)
			{
				for(j=0;j<maxj;j++)
				{
					if ((q.rQubits[j][Qidx]!=0) || (q.iQubits[j][Qidx] != 0))
						qc_X(mask,j,q,Qidx);
				}
			}
			else if (qAlgo[i] == GATE_Y)
			{
				for(j=0;j<maxj;j++)
				{
					if ((q.rQubits[j][Qidx]!=0) || (q.iQubits[j][Qidx] != 0))
						qc_Y(mask,j,q,Qidx);
				}
			}
			else if (qAlgo[i] == GATE_Z)
			{
				for(j=0;j<maxj;j++)
				{
					if ((q.rQubits[j][Qidx]!=0) || (q.iQubits[j][Qidx] != 0))
						qc_Z(mask,j,q,Qidx);
				}
			}
			else if (qAlgo[i] == GATE_m)
			{
				uint256 k = 0;
				//nQidx = (Qidx == 0)?1:0;
				for (j = 0; j < maxj; j++)
				{
					q.rQubits[j][nQidx] = q.rQubits[j][Qidx];
					if (q.rQubits[j][nQidx] < 0)
						q.rQubits[j][nQidx] = 0 - q.rQubits[j][nQidx];
					q.iQubits[j][nQidx] = q.iQubits[j][Qidx];
					if (q.iQubits[j][nQidx] < 0)
						q.iQubits[j][nQidx] = 0 - q.iQubits[j][nQidx];
					q.rQubits[j][nQidx] += q.iQubits[j][nQidx];

					k += uint(q.rQubits[j][nQidx]);
				}
				j = getRandom(k,randomSeed)+1;
				k = 0;
				while (j > uint(q.rQubits[k][nQidx]))
				{
					j -= uint(q.rQubits[k++][nQidx]);
				}	
				for (j = 0; j < maxj; j++)
				{
					q.rQubits[j][nQidx] = q.iQubits[j][nQidx] = 0;
				}
				if ((k & mask) == 0)
				{
					for(j=0;j<maxj;j++)
					{
						if ((q.rQubits[j][Qidx]!=0) || (q.iQubits[j][Qidx] != 0))
							qc_0(mask,j,q,Qidx);
					}
				}
				else
				{
					for(j=0;j<maxj;j++)
					{
						if ((q.rQubits[j][Qidx]!=0) || (q.iQubits[j][Qidx] != 0))
							qc_1(mask,j,q,Qidx);
					}
				}
			}
			else if (qAlgo[i] == GATE_N)
			{
				uint256 tempVal = 1;
				tempVal <<= numQubits-1;
				uint256 cMask = 0;

				for (j=0;j<numQubits;j++)
				{
					if (qAlgo[j] == GATE_C)
						cMask += tempVal;
					tempVal>>=1;
				}
				for(j=0;j<maxj;j++)
				{
					if ((q.rQubits[j][Qidx]!=0) || (q.iQubits[j][Qidx] != 0))
						qc_CN(cMask,mask,j,q,Qidx);
				}
			}
			else if ((qAlgo[i] == GATE_P) || (qAlgo[i] == GATE_p))
			{
				uint256 tempVal = 1;
				tempVal <<= numQubits-1;
				uint256 cMask = 0;

				for (j=0;j<numQubits;j++)
				{
					if (qAlgo[j] == GATE_C)
						cMask += tempVal;
					tempVal>>=1;
				}
				for(j=0;j<maxj;j++)
				{
					if ((q.rQubits[j][Qidx]!=0) || (q.iQubits[j][Qidx] != 0))
					{
						if (qAlgo[i] == GATE_P)
							qc_CP(cMask,mask,j,q,Qidx);
						else
							qc_Cp(cMask,mask,j,q,Qidx);
					}
				}
			}
			else if ((qAlgo[i] == GATE_T) || (qAlgo[i] == GATE_t))
			{
				uint256 tempVal = 1;
				tempVal <<= numQubits-1;
				uint256 cMask = 0;
				uint8[MAX_IDX] memory phaseDone;
				
				for (j=0;j<numQubits;j++)
				{
					if (qAlgo[j] == GATE_C)
						cMask += tempVal;
					tempVal>>=1;
				}
				tempVal = 0;
				for(j=0;j<maxj;j++)
				{
					phaseDone[j] = 0;
					if ((q.rQubits[j][Qidx]!=0) || (q.iQubits[j][Qidx] != 0))
					{
						if (qAlgo[i] == GATE_T)
							phaseDone[j] = qc_CT(cMask,mask,j,q,Qidx);
						else
							phaseDone[j] = qc_Ct(cMask,mask,j,q,Qidx);
						if (phaseDone[j] > 0)
							tempVal = 1;
					}
				}
				if (tempVal > 0)
				{
					for(j=0;j<maxj;j++)
					{
						if (phaseDone[j]==0)
						{
							q.rQubits[j][nQidx]*= 10;
							q.iQubits[j][nQidx]*= 10;
						}
						else
						{
							q.rQubits[j][nQidx]*= 7;
							q.iQubits[j][nQidx]*= 7;
						}
					}
				}
			}
			else
			{
				revert("Unknown or unsupported gate");
			}
			mask >>=1;
			Qidx = nQidx;
		}
		if (Qidx == 1)
			for (j=0;j<2**numQubits;j++)
			{
				q.rQubits[j][0] = q.rQubits[j][1];
				q.iQubits[j][0] = q.iQubits[j][1];
			}
				
		return numQubits;
	}

	function checkLicense(uint8 numQubits) internal pure returns (uint8)
	{
		if (numQubits > MAX_QUBITS)
			revert("Check subscription");
		return 0;
	}

	function runQScript(uint8 numQubits, string memory s, uint256 randomSeed) public view returns (uint256) 
	{
		Qubit memory q;
		bytes1[] memory nextGate;
		uint256 ret = 0;
		bool done = false;
		uint256 i = 0;
		uint256 j;
		uint256 slen = bytes(s).length; 

		checkLicense(numQubits);
		for (i=0;i<(2**numQubits);i++)
		{
			q.rQubits[i][0] = q.rQubits[i][1] = q.iQubits[i][0] = q.iQubits[i][1] = 0;
		}
		q.rQubits[0][0] = 1; // start with all qubits = 0;
	
		nextGate = new bytes1[](numQubits);
		i = 0;

		while (!done)
		{
			if (i + numQubits > slen)
			{
				if (bytes(s)[i] == DELIM_END)
				{
					done = true;
				}
				else
				{
					done = true;
					//revert("unexpected end-of-algo without .");
				}
			}
			else
			{
				for (j = 0;j < numQubits;j++)
				{
					nextGate[j] = bytes(s)[i++];
				}	
				numQubits = qc_exec(numQubits,nextGate,q,randomSeed);
				if (i < slen)
				{
					if (bytes(s)[i] == DELIM_END)
					{
						done = true;
					}
					else
						i++;
				}
				else
				{
					done = true;
					//revert("unexpected end-of-algo without .");
				}
				

			}
		}

		// measure in the computational basis

		i = 0;
		for (j = 0; j < (2**numQubits); j++)
		{
			if (q.rQubits[j][0] < 0)
				q.rQubits[j][0] = 0 - q.rQubits[j][0];
			if (q.iQubits[j][0] < 0)
				q.iQubits[j][0] = 0 - q.iQubits[j][0];

			i += uint(q.rQubits[j][0]);
		}
		j = getRandom(i,randomSeed)+1;
		ret = 0;
		while (j > uint(q.rQubits[ret][0]))
		{
			j -= uint(q.rQubits[ret++][0]);
		}	

		return ret;
			
	}

    function getGatesNames() external view returns (string[] memory) {
		return gatesNames;
	}

    function getNumberOfQubits() external pure returns (uint8) {
		return MAX_QUBITS;
	}

    function isSimulator() external pure returns (bool) {
		return true;
	}

    function isQPU() external pure returns (bool) {
		return false;
	}

	function getName() external pure returns (string memory) {
		return "pqcee_simulator";
	}

}
