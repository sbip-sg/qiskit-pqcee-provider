// SPDX-License-Identifier: MIT 
/*

Name: QuantumProviderContract
Description: An on-chain quantum provider running in an EVM smart contract
Author: Ciocirlan Stefan-Dan (sdcioc)
Date: Oct 2023

MIT License

*/

pragma solidity ^0.8.17;

import "./QuantumProviderInterface.sol";

contract QuantumProvider is IQuantumProvider
{
    event LogBackendRegistered(address backend);
    event LogBackendUnregistered(address backend);

	address public owner;
    uint8 constant MAX_BACKENDS=16;
    address[] public backends;

	constructor() 
	{
		owner = msg.sender;
    }

	function addBackend(address backend) public
	{
		require(msg.sender == owner, "Owner only");
	
		if (backends.length < MAX_BACKENDS)
        {
            backends.push(backend);
            emit LogBackendRegistered(backend);
        }
	}

    function deleteBackend(address backend) public
	{
		require(msg.sender == owner, "Owner only");
	
		for (uint index=0; index < backends.length; index++)
        {
            if (backends[index] == backend)
            {
                backends[index] = backends[backends.length - 1];
                backends.pop();
                emit LogBackendUnregistered(backend);
                break;
            }
        }
	}

    function getBackends() external view returns (address[] memory)
    {
        address[] memory return_backends = new address[](backends.length);
        for (uint index=0; index < backends.length; index++)
        {
            return_backends[index] = backends[index];
        }
        // return only the vlaid adressess
        return return_backends;
    }

}
