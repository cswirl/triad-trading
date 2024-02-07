import asyncio
import unittest

from trader import Trader
from uniswap import uniswap_api, utils
import triad_util
import triad_module



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
        extract_triplets()

        #triad_util.get_depth_rate,
        trader = Trader(
            self._test_depth_rate,
            calculate_seed_fund=triad_util.calculate_seed_fund,
            pathway = ['USDC_WETH', 'APE_WETH', 'APE_USDC'],
            pathway_triplet = "USDC_WETH_APE")
        asyncio.run(trader.start_trading())

    def test_multiple_trader_instance(self):
        asyncio.run(self._multiple_trader_instance())

    async def _multiple_trader_instance(self):





        trader1 = Trader(pathway = ['USDC_WETH', 'APE_WETH', 'APE_USDC'], pathway_triplet = "USDC_WETH_APE")
        trader2 = Trader(pathway=['APE_WETH', 'APE_USDC', 'USDC_WETH'], pathway_triplet = "WETH_APE_USDC")
        traders = [trader1, trader2]

        coroutine_list = []
        for trader in traders:
            coroutine_list.append(trader.start_trading())

        await asyncio.gather(*coroutine_list)


    def _test_depth_rate(self, token0_symbol, token1_symbol, amount_in):
        return amount_in * 1.03 # give 3% profit each trade - accumulates


    def test_extract_triplets(self):

        weth = "WETH"
        stablecoins = uniswap_api.STABLE_COINS
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