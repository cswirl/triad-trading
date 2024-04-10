# This is a sample Python script.
import asyncio

import global_triad as gt
import test_trader
import trader as trader_MODULE
from trader import Trader
from uniswap import uniswap_api, utils
import triad_util
import triad_module

from app_constants import *
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

async def entry_point_multiple_trader_instance():

    gt.g_trader_list = _traders_list()

    # testing
    gt.g_total_active_traders = len(gt.g_trader_list)

    coroutine_list = []
    for trader in gt.g_trader_list:
        coroutine_list.append(trader.start_trading())

    await asyncio.gather(trader_MODULE.trader_monitor(gt.g_trader_list), *coroutine_list)


def extract_seed_token(triplets_set_arg):
    """

    """
    delim = "_"

    trading_pairs = ['USDC_WETH', 'USDC_UST', 'UST_WETH']

    trade_sequence = ['USDC_WETH', 'UST_WETH', 'USDC_UST']

    triplets_set = triplets_set_arg # {"USDC", "WETH", "UST"}

    weth = "WETH"

    STABLE_COINS = ["USDC", "USDT", "DAI", "FRAX"]
    STARTING_TOKENS = [*STABLE_COINS, "WETH", "WBTC", "UNI"]  # ROUGH DRAFT

    approved_tokens_list = STARTING_TOKENS
    approved_tokens_set = set(approved_tokens_list)

    approved_tokens_intersect = triplets_set & approved_tokens_set

    seed_token = None
    if len(approved_tokens_intersect) == 1: # we found the seed token
        seed_token = approved_tokens_intersect.pop()

    elif len(approved_tokens_intersect) == 2 or len(approved_tokens_intersect) == 3: # 3: all are stable coins
        for token in approved_tokens_list: # the stablecoins_list must be in order of preference
            if token in approved_tokens_intersect:
                seed_token = token
                break
    else:
        print("Token not in approved list")
        return None

    # seed token = "USDC"

    return seed_token

def create_two_pathways(seed_token, triplets_set):
    delim = "_"
    # the forward and reverse pathway "USDC" - {"WETH", "UST"}
    # forward
    remaining_set = triplets_set.difference({seed_token})
    remaining_list = list(remaining_set)
    if len(remaining_list) > 2:
        # seed token is not in the approved list or None
        return None

    forward_path = seed_token + delim + remaining_list[0] + delim + remaining_list[1]
    reverse_path = seed_token + delim + remaining_list[1] + delim + remaining_list[0]

    return forward_path, reverse_path

def _traders_list():

    triplets_set, triplets_list = extract_triplets()

    pathway_triplet_list = []
    for triplet in triplets_set:
        unfreeze_set = set(triplet)
        seed_token = extract_seed_token(unfreeze_set)

        forward_reverse_tuple = create_two_pathways(seed_token, unfreeze_set)
        if forward_reverse_tuple:
            pathway_triplet_list.extend([*forward_reverse_tuple])

    if len(pathway_triplet_list) < 1: return None

    limit = 1000
    pathway_triplet_list_LIMITED = pathway_triplet_list[0:limit] if len(
        pathway_triplet_list) >= limit else pathway_triplet_list

    gt.g_total_active_traders = len(pathway_triplet_list_LIMITED)

    traders_list = []
    for pathway_triplet in pathway_triplet_list_LIMITED:
        trader = Trader(
            pathway_triplet,
            triad_util.get_depth_rate,
            test_trader.test_execute_flash,   # triad_util.execute_flash  #
            calculate_seed_fund=triad_util.get_seed_fund
        )
        traders_list.append(trader)

    limit = TRADER_LIST_LIMIT or len(traders_list)
    return traders_list[0:limit]

def extract_triplets():

    delim = uniswap_api.PAIRS_DELIMITER

    combined_list = triad_module.triad_trading_pairs(uniswap_api.TRIANGLE_STRUCTURE_PAIRS)

    triplets_set = set({})
    for combined in combined_list:                                      # combined example: : 'DAI_WETH,RAI_WETH,RAI_DAI'
        a,b,c = combined.split(',')                                     # a = 'DAI_WETH'
        triplet = {*a.split(delim), *b.split(delim),*c.split(delim)}    # using a set to avoid duplicates
        triplet_sorted = sorted(triplet)                                # use sort to easily identify duplicates
        # remember that sets have no order
        # - trust that frozenset preserves the order internally
        triplets_set.add(frozenset(triplet_sorted))                     # using a set to avoid duplicates - required to use frozenset

    triplets_list = [list(x)for x in triplets_set]
    # print in json format
    file_path = utils.filepath_builder(utils.DATA_FOLDER_PATH, "pathway_triplets.json")
    utils.save_json_to_file(triplets_list, file_path)

    return triplets_set, triplets_list

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print("hello")
    asyncio.run(entry_point_multiple_trader_instance())
