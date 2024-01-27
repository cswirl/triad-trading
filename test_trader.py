
import unittest

from trader import *


class TestTrader(unittest.TestCase):

    def test_trader_execute_trade(self):

        trader = Trader(['USDC_WETH', 'APE_WETH', 'APE_USDC'])

        trader.start_trading()


    def test_trader_wakeup(self):
        pass

