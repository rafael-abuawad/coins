import pytest
import boa
from src import Coins
from src.tokens import erc20


@pytest.fixture()
def bob():
    addr = boa.env.generate_address()
    boa.env.set_balance(addr, 10**18)
    return addr


@pytest.fixture()
def alice():
    addr = boa.env.generate_address()
    boa.env.set_balance(addr, 10**18)
    return addr


@pytest.fixture()
def charlie():
    addr = boa.env.generate_address()
    boa.env.set_balance(addr, 10**18)
    return addr


@pytest.fixture
def token_blueprint():
    return erc20.deploy_as_blueprint()


@pytest.fixture
def coins_contract(token_blueprint):
    return Coins.deploy(token_blueprint.address)


@pytest.fixture
def deploy_erc20(coins_contract):
    """
    Returns a callable (creator, name, symbol, decimals) -> ERC20 wrapper
    after Coins.create under the creator's prank.
    """

    def _deploy(
        creator,
        name: str = "Wrapped Ether",
        symbol: str = "WETH",
        decimals: int = 18,
        initial_supply: int = 0,
    ):
        with boa.env.prank(creator):
            token_addr = coins_contract.create(name, symbol, decimals, initial_supply)
        return erc20.at(token_addr)

    return _deploy
