# https://thegraph.com/hosted-service/subgraph/uniswap/uniswap-v3
import requests
import json
import utils
import constants
import token_pair

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
        pools = utils.load_json_file(utils.DATA_FOLDER_PATH, POOLS_CACHE_FILENAME) or fetch_uniswap_data_pools() or None
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
        utils.save_json_to_file(pools,utils.DATA_FOLDER_PATH, POOLS_CACHE_FILENAME)

    return pools

def create_list_pairs(data_pools):
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
        token_0_symbol = pool["token0"]["symbol"]
        token_0_id = pool["token0"]["id"]
        token_0_name = pool["token0"]["name"]
        token_0_decimals = int(pool["token0"]["decimals"])
        token_0_price = float(pool["token0Price"])

        token_1_symbol = pool["token1"]["symbol"]

        token_1_id = pool["token1"]["id"]
        token_1_name = pool["token1"]["name"]
        token_1_decimals = int(pool["token1"]["decimals"])
        token_1_price = float(pool["token1Price"])

        # TradingPair object
        id = pool["id"]
        tvl_eth = pool["totalValueLockedETH"]
        fee_tier = pool["feeTier"]
        pair_symbol = token_0_symbol + constants.PAIRS_DELIMITER + token_1_symbol
        base_token = token_pair.Token(
                                token_0_id
                               ,token_0_symbol
                               ,token_0_name
                               ,token_0_decimals
                               ,token_0_price
                            )

        quote_token = token_pair.Token(
                                token_1_id,
                                token_1_symbol,
                                token_1_name,
                                token_1_decimals,
                                token_1_price
                            )

        tokens_dict[token_0_symbol] = base_token
        tokens_dict[token_1_symbol] = quote_token

        # Add to key-value pair
        # Duplicate handling - Shaun's algorithm is preserving the first entry
        #     - overwrite the previous entry
        #   X - preserve the first entry
        # if pair_symbol not in pairs_map.keys():
        #     pairs_map[pair_symbol] = token_pair.TradingPair(id, pair_symbol, base_token, quote_token)

        pool = token_pair.TradingPair(id, tvl_eth, fee_tier, pair_symbol, base_token, quote_token)

        if pair_symbol in pairs_map.keys():
            pairs_map[pair_symbol].append(pool)
        else:
            pairs_map[pair_symbol] = [pool]

    return  pairs_map, tokens_dict