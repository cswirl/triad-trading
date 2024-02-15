
MAINNET_PROVIDER = "https://mainnet.infura.io/v3/09a82cc7df434cf98ccc9e4373dcf0d6"
TESTNET_PROVIDER = "https://sepolia.infura.io/v3/09a82cc7df434cf98ccc9e4373dcf0d6"


FACTORY_ADDRESS = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"

QUOTER_ADDRESS = "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6"
QUOTER_ABI_FILE_PATH = "assets/quoter.abi"

ROUTER_ADDRESS = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
ROUTER_ABI_FILE_PATH = "assets/router.abi"

FLASH_LOAN_ADDRESS = "0x2a4d0eD2b3ED22373018C46C4Db0f488A7250dD0"
FLASH_LOAN_ABI_FILE_PATH = "assets/flash_loan.abi"

STABLE_COINS = ["USDC", "USDT", "DAI", "FRAX"]  # must be a list to preserved order

APPROVED_TOKENS = ["WETH", "WBTC", "UNI"]       # must be a list to preserved order

STARTING_TOKENS = [*STABLE_COINS, *APPROVED_TOKENS] # must be a list to preserved order


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
            "address": QUOTER_ADDRESS,
            "abiName": "quoter"
        },
        "flashLoan": {
            "address": FLASH_LOAN_ADDRESS,
            "abiName": "flash_loan"
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