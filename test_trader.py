import asyncio
import unittest
from datetime import datetime

import trader as trader_MODULE
from trader import Trader
from uniswap import uniswap_api, utils
import triad_util
import triad_module

TRADER_LIST_LIMIT = 30  # Number of Traders. Use 0 for to get ALL


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



class TestTrader(unittest.TestCase):

    def test_trader_execute_trade(self):
        asyncio.run(self._test_trader_execute_trade())

    async def _test_trader_execute_trade(self):
        # triad_util.get_depth_rate,
        trader = Trader(
            "USDC_WETH_APE",
            triad_util.get_depth_rate,
            calculate_seed_fund=triad_util.calculate_seed_fund
        )
        traders_list = [trader]

        await asyncio.gather(trader.start_trading(), self.handle_user_input(traders_list))


    def test_multiple_trader_instance(self):
        asyncio.run(self._multiple_trader_instance())

    async def _multiple_trader_instance(self):
        traders_list = self._traders_list()

        coroutine_list = []
        for trader in traders_list:
            coroutine_list.append(trader.start_trading())

        trader_MODULE.TOTAL_ACTIVE_TRADERS = len(traders_list) * 1.5

        await asyncio.gather(*coroutine_list, trader_MODULE.trader_monitor(traders_list))

    def _traders_list(self):
        triplets_set, triplets_list = extract_triplets()

        pathway_triplet_list = []
        for triplet in triplets_set:
            unfreeze_set = set(triplet)
            seed_token = self.test_extract_seed_token(unfreeze_set)

            forward_reverse_tuple = self.test_create_two_pathways(seed_token, unfreeze_set)
            if forward_reverse_tuple:
                pathway_triplet_list.extend([*forward_reverse_tuple])

        if len(pathway_triplet_list) < 1: return None

        limit = 1000
        pathway_triplet_list_LIMITED = pathway_triplet_list[0:limit] if len(
            pathway_triplet_list) >= limit else pathway_triplet_list

        traders_list = []
        for pathway_triplet in pathway_triplet_list_LIMITED:
            # triad_util.get_depth_rate,
            trader = Trader(
                pathway_triplet,
                triad_util.get_depth_rate,
                calculate_seed_fund=triad_util.calculate_seed_fund
            )
            traders_list.append(trader)

        limit = TRADER_LIST_LIMIT or len(traders_list)
        return traders_list[0:limit]

    async def handle_user_input(self, traders_list):
        while True:
            command = await asyncio.to_thread(input, "Type what to halt: HUNTING ( hunt | resume ) : STOP ALL (stop) : ")
            if command == "hunt":
                print("Halting traders hunting for profit . . .")
                for trader in traders_list:
                    trader.hunt_profit_flag = False
            if command == "resume":
                print("Resume traders hunting for profit . . .")
                for trader in traders_list:
                    trader.hunt_profit_flag = True
            elif command == "stop":
                for trader in traders_list:
                    trader.start_trading_flag = False
                print("Exiting the program . . .")
                break

    def test_extract_triplets(self):

        weth = "WETH"
        stablecoins = set(uniswap_api.STABLE_COINS)

        triplets_with_stablecoin_list = []

        triplets_set, triplets_list = extract_triplets()
        weth_count  = 0
        non_weth_agg = []
        stablecoins_intersects_agg = []
        for s in triplets_set:
            if weth in s:
                weth_count += 1
            else:
                non_weth_agg.append(s)
            # get the intersection
            if len(stablecoins & s) > 0:
                triplets_with_stablecoin_list.append(s)
                stablecoins_intersects_agg.append(stablecoins & s)


        return

    def test_ask_for_funding(self):
        pass

    def test_extract_seed_token(self, triplets_set_arg):
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

    def test_create_two_pathways(self, seed_token, triplets_set):
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

    def test_trader_monitor(self):
        traders_list = self._traders_list()

        asyncio.run(trader_MODULE.trader_monitor(traders_list))



    #------------------------------------------------------------------------------------
    def _test_depth_rate(self, token0_symbol, token1_symbol, amount_in):
        return amount_in * 1.03 # give 3% profit each trade - accumulates
