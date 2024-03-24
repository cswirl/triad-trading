import json
import os

from web3 import Web3

def decimal_right_shift(val, decimals: int):
    return int(val * (10 ** decimals))


#---------------------------------------------------------------------

def _load_contract(w3: Web3, address: str, abi_name: str):
    address = Web3.to_checksum_address(address)
    return w3.eth.contract(address=address, abi=_load_abi(abi_name))

def _load_abi(name: str) -> str:
    path = f"{os.path.dirname(os.path.abspath(__file__))}/assets/"
    with open(os.path.abspath(path + f"{name}.abi")) as f:
        abi: str = json.load(f)
    return abi

#-----------------------------------------------------------------
def load_keys_from_file():

    #filename = os.path.join(KEYS_FOLDER_PATH, 'pkeys.json')
    file_path = "vault/pkeys.json"
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            print(f"json data from {file_path} was loaded")
            return data
    except FileNotFoundError:
        print(f"error loading json data: File '{file_path}' not found.")
    except json.JSONDecodeError:
        print(f"error decoding JSON in file '{file_path}'.")