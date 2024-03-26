import json
from enum import Enum
import web3
from web3 import Web3
from web3.exceptions import TimeExhausted

from uniswap import uniswap_api, uniswap_helper
from uniswap.constants import PAIRS_DELIMITER
from uniswap.uniswapV3 import Uniswap
from uniswap.config_file import *
from app_constants import *             # will override other constants modules?


class FundingResponse(Enum):
    ERROR = 0
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

    fee_tier = int(uniswap_api.find_pair_object(token0_symbol + PAIRS_DELIMITER + token1_symbol).fee_tier) or 3000

    amount_out = uniswap.quote_price_input(token0, token1, amount_in, fee=fee_tier)

    return amount_out, fee_tier

def get_seed_fund(symbol, pathway_triplet_set):

    triplet_set = set(pathway_triplet_set.split(uniswap_api.PATH_TRIPLET_DELIMITER))
    usd_amount_in = _get_funding_amount(triplet_set)

    # None if no pool for a given pair - rare tokens
    # None is something went wrong
    amount_out = convert_usd_to_token(usd_amount_in, symbol) or None

    if amount_out is None:
        return None, None

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

    # sanitation check
    if symbol not in pathway_triplet_set.split(uniswap_api.PATH_TRIPLET_DELIMITER):
        funding_response = FundingResponse.SYMBOL_NOT_IN_PATHWAY_TRIPLET
        return funding_response, None, None

    if symbol not in STARTING_TOKENS:
        funding_response = FundingResponse.SYMBOL_NOT_IN_STARTING_TOKEN
        return funding_response, None, None

    # flash swap do not need the stuffs below, we use the _get_funding_amount()
    #
    # Must check the account balance in a ethereum wallet - use uniswapV3 instance
    # $100 USD or in percentage of available funds like 5%, 10%, whichever is greater?
    triplet_set = set(pathway_triplet_set.split(uniswap_api.PATH_TRIPLET_DELIMITER))
    fund = _get_funding_amount(triplet_set)

    amount_in_usd = fund or MINIMUM_FUNDING_IN_USD  # minimum is 10 as of now
    amount_out = convert_usd_to_token(amount_in_usd, symbol)

    if amount_out is None:
        return FundingResponse.ERROR, None, None

    return FundingResponse.APPROVED, amount_in_usd, amount_out

def convert_usd_to_token(usd_amount, token_symbol_out):
    """
    Convert a USD amount to equivalent token using a live market exchange

    Caveat:
        Rare tokens with no direct pair with stable coins may result in very unfavorable pricing

    :param token_symbol_out (str): symbol of the token to be received
    :param usd_amount: input in USD amount
    :return (float | None): amount_out
    """
    # sanitation check
    if token_symbol_out in STABLE_COINS: return usd_amount

    token1 = uniswap_api.get_token(token_symbol_out)
    amount_out = None
    # try all stable coins - STABLE_COINS are already arranged in preferred order
    for coin in STABLE_COINS:
        stable_coin = uniswap_api.get_token(coin)
        amount_out = uniswap.quote_price_input(stable_coin, token1, usd_amount)
        if amount_out:
            return amount_out

    # If the above didn't work, try STABLES-->WETH--> token out
    # todo: compare results and return the maximum? - waste of infura query limit
    # Low liquidity pools paired with some stablecoins may give unfavorable exchange rate for the token
    if amount_out is None:
        weth = uniswap_api.get_token("WETH")
        for coin in STABLE_COINS:
            stable_coin = uniswap_api.get_token(coin)
            swap1 = uniswap.quote_price_input(stable_coin, weth, usd_amount)
            amount_out = uniswap.quote_price_input(weth, token1, swap1) if swap1 else None

    return amount_out

def flashloan_struct_param(pathway_triplet: str, quotation_dict: dict):
    """
            "Greetings from USDT_WETH_RLB_2f31aaa2-93c5-4540-8cf5-6147d3e79c0e",
            "Active Traders: 156  (inaccurate: testing for sleep calculation)",
            "Test Fund: 100 USDT ---approx. 100 USD",
            "Changing state: 'Hunting Profit'",
            "================================================================================Inquiring price",
            "Quote 1 : 100 USDT to 0.03978381769984377 WETH",
            "Quote 2 : 0.03978381769984377 WETH to 777.5967111439336 RLB",
            "Quote 3 : 777.5967111439336 RLB to 100.196489 USDT",
            "--------------------",
            "Min. rate : 0",
            "PnL : 0.1964889999999997",
            "PnL % : 0.1964889999999997",

            :return:
            """

    first_symbol,second_symbol,third_symbol = pathway_triplet.split(uniswap_api.PATH_TRIPLET_DELIMITER)

    # this is the order of the pathway triplet
    one = uniswap_api.get_token(first_symbol)
    two = uniswap_api.get_token(second_symbol)
    three = uniswap_api.get_token(third_symbol)

    # #
    # quote1 = int(0.03978381769984377 * (10 ** two.decimals))
    # quote2 = int(777.5967111439336 * (10 ** three.decimals))
    # quote3 = int(100.196489 * (10 ** one.decimals))
    # #
    swap1_amount = quotation_dict["seedAmount"]

    addToDeadline = 200  # seconds

    # only the first pair is important to be in correct order for the initFlash to identify the pool address
    # using zeroForOne worked on usdt and weth in which the zeroForOne is WETH_USDT
    zeroForOne = Web3.to_int(hexstr=one.id) < Web3.to_int(hexstr=two.id)
    if zeroForOne:
        token0 = one
        amount_0 = int(swap1_amount * (10 ** token0.decimals))
        borrowed_amount = amount_0

        token1 = two
        amount_1 = 0  # int(0.03978381769984377 * (10 ** two.decimals)) #0
    else:
        token0 = two
        amount_0 = 0  # int(0.03978381769984377 * (10 ** two.decimals)) #0

        token1 = one
        amount_1 = int(swap1_amount * (10 ** token1.decimals))
        borrowed_amount = amount_1

    FlashParams = {
        "token_0": token0.id,   # zeroForOne is used to correct ordering which is token_0 or token_1
        "token_1": token1.id,
        "amount0": amount_0,
        "amount1": amount_1,
        "borrowedAmount": borrowed_amount,  # the amount of token in correct decimals
        "token1": one.id,  # this is the token we need borrowing
        "token2": two.id,
        "token3": three.id,
        "quote1":  uniswap_helper.decimal_right_shift(quotation_dict["quote1"], two.decimals),
        "quote2": uniswap_helper.decimal_right_shift(quotation_dict["quote2"], three.decimals),
        "quote3": uniswap_helper.decimal_right_shift(quotation_dict["quote3"], one.decimals),
        "fee1": quotation_dict["fee1"],
        "fee2": quotation_dict["fee2"],
        "fee3": quotation_dict["fee3"],
        "sqrtPriceLimitX96": 0,         # we do not understand this as of now
        "addToDeadline": addToDeadline
    }

    return FlashParams

def execute_flash(flashParams_dict: dict):
    # Transaction variables

    flash = uniswap.flash_loan
    if flash is None:
        print("Error: flash loan contract did not load properly")
        return (False, None, None)

    # # Build Transaction -
    # tx_build = flash.functions.initFlash(flashParams_dict).build_transaction({
    #     # "from": uniswap.address,
    #     # "chainId": chain_id,
    #     # "value": 0,
    #     # "gas": gas,
    #     # "gasPrice": gas_price,
    #     # "nonce": nonce
    #     "chainId": chain_id,
    #     "value": 0,
    #     "gas": gas,
    #     "gasPrice": gas_price,
    #     "nonce": nonce
    # })

    tx_build = flash.functions.initFlash(flashParams_dict).build_transaction({
        "nonce": uniswap.last_nonce,
        "chainId": uniswap.chain_id,
        "value": 0,
        "gas": 300000,
        "gasPrice": Web3.to_wei("5.5", "gwei")
    })

    # Sign transaction
    tx_signed = w3.eth.account.sign_transaction(tx_build, private_key=uniswap.private_key)

    # Send transaction
    sent_tx = w3.eth.send_raw_transaction(tx_signed.rawTransaction)
    tx_hash = w3.to_hex(sent_tx)

    try:
        # see https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.wait_for_transaction_receipt
        tx_receipt = w3.eth.wait_for_transaction_receipt(sent_tx, timeout=flashParams_dict["addToDeadline"])
        print(tx_hash)

        return (int(tx_receipt["status"]), tx_hash, tx_receipt)
    except TimeExhausted as e:
        print(f"Error - TimeExhausted - {e} - hash: {tx_hash}")
        return (False, tx_hash, None)


def load_keys_from_file():

    #filename = os.path.join(KEYS_FOLDER_PATH, 'pkeys.json')
    file_path = "uniswap/vault/pkeys.json"
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            print(f"json data from {file_path} was loaded")
            return data
    except FileNotFoundError:
        print(f"error loading json data: File '{file_path}' not found.")
    except json.JSONDecodeError:
        print(f"error decoding JSON in file '{file_path}'.")

<<<<<<< HEAD

keys = load_keys_from_file()
network = uniswap_api.get_network("sepolia")
=======
networkName = "sepolia"
keys = uniswap_helper.load_keys_from_file()
network = uniswap_api.get_network(networkName)
print(f"running on network: {network}")
>>>>>>> sol_pair_flash
provider = Web3.HTTPProvider(network["provider"])
w3 = Web3(provider)
uniswap = Uniswap(pKeys=keys, network_config=network, provider=provider)


