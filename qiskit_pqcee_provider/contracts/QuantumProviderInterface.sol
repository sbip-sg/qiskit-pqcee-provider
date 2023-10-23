// SPDX-License-Identifier: MIT 
/*

Name: QuantumProviderInterface
Description: An on-chain quantum provider interface running in an EVM smart contract
Author: Ciocirlan Stefan-Dan (sdcioc)
Date: Oct 2023

MIT License

*/

pragma solidity ^0.8.17;


interface IQuantumProvider
{
    function getBackends() external view returns (address[] memory);
}
