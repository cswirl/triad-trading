import asyncio
import time

DEPTH_MIN_RATE = 1.5

ALL_TRADE_TIMEOUT = 60 * 60             # 60 * 60 = 1 hour
TRADE_TIMEOUT = 10

# RATE LIMIT WILL DICTATE THE SLEEP TIME
# FOR TRADE OBJECT TO QUERY THE NETWORK
TOTAL_ACTIVE_TRADERS = 33 * 30          # sleep_time = TOTAL_ACTIVE_TRADERS / RATE_LIMIT_PER_SECOND
RATE_LIMIT_PER_SECOND = 33
DEFAULT_SLEEP_TIME = 0.3
MAX_SLEEP_TIME = 1 / RATE_LIMIT_PER_SECOND      # OVERKILL AND UNSAFE:  1 / RATE_LIMIT_PER_SECOND + some value

def get_depth_rate(pathway: "a string"):
    return DEPTH_MIN_RATE + 1

class Trader:
    def __init__(self, pathway):
        self.pathway = pathway
        self.flags = [0,0,0]
        self.trade1_flags = 0
        self.trade2_flags = 0
        self.trade3_flags = 0
        self.print_status_flag = True


    def start_trading(self):
        #while True:

        self.hunt()
        # if the hunt() finds a good depth - it will break its inner loop to proceed next step
        seedFund = self.allocate_seed_fund(lambda x: 100)
        if seedFund and seedFund > 0:
            print(f"Seed fund: {seedFund}")
            asyncio.run(self.start_trade())

        else:
            print("No funds available")


        # exit program - do not forget to log it - json file is sufficient - use timestamp in file name
        # one full trade is enough for now for study


    def hunt(self):
        print("Changing state: 'Hunting'")
        while True:
            good_depth = self.inquire_depth(get_depth_rate)
            sleep_time = (RATE_LIMIT_PER_SECOND and TOTAL_ACTIVE_TRADERS / RATE_LIMIT_PER_SECOND) or DEFAULT_SLEEP_TIME
            print(f"sleep time {sleep_time}")
            time.sleep(float(sleep_time))
            if good_depth:
                print("Good Depth found. \nChanging State: 'Trading'")
                break

    def inquire_depth(self, func_depth_rate):
        depth_rate = func_depth_rate(self.pathway)

        if depth_rate >= DEPTH_MIN_RATE:
            return True

        return False

    def allocate_seed_fund(self, allocate_seed_fund: "a function"):
        seedFund = allocate_seed_fund("token address or symbol")
        return seedFund

    async def start_trade(self):
        await asyncio.gather(self.execute_trade(), self.check_trading_status())

    async def execute_trade(self):
        start = time.perf_counter()
        try:
            # Set a timeout of in seconds for async function
            trade1_result = await asyncio.wait_for(self.execute_trade_1(), timeout=TRADE_TIMEOUT)
            trade2_result = await asyncio.wait_for(self.execute_trade_2(), timeout=TRADE_TIMEOUT)
            trade3_result = await asyncio.wait_for(self.execute_trade_3(), timeout=TRADE_TIMEOUT)

        except asyncio.TimeoutError:
            print("The asynchronous function timed out.")
            self.print_status_flag = False
            print(f"Incomplete trade - Time-Out : elapsed in {time.perf_counter() - start:0.2f} seconds")
            # delegate to another entity program - like a 'failed trade resolver'
        except:
            self.print_status_flag = False
            print(f"Incomplete trade - Generic Error : elapsed in {time.perf_counter() - start:0.2f} seconds")
            # delegate to another entity program - like a 'failed trade resolver'
        finally:
            elapsed = time.perf_counter() - start
            print(f"COMPLETED - Three trades executed : elapsed in {elapsed:0.2f} seconds")


    async def execute_trade_1(self):
        start = time.perf_counter()
        self.trade1_flags = 1
        print("========================executing trade 1")

        await asyncio.sleep(5)

        # if trade 1 is executed without problem
        self.trade1_flags  = 2

        print(f"Trade-1 completed : elapsed in {time.perf_counter() - start:0.2f} seconds")

        return "done"



    async def execute_trade_2(self):
        start = time.perf_counter()
        self.trade2_flags = 1
        print("========================executing trade 2")

        await asyncio.sleep(TRADE_TIMEOUT - 7)

        # if trade 2 is executed without problem
        self.trade2_flags = 2
        print(f"Trade-2 completed : elapsed in {time.perf_counter() - start:0.2f} seconds")

        return "done"

    async def execute_trade_3(self):
        start = time.perf_counter()
        self.trade3_flags = 1
        print("========================executing trade 3")

        # if trade 3 is executed without problem
        await asyncio.sleep(2)

        self.trade3_flags = 2
        print(f"Trade-3 completed : elapsed in {time.perf_counter() - start:0.2f} seconds")

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
