
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

def get_depth_rate(address_from, address_to, amount_in):
    _sqrtPriceLimitX96 = sqrtPriceLimitX96
    _gas_fee = GAS_FEE

    # return result from blockchain quoter
    amount = 1

    return amount



