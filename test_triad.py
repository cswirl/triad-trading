import unittest

from uniswap import uniswap_api, utils, func_triangular_arb

import triad_module
from app_constants import *


def shaun_surface_rate(structured_pairs):
    surface_rates_list = []
    for t_pair in structured_pairs:
        surface_rate = func_triangular_arb.calc_triangular_arb_surface_rate(t_pair, min_rate=MIN_SURFACE_RATE)
        if len(surface_rate) > 0:
            surface_rates_list.append(surface_rate)

    if surface_rates_list:
        file_path = utils.filepath_today_folder(utils.DATA_FOLDER_PATH, "shaun_uniswap_surface_rates.json")
        utils.save_json_to_file(surface_rates_list, file_path)



class TestTriad(unittest.TestCase):

    def test_triad_creation(self):
        tri_struc_pairs = uniswap_api.TRIANGLE_STRUCTURE_PAIRS

        triad_obj_arr = triad_module.create_triad_objects(triad_module.triad_trading_pairs(tri_struc_pairs))

        surface_rates_all = []
        pathway_count = 0

        for triad in triad_obj_arr:
            pathway_count = pathway_count + len(triad.pathways)
            route_surface_rates = triad.start_pathways_surface_rate_calc()
            if route_surface_rates:
                surface_rates_all = [*surface_rates_all, *route_surface_rates]

        print(f"There are {pathway_count} total active pathways")
        print(f"There are {len(surface_rates_all)} surface rates that passed the threshold of {MIN_SURFACE_RATE}")

        if surface_rates_all and len(surface_rates_all) > 0:
            file_path = utils.filepath_today_folder(utils.DATA_FOLDER_PATH, uniswap_api.UNISWAP_SURFACE_RATES_FILENAME)
            utils.save_json_to_file(surface_rates_all, file_path)


        # This will save shaun's calculation to compare result
        shaun_surface_rate(tri_struc_pairs)


        # pools = uniswap_api.POOLS
        # pairs_dict = uniswap_api.PAIRS_DICT
        # tokens = uniswap_api.TOKENS_DICT
        #

