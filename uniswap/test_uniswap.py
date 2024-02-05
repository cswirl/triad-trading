
import unittest
from collections import namedtuple

import web3
from web3.exceptions import ContractLogicError

import uniswap_api
import uniswap_helper
from config_file import *
from web3 import Web3

TIER_100 = 100
TIER_500 = 500
TIER_3000 = 3000
TIER_10000 = 10000

fee = TIER_10000

network = uniswap_api.get_network("mainnet")

provider = Web3.HTTPProvider(network["provider"])
w3 = Web3(provider)


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



class TestUniswap(unittest.TestCase):

    def test_quoter_compare(self):
        print("============ QUOTER COMPARE ===============")
        multi_output_amount =  self._test_quoter_multipool()
        print(f"Multipool Output amount: {multi_output_amount}")
        print("-------------------------------")
        # Three separate swaps
        seed_amount = 100

        swap1_output = self._test_quoter(t_usdc, t_weth, seed_amount)
        print(f"Swap 1 : Swapping {seed_amount} {t_usdc.symbol} to {swap1_output} {t_weth.symbol}")
        # swap 2
        swap2_output = self._test_quoter(t_weth, t_ape, swap1_output)
        print(f"Swap 2 : Swapping {swap1_output} {t_weth.symbol} to {swap2_output} {t_ape.symbol}")
        # swap 3
        swap3_output = self._test_quoter(t_ape, t_usdc, swap2_output)
        print(f"Swap 3 : Swapping {swap2_output} {t_ape.symbol} to {swap3_output} {t_usdc.symbol}")

    def test_quoter_single(self):
        amount_in = 74
        stable = t_usdt

        amount_out = self._test_quoter(t_ape, t_usdc, amount_in)
        print(f"Quoter : Swapping {amount_in} {t_ape.symbol} for {amount_out} {stable.symbol}")

        amount_in = amount_out or 100
        amount_out = self._test_quoter(t_usdc, t_ape, amount_in)
        print(f"Quoter : Swapping {amount_in} {stable.symbol} for {amount_out} {t_ape.symbol}")


    def _test_quoter_multipool(self):

        quoter_config = network["quoter"]
        quoter = w3.eth.contract(address=quoter_config["address"], abi=quoter_config["abi"])

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


    def _test_quoter(self, token0, token1, qty, fee = 3000):

        quoter_config = network["quoter"]
        quoter = w3.eth.contract(address=quoter_config["address"], abi=quoter_config["abi"])

        qty_to_dec = qty * (10**token0.decimals)
        sqrtPriceLimitX96 = 0

        try:
            #print(w3.api)
            #print(quoter.functions.factory().call())

            # Call a function on the contract that might raise an error
            price = quoter.functions.quoteExactInputSingle(
                token0.id,
                token1.id,
                fee,
                int(qty_to_dec),
                sqrtPriceLimitX96
            ).call()

            print(f"quoted price from quoter: {price / 10**token1.decimals}")

            return price / 10**token1.decimals

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
        myContract = w3.eth.contract(address=router["address"], abi=router["abiPath"])

        print(myContract)


    def test_pools(self):
        s = uniswap_api.retrieve_data_pools()
        print(s)

    def test_create_pool_list(self):
        pools = uniswap_api.retrieve_data_pools()
        pairs_dict, tokens = uniswap_api.create_list_pairs(pools)

        #save pools to json file
        data_pools = []
        for k, v in pairs_dict.items():

            pools_list = []
            for pair in v:
                pair_dict = {
                    "id": pair.id,
                    "tvlEth": pair.tvl_eth,
                    "feeTier": pair.fee_tier,
                    "tradingPairSymbol": pair.pair_symbol,
                    "token0": self._token_to_dict(pair.base),
                    "token1": self._token_to_dict(pair.quote)
                }
                pools_list.append(pair_dict)

            pools_dict = {
                "tradingPairSymbol": k,
                "poolsTotal": len(pools_list),
                "pools": pools_list
            }

            data_pools.append(pools_dict)

        file_path = utils.filepath_today_folder(utils.DATA_FOLDER_PATH, "uniswap_data_pools.json")
        utils.save_json_to_file(data_pools, file_path)

    def _token_to_dict(self, token):
        return {
            "id": token.id,
            "symbol": token.symbol,
            "name": token.name,
            "decimals": token.decimals,
            "price": token.price
        }


