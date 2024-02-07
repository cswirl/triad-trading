PAIRS_DELIMITER = '_'
ROOT_PAIRS_DELIMITER = PAIRS_DELIMITER      # temporarily use the PAIRS_DELIMITER as it is safe and until we find a suitable delimiter
PATH_TRIPLET_DELIMITER = PAIRS_DELIMITER
MIN_SURFACE_RATE = 1.5
LIMIT = 500                                 # change values to lower than the cache length will cause soft error (not harmful)


#------------------- FILE NAME AND PATHS ------------------------------

POOLS_CACHE_FILENAME = "uniswap_pools.json"
TRIAD_JSON_FILENAME = "uniswap_triads.json"
UNISWAP_SURFACE_RATES_FILENAME = "uniswap_surface_rates.json"