import warnings
warnings.simplefilter(action="ignore", category=FutureWarning)

import unittest
from collections import namedtuple

from eth_utils import keccak
from eth_abi import encode

import triad_util as tu

from web3 import Web3

weth = Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
usdt = Web3.to_checksum_address("0xdac17f958d2ee523a2206206994597c13d831ec7")
rlb = Web3.to_checksum_address("0x046EeE2cc3188071C02BfC1745A6b17c656e3f3d")

CryptoToken_Exp1 = namedtuple("CryptoToken_Exp1", ["hex_address", "id", "symbol", "decimals"])

t_weth = CryptoToken_Exp1(Web3.to_bytes(hexstr=weth), weth, "WETH", 18)
t_usdt = CryptoToken_Exp1(Web3.to_bytes(hexstr=usdt), usdt, "USDT", 6)
t_rlb = CryptoToken_Exp1(Web3.to_bytes(hexstr=rlb), rlb, "RLB", 18)

# new
CryptoToken = namedtuple("CryptoToken_Exp1", ["id", "symbol", "decimals"])
usdc = CryptoToken(Web3.to_checksum_address("0xaC5e009C07540172DD8457Be7961895d58e4aD2d"), "USDC", 18)
wds = CryptoToken(Web3.to_checksum_address("0xdC0b7c0693B7689B324A0Ef8Ab210609Ba0cF994"), "WDS", 18)
yt = CryptoToken(Web3.to_checksum_address("0xDE3fC64BD79c1806Cb17F1C2eb794882114ca1cE"), "YT", 18)

# flash loan contract pair USDC / WTRIAD
wtriad = CryptoToken(Web3.to_checksum_address("0x1CFBddc8D66328ca250EC720c9f62DB08aa4BC6f"), "WTRIAD", 18)


class TestDeployer(unittest.TestCase):

    def test_deploy_1(self):
        """

        :return:
        """
        ROUTER_ADDRESS = Web3.to_checksum_address("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")

        FACTORY_ADDRESS = Web3.to_checksum_address("0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f")

        weth = Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")

    def test_struct_param(self, *args):
        myStruct = {
            'data': 'Hello',
            'issuer': '0x5B38Da6a701c568545dCfcB03FcB875f56beddC4'  # Example address
        }
        keys = ['(address,address)']
        values = [tuple(myStruct.values())]

        encoded = encode(keys, values)

        kecc = keccak(encoded)

        return kecc

    def test_struct_flash_params(self):
        """
        "Greetings from USDT_WETH_RLB_2f31aaa2-93c5-4540-8cf5-6147d3e79c0e",
        "Active Traders: 156  (inaccurate: testing for sleep calculation)",
        "Test Fund: 100 USDT ---approx. 100 USD",
        "Changing state: 'Hunting Profit'",
        "================================================================================Inquiring price",
        "Quote 1 : USDC to WDS",
        "Quote 2 : WDS to YT",
        "Quote 3 : YT to WDS",

        "Quote 3 : YT to USDC",
        "--------------------",

        """

        # sepolia


        swap1_amount = 10

        # the fee used in the quoter is the same
        fee1 = 3000
        fee2 = 3000
        fee3 = 3000
        addToDeadline = 200 # seconds

        # this is the order of the pathway triplet
        one = usdc
        two = wds
        three = yt
        # only the first pair is important to be in correct order for the initFlash to identify the pool address
        # using zeroForOne worked on usdt and weth in which the zeroForOne is WETH_USDT
        zeroForOne = Web3.to_int(hexstr=usdc.id) < Web3.to_int(hexstr=wtriad.id)
        if zeroForOne:
            token0 = one
            amount_0 = swap1_amount # int(swap1_amount * (10 ** token0.decimals))
            borrowed_amount = amount_0

            token1 = two
            amount_1 = 0    # int(0.03978381769984377 * (10 ** two.decimals)) #0
        else:
            token0 = two
            amount_0 = 0    #int(0.03978381769984377 * (10 ** two.decimals)) #0

            token1 = one
            amount_1 =  swap1_amount #int(swap1_amount * (10 ** token1.decimals))
            borrowed_amount = amount_1

        # token0 = one if zeroForOne else two
        # token1 = two if zeroForOne else one
        # amount_0 = swap1_amount if zeroForOne else 0
        # amount_1 = 0 if zeroForOne else swap1_amount1

        FlashParams = {
            "token_0": wtriad.id,
            "token_1": usdc.id,
            "fee0": 3000,
            "amount0": amount_0,  # amount_0 and amount_1 is where the seed amount is - in human or in blockchain?
            "amount1": amount_1,  # not sure if zero will work -other token in a pool where flash is invoked
            "borrowedAmount": borrowed_amount,  # the amount of token in correct decimals
            "token1": one.id,  # this is the token we need borrowing
            "token2": two.id,
            "token3": three.id,
            "quote1": 0,
            "quote2": 0,
            "quote3": 0,
            "fee1": fee1,
            "fee2": fee2,
            "fee3": fee3,
            "sqrtPriceLimitX96": 0,  # we do not understand this as of now
            "addToDeadline": addToDeadline
        }


        tup = str(FlashParams.values())

        values = [tuple(FlashParams.values())]

        print(str(tup).replace(" ", ""))

        return FlashParams

    def test_initFlash(self):

        # Variables
        chain_id = 11155111   # 56 Binance Smart Chain number, Ethereum is 1
        gas = 300000
        gas_price = Web3.to_wei("5.5", "gwei")
        send_bnb = 0.01
        amount = Web3.to_wei(send_bnb, "ether")  # not sure why "ether" is used

        # Nonce
        nonce = tu.w3.eth.get_transaction_count(tu.uniswap.address)  # public address of the sender i.e. your account

        flash = tu.uniswap.flash_loan

        _ = flash.functions.factory().call()

        params = self.test_struct_flash_params()

        # Build Transaction - BULL
        tx_build = flash.functions.initFlash(params).build_transaction({
            "chainId": chain_id,
            "value": 0,
            "gas": 8000000,
            "gasPrice": gas_price,
            "nonce": nonce
        })

        # Sign transaction
        tx_signed = tu.w3.eth.account.sign_transaction(tx_build, private_key=tu.uniswap.private_key)

        # Send transaction
        sent_tx = tu.w3.eth.send_raw_transaction(tx_signed.rawTransaction)
        print(tu.w3.to_hex(sent_tx))

        tx_receipt = tu.w3.eth.wait_for_transaction_receipt(sent_tx, timeout=params["addToDeadline"])
        print(tx_receipt)
        pass












