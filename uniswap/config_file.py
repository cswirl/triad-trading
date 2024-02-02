import  utils

PROVIDER = "https://sepolia.infura.io/v3/09a82cc7df434cf98ccc9e4373dcf0d6"

FACTORY_ADDRESS = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
ROUTER_ADDRESS = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
ROUTER_ABI_FILE_PATH = "../abi/router.abi"

addressFrom = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2" #// WETH
addressTo = "0x6B3595068778DD592e39A122f4f5a5cF09C90fE2" #// SUSHI


Contracts = {
        "router": {
            "address": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
            "abiPath": utils.load_json_file("../abi/router.abi")
        }
    }
