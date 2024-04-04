// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity =0.7.6;
pragma abicoder v2;

import '@uniswap/v3-core/contracts/interfaces/callback/IUniswapV3FlashCallback.sol';
import '@uniswap/v3-core/contracts/libraries/LowGasSafeMath.sol';

import '@uniswap/v3-periphery/contracts/base/PeripheryPayments.sol';
import '@uniswap/v3-periphery/contracts/base/PeripheryImmutableState.sol';
import '@uniswap/v3-periphery/contracts/libraries/PoolAddress.sol';
import '@uniswap/v3-periphery/contracts/libraries/CallbackValidation.sol';
import '@uniswap/v3-periphery/contracts/libraries/TransferHelper.sol';
import '@uniswap/v3-periphery/contracts/interfaces/ISwapRouter.sol';

/// @title Flash contract implementation
/// @notice An example contract using the Uniswap V3 flash function
contract PairFlash is IUniswapV3FlashCallback, PeripheryImmutableState, PeripheryPayments {
    using LowGasSafeMath for uint256;
    using LowGasSafeMath for int256;

    event LogCallBackInitParams(address token1, address token2, address token3, uint256 borrowedAmount);
    event Result(uint256 swap3_amountOut, uint256 totalOwing);

    ISwapRouter public immutable swapRouter;

    constructor(
        ISwapRouter _swapRouter,
        address _factory,
        address _WETH9
    ) PeripheryImmutableState(_factory, _WETH9) {
        swapRouter = _swapRouter;
    }

    function _triArbSwap(FlashCallbackData memory decoded) internal returns (uint256) {

        // get pathway triplet token addresses
        address token1 = decoded.token1;
        address token2 = decoded.token2;
        address token3 = decoded.token3;

        // If any one of the three swaps fails, the whole transaction will fail because
        //  exactInputSingle will throw an error: - if result is less than amountOutMinimum
        //  - require(amountOut >= params.amountOutMinimum, 'Too little received');

        // swap 1: swapping token1 for token2 in pool - use fee0 from callback argument
        TransferHelper.safeApprove(token1, address(swapRouter), decoded.borrowedAmount);

        uint256 swap1_amountOut =
            swapRouter.exactInputSingle(
                ISwapRouter.ExactInputSingleParams({
                    tokenIn: token1,
                    tokenOut: token2,
                    fee: decoded.poolFee1,
                    recipient: address(this),
                    deadline: block.timestamp + decoded.addToDeadline,
                    amountIn: decoded.borrowedAmount,
                    amountOutMinimum: decoded.quote1,
                    sqrtPriceLimitX96: decoded.sqrtPriceLimitX96
                })
            );

        // swap 2: swapping token 2 for token 3 - using fee used in quotation
        TransferHelper.safeApprove(token2, address(swapRouter), swap1_amountOut);

        uint256 swap2_amountOut =
            swapRouter.exactInputSingle(
                ISwapRouter.ExactInputSingleParams({
                    tokenIn: token2,
                    tokenOut: token3,
                    fee: decoded.poolFee2,
                    recipient: address(this),
                    deadline: block.timestamp + decoded.addToDeadline,
                    amountIn: swap1_amountOut,
                    amountOutMinimum: decoded.quote2,
                    sqrtPriceLimitX96: decoded.sqrtPriceLimitX96
                })
            );

        // swap 3: swapping token 3 for token 1 - using fee used in quotation
        TransferHelper.safeApprove(token3, address(swapRouter), swap2_amountOut);

        uint256 swap3_amountOut =
            swapRouter.exactInputSingle(
                ISwapRouter.ExactInputSingleParams({
                    tokenIn: token3,
                    tokenOut: token1,
                    fee: decoded.poolFee3,
                    recipient: address(this),
                    deadline: block.timestamp + decoded.addToDeadline,
                    amountIn: swap2_amountOut,
                    amountOutMinimum: decoded.quote3,
                    sqrtPriceLimitX96: decoded.sqrtPriceLimitX96
                })
            );

        // this calculation recognized that the fee is included for each swap
        // - however, the cost for the whole transaction is not included in the calculation

        return swap3_amountOut;
    }

    /// @param fee0 The fee from calling flash for token0
    /// @param fee1 The fee from calling flash for token1
    /// @param data The data needed in the callback passed as FlashCallbackData from `initFlash`
    /// @notice implements the callback called from flash
    /// @dev fails if the flash is not profitable, meaning the amountOut from the flash is less than the amount borrowed
    function uniswapV3FlashCallback(
        uint256 fee0,
        uint256 fee1,
        bytes calldata data
    ) external override {
        FlashCallbackData memory decoded = abi.decode(data, (FlashCallbackData));
        CallbackValidation.verifyCallback(factory, decoded.poolKey);

        // When this callback is invoked, it means this contract was already funded using pool.flash
        // in the function initFlash and stored in FlashCallbackData.borrowedAmount
        // and that value can be accessed here via the decoded.borrowedAmount

        uint256 amount0Owed = LowGasSafeMath.add(decoded.amount0, fee0);
        uint256 amount1Owed = LowGasSafeMath.add(decoded.amount1, fee1);

        // Calculate the amount to repay at the end
        uint256 totalOwing = decoded.borrowedAmount * (1 + decoded.poolFee1 / 1e6);

        // get pathway triplet token addresses
        address token1 = decoded.token1;
        address token2 = decoded.token2;
        address token3 = decoded.token3;

        emit LogCallBackInitParams(token1, token2, token3, decoded.borrowedAmount);

        uint256 swap3_amountOut = _triArbSwap(decoded);

        // this minimum check must be met - it may save some gas
        // - any profits even tiny will help offset the transaction cost, at the least
        emit Result(swap3_amountOut, totalOwing);

        // Try Counterflow Triangular
        if (swap3_amountOut <= totalOwing && decoded.counterFlow) {
            // Re-arrange tokens
            address tmp1 = decoded.token2;
            decoded.token2 = decoded.token3;
            decoded.token3 = tmp1;
            // Re-arrange Pool Fees
            uint24 feeTemp = decoded.poolFee1;
            decoded.poolFee1 = decoded.poolFee3;
            decoded.poolFee3 = feeTemp;

            swap3_amountOut = _triArbSwap(decoded);
            emit Result(swap3_amountOut, totalOwing);
        }

        // if a losing trade, the payback to the pool will fail, thus, the whole transaction will revert itself
        // if profitable, send profits to payer-->our wallet: decoded.payer

        // pay back the pool: pay both to make sure we don't miss any OR ELSE whole transaction will fail
        TransferHelper.safeApprove(decoded.poolKey.token0, address(this), amount0Owed);
        TransferHelper.safeApprove(decoded.poolKey.token1, address(this), amount1Owed);
        // pool address-->msg.sender
        if (amount0Owed > 0) pay(decoded.poolKey.token0, address(this), msg.sender, amount0Owed);
        if (amount1Owed > 0) pay(decoded.poolKey.token1, address(this), msg.sender, amount1Owed);

        // pay our wallet-->decoded.payer
        int256 profit = LowGasSafeMath.sub(int256(swap3_amountOut), int256(decoded.borrowedAmount));
        if (profit > 0) {
            uint256 profit0 = LowGasSafeMath.sub(swap3_amountOut, decoded.borrowedAmount);
            TransferHelper.safeApprove(token1, address(this), profit0);
            pay(token1, address(this), decoded.payer, profit0);
        }

    }

    //fee1, fee2, fee3 are the ones we used in the Quoter - from python program
    struct FlashParams {
        address token_0;
        address token_1;
        uint24 fee0;
        uint256 amount0;
        uint256 amount1;
        uint256 borrowedAmount;
        address token1;
        address token2;
        address token3;
        uint256 quote1;
        uint256 quote2;
        uint256 quote3;
        uint24 fee1;
        uint24 fee2;
        uint24 fee3;
        uint24 sqrtPriceLimitX96;
        uint24 addToDeadline;
        bool counterFlow;
    }
    //
    struct FlashCallbackData {
        uint256 amount0;
        uint256 amount1;
        uint256 borrowedAmount;
        address token1;
        address token2;
        address token3;
        uint256 quote1;
        uint256 quote2;
        uint256 quote3;
        address payer;
        PoolAddress.PoolKey poolKey;
        uint24 poolFee1;
        uint24 poolFee2;
        uint24 poolFee3;
        uint24 sqrtPriceLimitX96;
        uint24 addToDeadline;
        bool counterFlow;
    }

    /// @param params The parameters necessary for flash and the callback, passed in as FlashParams
    /// @notice Calls the pools flash function with data needed in `uniswapV3FlashCallback`
    function initFlash(FlashParams memory params) external {

        // token0 and token1 must be in correct place or else ot will throw exception because
        // PoolAddress.computeAddress function has require(key.token0 < key.token1)
        PoolAddress.PoolKey memory poolKey = PoolAddress.PoolKey({
            token0: params.token_0,
            token1: params.token_1,
            fee: params.fee0
            });

        IUniswapV3Pool pool = IUniswapV3Pool(PoolAddress.computeAddress(factory, poolKey));

        // recipient of borrowed amounts - recipient of flash should be THIS contract address
        // amount of token0 requested to borrow
        // amount of token1 requested to borrow
        //  - need amount 0 and amount1 in callback to pay back pool
        pool.flash(
            address(this),
            params.amount0,
            params.amount1,
            abi.encode(
                FlashCallbackData({
                    amount0: params.amount0,
                    amount1: params.amount1,
                    borrowedAmount: params.borrowedAmount,
                    token1: params.token1,
                    token2: params.token2,
                    token3: params.token3,
                    quote1: params.quote1,
                    quote2: params.quote2,
                    quote3: params.quote3,
                    payer: msg.sender,
                    poolKey: poolKey,
                    poolFee1: params.fee1,
                    poolFee2: params.fee2,
                    poolFee3: params.fee3,
                    sqrtPriceLimitX96: params.sqrtPriceLimitX96,
                    addToDeadline: params.addToDeadline,
                    counterFlow: params.counterFlow
                })
            )
        );
    }
}

