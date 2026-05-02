from moccasin.boa_tools import VyperContract
from moccasin.config import get_active_network
from src import Coins
from src.tokens import erc20


def deploy() -> VyperContract:
    active_network = get_active_network()

    print("\t 📘 Deploying token blueprint...")
    token_blueprint = erc20.at("0xA0aC4fc6ed42A5d1ABA1a8fE1C5b66168A29b33E")
    print("- Verifying token blueprint...")
    active_network.moccasin_verify(token_blueprint)
    print("- Token blueprint verified ✓")

    print("\t 🪙 Deploying coins registry...")
    coins = Coins.at("0x0d3508A5bEB6DbF4C67282c38fb08674Ae2d1280")
    print("- Verifying coins registry...")
    active_network.moccasin_verify(coins)
    print("- Coins registry verified ✓")

    return coins


def moccasin_main() -> VyperContract:
    return deploy()
