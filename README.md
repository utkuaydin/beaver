# Beaver (Capstone Project #0917)
Capstone project for CMP4999 course, by Utku Aydın and Ömer Buğra Selvi.

## Project Description
Algorithmic trading is the use of electronic platforms for entering trading orders with an algorithm which executes pre-programmed trading instructions without human intervention. Although according to modern portfolio theory it is not possible to predict the prices in the market, the traders in the industry use different indices and indicators to forecast the direction of prices and take trading decisions. The project provides tools for importing historical data, obtaining live market data from sources, creating trading strategies, managing portfolios and executing orders. It also implements some of well-known signal and portfolio strategies.

## To Run
First, clone the repo
```sh
git clone https://github.com/utkuaydin/beaver.git
```
Then you might want to create a virtual environment for the project as below:
```sh
virtualenv --python=python3 <folder-name>
source <folder-name>/bin/activate
pip install -r requirements.txt
```

Afterwards, you need to download the Borsa Istanbul data with the Python script called `bist_csv.py`
```sh
python bist_csv.py
```
This process might take up to 30 mins according to your download speed.
After this process is done, you can pick from three trading strategies and two portfolio strategies.
```sh
python main.py
```

## Sample Runs 
#### (Symbol: ASELS, Trading Strategy: SimpleMovingAverage, Portfolio Strategy: NaiveGreedy)
```
Cash: {'ASELS.E': 100000.0}
Signal: Symbol=ASELS.E, Type=LONG, Date=2016-04-19 00:00:00
Signal: Symbol=ASELS.E, Type=EXIT, Date=2016-06-03 00:00:00
Signal: Symbol=ASELS.E, Type=LONG, Date=2016-10-25 00:00:00
Signal: Symbol=ASELS.E, Type=EXIT, Date=2018-02-15 00:00:00
Signal: Symbol=ASELS.E, Type=LONG, Date=2018-07-31 00:00:00
Signal: Symbol=ASELS.E, Type=EXIT, Date=2018-11-29 00:00:00
Initial Capital: 100000.0
Total Holdings: 161812.22863450152
Total Return: 61.81%
Sharpe Ratio: 0.61
Max Drawdown: 82.02%
Drawdown Duration: 373
```
