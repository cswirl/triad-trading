import unittest

from web3 import Web3

eth = Web3.to_checksum_address("0x0000000000000000000000000000000000000000")
weth = Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
usdt = Web3.to_checksum_address("0xdac17f958d2ee523a2206206994597c13d831ec7")
vxv = Web3.to_checksum_address("0x7d29a64504629172a429e64183d6673b9dacbfce")

class TestWeb3(unittest.TestCase):

    def test_main(self):

        print(type(eth), eth)


