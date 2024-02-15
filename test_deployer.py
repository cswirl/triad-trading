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

CryptoToken = namedtuple("CryptoToken", ["hex_address", "id", "symbol", "decimals"])

t_weth = CryptoToken(Web3.to_bytes(hexstr=weth), weth, "WETH", 18)
t_usdt = CryptoToken(Web3.to_bytes(hexstr=usdt), usdt, "USDT", 6)
t_rlb = CryptoToken(Web3.to_bytes(hexstr=rlb), rlb, "RLB", 18)

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
        "Quote 1 : 100 USDT to 0.03978381769984377 WETH",
        "Quote 2 : 0.03978381769984377 WETH to 777.5967111439336 RLB",
        "Quote 3 : 777.5967111439336 RLB to 100.196489 USDT",
        "--------------------",
        "Min. rate : 0",
        "PnL : 0.1964889999999997",
        "PnL % : 0.1964889999999997",

        :return:
        """
        swap1_amount = 100
        swap1_amount1 = 0 #0.03978381769984377

        # the fee used in the quoter is the same
        fee1 = 3000
        fee2 = 3000
        fee3 = 3000
        addToDeadline = 200 # seconds

        # this is the order of the pathway triplet
        one = t_usdt
        two = t_weth
        three = t_rlb
        # only the first pair is important to be in correct order for the initFlash to identify the pool address
        # using zeroForOne worked on usdt and weth
        zeroForOne = one.id < two.id
        if zeroForOne:
            token0 = one
            amount_0 = int(swap1_amount * (10 ** token0.decimals))
            borrowed_amount = amount_0

            token1 = two
            amount_1 = 0    # int(0.03978381769984377 * (10 ** two.decimals)) #0
        else:
            token0 = two
            amount_0 = 0    #int(0.03978381769984377 * (10 ** two.decimals)) #0

            token1 = one
            amount_1 =  int(swap1_amount * (10 ** token1.decimals))
            borrowed_amount = amount_1

        # token0 = one if zeroForOne else two
        # token1 = two if zeroForOne else one
        # amount_0 = swap1_amount if zeroForOne else 0
        # amount_1 = 0 if zeroForOne else swap1_amount1

        FlashParams = {
            "token_0": token0.id,
            "token_1": token1.id,
            "amount0": amount_0,  # amount_0 and amount_1 is where the seed amount is - in human or in blockchain?
            "amount1": amount_1,  # not sure if zero will work -other token in a pool where flash is invoked
            "borrowedAmount": borrowed_amount,  # the amount of token in correct decimals
            "token1": one.id,  # this is the token we need borrowing
            "token2": two.id,
            "token3": three.id,
            "quote1": int(0.03978381769984377 * (10 ** two.decimals)),
            "quote2": int(777.5967111439336 * (10 ** three.decimals)),
            "quote3": int(100.196489 * (10 ** one.decimals)),
            "fee1": fee1,
            "fee2": fee2,
            "fee3": fee3,
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
        tx_build = flash.functions.initFlash(params).transact()

        # Sign transaction
        tx_signed = tu.w3.eth.account.sign_transaction(tx_build, private_key=tu.uniswap.private_key)

        # Send transaction
        sent_tx = tu.w3.eth.send_raw_transaction(tx_signed.rawTransaction)
        print(sent_tx)

        #tx_hash = greeter.functions.setGreeting('Nihao').transact()

        #tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        pass









