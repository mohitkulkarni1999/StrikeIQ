from datetime import datetime

class LiveChainState:

    def __init__(self, symbol: str, expiry: str, strikes=None):

        self.symbol = symbol
        self.expiry = expiry

        # 🔥 THIS HOLDS REGISTRY OPTION MAP
        # { strike : { CE:key , PE:key } }
        self.strike_map = strikes or {}

        self.calls = {}
        self.puts = {}

        self.spot = None
        self.pcr = 0
        self.last_updated = datetime.utcnow()

    def get_option_keys(self, atm: int, window: int = 10):

        strikes = sorted(self.strike_map.keys())

        if not strikes:
            return []

        # find nearest ATM strike
        nearest = min(strikes, key=lambda x: abs(x - atm))

        idx = strikes.index(nearest)

        lower = max(0, idx - window)
        upper = min(len(strikes), idx + window + 1)

        selected = strikes[lower:upper]

        keys = []

        for s in selected:
            opt = self.strike_map.get(s, {})
            if "CE" in opt:
                keys.append(opt["CE"])
            if "PE" in opt:
                keys.append(opt["PE"])

        return keys