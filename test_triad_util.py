import unittest

import triad_util
from app_constants import *


class TestTriadUtil(unittest.TestCase):

    def test_convert_usd_to_token(self):
        usd_amount = 100

        # Non - stable coins
        result = triad_util.convert_usd_to_token(usd_amount, "WETH")
        assert result is not None

        # stable coin
        result = triad_util.convert_usd_to_token(usd_amount, "DAI")
        assert result == usd_amount

        # Rare token
        result = triad_util.convert_usd_to_token(usd_amount, "RNG")
        assert result is not None

        # Non-existent coin
        result = triad_util.convert_usd_to_token(usd_amount, "random coin fdsa")
        assert result is None



    def test_calculate_seed_fund(self):

        t_symbol = "UNI"
        usd_amount, amount_out = triad_util.get_seed_fund(t_symbol, "WETH_UNI_USDC")
        print(f"{usd_amount} USD = {amount_out} {t_symbol}")


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


    def test_ask_for_funding(self):
        """
        todo: need rigorous test
        """

        # symbol not it triplet
        symbol = "AAVE"
        triplet = "WETH_RNG_PENDLE"
        a, b, c = triad_util.ask_for_funding(symbol, triplet)
        assert a == triad_util.FundingResponse.SYMBOL_NOT_IN_PATHWAY_TRIPLET

        # max trading transactions
        triad_util.g_trade_transaction_counter = MAX_TRADING_TRANSACTIONS + 1
        symbol = "WETH"
        triplet = "USDC_WETH_AAVE"
        a, b, c = triad_util.ask_for_funding(symbol, triplet)
        assert a == triad_util.FundingResponse.MAX_TRADING_TRANSACTIONS_EXCEEDED

        # reset variables used above - there must be a better way
        triad_util.g_trade_transaction_counter = 0

        # consecutive failed trades
        triad_util.g_consecutive_trade_failure = CONSECUTIVE_FAILED_TRADE_THRESHOLD + 1
        symbol = "WETH"
        triplet = "USDC_WETH_AAVE"
        a, b, c = triad_util.ask_for_funding(symbol, triplet)
        assert a == triad_util.FundingResponse.CONSECUTIVE_FAILED_TRADE_THRESHOLD_EXCEEDED

        # reset variables used above - there must be a better way
        triad_util.g_consecutive_trade_failure = 0

        #============================================
        symbol = "WETH"
        triplet = "USDC_WETH_AAVE"
        a,b,c = triad_util.ask_for_funding(symbol, triplet)
        assert a == triad_util.FundingResponse.APPROVED
        assert b == FUNDING_TIER_2   # USDC_WETH
        print(f"{b} USD in = {c} {symbol} out")    # amount based on market rate

        # FUNDING_TIER_3
        symbol = "WETH"
        triplet = "WETH_RNG_PENDLE"
        a, b, c = triad_util.ask_for_funding(symbol, triplet)
        assert a == triad_util.FundingResponse.APPROVED
        assert b == FUNDING_TIER_3  # WETH
        print(f"{b} USD in = {c} {symbol} out")  # amount based on market rate

    def test__get_flashswap_loaners(self):
        result = triad_util._get_flashswap_loaners("DOG","WETH",3000)
        reverse_res = triad_util._get_flashswap_loaners("WETH","DOG",3000)
        pass


