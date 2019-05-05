import os
import time
import queue

from data import BistDataHandler

events = queue.Queue()
symbols = ['ASELS.E']
csv_dir = os.getcwd() + '/data/bist/symbols/'

bars = BistDataHandler(events, csv_dir, symbols)
# strategy = Strategy()
# portfolio = Portfolio()
# broker = ExecutionHandler()

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
                    pass
                    # strategy.calculate_signals(event)
                    # portfolio.update_time_index(event)
                elif event.type == 'SIGNAL':
                    pass
                    # portfolio.update_signal(event)
                elif event.type == 'ORDER':
                    pass
                    # broker.execute_order(event)
                elif event.type == 'FILL':
                    pass
                    # portfolio.update_fill(event)
    latest_bars = bars.get_latest_bars('ASELS.E')
    print(latest_bars)
    time.sleep(1)
