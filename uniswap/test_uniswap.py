import web3

import uniswap
import utils
from config_file import *
from web3 import Web3

import unittest
import json


def load_keys_from_file():

    #file_path = os.path.join(KEYS_FOLDER_PATH, 'pkeys.json')
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
        s = uniswap.retrieve_data_pools()
        print(s)