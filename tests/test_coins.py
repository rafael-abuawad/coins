import boa

ZERO_ADDRESS = boa.eval("empty(address)")


class TestERC20Facade:
    """Integration tests for ERC20 token facade + Coins registry."""

    def test_deployment_metadata_and_views(self, deploy_erc20, bob):
        t = deploy_erc20(bob)

        assert t.totalSupply() == 0
        assert t.balanceOf(bob) == 0
        assert t.owner() == bob
        assert t.isMinter(bob) is True
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

    def test_approve_self_reverts(self, deploy_erc20, bob):
        t = deploy_erc20(bob)
        with boa.env.prank(bob), boa.reverts("coins: cannot approve itself"):
            t.approve(bob, 10**18)

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

    def test_mint_non_minter_reverts(self, deploy_erc20, bob, alice):
        t = deploy_erc20(bob)
        with boa.env.prank(alice), boa.reverts("coins: caller is not minter"):
            t.mint(alice, 10**18)

    def test_set_minter_grant_and_revoke(self, deploy_erc20, bob, alice):
        t = deploy_erc20(bob)
        assert t.isMinter(alice) is False
        with boa.env.prank(bob):
            t.setMinter(alice, True)
        assert t.isMinter(alice) is True
        with boa.env.prank(alice):
            t.mint(alice, 10**18)
        assert t.balanceOf(alice) == 10**18
        with boa.env.prank(bob):
            t.setMinter(alice, False)
        assert t.isMinter(alice) is False
        with boa.env.prank(alice), boa.reverts("coins: caller is not minter"):
            t.mint(alice, 1)

    def test_set_minter_non_owner_reverts(self, deploy_erc20, bob, alice, charlie):
        t = deploy_erc20(bob)
        with boa.env.prank(alice), boa.reverts("coins: caller is not owner"):
            t.setMinter(charlie, True)

    def test_set_minter_zero_address_reverts(self, deploy_erc20, bob):
        t = deploy_erc20(bob)
        with boa.env.prank(bob), boa.reverts("coins: minter is the zero address"):
            t.setMinter(ZERO_ADDRESS, True)

    def test_set_minter_owner_address_reverts(self, deploy_erc20, bob):
        t = deploy_erc20(bob)
        with boa.env.prank(bob), boa.reverts("coins: minter is owner address"):
            t.setMinter(bob, True)

    def test_transfer_ownership_updates_owner_and_clears_minters(
        self, deploy_erc20, bob, alice
    ):
        t = deploy_erc20(bob)
        with boa.env.prank(bob):
            t.setMinter(alice, True)
        assert t.isMinter(bob) is True
        assert t.isMinter(alice) is True

        with boa.env.prank(bob):
            t.transferOwnership(alice)

        assert t.owner() == alice
        assert t.isMinter(bob) is False
        assert t.isMinter(alice) is False

    def test_renounce_ownership(self, deploy_erc20, bob):
        t = deploy_erc20(bob)
        with boa.env.prank(bob):
            t.renounceOwnership()
        assert t.owner() == ZERO_ADDRESS
        assert t.isMinter(bob) is False

    def test_renounce_ownership_non_owner_reverts(self, deploy_erc20, bob, alice):
        t = deploy_erc20(bob)
        with boa.env.prank(alice), boa.reverts("coins: caller is not owner"):
            t.renounceOwnership()
