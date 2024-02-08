
MAINNET_PROVIDER = "https://mainnet.infura.io/v3/09a82cc7df434cf98ccc9e4373dcf0d6"
TESTNET_PROVIDER = "https://sepolia.infura.io/v3/09a82cc7df434cf98ccc9e4373dcf0d6"


FACTORY_ADDRESS = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"

QUOTER_ADDRESS = "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6"
QUOTER_ABI_FILE_PATH = "assets/quoter.abi"

ROUTER_ADDRESS = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
ROUTER_ABI_FILE_PATH = "assets/router.abi"

STABLE_COINS = ["USDC", "USDT", "DAI", "FRAX"]

STARTING_TOKENS = [*STABLE_COINS, "WETH", "WBTC", "UNI"] # ROUGH DRAFT


Contracts = {
        "router": {
            "address": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
            "abiName": "router"
        }
    }

#Tick spacing - value is Set data structure - use contract address?
TickSpacing = {
    "10": STABLE_COINS,        # stable
    "60": {"WETH", "token2"},    # medium

}

Networks = {
    "testnet": {
        "provider": TESTNET_PROVIDER,
        "quoter": {
            "address": "",
            "abiName": ""
        }
    },
    "mainnet": {
        "provider": MAINNET_PROVIDER,
        "quoter": {
            "address": QUOTER_ADDRESS,
            "abiName": "quoter"
        }
    }
}