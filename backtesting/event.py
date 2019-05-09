"""
Module for trading events which drive the backtesting. Customized for the
project after learning about event-driven backtesting from QuantStart. See:
https://www.quantstart.com/articles/Event-Driven-Backtesting-with-Python-Part-II
"""


class Event(object):
    """
    Base class for all of the events.
    """
    pass


class MarketEvent(Event):
    """
    Triggered by DataHandler when there
    is an update in the market data.
    """
    def __init__(self):
        self.type = 'MARKET'


class SignalEvent(Event):
    """
    Triggered when a new signal has been generated
    by Strategy after it evaluates the market data.
    """
    def __init__(self, symbol, datetime, signal_type):
        self.type = 'SIGNAL'
        self.symbol = symbol
        self.datetime = datetime
        self.signal_type = signal_type

    def __str__(self):
        template = "Signal: Symbol={}, Type={}, Date={}"
        return template.format(self.symbol, self.signal_type, self.datetime)


class OrderEvent(Event):
    """
    Triggered by Portfolio after it assesses signals,
    for sending the order to an execution system.
    """
    def __init__(self, symbol, order_type, quantity, direction, datetime):
        self.type = 'ORDER'
        self.symbol = symbol
        self.order_type = order_type
        self.quantity = quantity
        self.direction = direction
        self.datetime = datetime

    def __str__(self):
        template = "Order: Symbol={}, Type={}, Quantity={}, Direction={}"
        return template.format(self.symbol, self.order_type, self.quantity, self.direction)


class FillEvent(Event):
    """
    Represents a filled order which has been returned from a brokerage
    and contains information about the actual cost of the order.
    """
    def __init__(self, time_index, symbol, exchange, quantity, direction, fill_cost, commission=None):
        self.type = 'FILL'
        self.time_index = time_index
        self.symbol = symbol
        self.exchange = exchange
        self.quantity = quantity
        self.direction = direction
        self.fill_cost = fill_cost

        if commission is None:
            self.commission = self.calculate_commission()
        else:
            self.commission = commission

    def calculate_commission(self):
        return max(self.quantity * 0.05, 5.0)
