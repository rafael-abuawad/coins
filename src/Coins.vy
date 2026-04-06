# pragma version ==0.4.3
# pragma nonreentrancy off


event TokenCreated:
    _id: indexed(uint256)
    _token: address


TOKEN_BLUEPRINT: immutable(address)

_names: HashMap[uint256, String[25]]
_symbols: HashMap[uint256, String[5]]
_decimals: HashMap[uint256, uint8]
_total_supply: HashMap[uint256, uint256]
_balances: HashMap[uint256, HashMap[address, uint256]]
_allowances: HashMap[uint256, HashMap[address, HashMap[address, uint256]]]
_is_minter: HashMap[uint256, HashMap[address, bool]]
_owners: HashMap[uint256, address]
_ids: HashMap[uint256, address]


@deploy
@payable
def __init__(_token_blueprint: address):
    TOKEN_BLUEPRINT = _token_blueprint


@view
@external
def name(id: uint256) -> String[25]:
    return self._names[id]


@view
@external
def symbol(id: uint256) -> String[5]:
    return self._symbols[id]


@view
@external
def decimals(id: uint256) -> uint8:
    return self._decimals[id]


@view
@external
def totalSupply(id: uint256) -> uint256:
    return self._total_supply[id]


@view
@external
def balanceOf(id: uint256, owner: address) -> uint256:
    return self._balances[id][owner]


@view
@external
def allowance(id: uint256, owner: address, spender: address) -> uint256:
    return self._allowances[id][owner][spender]


@view
@external
def isMinter(id: uint256, account: address) -> bool:
    return self._is_minter[id][account]


@view
@external
def owner(id: uint256) -> address:
    return self._owners[id]


@view
@external
def id(id: uint256) -> address:
    return self._ids[id]


@external
def transfer(
    id: uint256, caller: address, to: address, amount: uint256
) -> bool:
    self._checkCallerIsToken(id)
    assert to != empty(address), "coin:cannot transfer to empty address"
    self._balances[id][caller] -= amount
    self._balances[id][to] += amount
    return True


@external
def transferFrom(
    id: uint256, caller: address, _from: address, to: address, amount: uint256
) -> bool:
    self._checkCallerIsToken(id)
    assert to != empty(address), "coins: cannot transfer to empty address"
    assert self._allowances[id][_from][caller] >= amount, "coins: allowance is not enough"
    assert self._balances[id][_from] >= amount, "coins: balance is not enough"

    self._allowances[id][_from][caller] -= amount
    self._balances[id][_from] -= amount
    self._balances[id][to] += amount
    return True


@external
def approve(
    id: uint256, caller: address, spender: address, allowance: uint256
) -> bool:
    self._checkCallerIsToken(id)
    assert caller != spender, "coins: cannot approve itself"
    self._allowances[id][caller][spender] = allowance
    return True


@external
def mint(id: uint256, caller: address, to: address, amount: uint256):
    self._checkCallerIsToken(id)
    assert self._is_minter[id][caller], "coins: caller is not minter"
    self._total_supply[id] += amount
    self._balances[id][to] += amount


@external
def setMinter(id: uint256, caller: address, minter: address, status: bool):
    self._checkCallerIsToken(id)
    assert caller == self._owners[id], "coins: caller is not owner"
    assert minter != empty(address), "coins: minter is the zero address"
    assert minter != caller, "coins: minter is owner address"
    self._is_minter[id][minter] = status


@external
def transferOwnership(id: uint256, caller: address, new_owner: address):
    self._checkCallerIsToken(id)
    self._is_minter[id][caller] = False
    self._is_minter[id][new_owner] = False
    self._owners[id] = new_owner


@external
def renounceOwnership(id: uint256, caller: address):
    self._checkCallerIsToken(id)
    assert caller == self._owners[id], "coins: caller is not owner"
    self._is_minter[id][caller] = False
    self._owners[id] = empty(address)


@external
def create(name: String[25], symbol: String[5], decimals: uint8) -> address:
    token: address = create_from_blueprint(TOKEN_BLUEPRINT, self)
    token_id: uint256 = convert(token, uint256)

    self._ids[token_id] = token
    self._names[token_id] = name
    self._symbols[token_id] = symbol
    self._decimals[token_id] = decimals
    self._owners[token_id] = msg.sender
    self._is_minter[token_id][msg.sender] = True
    log TokenCreated(_id=token_id, _token=token)
    return token


@internal
@view
def _checkCallerIsToken(id: uint256):
    assert self._ids[id] == msg.sender, "coins: caller is not token"
