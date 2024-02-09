import asyncio
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from web3.exceptions import ContractLogicError

from triad_util import FundingResponse
import triad_util
from uniswap import utils

from uniswap.constants import *
from uniswap.config_file import *
from app_constants import *


ALL_TRADE_TIMEOUT = 60 * 60             # DELETE? 60 * 60 = 1 hour
TRADE_TIMEOUT = 60 * 60

# RATE LIMIT WILL DICTATE THE SLEEP TIME
# FOR TRADE OBJECT TO QUERY THE NETWORK
SECONDS = 10    # will control the hunting sleep in seconds
TOTAL_ACTIVE_TRADERS = 33 * SECONDS          # sleep_time = TOTAL_ACTIVE_TRADERS / RATE_LIMIT_PER_SECOND
RATE_LIMIT_PER_SECOND = 33
DEFAULT_SLEEP_TIME = 0.3
NO_FUNDS_SLEEP_TIME = 30                    # REMEMBER: block time is 15 sec.

#Formula: AUTO-ADJUSTING SLEEP TIME = SECONDS_IN_A_DAY * TOTAL_ACTIVE_TRADERS / LIMIT_PER_DAY
SECONDS_IN_A_DAY = 86400    # There are 86400 seconds in a day
LIMIT_PER_DAY = 100000      # INFURA 100,000


indent_1 = "=" * 80

class TraderState(Enum):    # using a text mapping is available
    IDLE = "idle"
    ACTIVE = "active"
    HUNTING = "hunting"
    TRADING = "trading"
    DORMANT = "dormant" # object still in memory due to reference from traders list



class Trader:
    def __init__(self, pathway_triplet, func_depth_rate, calculate_seed_fund = None):
        self.id = uuid.uuid4()
        self.pathway_triplet = pathway_triplet   # The three tokens in a Triad in correct order. Example: USDT-WETH-APE
        self.pathway_root_symbol = pathway_triplet.split(PATH_TRIPLET_DELIMITER)[0]
        self.test_fund = calculate_seed_fund(self.pathway_root_symbol, pathway_triplet) or 100

        self.internal_state = TraderState.ACTIVE
        self.trade1_flag = 0
        self.trade2_flag = 0
        self.trade3_flag = 0

        self.lifespan_logs = []
        self.trade_logs = []

        self.hunt_profit_flag = True
        self.start_trading_flag = True

        self.get_depth_rate = func_depth_rate


        self.logger(f"Greetings from {str(self)}")
        self.logger(f"Active Traders: {TOTAL_ACTIVE_TRADERS}")
        self.logger(f"Test Fund: {self.test_fund}")

    async def start_trading(self):
        result = True


        while result and self.start_trading_flag:
            result = await self.execute_trade()

        self.logger(f"Terminating {self.id} : result = {result or "not set"}")

        self.save_logs()

        self.internal_state = TraderState.DORMANT

        # exit program - do not forget to log it - json file is sufficient - use timestamp in file name
        # one full trade is enough for now for study
        # return the fund back after - whether it is used or not


    async def hunt_profit(self, amount_out_1 = 0, amount_out_2 = 0, amount_out_3 = 0):
        self.logger("Changing state: 'Hunting Profit'")
        self.internal_state = TraderState.HUNTING
        while True:

            if self.hunt_profit_flag == False:
                continue

            good_depth = self.inquire_depth(self.get_depth_rate, amount_out_1, amount_out_2, amount_out_3)

            if good_depth:
                self.logger("Changing State: 'Trading'")
                break

            sleep_time = LIMIT_PER_DAY and SECONDS_IN_A_DAY * TOTAL_ACTIVE_TRADERS / LIMIT_PER_DAY
            #sleep_time = (RATE_LIMIT_PER_SECOND and TOTAL_ACTIVE_TRADERS / RATE_LIMIT_PER_SECOND) or DEFAULT_SLEEP_TIME
            self.logger(f"sleep time {sleep_time}")
            await asyncio.sleep(sleep_time)


    def inquire_depth(self, func_depth_rate,amount_out_1 = 0, amount_out_2 = 0, amount_out_3 = 0):

        self.logger(indent_1 + "Inquiring price")

        token1, token2, token3 = self.pathway_triplet.split(PATH_TRIPLET_DELIMITER)

        test_amount = self.test_fund

        if amount_out_1 == 0:
            amount_out_1 = func_depth_rate(token1,token2, test_amount)
            self.logger(f"Quote 1 : {test_amount} {token1} to {amount_out_1} {token2}")

        if amount_out_2 == 0:
            amount_out_2 = func_depth_rate(token2, token3, amount_out_1)
            self.logger(f"Quote 2 : {amount_out_1} {token2} to {amount_out_2} {token3}")

        if amount_out_3 == 0:
            amount_out_3 = func_depth_rate(token3, token1, amount_out_2)
            self.logger(f"Quote 3 : {amount_out_2} {token3} to {amount_out_3} {token1}")


        # calculate pnl and pnl percentage
        profit_loss = test_amount and amount_out_3 - test_amount
        profit_loss_perc = test_amount and profit_loss / float(test_amount) * 100

        self.logger("--------------------")
        self.logger(f"Min. rate : {DEPTH_MIN_RATE}")
        self.logger(f"PnL : {profit_loss}")
        self.logger(f"PnL % : {profit_loss_perc}")
        self.logger("--------------------")

        self.save_logs()

        if profit_loss_perc >= DEPTH_MIN_RATE:
            self.logger(indent_1 + "Profit Found")
            self.save_logs()
            return True

        return False

    async def ask_for_funding(self):

        response, fund_in_usd, fund = triad_util.ask_for_funding(self.pathway_root_symbol, self.pathway_triplet)

        if response is FundingResponse.MAX_TRADING_TRANSACTIONS_EXCEEDED:
            self.logger(f"{response}")
            await asyncio.sleep(NO_FUNDS_SLEEP_TIME)

        elif response is FundingResponse.CONSECUTIVE_FAILED_TRADE_THRESHOLD_EXCEEDED:
            self.logger(f"{response}")
            await asyncio.sleep(NO_FUNDS_SLEEP_TIME)

        elif response is FundingResponse.SYMBOL_NOT_IN_STARTING_TOKEN:
            self.logger(f"{response} - symbol: {self.pathway_root_symbol}")

        elif response is FundingResponse.SYMBOL_NOT_IN_PATHWAY_TRIPLET:
            raise UserWarning(f"Coding Error: {response}")

        elif response is FundingResponse.APPROVED:
            self.logger(f"Seed fund: {fund} ---approx. {fund_in_usd} USD")

        return response, fund_in_usd, fund

    async def execute_trade(self):
        start = time.perf_counter()
        try:
            # awaiting hunt_profit during sleep allows for other Trader instance to do their jobs concurrently
            await self.hunt_profit()
            # if the hunt_profit() finds a good depth - it will break its inner loop to proceed next line of code

            if self.pathway_root_symbol not in STARTING_TOKENS:
                self.logger(f"'{self.pathway_root_symbol}' is not in STARTING TOKEN")
                # this will continue the trading execution loop and continue logging profitable data
                return True


            # Few attempts on getting funding from wallet and generous sleep time amount is needed for this operation
            # - and then return False after enough attempts
            response, fund_in_usd, seedFund = await self.ask_for_funding()
            # Returning false will break the outer trading execution loop
            if response is not FundingResponse.APPROVED: return False

            self.internal_state = TraderState.TRADING

            # Set a timeout of in seconds for async function
            trade1_result = await asyncio.wait_for(self.execute_trade_1(), timeout=TRADE_TIMEOUT)

            #await self.hunt_profit(trade1_result)
            trade2_result = await asyncio.wait_for(self.execute_trade_2(), timeout=TRADE_TIMEOUT)

            #await self.hunt_profit(trade1_result, trade2_result)
            amount_out_3 = await asyncio.wait_for(self.execute_trade_3(), timeout=TRADE_TIMEOUT)

            # calculate pnl and pnl percentage
            profit_loss = seedFund and amount_out_3 - seedFund
            profit_loss_perc = seedFund and profit_loss / float(seedFund) * 100


            self.logger("### PROFIT AND LOSS ###")
            self.logger(f"PnL : {profit_loss}")
            self.logger(f"PnL % : {profit_loss_perc}")
            self.logger(f"Trade Execution elapsed in {time.perf_counter() - start:0.2f} seconds")
            self.logger("#####################################################################")
            self.logger(f"^^^^^^ TRIANGULAR TRADE COMPLETE ^^^^^^ {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}")
            self.logger("#####################################################################")

            result_dict = {
                "id": str(self),
                "pnl": profit_loss,
                "pnlPerc": profit_loss_perc,
                "trade_logs": self.lifespan_logs
            }

            self.save_result_json(result_dict)

        except asyncio.TimeoutError:
            self.logger(f"Incomplete trade - Time-Out : elapsed in {time.perf_counter() - start:0.2f} seconds")
            self.logger("The asynchronous function timed out.")
            # delegate to another entity program - like a 'failed trade resolver'
            return False

        except ContractLogicError as e:
            # Handle contract-specific logic errors
            print(f"Contract logic error: {e} - data: {e.data}")
            #todo: what to do here?
            await asyncio.sleep(60)
            return True

        except UserWarning as w:
            self.logger(f"Incomplete trade - {w} - {time.perf_counter() - start:0.2f} seconds")
            # delegate to another entity program - like a 'failed trade resolver'
            return False

        except Exception as e:
            self.logger(f"Incomplete trade - Generic Error : elapsed in {time.perf_counter() - start:0.2f} seconds")
            self.logger(f"Exception : {e.with_traceback(None)}")
            # delegate to another entity program - like a 'failed trade resolver'
            return False

        return False


    async def execute_trade_1(self):
        start = time.perf_counter()
        self.trade1_flag = 1
        self.logger(indent_1 + "executing trade 1")

        await asyncio.sleep(3)

        # if trade 1 is executed without problem
        self.trade1_flag  = 2

        #self.logger("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        self.logger(f"Trade-1 completed : elapsed in {time.perf_counter() - start:0.2f} seconds")

        return 1000



    async def execute_trade_2(self):
        start = time.perf_counter()
        self.trade2_flag = 1
        self.logger(indent_1 + "executing trade 2")

        await asyncio.sleep(4)

        # if trade 2 is executed without problem
        self.trade2_flag = 2

        #self.logger("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        self.logger(f"Trade-2 completed : elapsed in {time.perf_counter() - start:0.2f} seconds")

        return 1000

    async def execute_trade_3(self):
        start = time.perf_counter()
        self.trade3_flag = 1
        self.logger(indent_1 + "executing trade 3")

        # if trade 3 is executed without problem
        await asyncio.sleep(2)

        self.trade3_flag = 2

        #self.logger("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        self.logger(f"Trade-3 completed : elapsed in {time.perf_counter() - start:0.2f} seconds")

        return 1000


    def logger(self, msg):
        self.lifespan_logs.append(msg)
        self.trade_logs.append(msg)
        print(msg)

    def save_result_json(self, result_dict):
        # Generate a timestamp
        _now = datetime.now()   # for utc, use datetime.now(timezone.utc) - import timezone
        result_dict["timestamp"] = _now.strftime("%Y-%m-%d %H:%M:%S")
        filename_timestamp = _now.strftime("%Y-%m-%d_%Hh%Mm%Ss")
        filename = f"{str(self)}_{filename_timestamp}.json"

        file_path = utils.filepath_today_folder(utils.TRADE_RESULT_FOLDER_PATH, filename)
        utils.save_json_to_file(result_dict, file_path)

        # save lifespan logs after each of the three trades
        self.save_logs()
        # clear trade logs after each three trades
        self.trade_logs.clear()


    def save_logs(self):
        filename = str(self) + '.txt'
        logs = "\n".join(self.lifespan_logs)
        utils.save_text_file(logs, utils.filepath_today_folder(utils.LOGS_FOLDER_PATH, filename))


    def __str__(self):
        return self.pathway_triplet + '_' + str(self.id)





async def trader_monitor(traders_list:[Trader]):
    msg = []
    active_list = []
    dormant_list = []
    while len(traders_list) > 0:
        _now = datetime.now()  # for utc, use datetime.now(timezone.utc) - import timezone
        initial_active_traders = len(traders_list)

        header1 = f"Initial Active Traders: {initial_active_traders}"
        header2 = f"timestamp: {_now}"
        msg.append(header1)
        msg.append(header2)
        # below needs to be sliced-out when being extended by msg list below
        active_list.append(header1)
        active_list.append(header2)

        for trader in traders_list:
            if trader.internal_state == TraderState.DORMANT:
                dormant_list.append(f"status: {trader.internal_state} - {str(trader)}")
            elif trader.internal_state == TraderState.ACTIVE or trader.internal_state == TraderState.HUNTING:
                active_list.append(f"status: {trader.internal_state} - {str(trader)}")

        active_count = len(active_list) - 2
        msg.extend(active_list[2:])
        msg.extend(dormant_list)
        msg.append("============================================================")
        msg.append(f"{active_count} / {initial_active_traders} active traders")
        msg.append(f"{len(dormant_list)} / {initial_active_traders} dormant traders")

        active_list.append("============================================================")
        active_list.append(f"{active_count} / {initial_active_traders} active traders")

        # save log ever 30 sec
        filename_timestamp = _now.strftime("%Y-%m-%d_%Hh")

        filename = f"traders-list-status_{filename_timestamp}.txt"
        logs = "\n".join(msg)
        utils.save_text_file(logs, utils.filepath_builder(utils.LOGS_FOLDER_PATH, filename))

        filename = f"traders-list-status_ACTIVE_{filename_timestamp}.txt"
        logs = "\n".join(active_list)
        utils.save_text_file(logs, utils.filepath_builder(utils.LOGS_FOLDER_PATH, filename))

        msg.clear()
        active_list.clear()
        dormant_list.clear()
        await asyncio.sleep(20)