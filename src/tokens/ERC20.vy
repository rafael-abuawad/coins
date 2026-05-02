# pragma version ==0.4.3
# pragma nonreentrancy on
"""
@title `erc20` - ERC20 Coins implementation
@custom:contract-name erc20
@license MIT
@author Rafael Abuawad <@rafael-abuawad>
@notice This code is for testing purposes only, is not production ready and is not audited.
        Everything is subject to change. Use at your own risk.
"""


interface ICoins:
    def name(id: uint256) -> String[25]: view
    def symbol(id: uint256) -> String[5]: view
    def decimals(id: uint256) -> uint8: view
    def totalSupply(id: uint256) -> uint256: view
    def balanceOf(id: uint256, owner: address) -> uint256: view
    def allowance(
        id: uint256, owner: address, spender: address
    ) -> uint256: view
    def owner(id: uint256) -> address: view
    def transfer(
        id: uint256, caller: address, to: address, amount: uint256
    ) -> bool: nonpayable
    def transferFrom(
        id: uint256,
        caller: address,
        owner: address,
        to: address,
        amount: uint256,
    ) -> bool: nonpayable
    def approve(
        id: uint256, caller: address, spender: address, allowance: uint256
    ) -> bool: nonpayable
    def mint(
        id: uint256, caller: address, to: address, amount: uint256
    ): nonpayable
    def burnFrom(
        id: uint256, caller: address, owner: address, amount: uint256
    ): nonpayable
    def burn(id: uint256, caller: address, amount: uint256): nonpayable
    def transferOwnership(
        id: uint256, caller: address, new_owner: address
    ): nonpayable
    def renounceOwnership(id: uint256, caller: address): nonpayable


event Transfer:
    _from: indexed(address)
    _to: indexed(address)
    _amount: uint256


event Approval:
    _owner: indexed(address)
    _spender: indexed(address)
    _allowance: uint256


event OwnershipTransferred:
    _previous_owner: indexed(address)
    _new_owner: indexed(address)


COINS: immutable(ICoins)
ID: immutable(uint256)


@deploy
def __init__(coins: address):
    COINS = ICoins(coins)
    ID = convert(self, uint256)
    log OwnershipTransferred(
        _previous_owner=empty(address), _new_owner=msg.sender
    )


@view
@external
def name() -> String[25]:
    return staticcall COINS.name(ID)


@view
@external
def symbol() -> String[5]:
    return staticcall COINS.symbol(ID)


@view
@external
def decimals() -> uint8:
    return staticcall COINS.decimals(ID)


@view
@external
def totalSupply() -> uint256:
    return staticcall COINS.totalSupply(ID)


@view
@external
def balanceOf(owner: address) -> uint256:
    return staticcall COINS.balanceOf(ID, owner)


@view
@external
def allowance(owner: address, spender: address) -> uint256:
    return staticcall COINS.allowance(ID, owner, spender)


@view
@external
def owner() -> address:
    return staticcall COINS.owner(ID)


@external
def transfer(to: address, amount: uint256) -> bool:
    log Transfer(_from=msg.sender, _to=to, _amount=amount)
    return extcall COINS.transfer(ID, msg.sender, to, amount)


@external
def transferFrom(_from: address, to: address, amount: uint256) -> bool:
    log Transfer(_from=_from, _to=to, _amount=amount)
    return extcall COINS.transferFrom(ID, msg.sender, _from, to, amount)


@external
def approve(spender: address, allowance: uint256) -> bool:
    log Approval(_owner=msg.sender, _spender=spender, _allowance=allowance)
    return extcall COINS.approve(ID, msg.sender, spender, allowance)


@external
def mint(to: address, amount: uint256):
    log Transfer(_from=empty(address), _to=to, _amount=amount)
    extcall COINS.mint(ID, msg.sender, to, amount)


@external
def burn(amount: uint256):
    log Transfer(_from=msg.sender, _to=empty(address), _amount=amount)
    extcall COINS.burn(ID, msg.sender, amount)


@external
def burnFrom(owner: address, amount: uint256):
    log Transfer(_from=msg.sender, _to=empty(address), _amount=amount)
    extcall COINS.burnFrom(ID, msg.sender, owner, amount)


@external
def transferOwnership(new_owner: address):
    log OwnershipTransferred(_previous_owner=msg.sender, _new_owner=new_owner)
    extcall COINS.transferOwnership(ID, msg.sender, new_owner)


@external
def renounceOwnership():
    log OwnershipTransferred(
        _previous_owner=msg.sender, _new_owner=empty(address)
    )
    extcall COINS.renounceOwnership(ID, msg.sender)
