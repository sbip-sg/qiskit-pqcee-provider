// SPDX-License-Identifier: MIT 
/*

Name: QuantumBackendInterface
Description: An on-chain quantum backend interface running in an EVM smart contract
Author: Ciocirlan Stefan-Dan (sdcioc)
Date: Oct 2023

MIT License

*/

pragma solidity ^0.8.17;


interface IQuantumBackend
{
    function getGatesNames() external view returns (string[] memory);

    function getNumberOfQubits() external pure returns (uint8);

    function isSimulator() external pure returns (bool);

    function isQPU() external pure returns (bool);

    function getName() external pure returns (string memory);

    function runQScript(uint8 numQubits, string memory s, uint256 randomSeed) external view returns (uint256);

}
