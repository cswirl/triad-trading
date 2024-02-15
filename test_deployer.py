import unittest
from collections import namedtuple

from eth_utils import keccak
from eth_abi import encode

from uniswap import uniswap_api
from uniswap.uniswapV3 import Uniswap


from web3 import Web3

weth = Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
usdt = Web3.to_checksum_address("0xdac17f958d2ee523a2206206994597c13d831ec7")
rlb = Web3.to_checksum_address("0x046EeE2cc3188071C02BfC1745A6b17c656e3f3d")

CryptoToken = namedtuple("CryptoToken", ["hex_address", "id", "symbol", "decimals"])

t_weth = CryptoToken(Web3.to_hex(hexstr=weth), weth, "WETH", 18)
t_usdt = CryptoToken(Web3.to_hex(hexstr=usdt), usdt, "USDT", 6)
t_rlb = CryptoToken(Web3.to_hex(hexstr=rlb), rlb, "RLB", 18)

class TestDeployer(unittest.TestCase):

    def test_deploy_1(self):
        """

        :return:
        """
        ROUTER_ADDRESS = Web3.to_checksum_address("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")

        FACTORY_ADDRESS = Web3.to_checksum_address("0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f")

        weth = Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")


    def test_struct_param(self, *args):
        myStruct = {
            'data': 'Hello',
            'issuer': '0x5B38Da6a701c568545dCfcB03FcB875f56beddC4'  # Example address
        }
        keys = ['(address,address)']
        values = [tuple(myStruct.values())]

        encoded = encode(keys, values)

        kecc = keccak(encoded)

        return kecc

    def test_struct_flash_params(self):
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
        swap1_amount = 100
        swap1_amount1 = 0 #0.03978381769984377

        # the fee used in the quoter is the same
        fee1 = 3000
        fee2 = 3000
        fee3 = 3000
        addToDeadline = 200 # seconds

        # this is the order of the pathway triplet
        one = t_usdt
        two = t_weth
        three = t_rlb
        # the first pair is just important for the initFlash to identify the pool address
        zeroForOne = one.hex_address < two.hex_address
        if zeroForOne:
            token0 = one
            amount_0 = int(swap1_amount * (10 ** token0.decimals))
            borrowed_amount = amount_0

            token1 = two
            amount_1 = 0
        else:
            token0 = two
            amount_0 = 0

            token1 = one
            amount_1 =  int(swap1_amount * (10 ** token1.decimals))
            borrowed_amount = amount_1

        # token0 = one if zeroForOne else two
        # token1 = two if zeroForOne else one
        # amount_0 = swap1_amount if zeroForOne else 0
        # amount_1 = 0 if zeroForOne else swap1_amount1

        FlashParams = {
            "token_0": token0.hex_address,
            "token_1": token1.hex_address,
            "amount0": amount_0,  # amount_0 and amount_1 is where the seed amount is - in human or in blockchain?
            "amount1": amount_1,  # not sure if zero will work -other token in a pool where flash is invoked
            "token1": one.hex_address,  # this is the token we need borrowing
            "token2": two.hex_address,
            "token3": three.hex_address,
            "borrowedAmount": borrowed_amount,  # the amount of token in correct decimals
            "quote1": int(0.03978381769984377 * (10 ** two.decimals)),
            "quote2": int(777.5967111439336 * (10 ** three.decimals)),
            "quote3": int(100.196489 * (10 ** one.decimals)),
            "fee1": fee1,
            "fee2": fee2,
            "fee3": fee3,
            "addToDeadline": addToDeadline
        }


        tup = str(FlashParams)

        print(str(tup).replace(" ", ""))

    def test_initFlash(self):
        network = uniswap_api.get_network("testnet")

        provider = Web3.HTTPProvider(network["provider"])
        w3 = Web3(provider)

        uni = Uniswap(network_config=network, provider=provider)









