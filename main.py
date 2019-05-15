import os
import queue
import datetime

from backtesting.data import BistSQLDataHandler
from backtesting.execution import SimulatedExecutionHandler
from naive_greedy_portfolio import NaiveGreedyPortfolio
from optimized_greedy_portfolio import OptimizedGreedyPortfolio
from simple_moving_average import SimpleMovingAverageStrategy
from simple_moving_average_ribbon import SimpleMovingAverageRibbonStrategy
from simpler_simple_moving_average import SimplerSimpleMovingAverageStrategy
from export import export_all
from visualizer import visualize

events = queue.Queue()
symbols = []
csv_dir = os.getcwd() + '/data/bist/symbols/'

while True:
    symbol = input("Write a ticker symbol, or press ENTER to continue: ")

    if symbol == "":
        if len(symbols) > 0:
            break
        else:
            print("You must give at least one symbol")
            continue

    symbols.append(symbol + '.E')

start_date = datetime.date(2017, 1, 1)
bars = BistSQLDataHandler(events, csv_dir, symbols, start_date)

strategies = [
    SimpleMovingAverageStrategy(bars, events, 100, 40),
    SimplerSimpleMovingAverageStrategy(bars, events, 40),
    SimpleMovingAverageRibbonStrategy(bars, events, [10, 20, 30, 40, 50, 60]),
]

print('''
Trading strategies:
1) Simple Moving Average
2) Simpler SMA
3) SMA Ribbon
''')

strategy_choice = input('Pick: ')

print('''
Pick portfolio strategy:
1) Greedy
2) Optimized Greedy
''')

portfolio_choice = int(input('Pick: '))

strategy = strategies[int(strategy_choice) - 1]
portfolio = OptimizedGreedyPortfolio(bars, events, datetime.date(2017, 1, 1)) if portfolio_choice == 2 else NaiveGreedyPortfolio(bars, events, datetime.date(2017, 1, 1))
broker = SimulatedExecutionHandler(events, symbols)

while True:
    if bars.continue_backtest:
        bars.update_bars()
    else:
        print('\n'.join(['{}: {}'.format(column, value) for column, value in portfolio.output_summary_stats()]))
        export_all(bars, portfolio, broker, portfolio.simulation)
        visualize(bars.symbol_data, broker.history, portfolio.simulation)
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
