from uniswap import token_pair, uniswap_api
from uniswap.constants import *

def create_triad_objects(triad_pair_symbols):
    """
    Create a list of Triad objects

    :param triad_pair_symbols (list<string>):

        Each element contains the three(3) triangular trading pair symbol.
        Example: "USDC_WETH, APE_WETH, APE_USDC"

    :return triad_obj_list (list<Triad>): a list of Triad objects
    """

    print("creating Triad objects . . .")
    triad_obj_list = []

    for pair in triad_pair_symbols:
        a, b, c = pair.split(',')
        triad_obj_list.append(Triad([a, b, c], uniswap_api.find_pair_object))

    print(f'There are {len(triad_obj_list)} Triad objects created')

    return triad_obj_list

def triad_trading_pairs(structured_pairs):
    """temporaru use - to extract shauns structured_pairs
    :return combined_list (list<string>):
        Each element contains the three(3) triangular trading pair symbol.
        Example: "USDC_WETH, APE_WETH, APE_USDC"
    """
    combined_list = []
    for sp in structured_pairs:
        combined_list.append(sp["combined"])

    return combined_list



class Triad:
    """Triad class

    Contains the three trading pair symbols to be use for a triangular arbitrage.
    Uses Pathway class.
    """
    def __init__(self, triad_pairs_symbols, func_find_pair_object):
        """
        Parameters:
            list triad_pairs_symbols: a list of three trading pairs symbol of type string. Example: ["USDT_WETH", "BTC_USDT", "BTC_WETH"]
        """
        self.triad_pairs_symbols = triad_pairs_symbols
        self.pathway_six_roots = self._generate_six_pathway_root_pairs(triad_pairs_symbols)
        self.pathways = self._create_six_pathways(self.pathway_six_roots, func_find_pair_object)

    def _generate_six_pathway_root_pairs(self, triad_pairs_symbols):
        """internal use

        Each pair is a trading direction from left to right
        For example: BEAM_MC is a trade that starts from BEAM to be converted to MC

        Parameters:
            triad_pairs_symbols (list): a list of strings. Contains the three trading pairs symbol.
                Example - ['BEAM_MC', 'WETH_MC', 'WETH_BEAM']

        Returns:
            root_pairs (list): a list of six strings.
                Example Output - ['BEAM_MC', 'MC_BEAM', 'MC_WETH', 'WETH_MC', 'BEAM_WETH', 'WETH_BEAM']
        """
        root_pairs = []

        for pair in triad_pairs_symbols:
            base,quote = pair.split(PAIRS_DELIMITER)
            root_pairs.append(f'{base}{ROOT_PAIRS_DELIMITER}{quote}')
            root_pairs.append(f'{quote}{ROOT_PAIRS_DELIMITER}{base}')

        return root_pairs

    def _create_six_pathways(self, pathway_roots, func_find_pair_object):
        """internal use

        list pathway_roots: a list of string

        :return
            list: a list of Pathway objects
        """
        pathways = []
        for root in pathway_roots:
            pathways.append(Pathway(root, self.triad_pairs_symbols, func_find_pair_object))

        return pathways


# PUBLIC FUNCTIONS
    def start_pathways_surface_rate_calc(self):
        """
        Start calculating the surface rates of each of the six Pathways

        If something went wrong while calculating surface rate in a pathway,
        it will be excluded in the list.

        Returns:
            surface_rates (list): a list of dictionary. see Pathway.calculate_surface_rate()
        """
        surface_rates = []
        for route in self.pathways:
            surface_dict = route.calculate_surface_rate()
            if surface_dict:
                surface_rates.append(surface_dict)

        return  surface_rates



class Pathway:
    """
    Pathway class
    used by Triad class.

    Each triangular trading pairs has six unique pathways.
    """
    def __init__(self, root_pair, triad_pairs_symbols, func_find_pair_object):
        """
        Parameters:
            root_pair (str): contains the starting symbol and destination symbol.
                Example 'BTC_USDT' where the starting trade symbol is BTC to be traded to USDT

            triad_pairs_symbols (list): a list of string containing the three triangular trading pairs symbol.
                For example: ["USDT_WETH", "BTC_USDT", "BTC_WETH"]
        """

        self.triad_pairs_symbols = triad_pairs_symbols
        self.root_pair = root_pair
        self.startingToken = self.root_pair.split(ROOT_PAIRS_DELIMITER)[0]
        self.trade_sequence = self._create_trade_sequence(func_find_pair_object)


    def _create_trade_sequence(self, find_pair_object):
        """internal use
        Create a list containing the Trade Sequence in order where each sequence contains TradingPair object instance

        Parameters:
            find_pair_object (func): the function to be used, that will find and return an instance of TradingPair object

        Returns:
            trade_sequence (list): a list or TradingPair instance that will be used for surface rate calculation
        """

        trade_pair_sequence = []

        # sanitation check
        # triad_pairs_symbols example: ["USDT_WETH", "BTC_USDT", "BTC_WETH"]
        if len(self.triad_pairs_symbols) != 3:
            print("A triad must have three (3) trading pairs.")
            return None  # error

        triad_pair_symbols_copy = list(self.triad_pairs_symbols)

        # root_pair example: USDT_BTC which is USDT --> BTC
        starting_symbol, starting_symbol_destination = self.root_pair.split(ROOT_PAIRS_DELIMITER)

        # find TradingPair instance for trade 1
        # - both starting symbol and destination symbol in the root pair must be found
        found_trade_1 = False
        for i, pair_symbol in enumerate(triad_pair_symbols_copy):

            pair_symbol_split = pair_symbol.split(PAIRS_DELIMITER)
            for idx, symbol in enumerate(pair_symbol_split):
                # if matched remove that symbol to parse the remaining one
                if starting_symbol == symbol:
                    pair_symbol_split.pop(idx)

                    # if true means a pair is found for trade 1
                    if starting_symbol_destination == pair_symbol_split[0]:
                        pair_obj = find_pair_object(triad_pair_symbols_copy.pop(i))
                        # Return None is TradingPair object cannot be found
                        if pair_obj is None: return None
                        trade_pair_sequence.append(pair_obj)

                        found_trade_1 = True
                        break

            if found_trade_1: break # breaks out of the outer loop

        if len(trade_pair_sequence) != 1:  # no use i guess since code above: if pair_obj is None: return None
            return None # error

        # find TradingPair instance for trade 2
        #   - only the return symbol which is starting_symbol_destination must be found
        for idx, pair_symbol in enumerate(triad_pair_symbols_copy):
            pair_symbol_split = pair_symbol.split(PAIRS_DELIMITER)
            if starting_symbol_destination in pair_symbol_split:
                pair_obj = find_pair_object(triad_pair_symbols_copy.pop(idx))
                # Return None is TradingPair object cannot be found
                if pair_obj is None: return  None
                trade_pair_sequence.append(pair_obj)
                break

        if len(trade_pair_sequence) != 2: # no use i guess since code above: if pair_obj is None: return None
            return None # error

        # find TradingPair instance for trade 3
        #  - this will be the last remaining pair
        pair_obj = find_pair_object(triad_pair_symbols_copy.pop(0))
        # Return None is TradingPair object cannot be found
        if pair_obj is None: return None
        trade_pair_sequence.append(pair_obj)

        if len(trade_pair_sequence) != 3: # might be useful. might be as the last sanitation check
            return None # error

        return trade_pair_sequence


    def calculate_surface_rate(self):
        """
        Calculate the surface rates of the three (3) trade in a Pathway

        Returns:
            surface_dict (dict or None):
                a viable triangular arbitrage opportunity.

                It will return None if:
                    - the calculation didn't meet the MIN_SURFACE_RATE (see constants)
                    - something went wrong while doing calculation
        """

        # sanitation check
        # Return None if something went wrong in building trade_sequence of a Pathway
        if self.trade_sequence is None or len(self.trade_sequence) != 3:
            print(f"Error : Trade Sequence is missing or broken. see func calculate_surface_rate")
            return None

        # type TradingPair
        swap1 = self.trade_sequence[0]
        swap2 = self.trade_sequence[1]
        swap3 = self.trade_sequence[2]

        #print(self)
        initial_token = token_pair.InputToken(self.startingToken, 1)
        swap1_result = swap1.calculate_surface_rate(initial_token)

        trade_2_token = token_pair.InputToken(swap1_result["returnSymbol"], float(swap1_result["acquiredCoin"]))
        swap2_result = swap2.calculate_surface_rate(trade_2_token)

        trade_3_token = token_pair.InputToken(swap2_result["returnSymbol"], float(swap2_result["acquiredCoin"]))
        swap3_result = swap3.calculate_surface_rate(trade_3_token)


        # calculate pnl and pnl percentage
        profit_loss = float(swap3_result["acquiredCoin"]) - float(initial_token.amount)
        profit_loss_perc = (profit_loss / float(initial_token.amount)) * 100 if initial_token.amount != 0 else 0

        # Filter for significant opportunity size
        if profit_loss_perc >= MIN_SURFACE_RATE:
            t1_desc = f'Swap 1 - {swap1.pair_symbol} ({swap1_result["direction"]}): Start with {initial_token.symbol} of {initial_token.amount}. Swap at {swap1_result["swapRate"]} for {swap1_result["returnSymbol"]} acquiring {swap1_result["acquiredCoin"]}.'
            t2_desc = f'Swap 2 - {swap2.pair_symbol} ({swap2_result["direction"]}): Start with {trade_2_token.symbol} of {swap1_result["acquiredCoin"]}. Swap at {swap2_result["swapRate"]} for {swap2_result["returnSymbol"]} acquiring {swap2_result["acquiredCoin"]}.'
            t3_desc = f'Swap 3 - {swap3.pair_symbol} ({swap3_result["direction"]}): Start with {trade_3_token.symbol} of {swap2_result["acquiredCoin"]}. Swap at {swap3_result["swapRate"]} for {swap3_result["returnSymbol"]} acquiring {swap3_result["acquiredCoin"]}.'

            # Construct Output
            surface_dict = {
                "swap1": initial_token.symbol,
                "swap2": trade_2_token.symbol,
                "swap3": trade_3_token.symbol,
                "poolContract1": swap1.id,
                "poolContract2": swap2.id,
                "poolContract3": swap3.id,
                "poolDirectionTrade1": swap1_result["poolDirection"],
                "poolDirectionTrade2": swap2_result["poolDirection"],
                "poolDirectionTrade3": swap3_result["poolDirection"],
                "directionTrade1": swap1_result["direction"],
                "directionTrade2": swap2_result["direction"],
                "directionTrade3": swap3_result["direction"],
                "startingAmount": initial_token.amount,
                "acquiredCoinT1": swap1_result["acquiredCoin"],
                "acquiredCoinT2": swap2_result["acquiredCoin"],
                "acquiredCoinT3": swap3_result["acquiredCoin"],
                "swap1Rate": swap1_result["swapRate"],
                "swap2Rate": swap2_result["swapRate"],
                "swap3Rate": swap3_result["swapRate"],
                "profitLoss": profit_loss,
                "profitLossPerc": profit_loss_perc,
                "direction": "n/a",
                "tradeDesc1": t1_desc,
                "tradeDesc2": t2_desc,
                "tradeDesc3": t3_desc,
                "rootPair": self.root_pair.replace(PAIRS_DELIMITER, "->") or '<NOT SET>',
                "routeDesc": str(self),
                "swap1Pair": swap1.pair_symbol,
                "swap2Pair": swap2.pair_symbol,
                "swap3Pair": swap3.pair_symbol,
                "tradeSequence": str([swap1.pair_symbol,swap2.pair_symbol, swap3.pair_symbol]),
                "triad": str(self.triad_pairs_symbols)
            }
            #print(surface_dict)
            return surface_dict

        return None

    def __str__(self):
        root_pair = PAIRS_DELIMITER in self.root_pair and self.root_pair.replace(PAIRS_DELIMITER, '->')
        return f"Pathway {root_pair or self.root_pair}: Starting Token: {self.startingToken or '<NOT SET>'}"