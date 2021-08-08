// SPDX-License-Identifier: AGPL-3.0
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

import {
    BaseStrategy,
    StrategyParams
} from "@yearnvaults/contracts/BaseStrategy.sol";
import {
    SafeERC20,
    SafeMath,
    IERC20,
    Address
} from "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";

import "../interfaces/chainlink/AggregatorInterface.sol";
import "../interfaces/maker/IMaker.sol";
import "../interfaces/yearn/IVault.sol";

contract Strategy is BaseStrategy {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    uint256 internal constant WAD = 10**18;
    uint256 internal constant RAY = 10**27;
    uint256 internal constant RAD = 10**45;

    ManagerLike internal constant cdpManager =
        ManagerLike(0x5ef30b9986345249bc32d8928B7ee64DE9435E39);

    DaiJoinLike internal constant daiJoinAdapter =
        DaiJoinLike(0x9759A6Ac90977b93B58547b4A71c78317f391A28);

    JugLike internal constant jug =
        JugLike(0x19c0976f590D67707E62397C87829d896Dc0f1F1);

    GemJoinLike internal constant gemJoinAdapter =
        GemJoinLike(0x3ff33d9162aD47660083D7DC4bC02Fb231c81677);

    // Use Chainlink oracle to obtain latest YFI/USD price
    AggregatorInterface internal constant chainlinkYFItoUSDPriceFeed =
        AggregatorInterface(0xA027702dbb89fbd58938e4324ac03B58d812b0E1);

    // Use Chainlink oracle to obtain latest YFI/ETH price
    AggregatorInterface internal constant chainlinkYFItoETHPriceFeed =
        AggregatorInterface(0x7c5d4F8345e66f68099581Db340cd65B078C41f4);

    // DAI yVault
    IVault public yVault = IVault(0xdA816459F1AB5631232FE5e97a05BBBb94970c95);

    // TODO: ilk, join adapter and chainlink oracle should be dynamic to support different ilks
    bytes32 public ilk = "YFI-A";

    // Our vault identifier
    uint256 public cdpId;

    // Our desired collaterization ratio
    uint256 public collateralizationRatio;

    constructor(address _vault) public BaseStrategy(_vault) {
        // You can set these parameters on deployment to whatever you want
        // maxReportDelay = 6300;
        // profitFactor = 100;
        // debtThreshold = 0;
        cdpId = cdpManager.open(ilk, address(this));
        // Minimum collaterization ratio on YFI-A is 175%. Use 250% to be extra safe.
        collateralizationRatio = 250;
    }

    // Required to move funds to a new cdp and use a different cdpId after migration.
    // Should only be called by governance.
    function shiftToCdp(uint256 newCdpId) external onlyGovernance {
        cdpManager.shift(cdpId, newCdpId);
        cdpId = newCdpId;
    }

    // ******** OVERRIDE THESE METHODS FROM BASE CONTRACT ************

    function name() external view override returns (string memory) {
        // TODO: should be dynamic to support different ilks
        return "StrategyMakerYFI";
    }

    function delegatedAssets() external view override returns (uint256) {
        uint256 yvDAIShares = yVault.balanceOf(address(this));
        uint256 wantPrice = _getWantTokenPrice();
        return yvDAIShares.mul(yVault.pricePerShare()).div(wantPrice);
    }

    function estimatedTotalAssets() public view override returns (uint256) {
        return balanceOfWant().add(balanceOfMakerVault());
    }

    function prepareReturn(uint256 _debtOutstanding)
        internal
        override
        returns (
            uint256 _profit,
            uint256 _loss,
            uint256 _debtPayment
        )
    {
        // TODO: Do stuff here to free up any returns back into `want`
        // NOTE: Return `_profit` which is value generated by all positions, priced in `want`
        // NOTE: Should try to free up at least `_debtOutstanding` of underlying position
    }

    function adjustPosition(uint256 _debtOutstanding) internal override {
        uint256 wantBalance = balanceOfWant();

        if (wantBalance > _debtOutstanding) {
            uint256 amountToDeposit = wantBalance.sub(_debtOutstanding);
            _depositToCdp(amountToDeposit);
        }

        // TODO: check collateralization ratio to mint more dai or pay back dai
    }

    function liquidatePosition(uint256 _amountNeeded)
        internal
        override
        returns (uint256 _liquidatedAmount, uint256 _loss)
    {
        // TODO: Do stuff here to free up to `_amountNeeded` from all positions back into `want`
        // NOTE: Maintain invariant `want.balanceOf(this) >= _liquidatedAmount`
        // NOTE: Maintain invariant `_liquidatedAmount + _loss <= _amountNeeded`

        uint256 totalAssets = want.balanceOf(address(this));
        if (_amountNeeded > totalAssets) {
            _liquidatedAmount = totalAssets;
            _loss = _amountNeeded.sub(totalAssets);
        } else {
            _liquidatedAmount = _amountNeeded;
        }
    }

    function liquidateAllPositions() internal override returns (uint256) {
        // TODO: Liquidate all positions and return the amount freed.
        // Get all DAI back from yvDAI - attempt to repay debt
        // Get all collateral back
        return want.balanceOf(address(this));
    }

    // NOTE: Can override `tendTrigger` and `harvestTrigger` if necessary

    function prepareMigration(address _newStrategy) internal override {
        // Transfer Maker Vault ownership to the new startegy
        cdpManager.give(cdpId, _newStrategy);

        // Move yvDAI balance to the new strategy
        IERC20(yVault).safeTransfer(
            _newStrategy,
            yVault.balanceOf(address(this))
        );
    }

    function protectedTokens()
        internal
        view
        override
        returns (address[] memory)
    {
        address[] memory protected = new address[](2);
        protected[0] = yVault.token();
        protected[1] = address(yVault);
        return protected;
    }

    function ethToWant(uint256 _amtInWei)
        public
        view
        virtual
        override
        returns (uint256)
    {
        // YFI price in ETH with 18 decimals
        uint256 price = uint256(chainlinkYFItoETHPriceFeed.latestAnswer());
        return _amtInWei.mul(1e18).div(price);
    }

    // ----------------- INTERNAL FUNCTIONS SUPPORT -----------------

    function _checkAllowance(
        address _contract,
        IERC20 _token,
        uint256 _amount
    ) internal {
        if (_token.allowance(address(this), _contract) < _amount) {
            _token.safeApprove(_contract, 0);
            _token.safeApprove(_contract, type(uint256).max);
        }
    }

    function _getWantTokenPrice() internal view returns (uint256) {
        int256 price = chainlinkYFItoUSDPriceFeed.latestAnswer();
        require(price > 0); // dev: invalid price returned by chainlink oracle
        // Non-ETH pairs have 8 decimals, so we need to adjust it to 18
        return uint256(price * 1e10);
    }

    function _depositToCdp(uint256 amount) internal {
        if (amount == 0) {
            return;
        }

        uint256 price = _getWantTokenPrice();

        _checkAllowance(address(gemJoinAdapter), want, amount);

        // Both `amount` and `price` are in wad, therefore amount.mul(price).div(WAD) is the total USD value
        // This represents 100% of the collateral value in USD, so we divide by the collateralization ratio (expressed in %)
        // and multiply by 100 to correct the offset
        uint256 daiToMint =
            amount.mul(price).div(WAD).div(collateralizationRatio).mul(100);

        // Lock collateral and mint DAI
        _lockGemAndDraw(amount, daiToMint);

        // Send DAI to yvDAI
        _checkAllowance(address(yVault), IERC20(yVault.token()), daiToMint);
        yVault.deposit();
    }

    // ----------------- INTERNAL CALCS -----------------

    function balanceOfWant() internal view returns (uint256) {
        return want.balanceOf(address(this));
    }

    // Returns collateral balance in the vault
    function balanceOfMakerVault() internal view returns (uint256) {
        uint256 ink; // collateral balance
        uint256 art; // normalized outstanding stablecoin debt
        address urn = cdpManager.urns(cdpId);
        VatLike vat = VatLike(cdpManager.vat());
        (ink, art) = vat.urns(ilk, urn);
        return ink;
    }

    // ----------------- UTILS FROM MAKERDAO DSS-PROXY-ACTIONS -----------------

    function toInt(uint256 x) internal pure returns (int256 y) {
        y = int256(x);
        require(y >= 0, "int-overflow");
    }

    function mul(uint256 x, uint256 y) internal pure returns (uint256 z) {
        require(y == 0 || (z = x * y) / y == x, "mul-overflow");
    }

    function sub(uint256 x, uint256 y) internal pure returns (uint256 z) {
        require((z = x - y) <= x, "sub-overflow");
    }

    function toRad(uint256 wad) internal pure returns (uint256 rad) {
        rad = mul(wad, 10**27);
    }

    // Adapted from https://github.com/makerdao/dss-proxy-actions/blob/master/src/DssProxyActions.sol#L161
    function _getDrawDart(
        VatLike vat,
        address urn,
        uint256 wad
    ) internal returns (int256 dart) {
        // Updates stability fee rate
        uint256 rate = jug.drip(ilk);

        // Gets DAI balance of the urn in the vat
        uint256 dai = vat.dai(urn);

        // If there was already enough DAI in the vat balance, just exits it without adding more debt
        if (dai < mul(wad, RAY)) {
            // Calculates the needed dart so together with the existing dai in the vat is enough to exit wad amount of DAI tokens
            dart = toInt(sub(mul(wad, RAY), dai) / rate);
            // This is neeeded due to lack of precision. It might need to sum an extra dart wei (for the given DAI wad amount)
            dart = mul(uint256(dart), rate) < mul(wad, RAY) ? dart + 1 : dart;
        }
    }

    // Deposits collateral (gem) and mints DAI
    // Adapted from https://github.com/makerdao/dss-proxy-actions/blob/master/src/DssProxyActions.sol#L639
    function _lockGemAndDraw(uint256 collateralAmount, uint256 daiToMint)
        internal
    {
        address urn = cdpManager.urns(cdpId);
        VatLike vat = VatLike(cdpManager.vat());

        // Takes token amount from the strategy and joins into the vat
        gemJoinAdapter.join(urn, collateralAmount);

        // Locks token amount into the CDP and generates debt
        cdpManager.frob(
            cdpId,
            toInt(collateralAmount),
            _getDrawDart(vat, urn, daiToMint)
        );

        // Moves the DAI amount (balance in the vat in rad) to the strategy
        cdpManager.move(cdpId, address(this), toRad(daiToMint));

        // Allow access to DAI balance in the vat
        vat.hope(address(daiJoinAdapter));

        // Exits DAI to the user's wallet as a token
        daiJoinAdapter.exit(address(this), daiToMint);
    }
}
