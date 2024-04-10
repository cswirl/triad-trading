import json
import os

from web3 import Web3

import uniswap


def decimal_right_shift(val, decimals: int):
    return int(val * (10 ** decimals))

def standard_pool_structure(pools: []):
    std_pools = []
    for x in pools:
        pool = {
                    "id": x["id"],
                    "totalValueLockedETH": x["totalValueLockedUSD"],
                    "token0Price": "1",
                    "token1Price": "1",
                    "feeTier": float(x["fees"][2]["feePercentage"])  * (10 ** 4),
                    "token0": x["inputTokens"][0],
                    "token1": x["inputTokens"][1]
                }
        std_pools.append(pool)
    return std_pools

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

    #
    package_path = os.path.dirname(uniswap.__file__)
    file_path = "vault/pkeys.json"
    filename = os.path.join(package_path, file_path)
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
            print(f"json data from {file_path} was loaded")
            return data
    except FileNotFoundError:
        print(f"error loading json data: File '{file_path}' not found.")
    except json.JSONDecodeError:
        print(f"error decoding JSON in file '{file_path}'.")