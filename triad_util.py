from enum import Enum

from web3 import Web3

from uniswap import uniswap_api
from uniswap.token_pair import Token
from uniswap.uniswapV3 import Uniswap
from uniswap.config_file import *
from app_constants import *             # will override other constants modules?


class FundingResponse(Enum):
    APPROVED = 1
    MAX_TRADING_TRANSACTIONS_EXCEEDED = 2
    CONSECUTIVE_FAILED_TRADE_THRESHOLD_EXCEEDED = 3
    SYMBOL_NOT_IN_PATHWAY_TRIPLET = 4
    SYMBOL_NOT_IN_STARTING_TOKEN = 5



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

    amount_out = _uniswap.quote_price_input(token0, token1, amount_in)

    return amount_out

def calculate_seed_fund(symbol, pathway_triplet_set, stable_coin="USDC"):

    stable_coin = uniswap_api.get_token(stable_coin)
    token1 = uniswap_api.get_token(symbol)

    triplet_set = set(pathway_triplet_set.split(uniswap_api.PATH_TRIPLET_DELIMITER))
    usd_amount_in = _get_funding_amount(triplet_set)

    if symbol in STABLE_COINS:
        return  usd_amount_in, usd_amount_in

    # None if no pool of a given pair - rare tokens
    amount_out = _uniswap.quote_price_input(stable_coin, token1, usd_amount_in)

    if amount_out is None:
        #todo: calculate_seed_fund
        # try using path: usd -> weth -> rare token
        # but this is to be solved next since we are not interested to start trade with rare tokens
        # for now we use hard-coded 500 units for rare tokens
        return 500

    return usd_amount_in, amount_out



def _get_funding_amount(triplet_set):
    """
    classifications and combinations is complex. Venn Diagram was used and still a work in progress. see notes on Arbitrage notebook.

    :param triplet_set (set):
    :return:
    """
    stablecoins_intersect = len(triplet_set & set(STABLE_COINS))
    approved_intersect = len(triplet_set & set(APPROVED_TOKENS))
    starting_tokens_intersect = len(triplet_set & set(STARTING_TOKENS)) # MIXED OF STABLE COINS AND APPROVED TOKENS

    # the if-elif order is important - priority on top
    # notice at the top is FUNDING_TIER_0 --> FUNDING_TIER_1 --> FUNDING_TIER_2 and so on.
    #
    # TIER 0
    if stablecoins_intersect == 3:    # all stable coins - hard to get profits
        return FUNDING_TIER_0

    # TIER 1
    elif starting_tokens_intersect == 3:  # two in starting tokens
        return FUNDING_TIER_1
    elif approved_intersect == 3:    # all in starting tokens
        return FUNDING_TIER_1
    elif stablecoins_intersect == 2:  # two stable coins
        return FUNDING_TIER_1

    # TIER 2
    elif starting_tokens_intersect == 2:  # two in starting tokens
        return FUNDING_TIER_2
    elif approved_intersect == 2:
        return FUNDING_TIER_2

    # TIER 3
    elif starting_tokens_intersect == 1: # one in the mixed both - STARTING TOKENS
        return FUNDING_TIER_3

    # if it passes all the filters above - triplet of rare coins
    return MINIMUM_FUNDING_IN_USD

def ask_for_funding(symbol: str, pathway_triplet_set: str):
    # see app constant
    # MAX_TRADING_COUNT = 5  # losing gas fee for every reverted / fail triangular trade

    if symbol not in STARTING_TOKENS:
        funding_response = FundingResponse.SYMBOL_NOT_IN_STARTING_TOKEN
        return funding_response, None, None

    # sanitation check
    if symbol not in pathway_triplet_set.split(uniswap_api.PATH_TRIPLET_DELIMITER):
        funding_response = FundingResponse.SYMBOL_NOT_IN_PATHWAY_TRIPLET
        return funding_response, None, None

    # max transaction count reached
    if g_trade_transaction_counter > MAX_TRADING_TRANSACTIONS:
        funding_response = FundingResponse.MAX_TRADING_TRANSACTIONS_EXCEEDED
        return funding_response, None, None

    # consecutive trade failure
    if g_consecutive_trade_failure > CONSECUTIVE_FAILED_TRADE_THRESHOLD:
        funding_response = FundingResponse.CONSECUTIVE_FAILED_TRADE_THRESHOLD_EXCEEDED
        return funding_response, None, None

    # flash swap do not need the stuffs below, we use the _get_funding_amount()
    # must check the account balance in a ethereum wallet - use uniswapV3 instance
    # $100 USD or in percentage of available funds like 5%, 10%, whichever is greater?
    triplet_set = set(pathway_triplet_set.split(uniswap_api.PATH_TRIPLET_DELIMITER))
    fund = _get_funding_amount(triplet_set)

    amount_in_usd = fund or MINIMUM_FUNDING_IN_USD  # minimum is 10 as of now
    amount_out = get_token_price_in_usd(symbol, usd_amount=amount_in_usd)

    return FundingResponse.APPROVED, amount_in_usd, amount_out

def get_token_price_in_usd(symbol, stable_coin="USDC", usd_amount=100):
    stable_coin = uniswap_api.get_token(stable_coin)
    token1 = uniswap_api.get_token(symbol)

    usd_amount_in = usd_amount
    fee = 3000

    is_stables = symbol in STABLE_COINS
    if is_stables: return usd_amount_in

    # None if no pool of a given pair - rare tokens
    amount_out = _uniswap.quote_price_input(stable_coin, token1, usd_amount_in)

    return amount_out


network = uniswap_api.get_network("mainnet")
provider = Web3.HTTPProvider(network["provider"])
_uniswap = Uniswap(network_config=network, provider=provider)


# global counter variables
g_trade_transaction_counter = 0
g_consecutive_trade_failure = 0