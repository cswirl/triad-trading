from collections import  namedtuple

Direction = ["forward", "reverse"]
Pool_Direction = ["baseToQuote", "quoteToBase"]

Token = namedtuple("Token", ["id", "symbol", "name", "decimals", "price"])

#InputToken = namedtuple("InputToken", ["id", "symbol", "name", "decimals", "amount"])
InputToken = namedtuple("InputToken", ["symbol", "amount"])



class TradingPair:
    """
    TradingPair Class

    - Contains a Trading TradingPair Tokens.
    - Resembles a pool in UniSwap.
    - Calculate the surface rate of a pool.
    """
    def __init__(self, id, tvl_eth, fee_tier, pair_symbol, base:Token, quote:Token):
        """
        init
        :param id (str): the pools contract id
        :param pair_symbol (str): trading pair symbol. Ex. 'BTC_USDC'
        :param base (CryptoToken): base token
        :param quote (CryptoToken): quote token
        """
        self.id = id
        self.tvl_eth = tvl_eth
        self.fee_tier = fee_tier
        self.pair_symbol = pair_symbol
        self.base = base  # base/quote
        self.quote = quote


    def calculate_surface_rate(self, inputToken):
        """
        Calculates the surface rate of a trading pair.

        Parameters:
            inputToken (InputToken): the token to be traded.

        Returns:
            dictionary: contains calculation result and important metadata
        """

        # Configure TradingPair internal i.e. the direction and such
        #
        # Direction = ["forward", "reverse"]
        # Pool_Direction = ["baseToQuote", "quoteToBase"]

        # forward
        if inputToken.symbol == self.base.symbol:
            direction = Direction[0]
            swap_rate = self.quote.price
            pool_direction = Pool_Direction[0]
            returnToken = self.quote
            contract_id = self.quote.id

        # reverse
        else:
            direction = Direction[1]
            swap_rate = self.base.price
            pool_direction = Pool_Direction[1]
            returnToken = self.base
            contract_id = self.base.id

        # Compute trade
        acquired_coin = inputToken.amount * swap_rate

        return {
            "returnSymbol": returnToken.symbol,
            "swapRate": swap_rate,
            "acquiredCoin": acquired_coin,
            "direction": direction,
            "poolDirection": pool_direction,
            "contract": contract_id             # not used
        }

    def __str__(self):
        return f"TradingPair(id={self.id}, symbol={self.pair_symbol}, baseToken={self.base}, quoteToken={self.quote}"