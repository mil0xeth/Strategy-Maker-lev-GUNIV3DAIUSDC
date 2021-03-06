import pytest, time

from brownie import chain, reverts, Wei


def test_small_deposit_does_not_generate_debt_under_floor(
    vault, test_strategy, token, token_whale_BIG, yvault, borrow_token, gov, RELATIVE_APPROX_ROUGH
):
    price = test_strategy._getYieldBearingPrice()
    floor = Wei("14_000 ether")  # assume a price floor of 5k as in ETH-C

    # Amount in want that generates 'floor' debt minus a treshold
    token_floor = ((test_strategy.collateralizationRatio() * floor / 1e18) / price) * ( 10 ** token.decimals())

    # Deposit to the vault and send funds through the strategy
    token.approve(vault.address, token_floor, {"from": token_whale_BIG})

    vault.deposit(token_floor, {"from": token_whale_BIG})
    chain.sleep(1)
    test_strategy.harvest({"from": gov})

    # Debt floor is 5k for ETH-C, so the strategy should not take any debt
    # with a lower deposit amount
    assert test_strategy.balanceOfDebt() == 0
    assert yvault.balanceOf(test_strategy) == 0
    assert borrow_token.balanceOf(test_strategy) == 0

    # These are zero because all want is locked in Maker's vault
    assert (pytest.approx(test_strategy.balanceOfMakerVault(), rel=RELATIVE_APPROX_ROUGH) == token_floor)
    assert token.balanceOf(test_strategy) == 0
    assert token.balanceOf(vault) == 0

    # Collateral with no debt should be a high ratio
    assert (
        test_strategy.getCurrentMakerVaultRatio()
        > test_strategy.collateralizationRatio()
    )


def test_deposit_after_passing_debt_floor_generates_debt(
    vault, test_strategy, token, token_whale_BIG, yvault, borrow_token, gov, RELATIVE_APPROX, RELATIVE_APPROX_ROUGH, wsteth
):
    price = test_strategy._getYieldBearingPrice()
    floor = Wei("14_000 ether")  # assume a price floor of 5k as in ETH-C

    # Amount in want that generates 'floor' debt minus a treshold
    token_floor = ((test_strategy.collateralizationRatio() * floor / 1e18) / price) * (
        10 ** token.decimals()
    )
    initial_coll = test_strategy.collateralizationRatio()/1e18
    # Deposit to the vault and send funds through the strategy
    token.approve(vault.address, 2 ** 256 - 1, {"from": token_whale_BIG})
    vault.deposit(token_floor, {"from": token_whale_BIG})
    chain.sleep(1)
    test_strategy.harvest({"from": gov})

    # Debt floor is 10k for YFI-A, so the strategy should not take any debt
    # with a lower deposit amount
    assert test_strategy.balanceOfDebt() == 0
    assert yvault.balanceOf(test_strategy) == 0
    assert borrow_token.balanceOf(test_strategy) == 0
    assert (pytest.approx(test_strategy.balanceOfMakerVault(), rel=RELATIVE_APPROX_ROUGH) == token_floor)

    # Deposit enough want token to go over the dust
    additional_deposit = Wei("2 ether")

    vault.deposit(additional_deposit, {"from": token_whale_BIG})
    chain.sleep(1)
    test_strategy.harvest({"from": gov})

    # Ensure that we have now taken on debt and deposited into yVault
    assert yvault.balanceOf(test_strategy) > 0
    assert test_strategy.balanceOfDebt() > 0    
    reinvest = test_strategy.reinvestmentLeverageComponent()/10000
    #assert (pytest.approx(test_strategy.balanceOfMakerVault(), rel=RELATIVE_APPROX_ROUGH) == token_floor + additional_deposit)
    assert (pytest.approx(wsteth.getStETHByWstETH(test_strategy.balanceOfMakerVault()), rel=RELATIVE_APPROX_ROUGH) == token_floor + additional_deposit + (token_floor+additional_deposit)/initial_coll*reinvest)
    # Collateral with no debt should be a high ratio
    assert (pytest.approx(test_strategy.getCurrentMakerVaultRatio(), rel=RELATIVE_APPROX) == test_strategy.collateralizationRatio())


def test_withdraw_does_not_leave_debt_under_floor(
    vault, test_strategy, token, token_whale_BIG, yvault, dai, dai_whale, gov, RELATIVE_APPROX_ROUGH
):
    # Deposit to the vault and send funds through the strategy
    token.approve(vault.address, 2 ** 256 - 1, {"from": token_whale_BIG})
    vault.deposit(Wei("15 ether"), {"from": token_whale_BIG})
    chain.sleep(1)
    test_strategy.harvest({"from": gov})

    # We took some debt and deposited into yvDAI
    assert yvault.balanceOf(test_strategy) > 0

    # Send profits to yVault
    dai.transfer(yvault, yvault.totalAssets() * 0.03, {"from": dai_whale})
    time.sleep(1)

    shares = yvault.balanceOf(test_strategy)

    # Withdraw large amount so remaining debt is under floor
    withdraw_tx = vault.withdraw("14.5 ether", token_whale_BIG, 500, {"from": token_whale_BIG})
    withdraw_tx.wait(1)
    time.sleep(1)

    # Almost all yvDAI shares should have been used to repay the debt
    # and avoid the floor
    assert (yvault.balanceOf(test_strategy) - (shares - shares * (1 / 1.03))) < 1e18

    # Because debt is under floor, we expect Ratio to be 0
    assert (
        test_strategy.getCurrentMakerVaultRatio() == 0
    )

 
def test_large_deposit_does_not_generate_debt_over_ceiling(
    vault, test_strategy, token, token_whale_BIG, yvault, borrow_token, gov
):
    test_strategy.updateMaxSingleTrade(1e40, {"from": gov})
    # Deposit to the vault and send funds through the strategy
    token.approve(vault.address, 2 ** 256 - 1, {"from": token_whale_BIG})
    vault.deposit(token.balanceOf(token_whale_BIG), {"from": token_whale_BIG})
    chain.sleep(1)
    test_strategy.harvest({"from": gov})

    # Debt ceiling is ~100 million in ETH-C at this time
    # The whale should deposit >2x that to hit the ceiling
    assert yvault.balanceOf(test_strategy) > 0
    #negligible amount of wei of borrow token 
    assert borrow_token.balanceOf(test_strategy) < 100000

    # These are zero because all want is locked in Maker's vault
    assert token.balanceOf(test_strategy) == 0
    assert token.balanceOf(vault) == 0

    # Collateral ratio should be larger due to debt being capped by ceiling
    assert (test_strategy.collateralizationRatio()/1e18 > 10)


def DISABLED_withdraw_everything_with_vault_in_debt_ceiling(
    vault, test_strategy, token, token_whale_BIG, yvault, gov, RELATIVE_APPROX_ROUGH
):
    amount = token.balanceOf(token_whale_BIG)

    # Deposit to the vault and send funds through the strategy
    token.approve(vault.address, 2 ** 256 - 1, {"from": token_whale_BIG})
    vault.deposit(amount, {"from": token_whale_BIG})
    chain.sleep(1)
    test_strategy.harvest({"from": gov})

    #test_strategy.setLeaveDebtBehind(False, {"from": gov})
    vault.withdraw(vault.balanceOf(token_whale_BIG), token_whale_BIG, 1000, {"from": token_whale_BIG})
    time.sleep(1)

    assert vault.strategies(test_strategy).dict()["totalDebt"] == 0
    assert test_strategy.getCurrentMakerVaultRatio() == 0
    assert yvault.balanceOf(test_strategy) < 1e18  # dust
    assert pytest.approx(token.balanceOf(token_whale_BIG), rel=RELATIVE_APPROX_ROUGH) == amount


def test_large_want_balance_does_not_generate_debt_over_ceiling(
    vault, test_strategy, token, token_whale_BIG, yvault, borrow_token, gov
):
    test_strategy.updateMaxSingleTrade(1e40, {"from": gov})
    # Deposit to the vault and send funds through the strategy
    token.approve(vault.address, 2 ** 256 - 1, {"from": token_whale_BIG})
    vault.deposit(Wei("250_000 ether"), {"from": token_whale_BIG})

    # Send the funds through the strategy to invest
    chain.sleep(1)
    test_strategy.harvest({"from": gov})

    # Debt ceiling is ~100 million in ETH-C at this time
    # The whale should deposit >2x that to hit the ceiling
    assert yvault.balanceOf(test_strategy) > 0
    assert borrow_token.balanceOf(test_strategy) < 100000

    # These are zero because all want is locked in Maker's vault
    assert token.balanceOf(test_strategy) == 0
    assert token.balanceOf(vault) == 0

    # Collateral ratio should be larger due to debt being capped by ceiling
    assert (test_strategy.collateralizationRatio()/1e18 > 10)

def DISABLED_deposit_after_ceiling_reached_should_not_mint_more_dai(
    vault, test_strategy, token, token_whale_BIG, yvault, gov
):
    # Deposit to the vault and send funds through the strategy
    token.approve(vault.address, 2 ** 256 - 1, {"from": token_whale_BIG})
    vault.deposit(Wei("250_000 ether"), {"from": token_whale_BIG})

    # Send the funds through the strategy to invest
    chain.sleep(1)
    test_strategy.harvest({"from": gov})

    investment_before = yvault.balanceOf(test_strategy)
    ratio_before = test_strategy.getCurrentMakerVaultRatio()

    # Deposit to the vault and send funds through the strategy
    token.approve(vault.address, 2 ** 256 - 1, {"from": token_whale_BIG})
    vault.deposit(token.balanceOf(token_whale_BIG), {"from": token_whale_BIG})
    chain.sleep(1)
    test_strategy.harvest({"from": gov})

    assert investment_before >= yvault.balanceOf(test_strategy)
    assert ratio_before < test_strategy.getCurrentMakerVaultRatio()


# Fixture 'amount' is included so user has some balance
def test_withdraw_everything_cancels_entire_debt(
    vault, test_strategy, token, token_whale_BIG, user, amount, yvault, dai, dai_whale, gov, RELATIVE_APPROX_LOSSY
):
    amount_user = Wei("0.25 ether")
    amount_whale = Wei("100 ether")

    # Deposit to the vault and send funds through the strategy
    token.approve(vault.address, 2 ** 256 - 1, {"from": token_whale_BIG})
    vault.deposit(amount_whale, {"from": token_whale_BIG})

    token.approve(vault.address, 2 ** 256 - 1, {"from": user})
    vault.deposit(amount_user, {"from": user})

    chain.sleep(1)
    test_strategy.harvest({"from": gov})

    # Send profits to yVault
    dai.transfer(yvault, yvault.totalAssets() * 0.00001, {"from": dai_whale})

    #assert 0 == 1
    #assert pytest.approx(vault.withdraw(vault.balanceOf(token_whale_BIG), token_whale_BIG, 100, {"from": token_whale_BIG}).return_value, rel=RELATIVE_APPROX_LOSSY) == amount_whale
    #assert pytest.approx(vault.withdraw(vault.balanceOf(user), user, 500, {"from": user}).return_value, rel=RELATIVE_APPROX_LOSSY) == amount_user
    vault.withdraw(vault.balanceOf(token_whale_BIG), token_whale_BIG, 100, {"from": token_whale_BIG})
    time.sleep(1)
    vault.withdraw(vault.balanceOf(user), user, 500, {"from": user})
    time.sleep(1)
    assert vault.strategies(test_strategy).dict()["totalDebt"] == 0


def DISABLED_withdraw_under_floor_without_funds_to_cancel_entire_debt_should_fail(
    vault, test_strategy, token, token_whale_BIG, gov, yvault, RELATIVE_APPROX_LOSSY
):
    # Make sure the strategy will not sell want to repay debt
    #test_strategy.setLeaveDebtBehind(False, {"from": gov})

    price = test_strategy._getYieldBearingPrice()
    floor = Wei("5_100 ether")  # assume a price floor of 5k as in ETH-C

    # Amount in want that generates 'floor' debt minus a treshold
    token_floor = ((test_strategy.collateralizationRatio() * floor / 1e18) / price) * (
        10 ** token.decimals()
    )

    lower_rebalancing_bound = (
        test_strategy.collateralizationRatio() - test_strategy.rebalanceTolerance()
    )
    min_floor_in_band = (
        token_floor * lower_rebalancing_bound / test_strategy.collateralizationRatio()
    )

    # Deposit to the vault and send funds through the strategy
    token.approve(vault.address, 2 ** 256 - 1, {"from": token_whale_BIG})
    vault.deposit(token_floor, {"from": token_whale_BIG})
    chain.sleep(1)
    test_strategy.harvest({"from": gov})

    max_withdrawal = token_floor - min_floor_in_band - Wei("0.0001 ether")

    # Simulate a loss in yvault by sending some shares away
    yvault.transfer(
        token_whale_BIG, yvault.balanceOf(test_strategy) * 0.01, {"from": test_strategy}
    )

    assert (
        pytest.approx(vault.withdraw(max_withdrawal, token_whale_BIG, 100, {"from": token_whale_BIG}).return_value, rel=RELATIVE_APPROX_LOSSY)
        == max_withdrawal
    )

    # We are not simulating any profit in yVault, so there will not
    # be enough to repay the debt
    with reverts():
        vault.withdraw({"from": token_whale_BIG})


def test_small_withdraw_cancels_corresponding_debt(
    vault, strategy, token, token_whale_BIG, yvault, gov, RELATIVE_APPROX, RELATIVE_APPROX_LOSSY
):
    amount = Wei("10 ether")
    to_withdraw_pct = 0.2

    # Deposit to the vault and send funds through the strategy
    token.approve(vault.address, 2 ** 256 - 1, {"from": token_whale_BIG})
    vault.deposit(amount, {"from": token_whale_BIG})
    chain.sleep(1)
    strategy.harvest({"from": gov})

    # Shares in yVault at the current target ratio
    shares_before = yvault.balanceOf(strategy)

    assert (
        pytest.approx(vault.withdraw(amount * to_withdraw_pct, token_whale_BIG, 100, {"from": token_whale_BIG}).return_value, rel=RELATIVE_APPROX_LOSSY)
        == amount * to_withdraw_pct
    )

    assert pytest.approx(
        shares_before * (1 - to_withdraw_pct), rel=RELATIVE_APPROX
    ) == yvault.balanceOf(strategy)


def test_tend_trigger_with_debt_under_dust_returns_false(
    vault, test_strategy, token, token_whale_BIG, gov
):
    price = test_strategy._getYieldBearingPrice()
    floor = Wei("4_990 ether")  # assume a price floor of 5k as in ETH-C

    # Amount in want that generates 'floor' debt minus a treshold
    token_floor = ((test_strategy.collateralizationRatio() * floor / 1e18) / price) * (
        10 ** token.decimals()
    )

    # Deposit to the vault and send funds through the strategy
    token.approve(vault.address, token_floor, {"from": token_whale_BIG})

    vault.deposit(token_floor, {"from": token_whale_BIG})
    chain.sleep(1)
    test_strategy.harvest({"from": gov})

    # Debt floor is 5k for ETH-C, so the strategy should not take any debt
    # with a lower deposit amount
    assert test_strategy.tendTrigger(1) == False


def test_tend_trigger_without_more_mintable_dai_returns_false(
    vault, strategy, token, token_whale_BIG, gov
):
    # Deposit to the vault and send funds through the strategy
    token.approve(vault.address, 2 ** 256 - 1, {"from": token_whale_BIG})
    vault.deposit(Wei("250_000 ether"), {"from": token_whale_BIG})

    # Send the funds through the strategy to invest
    chain.sleep(1)
    strategy.harvest({"from": gov})

    assert strategy.tendTrigger(1) == False

    # Deposit to the vault and send funds through the strategy
    token.approve(vault.address, 2 ** 256 - 1, {"from": token_whale_BIG})
    vault.deposit(token.balanceOf(token_whale_BIG), {"from": token_whale_BIG})
    chain.sleep(1)
    strategy.harvest({"from": gov})

    assert strategy.tendTrigger(1) == False


def test_tend_trigger_with_funds_in_cdp_but_no_debt_returns_false(
    vault, strategy, token, token_whale_BIG, gov, dai, dai_whale, yvDAI, price_oracle_want_to_eth
):
    # Deposit to the vault and send funds through the strategy
    token.approve(vault.address, 2 ** 256 - 1, {"from": token_whale_BIG})
    vault.deposit(Wei("1_000 ether"), {"from": token_whale_BIG})

    # Send the funds through the strategy to invest
    chain.sleep(1)
    strategy.harvest({"from": gov})

    assert strategy.tendTrigger(1) == False

    # Send some profit to yVault
    #dai.transfer(yvDAI, yvDAI.totalAssets() * 0.05, {"from": dai_whale})
    dai.transfer(yvDAI, yvDAI.totalAssets() * 0.01, {"from": dai_whale})

    # Harvest 2: Realize profit
    strategy.harvest({"from": gov})
    chain.sleep(3600 * 6)  # 6 hrs needed for profits to unlock
    chain.mine(1)
    strategy.emergencyDebtRepayment(0, {"from": vault.management()})

    #For some reason needs to be retriggered after another 1 DAI transfer to yvDAI
    dai.transfer(yvDAI, "6000 ether", {"from": dai_whale})
    strategy.emergencyDebtRepayment(0, {"from": vault.management()})
    dai.transfer(yvDAI, "6000 ether", {"from": dai_whale})
    strategy.emergencyDebtRepayment(0, {"from": vault.management()})

    #strategy currently unlocks collateral that is unused
    #assert strategy.balanceOfMakerVault() > 0
    assert strategy.balanceOfDebt() == 0
    #assert strategy.getCurrentMakerVaultRatio() / 1e18 > 1000
    assert strategy.tendTrigger(1) == False
