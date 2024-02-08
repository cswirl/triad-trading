# This is a sample Python script.
import asyncio

import triad_util
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


from trader import Trader


async def test_main():
    # triad_util.get_depth_rate,
    trader = Trader(
        "USDC_WETH_APE",
        triad_util.get_depth_rate,
        calculate_seed_fund=triad_util.calculate_seed_fund
    )

    traders_list = [trader]

    # Create a task to run the infinite loop
    task = asyncio.create_task(trader.start_trading())

    try:
        # Wait for the user input to break the loop
        await asyncio.gather(
            task,
            handle_user_input(traders_list)
        )
    except KeyboardInterrupt:
        print("Received KeyboardInterrupt. Exiting...")


async def handle_user_input(traders_list):
    while True:
        command = await asyncio.to_thread(input, "Type what to halt (hunting 'hunt' : stop all 'stop' ) :")
        if command == "hunt":
            print("Halting traders hunting for profit . . .")
            for trader in traders_list:
                trader.hunt_profit_flag = False
        elif command == "stop":
            print("Exiting the program . . .")
            break


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print("hello")


test_main()




# See PyCharm help at https://www.jetbrains.com/help/pycharm/
