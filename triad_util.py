from web3 import Web3

from uniswap import uniswap_api
from uniswap.token_pair import Token
from uniswap.uniswapV3 import Uniswap

sqrtPriceLimitX96 = 0
GAS_FEE = 3000

"""
    STEPS:

    1. Filter 1 - Surface Rate
    2. Real Rate
"""

def activate_filter_1():
    """Filter 1 - Surface Rate Calculation

    In Filter 1, we weed out the trading pairs significantly.

	The filtered result will be passed on to the Filter 2.

    Returns:
        surface_dict (list):
    """
    surface_dict = []

    return surface_dict

def get_depth_rate(token0_symbol, token1_symbol, amount_in):
    _sqrtPriceLimitX96 = sqrtPriceLimitX96
    _gas_fee = GAS_FEE

    token0 = uniswap_api.get_token(token0_symbol)
    token1 = uniswap_api.get_token(token1_symbol)

    amount_out = _uniswap.quote_price(token0, token1, amount_in)

    return amount_out



network = uniswap_api.get_network("mainnet")
provider = Web3.HTTPProvider(network["provider"])
_uniswap = Uniswap(network_config=network, provider=provider)