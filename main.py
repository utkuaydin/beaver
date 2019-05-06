import os
import time
import queue
import datetime

from data import BistDataHandler
from strategy import BuyAndHoldStrategy
from portfolio import NaivePortfolio

events = queue.Queue()
symbols = ['ASELS.E', 'FENER.E', 'GSRAY.E']
csv_dir = os.getcwd() + '/data/bist/symbols/'

bars = BistDataHandler(events, csv_dir, symbols)
strategy = BuyAndHoldStrategy(bars, events)
portfolio = NaivePortfolio(bars, events, datetime.date(2015, 12, 1))
# broker = ExecutionHandler()

passed_days = 1

while True:
    if bars.continue_backtest:
        bars.update_bars()
    else:
        break

    while True:
        try:
            event = events.get(False)
        except queue.Empty:
            break
        else:
            if event is not None:
                if event.type == 'MARKET':
                    strategy.calculate_signals(event)
                    portfolio.update_time_index(event)
                elif event.type == 'SIGNAL':
                    portfolio.update_signal(event)
                elif event.type == 'ORDER':
                    pass
                    # broker.execute_order(event)
                elif event.type == 'FILL':
                    portfolio.update_fill(event)
    latest_bars = bars.get_latest_bars('ASELS.E', passed_days)
    print(latest_bars['CLOSING PRICE'])
    passed_days += 1
    time.sleep(1)
