"""
Module for position tracking and order management. Customized for the
project after learning about event-driven backtesting from QuantStart. See:
https://www.quantstart.com/articles/Event-Driven-Backtesting-with-Python-Part-V
"""

import pandas as pd

from abc import ABCMeta, abstractmethod

from backtesting.event import OrderEvent
from backtesting.performance import create_sharpe_ratio, create_drawdowns


class Portfolio(object):
    """
    The Portfolio class handles the positions and
    market value of all instruments at every bar.
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
        self.equity_curve = None

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

        print(len(self.symbol_list))
        for symbol in self.symbol_list:
            # Approximation to the real value
            market_value = self.current_positions[symbol] * bars[symbol].iloc[0]['closing_price']
            holdings[symbol] = market_value
            holdings['total'] += market_value

        # Append the current holdings
        self.all_holdings.append(holdings)

    def update_positions_from_fill(self, fill):
        """
        Takes a FiltEvent object and updates the position matrix
        to reflect the new position.

        Parameters:
        fill - The FillEvent object to update the positions with.
        """
        # Check whether the fill is a buy or sell
        direction = 0

        if fill.direction == 'BUY':
            direction = 1
        if fill.direction == 'SELL':
            direction = -1

        # Update positions list with new quantities
        self.current_positions[fill.symbol] += direction * fill.quantity

    def update_holdings_from_fill(self, fill):
        """
        Takes a FillEvent object and updates the holdings matrix
        to reflect the holdings value.

        Parameters:
        fill - The FillEvent object to update the holdings with.
        """
        # Check whether the fill is a buy or sell
        direction = 0

        if fill.direction == 'BUY':
            direction = 1
        if fill.direction == 'SELL':
            direction = -1

        # Update holdings list with new quantities
        cost = self.bars.get_latest_bars(fill.symbol).iloc[0]['closing_price']  # Close price
        cost = direction * cost * fill.quantity
        self.current_holdings[fill.symbol] += cost
        self.current_holdings['commission'] += fill.commission
        self.current_holdings['cash'] -= (cost + fill.commission)
        self.current_holdings['total'] -= (cost + fill.commission)

    def update_fill(self, event):
        """
        Updates the portfolio current positions and holdings
        from a FillEvent.
        """
        if event.type == 'FILL':
            self.update_positions_from_fill(event)
            self.update_holdings_from_fill(event)

    def generate_naive_order(self, signal):
        """
        Simply transacts an OrderEvent object as a constant
        quantity sizing of the signal object, without risk
        management or position sizing considerations.

        Parameters:
        signal - The SignalEvent signal information.
        """
        symbol = signal.symbol
        direction = signal.signal_type

        market_quantity = 100
        current_quantity = self.current_positions[symbol]
        order_type = 'MARKET'

        if direction == 'LONG' and current_quantity == 0:
            return OrderEvent(symbol, order_type, market_quantity, 'BUY', signal.datetime)
        if direction == 'SHORT' and current_quantity == 0:
            return OrderEvent(symbol, order_type, market_quantity, 'SELL', signal.datetime)
        if direction == 'EXIT' and current_quantity > 0:
            return OrderEvent(symbol, order_type, abs(current_quantity), 'SELL', signal.datetime)
        if direction == 'EXIT' and current_quantity < 0:
            return OrderEvent(symbol, order_type, abs(current_quantity), 'BUY', signal.datetime)

        return None

    def update_signal(self, event):
        """
        Acts on a SignalEvent to generate new
        orders based on the portfolio logic.
        """
        if event.type == 'SIGNAL':
            order_event = self.generate_naive_order(event)
            self.events.put(order_event)

    def create_equity_curve(self):
        """
        Creates a pandas DataFrame from the all_holdings
        list of dictionaries.
        """
        curve = pd.DataFrame(self.all_holdings)
        curve.set_index('datetime', inplace=True)
        curve['returns'] = curve['total'].pct_change()
        curve['equity_curve'] = (1.0 + curve['returns']).cumprod()
        self.equity_curve = curve

    def output_summary_stats(self):
        """
        Creates a list of summary statistics for the portfolio such
        as Sharpe Ratio and drawdown information.
        """
        self.create_equity_curve()

        total_return = self.equity_curve['equity_curve'][-1]
        returns = self.equity_curve['returns']
        pnl = self.equity_curve['equity_curve']

        sharpe_ratio = create_sharpe_ratio(returns)
        max_dd, dd_duration = create_drawdowns(pnl)

        stats = [("Initial Capital", self.initial_capital),
                 ("Total Holdings", self.all_holdings[-1]['total']),
                 ("Total Return", "%0.2f%%" % ((total_return - 1.0) * 100.0)),
                 ("Sharpe Ratio", "%0.2f" % sharpe_ratio),
                 ("Max Drawdown", "%0.2f%%" % (max_dd * 100.0)),
                 ("Drawdown Duration", "%d" % dd_duration)]
        return stats
