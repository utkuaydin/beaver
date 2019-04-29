import numpy as np
import pandas as pd
import sqlite3
import os
import sys

from backtest import Strategy, Portfolio


class RandomForecastingStrategy(Strategy):
    def __init__(self, symbol, bars):
        self.symbol = symbol
        self.bars = bars

    def generate_signals(self):
        signals = pd.DataFrame(index=self.bars.index)
        signals['signal'] = np.random.randint(size=len(signals), low=-1, high=2)
        signals['signal'][0:5] = 0.0
        return signals


class MarketOnOpenPortfolio(Portfolio):
    def __init__(self, symbol, bars, signals, initial_capital=100000.0):
        self.symbol = symbol
        self.bars = bars
        self.signals = signals
        self.initial_capital = float(initial_capital)
        self.positions = self.generate_positions()

    def generate_positions(self):
        positions = pd.DataFrame(index=self.signals.index).fillna(0.0)
        positions[self.symbol] = 100 * self.signals['signal']
        return positions

    def backtest_portfolio(self):
        portfolio = self.positions.multiply(self.bars['Open'], axis='index')
        pos_diff = self.positions.diff()

        portfolio['holdings'] = self.positions.multiply(self.bars['Open'], axis='index').sum(axis=1)
        portfolio['cash'] = self.initial_capital - pos_diff.multiply(self.bars['Open'], axis='index').sum(axis=1).cumsum()
        portfolio['total'] = portfolio['cash'] + portfolio['holdings']
        portfolio['returns'] = portfolio['total'].pct_change()

        return portfolio


def run():
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'ASELS.E'
    con = sqlite3.connect('{}/data/bist.db'.format(os.getcwd()))
    query = "SELECT TARIH AS 'Date', ACILIS_FIYATI AS 'Open' FROM data WHERE ISLEM__KODU=?"

    bars = pd.read_sql_query(query, con=con, params=[symbol])
    bars['Date'] = pd.to_datetime(bars['Date'])
    bars.set_index('Date', inplace=True)

    signals = RandomForecastingStrategy(symbol, bars).generate_signals()
    portfolio = MarketOnOpenPortfolio(symbol, bars, signals)
    returns = portfolio.backtest_portfolio()

    print(returns.head(10))
    print(returns.tail(10))


if __name__ == "__main__":
    run()
