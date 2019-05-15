import pandas as pd
import matplotlib.pyplot as plt


def visualize(data, orders, simulation=None):
    if simulation is not None:
        fig, (ax1, ax2) = plt.subplots(1, 2)
        draw_orders(ax1, data, orders)
        draw_sharpe(ax2, simulation)

    else:
        fig = plt.figure()
        draw_orders(fig.add_subplot(111), data, orders)

    plt.show()


def draw_sharpe(ax, simulation):
    all_weights, ret_arr, vol_arr, sharpe_arr = simulation
    ax.set_xlabel('Volatility')
    ax.set_ylabel('Return')
    im = ax.scatter(vol_arr, ret_arr, c=sharpe_arr, cmap='plasma')
    plt.colorbar(im, ax=ax)
    max_sr_pos = sharpe_arr.argmax()
    max_sr_ret = ret_arr[max_sr_pos]
    max_sr_vol = vol_arr[max_sr_pos]
    ax.scatter(max_sr_vol, max_sr_ret, c='red', s=50, edgecolors='black')


def draw_orders(ax, data, orders):
    directions = {}

    for symbol in orders:
        directions[symbol] = pd.DataFrame(orders[symbol]).set_index('date')['direction']

    for symbol in orders.keys():
        buy_dates = directions[symbol][directions[symbol] == 'BUY'].index
        sell_dates = directions[symbol][directions[symbol] == 'SELL'].index
        data[symbol]['closing_price'].plot(ax=ax, label=symbol[:-2] + ' Closing Price')
        ax.plot(buy_dates, data[symbol]['closing_price'][buy_dates],
                '^', markersize=10, label=symbol[:-2] + ' Buy Order')
        ax.plot(sell_dates, data[symbol]['closing_price'][sell_dates],
                'v', markersize=10, label=symbol[:-2] + ' Sell Order')

    ax.set_ylabel('Value in ₺')
    ax.legend()
