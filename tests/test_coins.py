import boa
from src.tokens import erc20

ZERO_ADDRESS = boa.eval("empty(address)")


def _token_id(token) -> int:
    return int(str(token.address), 0)


class TestCoinsRegistry:
    """Direct tests against the `Coins` registry and `create` behavior."""

    def test_create_emits_token_created_with_matching_id_and_token(
        self, coins_contract, bob
    ):
        with boa.env.prank(bob):
            token_addr = coins_contract.create("River", "RIV", 12, 0)
        token = erc20.at(token_addr)
        tid = _token_id(token)

        created = [
            L for L in coins_contract.get_logs() if type(L).__name__ == "TokenCreated"
        ]
        assert len(created) == 1
        assert created[0]._1 == tid
        assert created[0]._2 == token.address

    def test_create_initial_supply_mints_to_creator(self, coins_contract, bob):
        amt = 1_000 * 10**18
        with boa.env.prank(bob):
            token_addr = coins_contract.create("Air", "AIR", 18, amt)
        token = erc20.at(token_addr)
        tid = _token_id(token)
        assert token.balanceOf(bob) == amt
        assert token.totalSupply() == amt
        assert coins_contract.balanceOf(tid, bob) == amt
        assert coins_contract.totalSupply(tid) == amt

    def test_registry_views_match_token_facade(self, deploy_erc20, bob, coins_contract):
        t = deploy_erc20(bob, "Registry", "REG", 9)
        tid = _token_id(t)

        assert coins_contract.name(tid) == t.name()
        assert coins_contract.symbol(tid) == t.symbol()
        assert coins_contract.decimals(tid) == t.decimals()
        assert coins_contract.owner(tid) == t.owner()
        assert coins_contract.totalSupply(tid) == t.totalSupply()
        assert coins_contract.id(tid) == t.address

    def test_two_tokens_have_independent_balances_and_supplies(
        self, deploy_erc20, bob, alice
    ):
        t_a = deploy_erc20(bob, "Alpha", "A", 18)
        t_b = deploy_erc20(bob, "Beta", "B", 18)
        amt_a = 70 * 10**18
        amt_b = 3 * 10**18

        with boa.env.prank(bob):
            t_a.mint(alice, amt_a)
            t_b.mint(alice, amt_b)

        assert t_a.totalSupply() == amt_a
        assert t_b.totalSupply() == amt_b
        assert t_a.balanceOf(alice) == amt_a
        assert t_b.balanceOf(alice) == amt_b

    def test_transfer_called_on_registry_not_from_token_reverts(
        self, deploy_erc20, bob, alice, coins_contract
    ):
        t = deploy_erc20(bob)
        tid = _token_id(t)
        with boa.env.prank(bob):
            t.mint(bob, 10**18)
        with boa.env.prank(bob), boa.reverts("coins: caller is not token"):
            coins_contract.transfer(tid, bob, alice, 10**18)

    def test_mint_called_on_registry_not_from_token_reverts(
        self, deploy_erc20, bob, alice, coins_contract
    ):
        t = deploy_erc20(bob)
        tid = _token_id(t)
        with boa.env.prank(bob), boa.reverts("coins: caller is not token"):
            coins_contract.mint(tid, bob, alice, 10**18)


class TestERC20Facade:
    """Integration tests for ERC20 token facade + Coins registry."""

    def test_deployment_metadata_and_views(self, deploy_erc20, bob):
        t = deploy_erc20(bob)

        assert t.totalSupply() == 0
        assert t.balanceOf(bob) == 0
        assert t.owner() == bob
        assert t.name() == "Wrapped Ether"
        assert t.symbol() == "WETH"
        assert t.decimals() == 18

    def test_create_custom_metadata(self, deploy_erc20, bob):
        t = deploy_erc20(bob, "My Token", "MTK", 6)
        assert t.name() == "My Token"
        assert t.symbol() == "MTK"
        assert t.decimals() == 6

    def test_mint_increases_supply_and_balance(self, deploy_erc20, bob, alice):
        t = deploy_erc20(bob)
        amount = 100 * 10**18

        with boa.env.prank(bob):
            t.mint(alice, amount)

        assert t.totalSupply() == amount
        assert t.balanceOf(alice) == amount
        assert t.balanceOf(bob) == 0
        assert t.owner() == bob

    def test_transfer_success(self, deploy_erc20, bob, alice):
        t = deploy_erc20(bob)
        amount = 50 * 10**18
        with boa.env.prank(bob):
            t.mint(bob, amount)
        with boa.env.prank(bob):
            assert t.transfer(alice, amount) is True
        assert t.balanceOf(bob) == 0
        assert t.balanceOf(alice) == amount
        assert t.totalSupply() == amount

    def test_transfer_zero_amount_noop(self, deploy_erc20, bob, alice):
        t = deploy_erc20(bob)
        amount = 10 * 10**18
        with boa.env.prank(bob):
            t.mint(bob, amount)
        with boa.env.prank(bob):
            assert t.transfer(alice, 0) is True
        assert t.balanceOf(bob) == amount
        assert t.balanceOf(alice) == 0

    def test_transfer_to_zero_reverts(self, deploy_erc20, bob):
        t = deploy_erc20(bob)
        with boa.env.prank(bob):
            t.mint(bob, 10**18)
        with boa.env.prank(bob), boa.reverts("coin:cannot transfer to empty address"):
            t.transfer(ZERO_ADDRESS, 1)

    def test_transfer_insufficient_balance_reverts(self, deploy_erc20, bob, alice):
        t = deploy_erc20(bob)
        with boa.env.prank(bob), boa.reverts():
            t.transfer(alice, 1)

    def test_approve_and_allowance(self, deploy_erc20, bob, alice):
        t = deploy_erc20(bob)
        allowance = 10**18
        with boa.env.prank(bob):
            assert t.approve(alice, allowance) is True
        assert t.allowance(bob, alice) == allowance

    def test_transfer_from_full_allowance(self, deploy_erc20, bob, alice, charlie):
        amount = 100 * 10**18
        t = deploy_erc20(bob)
        with boa.env.prank(bob):
            t.mint(bob, amount)
        with boa.env.prank(bob):
            t.approve(alice, amount)
        with boa.env.prank(alice):
            assert t.transferFrom(bob, charlie, amount) is True
        assert t.balanceOf(bob) == 0
        assert t.balanceOf(charlie) == amount
        assert t.allowance(bob, alice) == 0

    def test_transfer_from_partial_allowance(self, deploy_erc20, bob, alice, charlie):
        total = 100 * 10**18
        spend = 30 * 10**18
        t = deploy_erc20(bob)
        with boa.env.prank(bob):
            t.mint(bob, total)
            t.approve(alice, total)
        with boa.env.prank(alice):
            assert t.transferFrom(bob, charlie, spend) is True
        assert t.balanceOf(bob) == total - spend
        assert t.balanceOf(charlie) == spend
        assert t.allowance(bob, alice) == total - spend

    def test_transfer_from_allowance_too_low_reverts(
        self, deploy_erc20, bob, alice, charlie
    ):
        amount = 100 * 10**18
        t = deploy_erc20(bob)
        with boa.env.prank(bob):
            t.mint(bob, amount)
            t.approve(alice, amount - 1)
        with boa.env.prank(alice), boa.reverts("coins: allowance is not enough"):
            t.transferFrom(bob, charlie, amount)

    def test_transfer_from_balance_too_low_reverts(
        self, deploy_erc20, bob, alice, charlie
    ):
        bal = 50 * 10**18
        t = deploy_erc20(bob)
        with boa.env.prank(bob):
            t.mint(bob, bal)
            t.approve(alice, 100 * 10**18)
        with boa.env.prank(alice), boa.reverts("coins: balance is not enough"):
            t.transferFrom(bob, charlie, bal + 1)

    def test_transfer_from_to_zero_reverts(self, deploy_erc20, bob, alice):
        amount = 10 * 10**18
        t = deploy_erc20(bob)
        with boa.env.prank(bob):
            t.mint(bob, amount)
            t.approve(alice, amount)
        with (
            boa.env.prank(alice),
            boa.reverts("coins: cannot transfer to empty address"),
        ):
            t.transferFrom(bob, ZERO_ADDRESS, amount)

    def test_mint_non_owner_reverts(self, deploy_erc20, bob, alice):
        t = deploy_erc20(bob)
        with boa.env.prank(alice), boa.reverts("coins: caller is not owner"):
            t.mint(alice, 10**18)

    def test_transfer_ownership_new_owner_can_mint_prior_owner_cannot(
        self, deploy_erc20, bob, alice
    ):
        t = deploy_erc20(bob)
        amt = 10**18

        with boa.env.prank(bob):
            t.transferOwnership(alice)

        assert t.owner() == alice

        with boa.env.prank(bob), boa.reverts("coins: caller is not owner"):
            t.mint(bob, amt)

        with boa.env.prank(alice):
            t.mint(alice, amt)
        assert t.balanceOf(alice) == amt

    def test_transfer_ownership_non_owner_reverts(self, deploy_erc20, bob, alice):
        t = deploy_erc20(bob)
        with boa.env.prank(alice), boa.reverts("coins: caller is not owner"):
            t.transferOwnership(alice)

    def test_renounce_ownership(self, deploy_erc20, bob):
        t = deploy_erc20(bob)
        with boa.env.prank(bob):
            t.renounceOwnership()
        assert t.owner() == ZERO_ADDRESS

    def test_renounce_ownership_non_owner_reverts(self, deploy_erc20, bob, alice):
        t = deploy_erc20(bob)
        with boa.env.prank(alice), boa.reverts("coins: caller is not owner"):
            t.renounceOwnership()

    def test_burn_reduces_supply_and_balance(self, deploy_erc20, bob):
        t = deploy_erc20(bob)
        amount = 100 * 10**18
        burn = 30 * 10**18
        with boa.env.prank(bob):
            t.mint(bob, amount)
        with boa.env.prank(bob):
            t.burn(burn)

        assert t.totalSupply() == amount - burn
        assert t.balanceOf(bob) == amount - burn

    def test_burn_entire_supply(self, deploy_erc20, bob):
        t = deploy_erc20(bob)
        amount = 10 * 10**18
        with boa.env.prank(bob):
            t.mint(bob, amount)
        with boa.env.prank(bob):
            t.burn(amount)

        assert t.totalSupply() == 0
        assert t.balanceOf(bob) == 0

    def test_burn_zero_is_noop(self, deploy_erc20, bob):
        t = deploy_erc20(bob)
        amount = 5 * 10**18
        with boa.env.prank(bob):
            t.mint(bob, amount)
        with boa.env.prank(bob):
            t.burn(0)

        assert t.totalSupply() == amount
        assert t.balanceOf(bob) == amount

    def test_burn_exceeding_balance_reverts(self, deploy_erc20, bob):
        t = deploy_erc20(bob)
        with boa.env.prank(bob):
            t.mint(bob, 10**18)
        with boa.env.prank(bob), boa.reverts():
            t.burn(2 * 10**18)

    def test_burn_from_with_allowance(self, deploy_erc20, bob, alice):
        t = deploy_erc20(bob)
        total = 100 * 10**18
        burn_amt = 40 * 10**18

        with boa.env.prank(bob):
            t.mint(bob, total)
            t.approve(alice, burn_amt)
        assert t.allowance(bob, alice) == burn_amt

        with boa.env.prank(alice):
            t.burnFrom(bob, burn_amt)

        assert t.totalSupply() == total - burn_amt
        assert t.balanceOf(bob) == total - burn_amt
        assert t.allowance(bob, alice) == 0

    def test_burn_from_partial_allowance(self, deploy_erc20, bob, alice):
        t = deploy_erc20(bob)
        total = 100 * 10**18
        approved = 50 * 10**18
        burn_amt = 20 * 10**18

        with boa.env.prank(bob):
            t.mint(bob, total)
            t.approve(alice, approved)

        with boa.env.prank(alice):
            t.burnFrom(bob, burn_amt)

        assert t.totalSupply() == total - burn_amt
        assert t.balanceOf(bob) == total - burn_amt
        assert t.allowance(bob, alice) == approved - burn_amt

    def test_burn_from_allowance_exhausted_then_reverts(self, deploy_erc20, bob, alice):
        t = deploy_erc20(bob)
        total = 50 * 10**18

        with boa.env.prank(bob):
            t.mint(bob, total)
            t.approve(alice, total)

        with boa.env.prank(alice):
            t.burnFrom(bob, total)

        with boa.env.prank(alice), boa.reverts("coins: caller is not owner or allowed"):
            t.burnFrom(bob, 1)

    def test_burn_from_insufficient_allowance_reverts(self, deploy_erc20, bob, alice):
        t = deploy_erc20(bob)

        with boa.env.prank(bob):
            t.mint(bob, 100 * 10**18)
            t.approve(alice, 10**18)

        with boa.env.prank(alice), boa.reverts("coins: caller is not owner or allowed"):
            t.burnFrom(bob, 10**18 + 1)

    def test_transfer_to_self_preserves_balance_and_supply(self, deploy_erc20, bob):
        t = deploy_erc20(bob)
        amount = 40 * 10**18
        with boa.env.prank(bob):
            t.mint(bob, amount)
        with boa.env.prank(bob):
            assert t.transfer(bob, amount // 2) is True
        assert t.balanceOf(bob) == amount
        assert t.totalSupply() == amount

    def test_transfer_from_zero_amount_succeeds(
        self, deploy_erc20, bob, alice, charlie
    ):
        total = 25 * 10**18
        t = deploy_erc20(bob)
        with boa.env.prank(bob):
            t.mint(bob, total)
            t.approve(alice, total)
        with boa.env.prank(alice):
            assert t.transferFrom(bob, charlie, 0) is True
        assert t.balanceOf(bob) == total
        assert t.balanceOf(charlie) == 0
        assert t.allowance(bob, alice) == total

    def test_approve_replaces_prior_allowance(self, deploy_erc20, bob, alice):
        t = deploy_erc20(bob)
        with boa.env.prank(bob):
            t.approve(alice, 5 * 10**18)
            t.approve(alice, 9 * 10**18)
        assert t.allowance(bob, alice) == 9 * 10**18

    def test_mint_after_renounce_ownership_reverts(self, deploy_erc20, bob):
        t = deploy_erc20(bob)
        with boa.env.prank(bob):
            t.renounceOwnership()
        assert t.owner() == ZERO_ADDRESS
        with boa.env.prank(bob), boa.reverts("coins: caller is not owner"):
            t.mint(bob, 1)

    def test_transfer_ownership_to_zero_address_revokes_mint(self, deploy_erc20, bob):
        t = deploy_erc20(bob)
        with boa.env.prank(bob):
            t.transferOwnership(ZERO_ADDRESS)
        assert t.owner() == ZERO_ADDRESS
        with boa.env.prank(bob), boa.reverts("coins: caller is not owner"):
            t.mint(bob, 1)

    def test_burn_from_own_balance_without_self_allowance_reverts(
        self, deploy_erc20, bob
    ):
        t = deploy_erc20(bob)
        with boa.env.prank(bob):
            t.mint(bob, 10**18)
        with boa.env.prank(bob), boa.reverts("coins: caller is not owner or allowed"):
            t.burnFrom(bob, 1)

    def test_burn_from_exceeds_owner_balance_reverts(self, deploy_erc20, bob, alice):
        t = deploy_erc20(bob)
        with boa.env.prank(bob):
            t.mint(bob, 10**18)
            t.approve(alice, 100 * 10**18)
        with boa.env.prank(alice), boa.reverts():
            t.burnFrom(bob, 2 * 10**18)
