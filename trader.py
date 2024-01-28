import asyncio
import time
import uuid
from datetime import datetime

import utils


DEPTH_MIN_RATE = 1.5

ALL_TRADE_TIMEOUT = 60 * 60             # 60 * 60 = 1 hour
TRADE_TIMEOUT = 10

# RATE LIMIT WILL DICTATE THE SLEEP TIME
# FOR TRADE OBJECT TO QUERY THE NETWORK
TOTAL_ACTIVE_TRADERS = 33 * 10          # sleep_time = TOTAL_ACTIVE_TRADERS / RATE_LIMIT_PER_SECOND
RATE_LIMIT_PER_SECOND = 33
DEFAULT_SLEEP_TIME = 0.3
MAX_SLEEP_TIME = 1 / RATE_LIMIT_PER_SECOND      # OVERKILL AND UNSAFE:  1 / RATE_LIMIT_PER_SECOND + some value
NO_FUNDS_SLEEP_TIME = 60

def get_depth_rate(trading_pair: "a string"):
    return DEPTH_MIN_RATE + 1

class Trader:
    def __init__(self, **kwargs):
        self.id = uuid.uuid4()
        self.pathway_triplet = kwargs["pathway_triplet"]    # The three tokens in a Triad in correct order. Example: USDT-WETH-APE
        self.pathway = kwargs["pathway"]
        self.seedFund = 0
        self.flags = [0,0,0]
        self.trade1_flag = 0
        self.trade2_flag = 0
        self.trade3_flag = 0
        self.print_status_flag = True
        self.lifespan_logs = []
        self.trade_logs = []

        self.logger(f"Greetings from {str(self)}")

    async def start_trading(self):
        result = True


        while result:
            result = await self.execute_trade()

        self.logger(f"Terminating {self.id} : result = {result}")

        self.save_logs()

        # exit program - do not forget to log it - json file is sufficient - use timestamp in file name
        # one full trade is enough for now for study
        # return the fund back it not used.


    async def hunt_profit(self, amount_out_1 = 0, amount_out_2 = 0, amount_out_3 = 0):
        self.logger("Changing state: 'Hunting'")
        while True:
            good_depth = self.inquire_depth(get_depth_rate, amount_out_1, amount_out_2, amount_out_3)
            sleep_time = (RATE_LIMIT_PER_SECOND and TOTAL_ACTIVE_TRADERS / RATE_LIMIT_PER_SECOND) or DEFAULT_SLEEP_TIME
            self.logger(f"sleep time {sleep_time}")
            await asyncio.sleep(float(sleep_time))
            if good_depth:
                self.logger("Good Depth found.")
                self.logger("Changing State: 'Trading'")
                break

    def inquire_depth(self, func_depth_rate,amount_out_1 = 0, amount_out_2 = 0, amount_out_3 = 0):
        return True

        seedAmount = self.seedFund
        # swap1 pnl
        #if self.trade1_flag == 0:  # idle: 0, in-progress: 1, completed:2
        #    swap1_outputAmount = func_depth_rate("token1_address","token2_address", seedFund)



        #if self.trade2_flag == 0:  # idle: 0, in-progress: 1, completed:2
        #   swap2_outputAmount = func_depth_rate("token1_address","token2_address", swap1_outputAmount)

        #if self.trade3_flag == 0:  # idle: 0, in-progress: 1, completed:2
        #    swap3_outputAmount = func_depth_rate("token1_address","token2_address", swap2_outputAmount)

        if amount_out_1 == 0:
            amount_out_1 = func_depth_rate("token1_address","token2_address", seedAmount)

        if amount_out_2 == 0:
            amount_out_2 = func_depth_rate("token1_address","token2_address", amount_out_1)

        if amount_out_3 == 0:
            amount_out_3 = func_depth_rate("token1_address","token2_address", amount_out_2)


        # calculate pnl and pnl percentage
        profit_loss = seedAmount and amount_out_3 - seedAmount
        profit_loss_perc = seedAmount and profit_loss / float(seedAmount) * 100

        if profit_loss_perc >= DEPTH_MIN_RATE:
            return True

        return False


    def allocate_seed_fund(self, allocate_seed_fund: "a function"):
        seedFund = allocate_seed_fund("token address or symbol")
        return seedFund

    async def get_seedFund(self):

        seedFund = self.allocate_seed_fund(lambda x: 100)
        self.seedFund = seedFund
        if seedFund and seedFund > 0:
            self.logger(f"Seed fund: {seedFund}")
            return seedFund
        else:
            self.logger("No funds available")
            await asyncio.sleep(NO_FUNDS_SLEEP_TIME)

        return None

    async def execute_trade(self):
        start = time.perf_counter()
        try:
            # awaiting hunt_profit during sleep allows for other Trader instance to do their jobs concurrently
            await self.hunt_profit()
            # if the hunt_profit() finds a good depth - it will break its inner loop to proceed next line of code

            seedFund = await self.get_seedFund()
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

        await asyncio.sleep(TRADE_TIMEOUT - 7)

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
        filename = str(self) + '.json'
        utils.save_json_to_file(result_dict, utils.TRADE_RESULT_FILE_PATH, filename)

        # save lifespan logs after each three trades
        self.save_logs()
        # clear trade logs after each three trades
        self.trade_logs.clear()


    def save_logs(self):
        filename = str(self) + '.txt'
        logs = "\n".join(self.lifespan_logs)
        utils.save_text_file(logs, utils.LOGS_FILE_PATH, filename)


    def __str__(self):
        return self.pathway_triplet + '_' + str(self.id)