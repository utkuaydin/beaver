from backtesting.strategy import Strategy
from backtesting.event import SignalEvent


class SimpleMovingAverageStrategy(Strategy):
    def __init__(self, bars, events, long_window, short_window):
        self.bars = bars
        self.events = events
        self.long_window = long_window
        self.short_window = short_window
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
                long_bars = self.bars.get_latest_bars(symbol, self.long_window)
                short_bars = self.bars.get_latest_bars(symbol, self.short_window)

                if len(long_bars.index) < self.long_window:
                    continue

                long_avg = long_bars['CLOSING PRICE'].mean()
                short_avg = short_bars['CLOSING PRICE'].mean()

                if short_avg > long_avg and not self.bought[symbol]:
                    signal = SignalEvent(symbol, long_bars.iloc[-1].name, 'LONG')
                    self.events.put(signal)
                    self.bought[symbol] = True

                if short_avg < long_avg and self.bought[symbol]:
                    signal = SignalEvent(symbol, long_bars.iloc[-1].name, 'EXIT')
                    self.events.put(signal)
                    self.bought[symbol] = False

