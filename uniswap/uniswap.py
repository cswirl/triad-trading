# https://thegraph.com/hosted-service/subgraph/uniswap/uniswap-v3
import requests
import json
import utils

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
        pools = utils.load_json_file(POOLS_CACHE_FILENAME) or fetch_uniswap_data_pools() or None
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