from backtesting.strategy import Strategy
from backtesting.event import SignalEvent


class SimplerSimpleMovingAverageStrategy(Strategy):
    def __init__(self, bars, events, window):
        self.bars = bars
        self.events = events
        self.window = window
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
                bars = self.bars.get_latest_bars(symbol, self.window)
                latest_closing_price = self.bars.get_latest_bars(symbol, 1)['CLOSING PRICE'][0]

                if len(bars.index) < self.window:
                    continue

                avg = bars['CLOSING PRICE'].mean()

                if latest_closing_price > avg and not self.bought[symbol]:
                    signal = SignalEvent(symbol, bars.iloc[-1].name, 'LONG')
                    self.events.put(signal)
                    self.bought[symbol] = True

                if latest_closing_price < avg and self.bought[symbol]:
                    signal = SignalEvent(symbol, bars.iloc[-1].name, 'EXIT')
                    self.events.put(signal)
                    self.bought[symbol] = False

