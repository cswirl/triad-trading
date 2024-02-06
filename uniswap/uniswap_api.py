# https://thegraph.com/hosted-service/subgraph/uniswap/uniswap-v3
import requests
import json
from web3 import Web3

from uniswap import constants, token_pair, utils
from uniswap.config_file import *

POOLS_CACHE_FILENAME = "uniswap_pools.json"
TRIAD_JSON_FILENAME = "uniswap_triads.json"
UNISWAP_SURFACE_RATES_FILENAME = "uniswap_surface_rates.json"



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
        pools = utils.load_json_file(file_path) or fetch_uniswap_data_pools() or None
    else:
        pools = fetch_uniswap_data_pools()

    if pools:
        print(f'There are {len(pools)} trading pairs in the list.')

    return pools

def fetch_uniswap_data_pools():
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

def create_list_pairs(data_pools:[]):
    """
    Create a dictionary of TradingPair objects from data pools

    Parameters:
        data_pools (json): a dictionary of the original json data from The Graph.

    Returns:
         pairs_map (dict): a dictionary of TradingPair object where key is the pair_symbol. Ex. 'USDT_BTC'
    """

    print("creating a list of trading pairs from data pools. . .")

    pools = data_pools[:constants.LIMIT] if constants.LIMIT <= len(data_pools) else data_pools      # will get an error if the limit is more than the length of the list

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

        pair_symbol = token_0_symbol + constants.PAIRS_DELIMITER + token_1_symbol
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

        if pair_symbol in pairs_map.keys():
            pairs_map[pair_symbol].append(pool)
        else:
            pairs_map[pair_symbol] = [pool]

    return  pairs_map, tokens_dict


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

POOLS = retrieve_data_pools(cache=True)
PAIRS_DICT, TOKENS_DICT = create_list_pairs(POOLS)