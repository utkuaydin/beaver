import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sqlite3
import os
import sys


from backtest import Strategy, Portfolio


class MovingAverageCrossStrategy(Strategy):
    def __init__(self, symbol, bars, short_window=100, long_window=400):
        self.symbol = symbol
        self.bars = bars

        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self):
        signals = pd.DataFrame(index=self.bars.index)
        signals['signal'] = 0.0

        signals['short_mavg'] = self.bars['Close'].rolling(self.short_window, min_periods=1, center=False).mean()
        signals['long_mavg'] = self.bars['Close'].rolling(self.long_window, min_periods=1, center=False).mean()

        signals['signal'][self.short_window:] = np.where(signals['short_mavg'][self.short_window:]
                                                         > signals['long_mavg'][self.short_window:], 1.0, 0.0)

        signals['positions'] = signals['signal'].diff()

        return signals


class MarketOnClosePortfolio(Portfolio):
    def __init__(self, symbol, bars, signals, initial_capital=100000.0):
        self.symbol = symbol
        self.bars = bars
        self.signals = signals
        self.initial_capital = float(initial_capital)
        self.positions = self.generate_positions()

    def generate_positions(self):
        positions = pd.DataFrame(index=self.signals.index).fillna(0.0)
        positions[self.symbol] = self.signals['signal'] * self.bars['Close']
        return positions

    def backtest_portfolio(self):
        portfolio = self.positions.multiply(self.bars['Close'], axis='index')
        pos_diff = self.positions.diff()

        portfolio['holdings'] = self.positions.multiply(self.bars['Close'], axis='index').sum(axis=1)
        portfolio['cash'] = self.initial_capital - pos_diff.multiply(self.bars['Close'], axis='index').sum(
            axis=1).cumsum()

        portfolio['total'] = portfolio['cash'] + portfolio['holdings']
        portfolio['returns'] = portfolio['total'].pct_change()
        return portfolio


def run():
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'ASELS.E'
    capital = float(sys.argv[2] if len(sys.argv) > 2 else 100000.0)

    con = sqlite3.connect('{}/data/bist.db'.format(os.getcwd()))
    query = '''SELECT TARIH AS 'Date', ACILIS_FIYATI AS 'Open', KAPANIS_FIYATI AS 'Close'
               FROM data WHERE ISLEM__KODU=? AND GECICI_DURDURMA=0 ORDER BY TARIH'''

    bars = pd.read_sql_query(query, con=con, params=[symbol])
    bars['Date'] = pd.to_datetime(bars['Date'])
    bars.set_index('Date', inplace=True)

    mac = MovingAverageCrossStrategy(symbol, bars)
    signals = mac.generate_signals()

    portfolio = MarketOnClosePortfolio(symbol, bars, signals, initial_capital=capital)
    returns = portfolio.backtest_portfolio()

    print(returns.tail(10))

    fig = plt.figure(figsize=(16, 8))

    ax1 = fig.add_subplot(111, ylabel='Price in ₺')
    bars['Close'].plot(ax=ax1, color='r', lw=2.)
    signals[['short_mavg', 'long_mavg']].plot(ax=ax1, lw=2.)
    ax1.plot(signals.loc[signals.positions == 1.0].index,
             signals.short_mavg[signals.positions == 1.0],
             '^', markersize=10, color='m')
    ax1.plot(signals.loc[signals.positions == -1.0].index,
             signals.short_mavg[signals.positions == -1.0],
             'v', markersize=10, color='k')
    plt.show()


if __name__ == "__main__":
    run()

