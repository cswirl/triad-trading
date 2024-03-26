from collections import  namedtuple

Direction = ["forward", "reverse"]
Pool_Direction = ["baseToQuote", "quoteToBase"]

Token = namedtuple("Token", ["id", "symbol", "name", "decimals"])

#InputToken = namedtuple("InputToken", ["id", "symbol", "name", "decimals", "amount"])
InputToken = namedtuple("InputToken", ["symbol", "amount"])



class TradingPair:
    """
    TradingPair Class

    - Contains a Trading TradingPair Tokens.
    - Resembles a pool in UniSwap.
    - Calculate the surface rate of a pool.
    """
    def __init__(self, id, tvl_eth, fee_tier, token0_price, token1_price, pair_symbol, token0:Token, token1:Token):
        """
        init
        :param id (str): the pools contract id
        :param pair_symbol (str): trading pair symbol. Ex. 'BTC_USDC'
        :param token0 (CryptoToken_Exp1): token0 token
        :param token1 (CryptoToken_Exp1): token1 token
        """
        self.id = id
        self.tvl_eth = tvl_eth
        self.fee_tier = fee_tier
        self.token0_price = token0_price
        self.token1_price = token1_price
        self.pair_symbol = pair_symbol  # no use in defi
        self.token0 = token0  # token0/token1
        self.token1 = token1


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
        if inputToken.symbol == self.token0.symbol:
            direction = Direction[0]
            swap_rate = self.token1_price
            pool_direction = Pool_Direction[0]
            returnToken = self.token1
            contract_id = self.token1.id

        # reverse
        else:
            direction = Direction[1]
            swap_rate = self.token0_price
            pool_direction = Pool_Direction[1]
            returnToken = self.token0
            contract_id = self.token0.id

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
        return f"TradingPair(id={self.id}, symbol={self.pair_symbol}, baseToken={self.token0}, quoteToken={self.token1}"