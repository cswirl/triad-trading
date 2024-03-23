
import unittest
from collections import namedtuple

from web3 import Web3
from web3.exceptions import ContractLogicError

from uniswap import utils, uniswap_api, uniswap_helper
from uniswap.config_file import *
from uniswap.uniswapV3 import Uniswap




TIER_100 = 100
TIER_500 = 500
TIER_3000 = 3000
TIER_10000 = 10000

fee = TIER_10000

keys = uniswap_helper.load_keys_from_file()
network = uniswap_api.get_network("sepolia")
provider = Web3.HTTPProvider(network["provider"])
w3 = Web3(provider)
_uniswap = Uniswap(pKeys=keys, network_config=network, provider=provider)

eth = Web3.to_checksum_address("0x0000000000000000000000000000000000000000")
weth = Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
usdt = Web3.to_checksum_address("0xdac17f958d2ee523a2206206994597c13d831ec7")
usdc = Web3.to_checksum_address("0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48")
sushi = Web3.to_checksum_address("0x6B3595068778DD592e39A122f4f5a5cF09C90fE2")
ape = Web3.to_checksum_address("0x4d224452801aced8b2f0aebe155379bb5d594381")

CryptoToken = namedtuple("CryptoToken", ["id", "symbol", "decimals"])

t_weth = CryptoToken(weth, "WETH", 18)
t_usdt = CryptoToken(usdt, "USDT", 6)
t_usdc = CryptoToken(usdc, "USDC", 6)
t_ape = CryptoToken(ape, "APE", 18)

usdc_decimals = 6
weth_decimals = 18

# new
token1 = CryptoToken(Web3.to_checksum_address("0xaC5e009C07540172DD8457Be7961895d58e4aD2d"), "USDC", 18)
token2 = CryptoToken(Web3.to_checksum_address("0xdC0b7c0693B7689B324A0Ef8Ab210609Ba0cF994"), "WDS", 18)
token3 = CryptoToken(Web3.to_checksum_address("0xDE3fC64BD79c1806Cb17F1C2eb794882114ca1cE"), "YT", 18)


def path_builder(fee):
    """
    USDC, 60, WETH
    WETH, 60, APE
    APE, 60, USDC

    USDC, 60, WETH, 60, APE, 60, USDC

    USDC60WETH60APE60USDC - this is what is needed in bytes. Replace the symbols with hex addresses

    :param args:
    :return:
    """

    byte_usdc = Web3.to_bytes(hexstr=usdc)
    byte_fee = fee.to_bytes(3, byteorder='big')
    byte_weth = Web3.to_bytes(hexstr=weth)
    byte_ape = Web3.to_bytes(hexstr=ape)

    # USDC, 60, WETH, 60, APE, 60, USDC
    path = bytes(byte_usdc + byte_fee + byte_weth + byte_fee + byte_ape + byte_fee + byte_usdc)

    return path



class TestUniswapApi(unittest.TestCase):

    def test_deployer(self):
        pass

    def test_quoter_compare(self):
        """
        May only work in mainnet as it is using Quoter not QuoterV2

        """
        print("============ QUOTER COMPARE ===============")
        multi_output_amount =  self._test_quoter_multipool()
        print(f"Multipool Output amount: {multi_output_amount}")
        print("-------------------------------")
        # Three separate swaps
        seed_amount = 100

        swap1_output = _uniswap.quote_price_input(t_usdc, t_weth, seed_amount)
        print(f"Swap 1 : Swapping {seed_amount} {t_usdc.symbol} to {swap1_output} {t_weth.symbol}")
        # swap 2
        swap2_output = _uniswap.quote_price_input(t_weth, t_ape, swap1_output)
        print(f"Swap 2 : Swapping {swap1_output} {t_weth.symbol} to {swap2_output} {t_ape.symbol}")
        # swap 3
        swap3_output = _uniswap.quote_price_input(t_ape, t_usdc, swap2_output)
        print(f"Swap 3 : Swapping {swap2_output} {t_ape.symbol} to {swap3_output} {t_usdc.symbol}")

    def test_quoter_single(self):
        """
        token1 = CryptoToken(Web3.to_checksum_address("0xaC5e009C07540172DD8457Be7961895d58e4aD2d"), "USDC", 18)
        token2 = CryptoToken(Web3.to_checksum_address("0xdC0b7c0693B7689B324A0Ef8Ab210609Ba0cF994"), "WDS", 18)
        token3 = CryptoToken(Web3.to_checksum_address("0xDE3fC64BD79c1806Cb17F1C2eb794882114ca1cE"), "YT", 18)
        :return:
        """
        amount_in = 10
        stable = token1

        amount_out = _uniswap.quote_price_input(token2, stable, amount_in)
        print(f"Quoter : Swapping {amount_in} {token2.symbol} for {amount_out} {stable.symbol}")

        amount_in = amount_out or 100
        amount_out = _uniswap.quote_price_input(stable, token2, amount_in)
        print(f"Quoter : Swapping {amount_in} {stable.symbol} for {amount_out} {token2.symbol}")


    def _test_quoter_multipool(self):
        quoter = _uniswap.quoter

        qty = 100
        sqrtPriceLimitX96 = 0

        try:
            path = path_builder(3000)
            print(f"path bytes: {path}")

            qty_dec = qty * (10 ** usdc_decimals)

            # Call a function on the contract that might raise an error
            price = quoter.functions.quoteExactInput(
                path,
                qty_dec
            ).call()

            print(f"quoter multipool USDC-WETH-APE-USDC: from {qty} USDC to {price / (10 ** usdc_decimals)} USDC")

            return price / (10 ** usdc_decimals)

        except ContractLogicError as e:
            # Handle contract-specific logic errors
            print(f"Contract logic error: {e} - data: {e.data}")

        except Exception as e:
            # Handle other general exceptions
            print(f"An error occurred: {e}")


    def test_main(self):

        res = Web3.to_wei(1, 'ether')
        print(res)

        res = Web3.from_wei(res, 'gwei')
        print(res)

        print(w3.is_connected())


        pkeys = uniswap_helper.load_keys_from_file()
        publicKey = pkeys["publicKey"]

        # Nonce
        nonce = w3.eth.get_transaction_count(publicKey)

        bal = w3.eth.get_balance(publicKey)

        print(w3.eth.accounts)


    def test_contract(self):
        router = Contracts["router"]
        myContract = w3.eth.contract(address=router["address"], abi=uniswap_helper._load_abi(router["abiName"]))

        print(myContract)


    def test_pools(self):
        s = uniswap_api.retrieve_data_pools(cache=True)
        print(s)

    def test_create_pool_list(self):
        pools = uniswap_api.POOLS
        pairs_dict = uniswap_api.PAIRS_DICT
        tokens = uniswap_api.TOKENS_DICT
        tri_struc_pairs = uniswap_api.TRIANGLE_STRUCTURE_PAIRS




    def test_get_token(self):
        symbol = "ez-yvCurve-IronBank"

        result = uniswap_api.get_token(symbol)
        if result:
            print(f"'{symbol}' symbol found: {result}")
        else:
            print(f"No symbol '{symbol}' exists in the Tokens list")


    def test_checksum_address(self):
        _ =  weth
        print(_)
        _ =""