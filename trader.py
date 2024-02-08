import asyncio
import time
import uuid
from datetime import datetime
from typing import Optional

import triad_util
from uniswap import utils

from uniswap.constants import *
from uniswap.config_file import *


DEPTH_MIN_RATE = 0

USD_SEED_AMOUNT = 200   # The amount in US dollar to be used for price quotation

ALL_TRADE_TIMEOUT = 60 * 60             # 60 * 60 = 1 hour
TRADE_TIMEOUT = 60 * 60

# RATE LIMIT WILL DICTATE THE SLEEP TIME
# FOR TRADE OBJECT TO QUERY THE NETWORK
SECONDS = 10    # will control the hunting sleep in seconds
TOTAL_ACTIVE_TRADERS = 33 * SECONDS          # sleep_time = TOTAL_ACTIVE_TRADERS / RATE_LIMIT_PER_SECOND
RATE_LIMIT_PER_SECOND = 33
DEFAULT_SLEEP_TIME = 0.3
MAX_SLEEP_TIME = 1 / RATE_LIMIT_PER_SECOND      # OVERKILL AND UNSAFE:  1 / RATE_LIMIT_PER_SECOND + some value
NO_FUNDS_SLEEP_TIME = 60

class Trader:
    def __init__(self, pathway_triplet, func_depth_rate, calculate_seed_fund = None):
        self.id = uuid.uuid4()
        self.pathway_triplet = pathway_triplet   # The three tokens in a Triad in correct order. Example: USDT-WETH-APE
        self.pathway_root_symbol = self.pathway_triplet.split(PATH_TRIPLET_DELIMITER)[0]
        self.test_fund = calculate_seed_fund(self.pathway_root_symbol, usd_amount=USD_SEED_AMOUNT) or 1
        self.flags = [0,0,0]
        self.trade1_flag = 0
        self.trade2_flag = 0
        self.trade3_flag = 0
        self.print_status_flag = True
        self.lifespan_logs = []
        self.trade_logs = []

        self.get_depth_rate = func_depth_rate

        self.logger(f"Greetings from {str(self)}")

    async def start_trading(self):
        result = True


        while result:
            result = await self.execute_trade()

        self.logger(f"Terminating {self.id} : result = {result or "not set"}")

        self.save_logs()

        # exit program - do not forget to log it - json file is sufficient - use timestamp in file name
        # one full trade is enough for now for study
        # return the fund back after - whether it is used or not


    async def hunt_profit(self, amount_out_1 = 0, amount_out_2 = 0, amount_out_3 = 0):
        self.logger("Changing state: 'Hunting'")
        while True:
            good_depth = self.inquire_depth(self.get_depth_rate, amount_out_1, amount_out_2, amount_out_3)

            sleep_time = (RATE_LIMIT_PER_SECOND and TOTAL_ACTIVE_TRADERS / RATE_LIMIT_PER_SECOND) or DEFAULT_SLEEP_TIME
            self.logger(f"sleep time {sleep_time}")
            await asyncio.sleep(float(sleep_time))
            if good_depth:
                self.logger("Changing State: 'Trading'")
                break

    def inquire_depth(self, func_depth_rate,amount_out_1 = 0, amount_out_2 = 0, amount_out_3 = 0):

        token1, token2, token3 = self.pathway_triplet.split(PATH_TRIPLET_DELIMITER)

        test_amount = self.test_fund

        if amount_out_1 == 0:
            amount_out_1 = func_depth_rate(token1,token2, test_amount)

        if amount_out_2 == 0:
            amount_out_2 = func_depth_rate(token2, token3, amount_out_1)

        if amount_out_3 == 0:
            amount_out_3 = func_depth_rate(token3, token1, amount_out_2)


        # calculate pnl and pnl percentage
        profit_loss = test_amount and amount_out_3 - test_amount
        profit_loss_perc = test_amount and profit_loss / float(test_amount) * 100

        if profit_loss_perc >= DEPTH_MIN_RATE:
            self.logger("========Profit Found")
            self.logger(f"Quote 1 : {test_amount} {token1} to {amount_out_1} {token2}")
            self.logger(f"Quote 2 : {amount_out_1} {token2} to {amount_out_2} {token3}")
            self.logger(f"Quote 3 : {amount_out_2} {token3} to {amount_out_3} {token1}")
            self.logger("--------------------")
            self.logger(f"Min. rate : {DEPTH_MIN_RATE}")
            self.logger(f"PnL : {profit_loss}")
            self.logger(f"PnL % : {profit_loss_perc}")

            self.save_logs()

            return True

        return False

    async def ask_for_funding(self):

        fund_in_usd, fund = triad_util.ask_for_funding(self.pathway_root_symbol)

        if fund is None:
            self.logger("No funds available")
            await asyncio.sleep(NO_FUNDS_SLEEP_TIME)
        else:
            self.logger(f"Seed fund: {fund} ---approx. {fund_in_usd} USD")

        return fund

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
            seedFund = await self.ask_for_funding()
            # Returning false will break the outer trading execution loop
            if seedFund is None: return False

            # Set a timeout of in seconds for async function
            trade1_result = await asyncio.wait_for(self.execute_trade_1(), timeout=TRADE_TIMEOUT)

            await self.hunt_profit(trade1_result)
            trade2_result = await asyncio.wait_for(self.execute_trade_2(), timeout=TRADE_TIMEOUT)

            await self.hunt_profit(trade1_result, trade2_result)
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
            self.logger("The asynchronous function timed out.")
            self.print_status_flag = False
            self.logger(f"Incomplete trade - Time-Out : elapsed in {time.perf_counter() - start:0.2f} seconds")
            # delegate to another entity program - like a 'failed trade resolver'
            return False
        except:
            self.print_status_flag = False
            self.logger(f"Incomplete trade - Generic Error : elapsed in {time.perf_counter() - start:0.2f} seconds")
            # delegate to another entity program - like a 'failed trade resolver'
            return False

        return False


    async def execute_trade_1(self):
        start = time.perf_counter()
        self.trade1_flag = 1
        self.logger("========================executing trade 1")

        await asyncio.sleep(5)

        # if trade 1 is executed without problem
        self.trade1_flag  = 2

        self.logger("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        self.logger(f"Trade-1 completed : elapsed in {time.perf_counter() - start:0.2f} seconds")

        return 1000



    async def execute_trade_2(self):
        start = time.perf_counter()
        self.trade2_flag = 1
        self.logger("========================executing trade 2")

        await asyncio.sleep(4)

        # if trade 2 is executed without problem
        self.trade2_flag = 2

        self.logger("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        self.logger(f"Trade-2 completed : elapsed in {time.perf_counter() - start:0.2f} seconds")

        return 1000

    async def execute_trade_3(self):
        start = time.perf_counter()
        self.trade3_flag = 1
        self.logger("========================executing trade 3")

        # if trade 3 is executed without problem
        await asyncio.sleep(2)

        self.trade3_flag = 2

        self.logger("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        self.logger(f"Trade-3 completed : elapsed in {time.perf_counter() - start:0.2f} seconds")

        return 1000

    async def check_trading_status(self):
        counter = 0
        while self.print_status_flag \
            and not (2 == self.trade1_flag == self.trade2_flag == self.trade3_flag) \
            and counter <= ALL_TRADE_TIMEOUT:

            self.print_status()
            counter += 1
            await asyncio.sleep(1)

        self.print_status()

    def print_status(self):
        self.logger("####################")
        trade1_status = self.get_print_status(self.trade1_flag)
        self.logger(f"Trade 1 status: {trade1_status}")
        # print(f" trade1_flag: {self.trade1_flag}")

        trade2_status = self.get_print_status(self.trade2_flag)
        self.logger(f"Trade 2 status: {trade2_status}")
        # print(f" trade2_flag: {self.trade2_flag}")

        trade3_status = self.get_print_status(self.trade3_flag)
        self.logger(f"Trade 3 status: {trade3_status}")
        # print(f" trade3_flag: {self.trade3_flag}")

    def get_print_status(self, flag):
        if flag == 0: return "idle"
        elif flag == 1: return "in-progress"
        elif flag == 2: return "completed"
        else: return "Invalid trade flag value"


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