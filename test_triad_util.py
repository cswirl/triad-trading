import unittest

import triad_util

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