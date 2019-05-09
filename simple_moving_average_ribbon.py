from backtesting.strategy import Strategy
from backtesting.event import SignalEvent


class SimpleMovingAverageRibbonStrategy(Strategy):
    def __init__(self, bars, events, windows):
        self.bars = bars
        self.events = events
        self.windows = windows
        self.symbol_list = self.bars.symbol_list
        self.bought = self._calculate_initial_bought()

    def _calculate_initial_bought(self):
        bought = {}

        for symbol in self.symbol_list:
            bought[symbol] = False

        return bought

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            for symbol in self.symbol_list:
                latest_closing_bar = self.bars.get_latest_bars(symbol, 1)
                bars = []
                for val in self.windows:
                    bars.append(self.bars.get_latest_bars(symbol, val))

                if len(bars[-1].index) < self.windows[-1]:
                    continue

                bars_mean = []
                for val in bars:
                    bars_mean.append(val['CLOSING PRICE'].mean())

                if self.should_buy(latest_closing_bar['CLOSING PRICE'][0], bars_mean) and not self.bought[symbol]:
                    signal = SignalEvent(symbol, latest_closing_bar.iloc[-1].name, 'LONG')
                    self.events.put(signal)
                    self.bought[symbol] = True

                if self.should_sell(latest_closing_bar['CLOSING PRICE'][0], bars_mean) and self.bought[symbol]:
                    signal = SignalEvent(symbol, latest_closing_bar.iloc[-1].name, 'EXIT')
                    self.events.put(signal)
                    self.bought[symbol] = False

    @staticmethod
    def should_buy(latest_closing_bar, bars_mean):
        i = 0
        for val in bars_mean:
            if latest_closing_bar > val:
                i += 1
        if i >= (len(bars_mean) / 2) + 1:
            return True
        else:
            return False

    @staticmethod
    def should_sell(latest_closing_bar, bars_mean):
        i = 0
        for val in bars_mean:
            if latest_closing_bar < val:
                i += 1
        if i >= (len(bars_mean) / 2) + 1:
            return True
        else:
            return False