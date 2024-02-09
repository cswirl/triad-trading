
# todo: place one trade then go dormant
# assigning True will make the trader instance to place trade against the pool thereafter
# - may cause many duplicate trade on same pathway - or repeated trade failure or
# - until a clearing system is implemented
POST_TRADE_CONTINUE = False

# REMEMBER: block time is 15 sec.
POST_TRADE_EXECUTION_SLEEP = 60 * 1 # tentative
DEFAULT_SLEEP_TIME = 16
NO_FUNDS_SLEEP_TIME = 30
CONTRACT_LOGIC_ERROR_SLEEP = 60 * 2

DEPTH_MIN_RATE = 0
MIN_SURFACE_RATE = 1.5
sqrtPriceLimitX96 = 0
GAS_FEE = 3000


MAX_TRADING_TRANSACTIONS = 6  # losing gas fee for every reverted / fail triangular trade
CONSECUTIVE_FAILED_TRADE_THRESHOLD = 3

# FUNDING_TIER_0 = 500    #all stable coins
# FUNDING_TIER_1 = 200
# FUNDING_TIER_2 = 100
# FUNDING_TIER_3 = 50
# FUNDING_TIER_4 = 30
# MINIMUM_FUNDING_IN_USD = 10

# ---------------- TESTING --------------------------------------------
# FOR TEST RUN - better to start small! then adjust little by little
MULTI = 2
FUNDING_TIER_0 = 100 * MULTI    #all stable coins
FUNDING_TIER_1 = 80 * MULTI
FUNDING_TIER_2 = 50 * MULTI
FUNDING_TIER_3 = 30 * MULTI
MINIMUM_FUNDING_IN_USD = 10 * MULTI


TRADER_LIST_LIMIT = 0  # Number of Traders. Use 0 for to get ALL


#-------------------- GLOBAL VARIABLES ? -----------------------------------
