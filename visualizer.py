import pandas as pd
import matplotlib.pyplot as plt


def visualize(data, portfolio, orders, simulation=None):
    directions = []

    for symbol in orders:
        directions.append(pd.DataFrame(orders[symbol]).set_index('date')['direction'])
        
    orders_df = pd.DataFrame(directions).T.fillna('HOLD')
    orders_df.columns = [symbol + '_ORDER' for symbol in orders.keys()]
    df = pd.DataFrame(portfolio).drop('cash', axis=1).drop_duplicates(subset='datetime').set_index('datetime')
    df = df.merge(orders_df, how='left', left_index=True, right_index=True).fillna('HOLD')

    fig = plt.figure(figsize=(16,8))
    ax1 = fig.add_subplot(111,  ylabel='Value in ₺')

    for symbol in orders.keys():
        column = symbol + '_ORDER'
        data[symbol]['CLOSING PRICE'].plot(label=symbol[:-2])
        ax1.plot(df[column].loc[df[column] == 'BUY'].index, data[symbol]['CLOSING PRICE'][df[column] == 'BUY'], '^', markersize=10, label=symbol[:-2] + ' Buy Order')
        ax1.plot(df[column].loc[df[column] == 'SELL'].index, data[symbol]['CLOSING PRICE'][df[column] == 'SELL'], 'v', markersize=10, label=symbol[:-2] + ' Sell Order')
            
    ax1.legend()
    plt.show()
