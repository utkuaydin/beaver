import pandas as pd
import matplotlib.pyplot as plt


def visualize(data, portfolio, orders, simulation=None):
    directions = {}

    for symbol in orders:
        directions[symbol] = pd.DataFrame(orders[symbol]).set_index('date')['direction']

    fig = plt.figure(figsize=(16, 8))
    ax1 = fig.add_subplot(111, ylabel='Value in ₺')

    for symbol in orders.keys():
        buy_dates = directions[symbol].index
        sell_dates = directions[symbol].index
        data[symbol]['closing_price'].plot(label=symbol[:-2] + ' Closing Price')
        ax1.plot(buy_dates, data[symbol]['closing_price'][buy_dates], '^', markersize=10, label=symbol[:-2] + ' Buy Order')
        ax1.plot(sell_dates, data[symbol]['closing_price'][sell_dates], 'v', markersize=10, label=symbol[:-2] + ' Sell Order')
            
    ax1.legend()
    plt.show()
