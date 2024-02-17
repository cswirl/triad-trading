import asyncio
import time
import uuid
import traceback
from datetime import datetime
from enum import Enum

from web3.exceptions import ContractLogicError

import global_triad as gt
from triad_util import FundingResponse
import triad_util
from uniswap import utils

from uniswap.constants import *
from app_constants import *

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

        usd_amount_in, amount_out = calculate_seed_fund(self.pathway_root_symbol, pathway_triplet)
        self.test_fund = amount_out
        self.test_fund_usd = usd_amount_in

        self.internal_state = TraderState.ACTIVE
        self.internal_state_reason = "<not set>"
        self.trade1_flag = 0
        self.trade2_flag = 0
        self.trade3_flag = 0

        self.lifespan_logs = []
        self.trade_logs = []

        self.hunt_profit_flag = True

        self.get_depth_rate = func_depth_rate

        self.logger(f"Greetings from {str(self)}")
        self.logger(f"Active Traders: {gt.g_total_active_traders}  (inaccurate: testing for sleep calculation)")
        self.logger(f"Test Fund: {self.test_fund} {self.pathway_root_symbol} ---approx. {self.test_fund_usd} USD")

    async def start_trading(self):
        continue_trading = True
        while continue_trading:
            continue_trading = await self.execute_trade()

            if continue_trading:
                await asyncio.sleep(POST_TRADE_EXECUTION_SLEEP)

        self.internal_state = TraderState.DORMANT
        self.internal_state_reason = "FLAGGED TO DISCONTINUE"
        self.logger(f"Changing State to DORMANT : {self}")
        self.save_logs()

        # exit program - do not forget to log it - json file is sufficient - use timestamp in file name
        # one full trade is enough for now for study
        # return the fund back after - whether it is used or not

    async def execute_trade(self):
        CONTINUE_OUTER_LOOP = True
        BREAK_OUTER_LOOP = False
        start = time.perf_counter()

        try:
            # awaiting hunt_profit during sleep allows for other Trader instance to do their jobs concurrently
            quotation_dict = await self.hunt_profit()
            # if the hunt_profit() finds a good depth - it will break its inner loop to proceed next line of code

            # Few attempts on getting funding from wallet and generous sleep time amount is needed for this operation
            # - and then return False after enough attempts

            response, fund_in_usd, seedFund = await self.ask_for_funding()

            # Returning false will break the outer trading execution loop
            if response is not FundingResponse.APPROVED:
                return CONTINUE_OUTER_LOOP

            self.internal_state = TraderState.TRADING

            async with gt.g_lock:
                gt.g_trade_transaction_counter += 1

            # execute flash loan - initFlash
            result = await self.flashloan_execute()  #triad_util.execute_flash(quotation_dict)

            amount_out_3 = quotation_dict["quote3"]

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
            return BREAK_OUTER_LOOP

        except ContractLogicError as e:
            # Handle contract-specific logic errors
            self.logger(f"Contract logic error: {e} - data: {e.data}")
            self.logger(f"{self} - sleep for {CONTRACT_LOGIC_ERROR_SLEEP}")
            # todo: what to do here?
            await asyncio.sleep(CONTRACT_LOGIC_ERROR_SLEEP)
            return CONTINUE_OUTER_LOOP

        except UserWarning as w:
            self.logger(f"Incomplete trade - {w} - {time.perf_counter() - start:0.2f} seconds")
            self.logger((f"User warning : {traceback.format_exc()}"))
            # delegate to another entity program - like a 'failed trade resolver'
            return BREAK_OUTER_LOOP

        except Exception as e:
            self.logger(f"Incomplete trade - Generic Error : elapsed in {time.perf_counter() - start:0.2f} seconds")
            self.logger(f"Exception : {traceback.format_exc()}")
            # delegate to another entity program - like a 'failed trade resolver'
            return BREAK_OUTER_LOOP

        return POST_TRADE_CONTINUE

    async def hunt_profit(self, amount_out_1 = 0, amount_out_2 = 0, amount_out_3 = 0):
        self.logger("Changing state: 'Hunting Profit'")
        self.internal_state = TraderState.HUNTING
        while True:

            if self.hunt_profit_flag == False:
                continue

            good_depth, quotation_dict = self.inquire_depth(self.get_depth_rate, amount_out_1, amount_out_2, amount_out_3)

            if good_depth:
                self.logger("Changing State: 'Trading'")
                return quotation_dict

            sleep_time = calculate_sleep_time()
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

            quotation_dict = {
                "pathwayTripletSymbols": self.pathway_triplet,
                "seedAmount": test_amount,
                "quote1": amount_out_1,
                "quote2": amount_out_2,
                "quote3": amount_out_3,
                "fee1": GAS_FEE,
                "fee2": GAS_FEE,
                "fee3": GAS_FEE
            }
            return (True, quotation_dict)

        return (False, None)

    async def ask_for_funding(self):
        self.logger(indent_1 + " asking for funding")

        async with gt.g_lock:
            # max transaction count reached
            if gt.g_trade_transaction_counter >= MAX_TRADING_TRANSACTIONS:
                self.internal_state = TraderState.IDLE
                self.internal_state_reason = "MAX_TRADING_TRANSACTIONS_EXCEEDED"
                self.logger(f"MAX_TRADING_TRANSACTIONS_EXCEEDED")
                self.logger(f"sleep time : {MAX_TRADING_TRANSACTIONS_SLEEP}")
                await asyncio.sleep(MAX_TRADING_TRANSACTIONS_SLEEP)
                #
                # upon wake-up resume state to active
                self.internal_state = TraderState.ACTIVE
                self.internal_state_reason = None
                self.logger(f"Waking-up - Changing State to Active")
                funding_response = FundingResponse.MAX_TRADING_TRANSACTIONS_EXCEEDED
                return funding_response, None, None

            # todo: consecutive trade failures - For all traders
            # This is a little complicated, it will be dealt with at a later time
            # - since transaction result is not known immediately
            # For now, after reaching the MAX_TRADING_TRANSACTIONS, the program should terminate
            if gt.g_consecutive_trade_failure >= CONSECUTIVE_FAILED_TRADE_THRESHOLD:
                self.internal_state = TraderState.IDLE
                self.internal_state_reason = "CONSECUTIVE_FAILED_TRADE_THRESHOLD_EXCEEDED"
                self.logger(f"CONSECUTIVE_FAILED_TRADE_THRESHOLD_EXCEEDED")
                self.logger(f"sleep time : {CONSECUTIVE_FAILED_TRADE_SLEEP}")
                await asyncio.sleep(CONSECUTIVE_FAILED_TRADE_SLEEP)
                funding_response = FundingResponse.CONSECUTIVE_FAILED_TRADE_THRESHOLD_EXCEEDED
                return funding_response, None, None

        # In Traditional finance, we would allocate this using the available funds in our account
        # since we are using flash swaps, no need to allocate since fund is loaned - this method is peculiar
        response, fund_in_usd, fund = triad_util.ask_for_funding(self.pathway_root_symbol, self.pathway_triplet)

        if response is FundingResponse.SYMBOL_NOT_IN_STARTING_TOKEN:
            self.logger(f"sleep time : {SYMBOL_NOT_IN_STARTING_TOKEN_SLEEP}")
            self.logger(f"{response} - symbol: {self.pathway_root_symbol}")
            await asyncio.sleep(SYMBOL_NOT_IN_STARTING_TOKEN_SLEEP)

        #-------- ABOVE STATEMENTS ALLOW FOR CONTINOUS LOOP
        elif response is FundingResponse.SYMBOL_NOT_IN_PATHWAY_TRIPLET:
            raise UserWarning(f"Coding Error: {response}")

        elif response is FundingResponse.APPROVED:
            self.logger(f"Seed fund: {fund} ---approx. {fund_in_usd} USD")

        return response, fund_in_usd, fund

    async def flashloan_execute(self):
        start = time.perf_counter()
        self.logger(indent_1 + "executing flash loan")

        await asyncio.sleep(3)

        self.logger(f"Trade completed : elapsed in {time.perf_counter() - start:0.2f} seconds")

        return "transaction hash"

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





async def trader_monitor(traders_list:[Trader], counter = 0):
    msg = []
    active_list_log = []
    active_list_msg = []
    dormant_list_msg = []
    idle_list = []
    idle_list_msg = []

    while len(traders_list) > 0:
        _now = datetime.now()  # for utc, use datetime.now(timezone.utc) - import timezone
        initial_active_traders = len(traders_list)

        # below needs to be sliced-out when being extended by msg list below
        for trader in traders_list:
            if trader.internal_state == TraderState.DORMANT:
                dormant_list_msg.append(f"status: {trader.internal_state} - {str(trader)} - {trader.internal_state_reason}")
            elif trader.internal_state == TraderState.ACTIVE or trader.internal_state == TraderState.HUNTING:
                active_list_msg.append(f"status: {trader.internal_state} - {str(trader)}")
            elif trader.internal_state == TraderState.IDLE:
                idle_list_msg.append(f"status: {trader.internal_state} - {str(trader)} - {trader.internal_state_reason}")
                idle_list.append(trader)

        headings = []
        headings.append(f"Initial Active Traders: {initial_active_traders}")
        headings.append(f"Numbers Trades Executed: {gt.g_trade_transaction_counter}")
        headings.append(f"g_total_active_traders: {gt.g_total_active_traders} (static only)")
        headings.append(f"g_trade_transaction_counter: {gt.g_trade_transaction_counter}")
        headings.append(f"MAX_TRADING_TRANSACTIONS: {MAX_TRADING_TRANSACTIONS}")
        headings.append(f"sleep time: {calculate_sleep_time()} seconds")
        headings.append("---------------------------------------------------")
        headings.append(f"{len(active_list_msg)} / {initial_active_traders} active traders")
        headings.append(f"{len(dormant_list_msg)} / {initial_active_traders} dormant traders")
        headings.append(f"{len(idle_list)} / {len(active_list_msg)} idling traders")
        headings.append("---------------------------------------------------")
        headings.append(f"timestamp: {_now}")
        headings.append(f"refresh every: {TRADER_MONITOR_SLEEP} seconds")
        headings.append("=====================================================================")

        msg.extend(headings)
        msg.extend(idle_list_msg)
        msg.extend(active_list_msg)
        msg.extend(dormant_list_msg)
        msg.append("============================================================")

        msg.append(f"idling traders:")
        for trader in idle_list:
            msg.append(f"{trader.internal_state_reason} --- {str(trader)}")

        active_list_log.extend(headings)
        active_list_log.extend(active_list_msg)
        active_list_msg.append("=====================================================================")
        active_list_msg.append(f"{len(active_list_msg)} / {initial_active_traders} active traders")

        # save log ever 30 sec
        filename_timestamp = _now.strftime("%Y-%m-%d_%Hh")

        filename = f"traders-list-status_{filename_timestamp}.txt"
        logs = "\n".join(msg)
        utils.save_text_file(logs, utils.filepath_builder(utils.LOGS_FOLDER_PATH, filename), quiet_mode=(counter > 0))

        filename = f"traders-list-status_ACTIVE_{filename_timestamp}.txt"
        logs = "\n".join(active_list_log)
        utils.save_text_file(logs, utils.filepath_builder(utils.LOGS_FOLDER_PATH, filename), quiet_mode=(counter > 0))

        counter += 1

        msg.clear()
        active_list_log.clear()
        active_list_msg.clear()
        dormant_list_msg.clear()
        idle_list.clear()
        idle_list_msg.clear()

        await asyncio.sleep(TRADER_MONITOR_SLEEP)


def calculate_sleep_time():
    """ AUTO-ADJUSTING - Depending on the number of active traders and infura daily limit

    Formula:
        SLEEP TIME = SECONDS_IN_A_DAY * g_total_active_traders * TRADER_NUMBER_OF_REQUEST_PER_ROUND / LIMIT_PER_DAY

    SECONDS_IN_A_DAY = 86400    # 1 Day = 60 sec * 60 min * 24 hour = 86400 seconds
    LIMIT_PER_DAY = 100000      # INFURA 100,000 Daily Limit
    """
    total_active_traders = len([x for x in gt.g_trader_list if x.internal_state != TraderState.DORMANT])
    sleep_time = (LIMIT_PER_DAY and SECONDS_IN_A_DAY * total_active_traders * TRADER_NUMBER_OF_REQUEST_PER_ROUND / LIMIT_PER_DAY) or DEFAULT_SLEEP_TIME
    return sleep_time
