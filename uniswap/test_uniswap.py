import web3

import uniswap_api
import utils
from config_file import *
from web3 import Web3

import unittest
import json


def load_keys_from_file():

    #filename = os.path.join(KEYS_FOLDER_PATH, 'pkeys.json')
    file_path = "../vault/pkeys.json"
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            print(f"json data from {file_path} was loaded")
            return data
    except FileNotFoundError:
        print(f"error loading json data: File '{file_path}' not found.")
    except json.JSONDecodeError:
        print(f"error decoding JSON in file '{file_path}'.")




provider = Web3.HTTPProvider(PROVIDER)
w3 = Web3(provider)

class TestUniswap(unittest.TestCase):



    def test_main(self):

        res = Web3.to_wei(1, 'ether')
        print(res)

        res = Web3.from_wei(res, 'gwei')
        print(res)

        print(w3.is_connected())


        pkeys = load_keys_from_file()
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


