from eth_account import Account
import secrets
import configparser
import web3
from web3.middleware import construct_sign_and_send_raw_middleware
from web3.middleware import geth_poa_middleware
from web3.exceptions import InvalidTransaction
import pathlib
from solcx import compile_source
import logging

logger = logging.getLogger(__name__)


def save_config(config: configparser.ConfigParser, filename: str):
    r"""
    Save the configuration to the file.

    Args:
        config : The configuration.
        filename : The filename.

    Returns:
        None
    """
    mod_path = pathlib.Path(__file__).parent.absolute()
    absolute_path = (
        mod_path / filename
    ).resolve()
    with open(absolute_path, 'w') as configfile:
        config.write(configfile)
    logger.info("FILE SAVED: %s", absolute_path)


def save_credentials(
    config: configparser.ConfigParser
):
    r"""
    Save the credentials to the file.

    Args:
        config : The configuration.

    Returns:
        None
    """
    save_config(config, "mumbai_testnet_credential.ini")


def save_provider(
    config: configparser.ConfigParser
):
    r"""
    Save the provider to the file.

    Args:
        config : The configuration.

    Returns:
        None
    """
    save_config(config, "mumbai_testnet_provider.ini")


def setup_provider_contract(
    web3_provider: web3.Web3,
) -> (str, str):
    r"""
    Setup the provider smart contract on the given web3 provider.

    Args:
        web3_provider : The web3 provider.

    Returns:
        The provider contract address and the abi.

    Raises:
        InvalidTransaction: If there is not enough MATIC in the account.
    """
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
        output_values=['abi', 'bin'],
        evm_version='paris'
    )
    # first the interface
    contract_id, contract_interface = compiled_sol.popitem()
    # second the contract
    contract_id, contract_interface = compiled_sol.popitem()
    abi = contract_interface['abi']
    bytecode = contract_interface['bin']
    # print(bytecode)
    provider_contract = web3_provider.eth.contract(
        abi=abi,
        bytecode=bytecode
    )
    gas_needed = provider_contract.constructor().estimate_gas()
    logger.info("Provider gas needed: %s", gas_needed)
    mumbai_balance = web3_provider.eth.get_balance(
        web3_provider.eth.default_account
    )
    if gas_needed > mumbai_balance:
        logger.error(
            "Requesting MATIC from the mumbai testnet for address:",
            web3_provider.eth.default_account,
            " on https://mumbaifaucet.com/"
        )
        raise InvalidTransaction("Not enough MATIC")
    tx_hash = provider_contract.constructor().transact()
    tx_receipt = web3_provider.eth.wait_for_transaction_receipt(tx_hash)
    provider_contract_address = tx_receipt.contractAddress
    logger.info("Provider contract address: %s", provider_contract_address)

    return (provider_contract_address, abi)


def setup_backend_contract(
    web3_provider: web3.Web3,
    provider_contract: web3.contract.Contract,
) -> None:
    r"""
    Setup the backend smart contract on the given web3 provider.
    And register the backend address with the local provider.

    Args:
        web3_provider : The web3 provider.
        provider_contract : The provider contract.

    Returns:
        None

    Raises:
        InvalidTransaction: If there is not enough MATIC in the account.
    """
    mod_path = pathlib.Path(__file__).parent.absolute()
    absolute_path = (
        mod_path / "contracts" / "QuantumBackendContract.sol"
    ).resolve()
    base_path = (
        mod_path / "contracts"
    ).resolve()
    sc_backend_code = absolute_path.read_text()
    compiled_sol = compile_source(
        sc_backend_code,
        base_path=base_path,
        output_values=['abi', 'bin'],
        evm_version='paris'
    )
    # first the interface
    contract_id, contract_interface = compiled_sol.popitem()
    # than the smart contract
    contract_id, contract_interface = compiled_sol.popitem()
    abi = contract_interface['abi']
    bytecode = contract_interface['bin']
    backend_contract = web3_provider.eth.contract(
        abi=abi,
        bytecode=bytecode
    )
    gas_needed = backend_contract.constructor().estimate_gas()
    logger.info("Backend gas needed: %s", gas_needed)
    mumbai_balance = web3_provider.eth.get_balance(
        web3_provider.eth.default_account
    )
    if gas_needed > mumbai_balance:
        logger.error(
            "Requesting MATIC from the mumbai testnet for address:",
            web3_provider.eth.default_account,
            " on https://mumbaifaucet.com/"
        )
        raise InvalidTransaction("Not enough MATIC")
    tx_hash = backend_contract.constructor().transact()
    tx_receipt = web3_provider.eth.wait_for_transaction_receipt(tx_hash)
    backend_address = tx_receipt.contractAddress

    # register the backend adress with the local provider
    gas_needed = provider_contract.functions.addBackend(
        backend_address
    ).estimate_gas()
    logger.info("addBackend gas needed: %s", gas_needed)
    mumbai_balance = web3_provider.eth.get_balance(
        web3_provider.eth.default_account
    )
    if gas_needed > mumbai_balance:
        logger.error(
            "Requesting MATIC from the mumbai testnet for address:",
            web3_provider.eth.default_account,
            " on https://mumbaifaucet.com/"
        )
        raise InvalidTransaction("Not enough MATIC")
    tx_hash = (
        provider_contract.functions.addBackend(backend_address).transact()
    )
    tx_receipt = web3_provider.eth.wait_for_transaction_receipt(tx_hash)
    logger.info("Backend contract address: %s", backend_address)


def setup_mumbai_testnet():
    r"""
    Setup the an account on the mumbai testnet togheter with a provider
    contract and a backend contract.

    Args:
        None

    Returns:
        None
    """
    credential_config = configparser.ConfigParser(allow_no_value=True)

    # ge tthe current directory
    mod_path = pathlib.Path(__file__).parent.absolute()

    credential_absolute_path = (
        mod_path / "mumbai_testnet_credential.ini"
    ).resolve()
    credential_config.read(credential_absolute_path)
    logger.info("credentials READ: %s", credential_absolute_path)

    # create the wallet account if it doesn't exist
    private_key = None
    account_address = None
    if 'user' in credential_config:
        if 'private_key' in credential_config['user']:
            private_key = credential_config['user']['private_key']
        if 'account_address' in credential_config['user']:
            account_address = credential_config['user']['account_address']
    else:
        credential_config['user'] = {}

    if private_key is None:
        priv = secrets.token_hex(32)
        private_key = "0x" + priv
        credential_config['user']['private_key'] = private_key

    web3_account = Account.from_key(private_key)
    if account_address is None or account_address != web3_account.address:
        account_address = web3_account.address
        credential_config['user']['account_address'] = account_address

    logger.info("Account address: %s", web3_account.address)

    save_credentials(credential_config)

    provider_config = configparser.ConfigParser(allow_no_value=True)

    provider_absolute_path = (
        mod_path / "mumbai_testnet_config.ini"
    ).resolve()
    provider_config.read(provider_absolute_path)
    logger.info("Provider config READ: %s", provider_absolute_path)

    # verify if there are contracts already deployed
    provider_contract_address = None
    if 'mumbai' in provider_config:
        if 'provider_address' in provider_config['mumbai']:
            provider_contract_address = (
                provider_config['mumbai']['provider_address']
            )
    else:
        provider_config['mumbai'] = {}

    # working address for qeb3 https://rpc-mumbai.maticvigil.com/
    web3_provider = web3.Web3(
        web3.Web3.HTTPProvider(
            endpoint_uri='https://rpc-mumbai.maticvigil.com/'
        )
    )
    # setup de default account
    # setup the sigining as a middleware
    # add poa
    web3_provider.middleware_onion.inject(geth_poa_middleware, layer=0)
    # add account
    web3_provider.middleware_onion.add(
        construct_sign_and_send_raw_middleware(web3_account)
    )
    web3_provider.eth.default_account = web3_account.address
    # verify the balance
    mumbai_balance = web3_provider.eth.get_balance(account_address)
    logger.info("Mumbai balance: %s", mumbai_balance)
    provider_contract = None
    # get the current provider contract if it exists
    if provider_contract_address is not None:
        relative_path = (
            mod_path / "contracts" / "QuantumProviderInterface.sol"
        ).resolve()
        sc_interface_code = relative_path.read_text()
        compiled_sol = compile_source(sc_interface_code, output_values=['abi'])
        contract_id, contract_interface = compiled_sol.popitem()
        abi = contract_interface['abi']
        provider_contract = web3_provider.eth.contract(
            address=provider_contract_address,
            abi=abi
        )
    logger.info("Provider contract address: %s", provider_contract_address)

    # get the backends register with the provider
    web3_backends = []
    if provider_contract is not None:
        web3_backends = provider_contract.functions.getBackends().call()
    logger.info("Backends: %s", web3_backends)

    # deploy the provider contract if it doesn't exist
    # or it does not have backends registered
    # deploy a backend contract and register it with the provider
    if len(web3_backends) == 0:
        try:
            # deploy the provider contract if it doesn't exist
            # or it does not have backends
            (provider_contract_address, abi) = setup_provider_contract(
                web3_provider=web3_provider
            )
            provider_config['mumbai']['provider_address'] = (
                provider_contract_address
            )
            provider_contract = web3_provider.eth.contract(
                address=provider_contract_address,
                abi=abi
            )
            # deploy the backend contract and register address in the
            # provider
            setup_backend_contract(
                web3_provider=web3_provider,
                provider_contract=provider_contract
            )
        except InvalidTransaction:
            exit(-1)

    save_provider(provider_config)


if __name__ == "__main__":
    setup_mumbai_testnet()
