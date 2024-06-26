import os
from typing import Optional

from web3 import Web3
from web3.exceptions import ContractLogicError
from web3.types import Nonce

from uniswap import uniswap_helper


class Uniswap:
    """
    Wrapper around Uniswap contracts.
    """
    version: int
    w3: Web3

    default_slippage: float
    use_estimate_gas: bool

    def __init__(
        self,
        network_config: dict,
        pKeys: dict = None,
        provider: Optional[str] = None,
        default_slippage: float = 0.01,
        use_estimate_gas: bool = True,
    ) -> None:
        """
        :param network_config (dict):
        :param pKeys (dict): A dictionary containing the private key and address (public key)
        :param provider: the provider to be used in Web3 instance.
        :param default_slippage: - NOT YET IMPLEMENTED - Default slippage for a trade, as a float (0.01 is 1%). WARNING: slippage is untested.
        """
        self.network_config = network_config
        keys = pKeys
        if keys is None: print("No keys found.")

        self.private_key = keys and keys["privateKey"] or "0x0000000000000000000000000000000000000000000000000000000000000000"
        public_address = keys and keys["publicKey"] or "0x0000000000000000000000000000000000000000000000000000000000000000"
        self.address = Web3.to_checksum_address(public_address)

        self.version = 3
        self.w3 = Web3(provider)
        self.last_nonce = self.w3.eth.get_transaction_count(self.address)
        self.chain_id = int(network_config["chainId"]) if "chainId" in network_config.keys() else 0

        # TODO: Write tests for slippage
        self.default_slippage = default_slippage    # not used
        self.use_estimate_gas = use_estimate_gas    # not used

        # # This code automatically approves you for trading on the exchange.
        # # max_approval is to allow the contract to exchange on your behalf.
        # # max_approval_check checks that current approval is above a reasonable number
        # # The program cannot check for max_approval each time because it decreases
        # # with each trade.
        # max_approval_hex = f"0x{64 * 'f'}"
        # self.max_approval_int = int(max_approval_hex, 16)
        # max_approval_check_hex = f"0x{15 * '0'}{49 * 'f'}"
        # self.max_approval_check_int = int(max_approval_check_hex, 16)

        # https://github.com/Uniswap/uniswap-v3-periphery/blob/main/deploys.md


        quoter_conf = network_config["quoter"]
        self.quoter = uniswap_helper._load_contract(
            self.w3,
            address=quoter_conf["address"],
            abi_name=quoter_conf["abiName"]
        )

        if "flashLoan" in network_config.keys():
            flash_config = network_config["flashLoan"]
            self.flash_loan = uniswap_helper._load_contract(
                self.w3,
                address=flash_config["address"],
                abi_name=flash_config["abiName"]
            )


        # self.positionManager_addr = _str_to_addr(
        #     "0xC36442b4a4522E871399CD717aBDD847Ab11FE88"
        # )
        # self.nonFungiblePositionManager = _load_contract(
        #     self.w3,
        #     abi_name="uniswap-v3/nonFungiblePositionManager",
        #     address=self.positionManager_addr,
        # )
        # if self.netname == "arbitrum":
        #     multicall2_addr = _str_to_addr(
        #         "0x50075F151ABC5B6B448b1272A0a1cFb5CFA25828"
        #     )
        # else:
        #     multicall2_addr = _str_to_addr(
        #         "0x5BA1e12693Dc8F9c48aAD8770482f4739bEeD696"
        #     )
        # self.multicall2 = _load_contract(
        #     self.w3, abi_name="uniswap-v3/multicall", address=multicall2_addr
        # )

    def quote_price_input(self, token0, token1, qty, fee=3000):
        if self.network_config["chainId"] == "11155111":
            return self._sepolia_quote_price_input(token0, token1, qty, fee)
        else:
            return self._mainnet_quote_price_input(token0, token1, qty, fee)

    def _mainnet_quote_price_input(self, token0, token1, qty, fee=3000):
        qty_to_dec = qty * (10 ** token0.decimals)
        sqrtPriceLimitX96 = 0

        try:
            # Call a function on the contract that might raise an error
            price = self.quoter.functions.quoteExactInputSingle(
                token0.id,
                token1.id,
                fee,
                int(qty_to_dec),
                sqrtPriceLimitX96
            ).call()

            return price / 10 ** token1.decimals

        except ContractLogicError as e:
            # Handle contract-specific logic errors
            print(f"Contract logic error: {e} - data: {e.data}")

        except Exception as e:
            # Handle other general exceptions
            print(f"An error occurred: {e}")

    def _sepolia_quote_price_input(self, token0, token1, qty, fee=3000):
        qty_to_dec = qty * (10 ** token0.decimals)
        sqrtPriceLimitX96 = 0

        params = {
            "tokenIn": token0.id,
            "tokenOut": token1.id,
            "fee": fee,
            "amountIn": int(qty_to_dec),
            "sqrtPriceLimitX96": sqrtPriceLimitX96
        }

        try:
            # print(w3.api)
            # print(quoter.functions.factory().call())

            # Call a function on the contract that might raise an error
            # https://sepolia.etherscan.io/address/0xEd1f6473345F45b75F8179591dd5bA1888cf2FB3#code
            # look for quoteExactInputSingle
            price, _, _, _ = self.quoter.functions.quoteExactInputSingle(params).call()

            amount_out = price / 10 ** token1.decimals

            print(f"quoted price from quoter: {amount_out}")

            return amount_out

        except ContractLogicError as e:
            # Handle contract-specific logic errors
            print(f"Contract logic error: {e} - data: {e.data}")

        except Exception as e:
            # Handle other general exceptions
            print(f"An error occurred: {e}")
