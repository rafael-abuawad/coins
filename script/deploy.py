from moccasin.boa_tools import VyperContract
from src import Coins
from src.tokens import erc20


def deploy() -> VyperContract:
    token_blueprint = erc20.deploy_as_blueprint()
    coins = Coins.deploy(token_blueprint.address)

    print("Token blueprint:", token_blueprint.address)
    print("Coins registry:", coins.address)

    return coins


def moccasin_main() -> VyperContract:
    return deploy()
