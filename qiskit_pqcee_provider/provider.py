from qiskit.providers import ProviderV1 as Provider
from qiskit.providers.providerutils import filter_backends

from .backend import BlockchainBackend

import web3
import pathlib
from solcx import compile_source
import configparser
from web3.middleware import geth_poa_middleware


class BlockchainProvider(Provider):
    r"""
    Thq quantum provider on the blockchain.
    """

    web3_provider: web3.Web3 = None
    r"""
    The web3 provider for the blockchain.
    """
    web3_contract: web3.contract.Contract = None
    r"""
    The provider smart contract.
    """

    def __init__(
        self,
        web3_provider: web3.Web3,
        provider_address: str,
        is_local: bool = False,
        basic_approx_depth: int = 3,
        skd_recursion_degree: int = 3
    ):
        r"""
        Args:
            web3_provider: The web3 provider for the blockchain.
            provider_address: The address of the provider smart contract.
            is_local: If the provider is local or not.
            basic_approx_depth: The basic approximation depth.
            skd_recursion_degree: The skd recursion degree.
        """
        super().__init__()
        self.web3_provider = web3_provider
        # compile the provider interface for the abi
        mod_path = pathlib.Path(__file__).parent.absolute()
        absolute_path = (
            mod_path / "contracts" / "QuantumProviderInterface.sol"
        ).resolve()
        sc_interface_code = absolute_path.read_text()
        compiled_sol = compile_source(sc_interface_code, output_values=['abi'])
        contract_id, contract_interface = compiled_sol.popitem()
        abi = contract_interface['abi']
        # connect to provider contract
        self.web3_contract = self.web3_provider.eth.contract(
            address=provider_address,
            abi=abi
        )
        # getting the backend addresses from the provider contract
        web3_backends = self.web3_contract.functions.getBackends().call()

        self._backends = [
            BlockchainBackend(
                provider=self,
                web3_provider=web3_provider,
                backend_address=backend_address,
                is_local=is_local,
                backend_seed=0,
                basic_approx_depth=basic_approx_depth,
                skd_recursion_degree=skd_recursion_degree
            )
            for backend_address in web3_backends
        ]

    def backends(self, name=None, **kwargs):
        backends = self._backends
        if name:
            backends = [
                backend for backend in self._backends if backend.name == name]
        return filter_backends(backends, filters=None, **kwargs)


class LocalPqceeProvider(BlockchainProvider):
    r"""
    The local quantum provider on the blockchain usyng pyevm.
    """

    def __init__(
        self,
        basic_approx_depth: int = 3,
        skd_recursion_degree: int = 3
    ):
        """
        Args:
            basic_approx_depth: The basic approximation depth.
            skd_recursion_degree: The skd recursion degree.
        """
        web3_provider = web3.Web3(web3.Web3.EthereumTesterProvider())
        web3_account = web3_provider.eth.accounts[0]
        web3_provider.eth.default_account = web3_account

        # register the provider smart contract
        mod_path = pathlib.Path(__file__).parent.absolute()
        absolute_path = (
            mod_path / "contracts" / "QuantumProviderContract.sol"
        ).resolve()
        base_path = (
            mod_path / "contracts"
        ).resolve()
        sc_provider_code = absolute_path.read_text()
        compiled_sol = compile_source(
            sc_provider_code,
            base_path=base_path,
            output_values=['abi', 'bin']
        )
        # interface
        contract_id, contract_interface = compiled_sol.popitem()
        # the contract
        contract_id, contract_interface = compiled_sol.popitem()
        abi = contract_interface['abi']
        bytecode = contract_interface['bin']
        provider_contract = web3_provider.eth.contract(
            abi=abi,
            bytecode=bytecode
        )
        # deploy the contract
        tx_hash = provider_contract.constructor().transact()
        tx_receipt = web3_provider.eth.wait_for_transaction_receipt(tx_hash)
        provider_address = tx_receipt.contractAddress
        # connect to the contract
        provider_contract = web3_provider.eth.contract(
            address=provider_address,
            abi=abi
        )
        # register the backend smart contract
        mod_path = pathlib.Path(__file__).parent.absolute()
        absolute_path = (
            mod_path / "contracts" / "QuantumBackendContract.sol"
        ).resolve()
        sc_backend_code = absolute_path.read_text()
        compiled_sol = compile_source(
            sc_backend_code,
            base_path=base_path,
            output_values=['abi', 'bin']
        )
        # interface
        contract_id, contract_interface = compiled_sol.popitem()
        # the contract
        contract_id, contract_interface = compiled_sol.popitem()
        abi = contract_interface['abi']
        bytecode = contract_interface['bin']
        backend_contract = web3_provider.eth.contract(
            abi=abi,
            bytecode=bytecode
        )
        # deploy the contract
        tx_hash = backend_contract.constructor().transact()
        tx_receipt = web3_provider.eth.wait_for_transaction_receipt(tx_hash)
        backend_address = tx_receipt.contractAddress

        # register the backend adress with the local provider
        tx_hash = (
            provider_contract.functions.addBackend(backend_address).transact()
        )
        tx_receipt = web3_provider.eth.wait_for_transaction_receipt(tx_hash)

        super().__init__(
            web3_provider=web3_provider,
            provider_address=provider_address,
            is_local=True,
            basic_approx_depth=basic_approx_depth,
            skd_recursion_degree=skd_recursion_degree
        )


class PqceeProvider(BlockchainProvider):
    r"""
    The quantum provider from pQCee on the blockchain using mumbai testnet.
    """

    def __init__(
        self,
        basic_approx_depth: int = 3,
        skd_recursion_degree: int = 3
    ):
        """
        Args:
            basic_approx_depth: The basic approximation depth.
            skd_recursion_degree: The skd recursion degree.
        """
        # read the config file
        config = configparser.ConfigParser(allow_no_value=True)
        mod_path = pathlib.Path(__file__).parent.absolute()
        absolute_path = (
            mod_path / "mumbai_testnet_config.ini"
        ).resolve()
        config.read(absolute_path)
        # verify if there are contracts already deployed
        provider_address = None
        if 'mumbai' in config:
            if 'provider_address' in config['mumbai']:
                provider_address = config['mumbai']['provider_address']
            else:
                raise Exception("No provider address in config file")
        else:
            raise Exception("No mumbai in config file")

        # working connection on web3 https://rpc-mumbai.maticvigil.com/
        web3_provider = web3.Web3(
            web3.Web3.HTTPProvider(
                endpoint_uri='https://rpc-mumbai.maticvigil.com/'
            )
        )
        # setup poa
        web3_provider.middleware_onion.inject(geth_poa_middleware, layer=0)

        super().__init__(
            web3_provider=web3_provider,
            provider_address=provider_address,
            is_local=False,
            basic_approx_depth=basic_approx_depth,
            skd_recursion_degree=skd_recursion_degree
        )
