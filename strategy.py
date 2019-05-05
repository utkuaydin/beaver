from abc import ABCMeta, abstractmethod

from event import SignalEvent


class Strategy(object):
    """
    Strategy is the base class that
    generates signals for symbols.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def calculate_signals(self, event):
        """
        Provides the mechanisms to calculate the list of signals.
        """
        raise NotImplementedError("Should implement calculate_signals()")


class BuyAndHoldStrategy(Strategy):
    def __init__(self, bars, events):
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events

        # Once buy & hold signal is given, these are set to True
        self.bought = self._calculate_initial_bought()

    def _calculate_initial_bought(self):
        bought = {}

        for symbol in self.symbol_list:
            bought[symbol] = False

        return bought

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            for symbol in self.symbol_list:
                bars = self.bars.get_latest_bars(symbol)

                if bars is not None and not bars.empty:
                    if not self.bought[symbol]:
                        signal = SignalEvent(symbol, bars.iloc[0].name, 'LONG')
                        self.events.put(signal)
                        self.bought[symbol] = True
