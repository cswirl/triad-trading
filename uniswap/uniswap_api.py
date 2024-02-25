# https://thegraph.com/hosted-service/subgraph/uniswap/uniswap-v3
import requests
import json
from web3 import Web3

from uniswap import token_pair, utils, func_triangular_arb
from uniswap.config_file import *
from uniswap.constants import *
from uniswap.token_pair import TradingPair

""" RETRIEVE GRAPH QL MID PRICES FOR UNISWAP """
def retrieve_uniswap_information():
    query = """
             {
                  pools (orderBy: totalValueLockedETH, 
                    orderDirection: desc,
                    first:500) 
                    {
                        id
                        totalValueLockedETH
                        token0Price
                        token1Price
                        feeTier
                        token0 {id symbol name decimals}
                        token1 {id symbol name decimals}
                    }
            }
        """

    url = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"
    req = requests.post(url, json={'query': query})
    json_dict = json.loads(req.text)
    return json_dict

def retrieve_data_pools(cache=True):
    """
    Fetches data from an external data source (The Graph) or local cache

    :return pools (dict): the data returned is a json file received from The Graph.
    """

    if cache:
        print(f"getting data pools from local cache...")
        # if no local cache found then pull data from a data source
        file_path = utils.filepath_builder(utils.DATA_FOLDER_PATH, POOLS_CACHE_FILENAME)
        pools = utils.load_json_file(file_path) or _fetch_uniswap_data_pools() or None
    else:
        pools = _fetch_uniswap_data_pools()

    if pools:
        print(f'There are {len(pools)} trading pairs in the list.')

    return pools

def _fetch_uniswap_data_pools():
    """internal use
    Fetch uniswap data pools and save it to local cache

    :return pools (dict): the data returned is a json file received from The Graph.
    """
    print("fetching uniswap data pools...")
    pools = retrieve_uniswap_information()["data"]["pools"]

    if pools:
        # save to local cache
        file_path = utils.filepath_builder(utils.DATA_FOLDER_PATH, POOLS_CACHE_FILENAME)
        utils.save_json_to_file(pools, file_path)

    return pools

def create_tokens_and_trading_pairs(data_pools:[]):
    """
    Create a dictionary of TradingPair objects from data pools

    Parameters:
        data_pools (json): a dictionary of the original json data from The Graph.

    Returns:
         pairs_map (dict): a dictionary of TradingPair object where key is the pair_symbol. Ex. 'USDT_BTC'
    """

    print("creating a list of trading pairs from data pools. . .")

    pools = data_pools[:LIMIT] if LIMIT <= len(data_pools) else data_pools

    pairs_map = {}
    tokens_dict = {}

    for pool in pools:
        token_0 = pool["token0"]
        token_0_symbol = token_0["symbol"]
        token_0_id = Web3.to_checksum_address(token_0["id"])
        token_0_name = token_0["name"]
        token_0_decimals = int(token_0["decimals"])

        token_1 = pool["token1"]
        token_1_symbol = token_1["symbol"]
        token_1_id = Web3.to_checksum_address(token_1["id"])
        token_1_name = token_1["name"]
        token_1_decimals = int(token_1["decimals"])


        # TradingPair object
        id = Web3.to_checksum_address(pool["id"])
        tvl_eth = pool["totalValueLockedETH"]
        fee_tier = pool["feeTier"]
        token_0_price = float(pool["token0Price"])
        token_1_price = float(pool["token1Price"])

        pair_symbol = token_0_symbol + PAIRS_DELIMITER + token_1_symbol
        base_token = token_pair.Token(
                                token_0_id
                               ,token_0_symbol
                               ,token_0_name
                               ,token_0_decimals
                            )

        quote_token = token_pair.Token(
                                token_1_id,
                                token_1_symbol,
                                token_1_name,
                                token_1_decimals
                            )

        tokens_dict[token_0_symbol] = base_token
        tokens_dict[token_1_symbol] = quote_token

        # Add to key-value pair
        # Duplicate handling - Shaun's algorithm is preserving the first entry
        #     - overwrite the previous entry
        #     - preserve the first entry
        #   X - using a list of pools for each Trading Pair

        pool = token_pair.TradingPair(
            id,
            tvl_eth,
            fee_tier,
            token_0_price,
            token_1_price,
            pair_symbol,
            base_token,
            quote_token
        )

        if generate_pool_key(pair_symbol) in pairs_map.keys():
            pairs_map[generate_pool_key(pair_symbol)].append(pool)
        else:
            pairs_map[generate_pool_key(pair_symbol)] = [pool]


    #save to json file for study
    # save Tokens dict
    file_path = utils.filepath_today_folder(utils.DATA_FOLDER_PATH, "uniswap_tokens.json")
    utils.save_json_to_file(tokens_dict, file_path)

    # save Trading Pairs
    _save_trading_pairs(pairs_map)

    return  pairs_map, tokens_dict

def _save_trading_pairs(pairs_dict_list: []):
    # save pools to json file
    data_pools = []
    for k, v in pairs_dict_list.items():

        pools_list = []
        for pair in v:
            pair_dict = {
                "id": pair.id,
                "tvlEth": pair.tvl_eth,
                "feeTier": pair.fee_tier,
                "token0Price": pair.token0_price,
                "token1Price": pair.token1_price,
                "tradingPairSymbol": pair.pair_symbol,
                "token0": _token_to_dict(pair.token0),
                "token1": _token_to_dict(pair.token1)
            }
            pools_list.append(pair_dict)

        pools_dict = {
            "poolKey": k,
            "poolsTotal": len(pools_list),
            "pools": pools_list
        }

        data_pools.append(pools_dict)

    file_path = utils.filepath_today_folder(utils.DATA_FOLDER_PATH, "uniswap_data_pools.json")
    utils.save_json_to_file(data_pools, file_path)

def _token_to_dict(token):
    return {
        "id": token.id,
        "symbol": token.symbol,
        "name": token.name,
        "decimals": token.decimals
    }

def retrieve_structured_pairs(data_pools, cache=True):
    """
    Retrieve Triangular Structure Pairs - uses the algorithm created by shaun. see func_triangular_arb

    Auto-saves the data to a local file in json format.

    :param data_pools (json): a dictionary of the original json data from The Graph.

    :return structured_pairs (list<dict>):
        list of triad pairs. each item contains the triangular trading pairs with sufficient information
        containing contract id, relative price, decimals, etc. see "data/uniswap_triads.json" file
    """
    if cache:
        print(f"getting triad structures from local cache")
        file_path = utils.filepath_builder(utils.DATA_FOLDER_PATH, TRIAD_JSON_FILENAME)
        structured_pairs = utils.load_json_file(file_path)
        # force re-create triad pairs if no local file exists
        if not structured_pairs:
            print(f"No triad structures from local cache")
            structured_pairs = _recreate_triad_structure(data_pools)
    else:
        structured_pairs = _recreate_triad_structure(data_pools)

    return structured_pairs

def _recreate_triad_structure(pools_data):
    """internal use"""
    print("re-creating triad structures . . .")
    structured_pairs = func_triangular_arb.structure_trading_pairs(pools_data, limit=LIMIT)

    if structured_pairs:
        file_path = utils.filepath_builder(utils.DATA_FOLDER_PATH, TRIAD_JSON_FILENAME)
        utils.save_json_to_file(structured_pairs, file_path)

    return structured_pairs

# #####################################################
#     Utilities
# #####################################################
def find_pair_object(pair_symbol)->TradingPair:
    """
    Find the TradingPair object instance in the pairs_map

    :param pair_symbol (str): unique key
    :return pair_obj (TradingPair or None): TradingPair instance
    """
    try:
        pair_symbol = generate_pool_key(pair_symbol)
        pair_obj = (pair_symbol in PAIRS_DICT and PAIRS_DICT[pair_symbol]) or None
        if pair_obj or len(pair_obj) > 1:
            # todo: get the pool with greatest amount of tvl eth?
            #return max(pair_obj, key=lambda x : x.tvl_eth)
            #already sorted by tvlETH
            return pair_obj[0] # using shaun algorithm where it uses the first pool found
        else:
            print(f"Key '{pair_symbol}' does not exist in the list of Trading Pairs.")

    except KeyError as e:
        print(f"KeyError: {e}. Key '{pair_symbol}' does not exist in the dictionary.")

    return None

def get_network(network="mainnet"):
    # reserve for later
    return Networks[network] if network in Networks.keys() else None


def get_token(symbol):
    """
    Find the Token object instance in the TOKENS_DICT

    :param symbol (str): unique symbol
    :return token (Token or None): Token instance
    """
    token = (symbol in TOKENS_DICT and TOKENS_DICT[symbol]) or None
    if token is None:
        print(f"Key '{symbol}' does not exist in the Tokens dictionary list.")

    return token

def generate_pool_key(pair_symbol: str):
    pool_key = sorted(pair_symbol.split(PAIRS_DELIMITER))
    return "_".join(pool_key)


#-----------------------------------------------------------------

user_input = input("Input 'y' to fetch newest data pools from external data source OR Press ENTER to load pools from local cache: ")
use_cache = user_input.lower() != 'y'

POOLS = retrieve_data_pools(use_cache)
PAIRS_DICT, TOKENS_DICT = create_tokens_and_trading_pairs(POOLS)
TRIANGLE_STRUCTURE_PAIRS = retrieve_structured_pairs(POOLS, use_cache)

# original author shaun implementation - saves to local storage: shaun_uniswap_surface_rates.json