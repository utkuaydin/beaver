import os
import queue
import datetime

from backtesting.data import BistDataHandler
from backtesting.execution import SimulatedExecutionHandler
from naive_greedy_portfolio import NaiveGreedyPortfolio

from simple_moving_average_ribbon import SimpleMovingAverageRibbonStrategy
from export import export_all

events = queue.Queue()
symbols = ['THYAO.E', 'PGSUS.E', 'ULKER.E', 'GARAN.E']
csv_dir = os.getcwd() + '/data/bist/symbols/'

start_date = datetime.date(2017, 1, 1)
bars = BistDataHandler(events, csv_dir, symbols, start_date)
strategy = SimpleMovingAverageRibbonStrategy(bars, events, [10, 20, 30, 40, 50, 60])
portfolio = NaiveGreedyPortfolio(bars, events, datetime.date(2015, 12, 1))
broker = SimulatedExecutionHandler(events, symbols)

while True:
    if bars.continue_backtest:
        bars.update_bars()
    else:
        print('\n'.join(['{}: {}'.format(column, value) for column, value in portfolio.output_summary_stats()]))
        export_all(bars, portfolio, broker)
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
                    print(event)
                elif event.type == 'ORDER':
                    broker.execute_order(event)
                elif event.type == 'FILL':
                    portfolio.update_fill(event)
