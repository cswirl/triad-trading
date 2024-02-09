import unittest

import triad_util
from app_constants import *


class TestTriadUtil(unittest.TestCase):

    def test_calculate_seed_fund(self):

        t_symbol = "UNI"
        usd_amount = 10
        output = triad_util.calculate_seed_fund(t_symbol, usd_amount=usd_amount)
        print(f"{usd_amount} USD = {output} {t_symbol}")

    def test_ask_for_funding(self):
        t_symbol = "UNI"

        usd_amount, output = triad_util.ask_for_funding(t_symbol)
        print(f"{usd_amount} USD = {output} {t_symbol}")

        self.test_calculate_seed_fund()

    def test_get_funding_amount(self):
        """
        TODO: GOOD USE OF TESTING! verify this test and enhance
        """
        triplet = "USDC_USDT_DAI"
        triplet_list = triplet.split('_')
        triplet_set = set(triplet_list)

        # FUNDING_TIER_0
        result = triad_util._get_funding_amount(triplet_set)
        assert result == FUNDING_TIER_0

        # FUNDING_TIER_1
        result = triad_util._get_funding_amount({"USDC", "WETH", "FRAX"})
        assert result == FUNDING_TIER_1
        #
        result = triad_util._get_funding_amount({"WBTC", "WETH", "UNI"})
        assert result == FUNDING_TIER_1
        #
        result = triad_util._get_funding_amount({"APE", "DAI", "FRAX"})
        assert result == FUNDING_TIER_1

        # FUNDING_TIER_2
        result = triad_util._get_funding_amount({"APE", "WETH", "FRAX"})
        assert result == FUNDING_TIER_2
        #
        result = triad_util._get_funding_amount({"WBTC", "APE", "UNI"})
        assert result == FUNDING_TIER_2

        # FUNDING_TIER_3
        result = triad_util._get_funding_amount({"APE", "ELON", "FRAX"})
        assert result == FUNDING_TIER_3
        #
        result = triad_util._get_funding_amount({"APE", "ELON", "DAI"})
        assert result == FUNDING_TIER_3



