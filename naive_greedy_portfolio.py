import pandas as pd

from backtesting.event import OrderEvent
from backtesting.performance import create_sharpe_ratio, create_drawdowns
from backtesting.portfolio import Portfolio


class NaiveGreedyPortfolio(Portfolio):
    def __init__(self, bars, events, start_date, initial_capital=100000.0):
        self.bars = bars
        self.events = events
        self.symbol_list = self.bars.symbol_list
        self.start_date = pd.to_datetime(start_date)
        self.initial_capital = initial_capital
        self.equity_curve = None
        self.simulation = None

        self.all_positions = self.construct_all_positions()
        self.current_positions = {key: value for key, value in [(symbol, 0) for symbol in self.symbol_list]}

        self.all_holdings = self.construct_all_holdings()
        self.current_holdings = self.construct_initial_holdings()

    def construct_all_positions(self):
        dictionary = {key: value for key, value in [(symbol, 0) for symbol in self.symbol_list]}
        dictionary['datetime'] = self.start_date
        return [dictionary]

    def construct_all_holdings(self):
        dictionary = {key: value for key, value in [(symbol, 0.0) for symbol in self.symbol_list]}
        dictionary['datetime'] = self.start_date
        capital_per_sym = self.initial_capital / len(self.symbol_list)
        dictionary['cash'] = {key: value for key, value in [(symbol, capital_per_sym) for symbol in self.symbol_list]}
        dictionary['remaining_cash'] = self.initial_capital  # spare cash in the account after any purchases
        dictionary['commission'] = 0.0  # the cumulative commission accrued
        dictionary['total'] = self.initial_capital  # the total account equity including cash and any open positions
        return [dictionary]

    def construct_initial_holdings(self):
        dictionary = {key: value for key, value in [(symbol, 0.0) for symbol in self.symbol_list]}
        capital_per_sym = self.initial_capital / len(self.symbol_list)
        dictionary['cash'] = {key: value for key, value in [(symbol, capital_per_sym) for symbol in self.symbol_list]}
        print('Cash:', dictionary['cash'])
        dictionary['remaining_cash'] = self.initial_capital
        dictionary['commission'] = 0.0
        dictionary['total'] = self.initial_capital
        return dictionary

    def update_time_index(self, event):
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
        cash_per_symbol = [(symbol, self.current_holdings['cash'][symbol]) for symbol in self.symbol_list]
        holdings['cash'] = {key: value for key, value in cash_per_symbol}
        holdings['remaining_cash'] = self.current_holdings['remaining_cash']
        holdings['commission'] = self.current_holdings['commission']
        holdings['total'] = self.current_holdings['remaining_cash']

        for symbol in self.symbol_list:
            # Approximation to the real value
            market_value = self.current_positions[symbol] * bars[symbol].iloc[0]['CLOSING PRICE']
            holdings[symbol] = market_value
            holdings['total'] += market_value

        # Append the current holdings
        self.all_holdings.append(holdings)

    def update_positions_from_fill(self, fill):
        # Check whether the fill is a buy or sell
        direction = 0

        if fill.direction == 'BUY':
            direction = 1
        if fill.direction == 'SELL':
            direction = -1

        # Update positions list with new quantities
        self.current_positions[fill.symbol] += direction * fill.quantity

    def update_holdings_from_fill(self, fill):
        # Check whether the fill is a buy or sell
        direction = 0

        if fill.direction == 'BUY':
            direction = 1
        if fill.direction == 'SELL':
            direction = -1

        # Update holdings list with new quantities
        cost = self.bars.get_latest_bars(fill.symbol).iloc[0]['CLOSING PRICE']  # Close price
        cost = direction * cost * fill.quantity
        self.current_holdings[fill.symbol] += cost
        self.current_holdings['commission'] += fill.commission
        self.current_holdings['cash'][fill.symbol] -= (cost + fill.commission)
        self.current_holdings['remaining_cash'] -= (cost + fill.commission)
        self.current_holdings['total'] -= (cost + fill.commission)

    def update_fill(self, event):
        if event.type == 'FILL':
            self.update_positions_from_fill(event)
            self.update_holdings_from_fill(event)

    def generate_naive_order(self, signal):
        symbol = signal.symbol
        direction = signal.signal_type
        close_price = self.bars.get_latest_bars(symbol).iloc[0]['CLOSING PRICE']
        symbol_cash = self.current_holdings['cash'][symbol]
        market_quantity = symbol_cash / close_price
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
        if event.type == 'SIGNAL':
            order_event = self.generate_naive_order(event)
            self.events.put(order_event)

    def create_equity_curve(self):
        curve = pd.DataFrame(self.all_holdings)
        curve.set_index('datetime', inplace=True)
        curve['returns'] = curve['total'].pct_change()
        curve['equity_curve'] = (1.0 + curve['returns']).cumprod()
        self.equity_curve = curve

    def output_summary_stats(self):
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
