from web3 import Web3

MAINNET_PROVIDER = "https://mainnet.infura.io/v3/09a82cc7df434cf98ccc9e4373dcf0d6"
SEPOLIA_PROVIDER = "https://sepolia.infura.io/v3/09a82cc7df434cf98ccc9e4373dcf0d6"


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

SEPOLIA_WETH9 = Web3.to_checksum_address("0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14")

"""
CAVEAT:
    Sepolia is using QuoterV2
"""
Networks = {
    "sepolia": {
        "chainId": "11155111",
        "provider": SEPOLIA_PROVIDER,
        "factory":  Web3.to_checksum_address("0x0227628f3F023bb0B980b67D528571c95c6DaC1c"),
        "router": Web3.to_checksum_address("0x78210a67539E8BC08Ce33C1156Fe28797AB206F5"),
        "quoter": {
            "address": Web3.to_checksum_address("0xEd1f6473345F45b75F8179591dd5bA1888cf2FB3"),
            "abiName": "sepolia_quoter"
        },
        "flashLoan": {
            "address": Web3.to_checksum_address("0xa3b9188B62a2aFab8c42cb53127dA0226e865096"),
            "abiName": "sepolia_flash_loan"
        }
    },
    "opSepolia": {
        "chainId": "11155420",
        "provider": "https://sepolia.optimism.io/",
        "factory":  Web3.to_checksum_address("0x4752ba5DBc23f44D87826276BF6Fd6b1C372aD24"),
        "router": Web3.to_checksum_address("0x94cC0AaC535CCDB3C01d6787D6413C739ae12bc4"),
        "quoter": {
            "address": Web3.to_checksum_address("0xC5290058841028F1614F3A6F0F5816cAd0df5E27"),
            "abiName": "op_sepolia_quoter"
        }

    },
    "mainnet": {
        "chainId": "1",
        "provider": MAINNET_PROVIDER,
        "factory": Web3.to_checksum_address("0x1F98431c8aD98523631AE4a59f267346ea31F984"),
        "router": Web3.to_checksum_address("0xE592427A0AEce92De3Edee1F18E0157C05861564"),
        "quoter": {
            "address": Web3.to_checksum_address("0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6"),
            "abiName": "quoter"
        }
    }
}

# Test