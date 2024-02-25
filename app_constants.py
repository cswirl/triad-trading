
# todo: place one trade then go dormant
# assigning True will make the trader instance to place trade against the pool thereafter
# - may cause many duplicate trade on same pathway - or repeated trade failure or
# - until a clearing system is implemented
POST_TRADE_CONTINUE = True

SECONDS_IN_A_DAY = 86400    # 1 Day = 60 sec * 60 min * 24 hour = 86400 seconds
# REMEMBER: block time is 15 sec.
POST_TRADE_EXECUTION_SLEEP = 60*60 # tentative
DEFAULT_SLEEP_TIME = 16
NO_FUNDS_SLEEP_TIME = 30
CONTRACT_LOGIC_ERROR_SLEEP = 60 * 2
TRADE_TIMEOUT = 60 * 60
#------------------
MAX_TRADING_TRANSACTIONS_SLEEP = 60
CONSECUTIVE_FAILED_TRADE_SLEEP = SECONDS_IN_A_DAY
SYMBOL_NOT_IN_STARTING_TOKEN_SLEEP = 30 # or zero

TRADER_MONITOR_SLEEP = 8

TRADER_NUMBER_OF_REQUEST_PER_ROUND = 4.5

# INFURA NETWORK QUERY LIMIT
#  100,000 in a day
#  33 in a second

#Formulas: AUTO-ADJUSTING
# a single trader, must not exceed 33 request in a second
#   sleep time = 1 second / 33
#
#  Therefore, sleep time = total_active_traders / RATE_LIMIT_PER_SECOND
RATE_LIMIT_PER_SECOND = 33

# SLEEP TIME = SECONDS_IN_A_DAY * total_active_traders * TRADER_NUMBER_OF_REQUEST_PER_ROUND / LIMIT_PER_DAY
LIMIT_PER_DAY = 100000      # INFURA 100,000 Daily Limit


DEPTH_MIN_RATE = 1.5    # in percent
MIN_SURFACE_RATE = 1.5
sqrtPriceLimitX96 = 0
GAS_FEE = 3000


MAX_TRADING_TRANSACTIONS = 10 # losing gas fee for every reverted / fail triangular trade
CONSECUTIVE_FAILED_TRADE_THRESHOLD = 5

# FUNDING_TIER_0 = 500    #all stable coins
# FUNDING_TIER_1 = 200
# FUNDING_TIER_2 = 100
# FUNDING_TIER_3 = 50
# FUNDING_TIER_4 = 30
# MINIMUM_FUNDING_IN_USD = 10

# ---------------- TESTING --------------------------------------------
# FOR TEST RUN - better to start small! then adjust little by little
MULTI = 20
FUNDING_TIER_0 = 100 * MULTI    #all stable coins
FUNDING_TIER_1 = 80 * MULTI
FUNDING_TIER_2 = 50 * MULTI
FUNDING_TIER_3 = 30 * MULTI
MINIMUM_FUNDING_IN_USD = 10 * MULTI


TRADER_LIST_LIMIT = 0  # Number of Traders. Use 0 for to get ALL


