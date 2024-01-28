import asyncio
import unittest

from trader import *


class TestTrader(unittest.TestCase):

    def test_trader_execute_trade(self):
        trader = Trader(['USDC_WETH', 'UST_WETH', 'USDC_UST'])
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


    def test_trader_wakeup(self):
        pass

