import asyncio


async def trade_transaction_counter(increment_int):
    #g_trade_transaction_counter += increment_int
    pass





# -------------------- GLOBAL VARIABLES ? -----------------------------------

SECONDS = 10  # will control the hunting sleep in seconds
g_total_active_traders = 33 * SECONDS  # sleep_time = g_total_active_traders / RATE_LIMIT_PER_SECOND
g_trade_transaction_counter = 0
g_consecutive_trade_failure = 0