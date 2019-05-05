"""
Module for position tracking and order management. Customized for the
project after learning about event-driven backtesting from QuantStart. See:
https://www.quantstart.com/articles/Event-Driven-Backtesting-with-Python-Part-IV
"""

import pandas as pd

from abc import ABCMeta, abstractmethod


class Portfolio(object):
    """
    The Portfolio class handles the positions and market
    value of all instruments at a resolution of a "bar".
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def update_signal(self, event):
        """
        Acts on a SignalEvent to generate new
        orders based on the portfolio logic.
        """
        raise NotImplementedError("Should implement update_signal()")

    @abstractmethod
    def update_fill(self, event):
        """
        Updates the portfolio current positions
        and holdings from a FillEvent.
        """
        raise NotImplementedError("Should implement update_fill()")


class NaivePortfolio(Portfolio):
    """
    The NaivePortfolio object is designed to send orders to
    a brokerage object with a constant quantity size blindly,
    i.e. without any risk management or position sizing. It is
    used to test simpler strategies such as BuyAndHoldStrategy.
    """

    def __init__(self, bars, events, start_date, initial_capital=100000.0):
        """
        Initialises the portfolio with bars and an event queue.
        Also includes a starting datetime index and initial capital
        (USD unless otherwise stated).

        Parameters:
        bars - The DataHandler object with current market data.
        events - The Event Queue object.
        start_date - The start date (bar) of the portfolio.
        initial_capital - The starting capital in USD.
        """
        self.bars = bars
        self.events = events
        self.symbol_list = self.bars.symbol_list
        self.start_date = pd.to_datetime(start_date)
        self.initial_capital = initial_capital

        self.all_positions = self.construct_all_positions()
        self.current_positions = {key: value for key, value in [(symbol, 0) for symbol in self.symbol_list]}

        self.all_holdings = self.construct_all_holdings()
        self.current_holdings = self.construct_current_holdings()

    def construct_all_positions(self):
        """
        Constructs the positions list using the start_date
        to determine when the time index will begin.
        """
        dictionary = {key: value for key, value in [(symbol, 0) for symbol in self.symbol_list]}
        dictionary['datetime'] = self.start_date
        return [dictionary]

    def construct_all_holdings(self):
        """
        Constructs the holdings list using the start_date
        to determine when the time index will begin.
        """
        dictionary = {key: value for key, value in [(symbol, 0.0) for symbol in self.symbol_list]}
        dictionary['datetime'] = self.start_date
        dictionary['cash'] = self.initial_capital  # spare cash in the account after any purchases
        dictionary['commission'] = 0.0  # the cumulative commission accrued
        dictionary['total'] = self.initial_capital  # the total account equity including cash and any open positions
        return [dictionary]

    def construct_current_holdings(self):
        """
        This constructs the dictionary which will hold the instantaneous
        value of the portfolio across all symbols.
        """
        dictionary = {key: value for key, value in [(symbol, 0.0) for symbol in self.symbol_list]}
        dictionary['cash'] = self.initial_capital
        dictionary['commission'] = 0.0
        dictionary['total'] = self.initial_capital
        return dictionary

    def update_time_index(self, event):
        """
        Adds a new record to the positions matrix for the current
        market data bar. This reflects the PREVIOUS bar, i.e. all
        current market data at this stage is known (OLHCVI).

        Makes use of a MarketEvent from the events queue.
        """
        bars = {}
        for symbol in self.symbol_list:
            bars[symbol] = self.bars.get_latest_bars(symbol)

        # Update positions
        positions = {key: value for key, value in [(symbol, 0) for symbol in self.symbol_list]}
        positions['datetime'] = pd.to_datetime(bars[self.symbol_list[0]].iloc[0].name)

        for symbol in self.symbol_list:
            positions[symbol] = self.current_positions[symbol]

        # Append the current positions
        self.all_positions.append(positions)

        # Update holdings
        holdings = {key: value for key, value in [(symbol, 0) for symbol in self.symbol_list]}
        holdings['datetime'] = pd.to_datetime(bars[self.symbol_list[0]].iloc[0].name)
        holdings['cash'] = self.current_holdings['cash']
        holdings['commission'] = self.current_holdings['commission']
        holdings['total'] = self.current_holdings['cash']

        for symbol in self.symbol_list:
            # Approximation to the real value
            market_value = self.current_positions[symbol] * bars[symbol].iloc[0]['CLOSING PRICE']
            holdings[symbol] = market_value
            holdings['total'] += market_value

        # Append the current holdings
        self.all_holdings.append(holdings)
