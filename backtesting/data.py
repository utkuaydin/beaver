"""
Module for obtaining the market data for the backtesting. Customized for the
project after learning about event-driven backtesting from QuantStart. See:
https://www.quantstart.com/articles/Event-Driven-Backtesting-with-Python-Part-III
"""
import datetime
import os, os.path
import pandas as pd
from sqlalchemy import create_engine


from abc import ABCMeta, abstractmethod

from backtesting.event import MarketEvent


class DataHandler(object):
    """
    DataHandler is an abstract base class
    providing an interface for data handlers.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_latest_bars(self, symbol, n=1):
        """
        Returns the last N bars or fewer from the symbol
        list or fewer if less bars are available.
        """
        raise NotImplementedError("Should implement get_latest_bars()")

    @abstractmethod
    def update_bars(self):
        """
        Pushes the latest bar to the symbol list.
        """
        raise NotImplementedError("Should implement update_bars()")


class BistDataHandler(DataHandler):
    def __init__(self, events, csv_dir, symbol_list, start_date=datetime.date(2015, 12, 1)):
        self.events = events
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list
        self.start_date = start_date

        self.symbol_data = {}
        self.latest_symbol_data = {}
        self.historical_symbol_data = {}
        self.continue_backtest = True

        self._read_data()

    def _read_data(self):
        index = None

        for symbol in self.symbol_list:
            self.symbol_data[symbol] = pd.read_csv(os.path.join(self.csv_dir, '%s.csv' % symbol), header=0, index_col=0)
            self.symbol_data[symbol].index = pd.to_datetime(self.symbol_data[symbol].index)

            if index is None:
                index = self.symbol_data[symbol].index
            else:
                index.union(self.symbol_data[symbol].index)

            self.latest_symbol_data[symbol] = pd.DataFrame(columns=self.symbol_data[symbol].columns)

        for symbol in self.symbol_list:
            data = self.symbol_data[symbol].reindex(index=index, method='pad')
            self.historical_symbol_data[symbol] = data[:pd.to_datetime(self.start_date)]
            data = data[pd.to_datetime(self.start_date):]
            self.symbol_data[symbol] = data.iterrows()

    def _get_new_bar(self, symbol):
        for index, bar in self.symbol_data[symbol]:
            yield bar

    def get_latest_bars(self, symbol, n=1):
        return self.latest_symbol_data[symbol].tail(n)

    def update_bars(self):
        for symbol in self.symbol_list:
            try:
                bar = self._get_new_bar(symbol).__next__()
            except StopIteration:
                self.continue_backtest = False
            else:
                if bar is not None:
                    self.latest_symbol_data[symbol] = self.latest_symbol_data[symbol].append(bar)

        self.events.put(MarketEvent())


class BistSQLDataHandler(DataHandler):
    def __init__(self, events, csv_dir, symbol_list, start_date=datetime.date(2015, 12, 1)):
        self.events = events
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list
        self.start_date = pd.to_datetime(start_date)
        self.engine = create_engine('postgresql://localhost:5432/bist')

        self.index = None
        self.index_iter = None
        self.symbol_data = {}
        self.latest_symbol_data = {}
        self.historical_symbol_data = {}
        self.continue_backtest = True

        self._read_data()

    def _read_data(self):
        self.index = None

        for symbol in self.symbol_list:
            query = 'SELECT * FROM data WHERE instrument_series_code=%(symbol)s'
            self.symbol_data[symbol] = pd.read_sql_query(query, con=self.engine, params={'symbol': symbol}, index_col='trade_date')
            self.symbol_data[symbol].index = pd.to_datetime(self.symbol_data[symbol].index)

            if self.index is None:
                self.index = self.symbol_data[symbol].index
            else:
                self.index.union(self.symbol_data[symbol].index)

            self.index = self.index.sort_values()
            self.end_date = self.index[-1]
            self.latest_symbol_data[symbol] = pd.DataFrame(columns=self.symbol_data[symbol].columns)

        for symbol in self.symbol_list:
            data = self.symbol_data[symbol].sort_index().reindex(index=self.index, method='pad')
            self.historical_symbol_data[symbol] = data[:self.start_date]
            self.symbol_data[symbol] = data[self.start_date:]

        self.index_iter = self.index.to_series()[self.start_date:].iteritems()

    def _get_next_index(self):
        for index in self.index_iter:
            yield index[0]

    def get_latest_bars(self, symbol, n=1):
        return self.latest_symbol_data[symbol].tail(n)

    def update_bars(self):
        for symbol in self.symbol_list:
            try:
                index = self._get_next_index().__next__()
            except StopIteration:
                self.continue_backtest = False
            else:
                if index is not None:
                    self.latest_symbol_data[symbol] = self.symbol_data[symbol][:index]

        self.events.put(MarketEvent())
