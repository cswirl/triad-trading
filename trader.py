import asyncio
import time

DEPTH_MIN_RATE = 1.5
ALL_TRADE_TIMEOUT = 60 * 60     # 60 * 60 = 1 hour
TRADE_TIMEOUT = 10


def get_depth_rate():
    print("seek depth")

class Trader:
    def __init__(self, pathway):
        self.pathway = pathway
        self.flags = [0,0,0]
        self.trade1_flags = 0
        self.trade2_flags = 0
        self.trade3_flags = 0
        self.print_status_flag = True

    def inquire_depth(self, func_depth_rate):
        depth_rate = func_depth_rate(self.pathway)

        if depth_rate >= DEPTH_MIN_RATE:
            asyncio.run(self.start_trade())

    async def start_trade(self):
        await asyncio.gather(self.execute_trade(), self.check_trading_status())

    async def execute_trade(self):
        try:
            # Set a timeout of in seconds for async function
            trade1_result = await asyncio.wait_for(self.execute_trade_1(), timeout=TRADE_TIMEOUT)
            trade2_result = await asyncio.wait_for(self.execute_trade_2(), timeout=TRADE_TIMEOUT)
            trade3_result = await asyncio.wait_for(self.execute_trade_3(), timeout=TRADE_TIMEOUT)

        except asyncio.TimeoutError:
            print("The asynchronous function timed out.")
            self.print_status_flag = False
            # delegate to another entity program - like a 'failed trade resolver'

    async def execute_trade_1(self):
        self.trade1_flags = 1
        print("========================executing trade 1")

        await asyncio.sleep(5)

        # if trade 1 is executed without problem
        self.trade1_flags  = 2

        return "done"



    async def execute_trade_2(self):
        self.trade2_flags = 1
        print("========================executing trade 2")

        await asyncio.sleep(TRADE_TIMEOUT - 7)

        # if trade 2 is executed without problem
        self.trade2_flags = 2

        return "done"

    async def execute_trade_3(self):
        self.trade3_flags = 1
        print("========================executing trade 3")

        # if trade 3 is executed without problem
        await asyncio.sleep(2)

        self.trade3_flags = 2

        return "done"

    async def check_trading_status(self):
        counter = 0
        while self.print_status_flag \
            and not (2 == self.trade1_flags == self.trade2_flags == self.trade3_flags) \
            and counter <= ALL_TRADE_TIMEOUT:

            self.print_status()
            counter += 1
            await asyncio.sleep(1)

        self.print_status()

    def print_status(self):
        print("####################")
        trade1_status = self.get_print_status(self.trade1_flags)
        print(f"Trade 1 status: {trade1_status}")
        # print(f" trade1_flag: {self.trade1_flags}")

        trade2_status = self.get_print_status(self.trade2_flags)
        print(f"Trade 2 status: {trade2_status}")
        # print(f" trade2_flag: {self.trade2_flags}")

        trade3_status = self.get_print_status(self.trade3_flags)
        print(f"Trade 3 status: {trade3_status}")
        # print(f" trade3_flag: {self.trade3_flags}")

    def get_print_status(self, flag):
        if flag == 0: return "idle"
        elif flag == 1: return "in-progress"
        elif flag == 2: return "completed"
        else: return "Invalid trade flag value"
