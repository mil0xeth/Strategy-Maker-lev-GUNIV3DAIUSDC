from brownie import chain


def test_increase(
    vault, strategy, gov, token, token_whale, borrow_token, borrow_whale, yvault
):
    token.approve(vault, 2 ** 256 - 1, {"from": token_whale})
    vault.deposit(20 * (10 ** token.decimals()), {"from": token_whale})
    vault.updateStrategyDebtRatio(strategy, 5_000, {"from": gov})

    chain.sleep(1)
    strategy.harvest({"from": gov})
    assert vault.strategies(strategy).dict()["totalDebt"] == 10 * (
        10 ** token.decimals()
    )

    borrow_token.transfer(
        yvault, 200 * (10 ** borrow_token.decimals()), {"from": borrow_whale}
    )

    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(60 * 60 * 24 * 2)
    chain.mine(1)

    vault.updateStrategyDebtRatio(strategy, 10_000, {"from": gov})
    strategy.harvest({"from": gov})
    assert vault.strategies(strategy).dict()["totalDebt"] >= 20 * (
        10 ** token.decimals()
    )
    assert vault.strategies(strategy).dict()["totalLoss"] == 0


def test_decrease(wsteth, steth, yvault, vault, strategy, gov, token, token_whale):
    token.approve(vault, 2 ** 256 - 1, {"from": token_whale})
    vault.deposit(20 * (10 ** token.decimals()), {"from": token_whale})
    assert vault.totalAssets() == 20e18
    chain.sleep(1)
    strategy.harvest({"from": gov})
    assert vault.strategies(strategy).dict()["totalDebt"] == 20 * (
        10 ** token.decimals()
    )

    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(60 * 60 * 24 * 2)
    chain.mine(1)
    #assert vault.totalAssets() > 20e18

    vault.updateStrategyDebtRatio(strategy, 5_000, {"from": gov})
    strategy.harvest({"from": gov})

    # 15 because it should be less than 20 but there is some profit.
    assert vault.strategies(strategy).dict()["totalDebt"] < 15 * (
        10 ** token.decimals()
    )
    assert vault.strategies(strategy).dict()["totalLoss"] < 1e17


def test_gradual_decrease(yvault, vault, strategy, gov, token, token_whale, healthCheck):
    token.approve(vault, 2 ** 256 - 1, {"from": token_whale})
    vault.deposit(20 * (10 ** token.decimals()), {"from": token_whale})

    chain.sleep(1)
    strategy.harvest({"from": gov})
    assert vault.strategies(strategy).dict()["totalDebt"] == 20 * (
        10 ** token.decimals()
    )

    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(60 * 60 * 24 * 2)
    chain.mine(1)

    vault.updateStrategyDebtRatio(strategy, 9_500, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 9_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 8_500, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 8_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 8_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 7_500, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 7_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 6_500, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 6_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 5_500, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 5_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 4_500, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 4_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 3_500, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 3_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 2_500, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    vault.updateStrategyDebtRatio(strategy, 2_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    vault.updateStrategyDebtRatio(strategy, 1_500, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    vault.updateStrategyDebtRatio(strategy, 1_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    vault.updateStrategyDebtRatio(strategy, 500, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    vault.updateStrategyDebtRatio(strategy, 400, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    vault.updateStrategyDebtRatio(strategy, 300, {"from": gov})
    chain.sleep(1)
    chain.mine(1)
    strategy.harvest({"from": gov})
    chain.mine(1)
    vault.updateStrategyDebtRatio(strategy, 200, {"from": gov})
    chain.sleep(1)
    chain.mine(1)
    strategy.harvest({"from": gov})
    healthCheck.setlossLimitRatio(9000, {"from": gov})
    chain.mine(1)
    vault.updateStrategyDebtRatio(strategy, 100, {"from": gov})
    chain.sleep(1)
    chain.mine(1)
    strategy.harvest({"from": gov})
    chain.mine(1)
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 0, {"from": gov})
    chain.mine(1)
    chain.sleep(1)
    strategy.harvest({"from": gov})

    # 15 because it should be less than 20 but there is some profit.
    assert vault.strategies(strategy).dict()["totalDebt"] < 15 * (
        10 ** token.decimals()
    )
    #assert vault.strategies(strategy).dict()["totalLoss"] < 1e18



def DISABLED_gradual_decrease_with_profitable_vault(yvault, vault, strategy, gov, token, token_whale, healthCheck):
    healthCheck.setProfitLimitRatio(9999, {"from": gov})  #default 100, # 1%
    healthCheck.setlossLimitRatio(9999, {"from": gov})  #default 100, # 1%
    token.approve(vault, 2 ** 256 - 1, {"from": token_whale})
    depositvalue = 200e18
    vault.deposit(depositvalue, {"from": token_whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})

    token.approve(strategy, "40 ether", {"from": token_whale})
    token.transfer(strategy, "40 ether", {'from': token_whale})

    chain.sleep(1)
    strategy.harvest({"from": gov})
    assert vault.strategies(strategy).dict()["totalDebt"] == depositvalue

    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(60 * 60 * 24 * 2)
    chain.mine(1)

    vault.updateStrategyDebtRatio(strategy, 9_500, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 9_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 8_500, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 8_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 8_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 7_500, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 7_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 6_500, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 6_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 5_500, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 5_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 4_500, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 4_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 3_500, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 3_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 2_500, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    vault.updateStrategyDebtRatio(strategy, 2_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    vault.updateStrategyDebtRatio(strategy, 1_500, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    vault.updateStrategyDebtRatio(strategy, 1_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    vault.updateStrategyDebtRatio(strategy, 500, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    vault.updateStrategyDebtRatio(strategy, 400, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    vault.updateStrategyDebtRatio(strategy, 300, {"from": gov})
    chain.sleep(1)
    chain.mine(1)
    strategy.harvest({"from": gov})
    chain.mine(1)
    vault.updateStrategyDebtRatio(strategy, 200, {"from": gov})
    chain.sleep(1)
    chain.mine(1)
    strategy.harvest({"from": gov})
    chain.sleep(60 * 60 * 24 * 2)
    chain.mine(1)
    vault.updateStrategyDebtRatio(strategy, 100, {"from": gov})
    chain.sleep(1)
    chain.mine(1)
    strategy.harvest({"from": gov})
    chain.mine(1)
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 0, {"from": gov})
    chain.mine(1)
    chain.sleep(1)
    strategy.harvest({"from": gov})

    # 15 because it should be less than 20 but there is some profit.
    assert vault.strategies(strategy).dict()["totalDebt"] < 15 * (
        10 ** token.decimals()
    )
    assert vault.strategies(strategy).dict()["totalLoss"] < 1e17




def DISABLED_gradual_decrease_with_profitable_vault_wsteth(yvault, vault, strategy, gov, token, token_whale, wsteth, steth, StableSwapSTETH, healthCheck):
    healthCheck.setProfitLimitRatio(9999, {"from": gov})  #default 100, # 1%
    healthCheck.setlossLimitRatio(9999, {"from": gov})  #default 100, # 1%
    token.approve(vault, 2 ** 256 - 1, {"from": token_whale})
    depositvalue = 200e18
    vault.deposit(depositvalue, {"from": token_whale})

    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(60 * 60 * 24 * 2)

    #acquire wsteth
    balanceBefore = steth.balanceOf(token_whale) == 0
    StableSwapSTETH.exchange(0, 1, "100 ether", "99.5 ether", {'from': token_whale, 'value': "100 ether"})
    #StableSwapSTETH.exchange(0, 1, "100 ether", "100 ether", {'from': token_whale, 'value': "100 ether"})
    assert steth.balanceOf(token_whale) > balanceBefore

    #steth to wsteth
    #assert wsteth.balanceOf(token_whale) == 0
    balanceBefore = wsteth.balanceOf(token_whale)
    steth.approve(wsteth, 2 ** 256 - 1, {'from': token_whale})
    wsteth.wrap("99 ether", {'from': token_whale})
    assert wsteth.balanceOf(token_whale) > balanceBefore



    wsteth.approve(strategy, "15 ether", {"from": token_whale})
    wsteth.transfer(strategy, "15 ether", {'from': token_whale})

    chain.sleep(1)
    chain.sleep(60 * 60 * 24 * 2)
    strategy.harvest({"from": gov})
    assert vault.strategies(strategy).dict()["totalDebt"] == depositvalue

    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(60 * 60 * 24 * 2)
    chain.mine(1)

    vault.updateStrategyDebtRatio(strategy, 9_500, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 9_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 8_500, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 8_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 8_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 7_500, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 7_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 6_500, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 6_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 5_500, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 5_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 4_500, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 4_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 3_500, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 3_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 2_500, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    vault.updateStrategyDebtRatio(strategy, 2_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    vault.updateStrategyDebtRatio(strategy, 1_500, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    vault.updateStrategyDebtRatio(strategy, 1_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    vault.updateStrategyDebtRatio(strategy, 500, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    vault.updateStrategyDebtRatio(strategy, 400, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    vault.updateStrategyDebtRatio(strategy, 300, {"from": gov})
    chain.sleep(1)
    chain.mine(1)
    strategy.harvest({"from": gov})
    chain.mine(1)
    vault.updateStrategyDebtRatio(strategy, 200, {"from": gov})
    chain.sleep(1)
    chain.mine(1)
    strategy.harvest({"from": gov})
    chain.mine(1)
    vault.updateStrategyDebtRatio(strategy, 100, {"from": gov})
    chain.sleep(1)
    chain.mine(1)
    strategy.harvest({"from": gov})
    chain.mine(1)
    chain.sleep(1)
    vault.updateStrategyDebtRatio(strategy, 0, {"from": gov})
    chain.mine(1)
    chain.sleep(1)
    strategy.harvest({"from": gov})

    # 15 because it should be less than 20 but there is some profit.
    assert vault.strategies(strategy).dict()["totalDebt"] < 15 * (
        10 ** token.decimals()
    )
    assert vault.strategies(strategy).dict()["totalLoss"] < 1e17









