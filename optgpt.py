import pandas as pd
import yfinance as yf
import numpy as np
import csv
from datetime import datetime, timedelta

def moving_average_cross_strategy(data, short_window, long_window):
    signals = pd.DataFrame(index=data.index)
    signals['signal'] = 0.0

    signals['short_mavg'] = data['Close'].rolling(window=short_window, min_periods=1, center=False).mean()
    signals['long_mavg'] = data['Close'].rolling(window=long_window, min_periods=1, center=False).mean()

    signals['signal'][short_window:] = np.where(signals['short_mavg'][short_window:] > signals['long_mavg'][short_window:], 1.0, 0.0)

    signals['positions'] = signals['signal'].diff()

    return signals


def apply_sell_conditions(data, signals):
    sell_dates = signals[signals['positions'] == -1].index
    for sell_date in sell_dates:
        # Find the last buy signal date before the current sell signal date
        previous_buy_dates = signals.loc[:sell_date].loc[signals['positions'] == 1].index

        if len(previous_buy_dates) > 0:
            buy_date = previous_buy_dates[-1]

            # Check if the 5th, 15th, and 30th day conditions are met
            days_held = (sell_date - buy_date).days
            if days_held == 5 or days_held == 15 or days_held == 30:
                continue
            else:
                signals.loc[sell_date, 'positions'] = 0
        else:
            signals.loc[sell_date, 'positions'] = 0

    return signals


def calculate_performance(data, signals, shares):
    initial_capital = float(shares * data['Close'].iloc[0])
    positions = pd.DataFrame(index=signals.index).fillna(0.0)
    positions['SPY'] = shares * signals['positions']

    portfolio = positions.multiply(data['Close'], axis=0)
    pos_diff = positions.diff()
    portfolio['holdings'] = (positions.multiply(data['Close'], axis=0)).sum(axis=1)
    portfolio['cash'] = initial_capital - (pos_diff.multiply(data['Close'], axis=0)).sum(axis=1).cumsum()
    portfolio['total'] = portfolio['cash'] + portfolio['holdings']
    portfolio['returns'] = portfolio['total'].pct_change()

    return portfolio

def get_performance_metrics(portfolio, long_ma):
    total_trades = len(portfolio[portfolio['returns'].notnull()])
    positive_trades = len(portfolio[portfolio['returns'] > 0])
    negative_trades = len(portfolio[portfolio['returns'] < 0])
    average_positive_return = portfolio[portfolio['returns'] > 0]['returns'].mean()
    average_negative_return = portfolio[portfolio['returns'] < 0]['returns'].mean()
    total_profit = portfolio[portfolio['returns'] > 0]['returns'].sum()
    total_loss = portfolio[portfolio['returns'] < 0]['returns'].sum()
    overall_performance = portfolio['total'].iloc[-1] / portfolio['total'].iloc[0] - 1

    return (long_ma, overall_performance, total_trades, positive_trades, negative_trades, average_positive_return, average_negative_return, total_profit, total_loss)

# Include the previously discussed functions here
# moving_average_cross_strategy
# apply_sell_conditions
# calculate_performance
# get_performance_metrics

def grid_search(data, short_ma_values, long_ma_values):
    best_performance = -np.inf
    best_pair = None
    results = []

    for short_ma in short_ma_values:
        for long_ma in long_ma_values:
            if long_ma > short_ma:
                signals = moving_average_cross_strategy(data, short_ma, long_ma)
                signals = apply_sell_conditions(data, signals)
                portfolio = calculate_performance(data, signals, 4)
                performance_metrics = get_performance_metrics(portfolio, long_ma)

                current_performance = performance_metrics[1]  # Overall Performance (index 1)

                results.append((short_ma, long_ma, current_performance))

                if current_performance > best_performance:
                    best_performance = current_performance
                    best_pair = (short_ma, long_ma)

    return best_pair, results

def grid_search_for_selling(data, buy_short_ma, buy_long_ma, sell_short_ma_values, sell_long_ma_values):
    best_performance = -np.inf
    best_sell_pair = None
    results = []

    buy_signals = moving_average_cross_strategy(data, buy_short_ma, buy_long_ma)

    for sell_short_ma in sell_short_ma_values:
        for sell_long_ma in sell_long_ma_values:
            if sell_long_ma > sell_short_ma:
                sell_signals = moving_average_cross_strategy(data, sell_short_ma, sell_long_ma)
                combined_signals = buy_signals.copy()
                combined_signals['sell_positions'] = -sell_signals['positions']
                combined_signals['positions'] += combined_signals['sell_positions']

                combined_signals = apply_sell_conditions(data, combined_signals)
                portfolio = calculate_performance(data, combined_signals, 4)
                performance_metrics = get_performance_metrics(portfolio, sell_long_ma)

                current_performance = performance_metrics[1]  # Overall Performance (index 1)

                results.append((sell_short_ma, sell_long_ma, current_performance))

                if current_performance > best_performance:
                    best_performance = current_performance
                    best_sell_pair = (sell_short_ma, sell_long_ma)

    return best_sell_pair, results



def main():
    ticker = "SPY"
    start_date = "2000-01-01"
    end_date = "2023-03-31"

    data = yf.download(ticker, start=start_date, end=end_date)

    short_ma_values = range(3, 50)  # Define a range of short MA values for buying
    long_ma_values = range(4, 51)  # Define a range of long MA values for buying

    # Find the best buy pair
    best_buy_pair, buy_results = grid_search(data, short_ma_values, long_ma_values)
    print("Best performing moving average cross for buying:", best_buy_pair)

    sell_short_ma_values = range(3, 21)  # Define a range of short MA values for selling
    sell_long_ma_values = range(22, 51)  # Define a range of long MA values for selling

    # Find the best sell pair based on the best buy pair
    best_sell_pair, sell_results = grid_search_for_selling(data, best_buy_pair[0], best_buy_pair[1], sell_short_ma_values, sell_long_ma_values)
    print("Best performing moving average cross for selling:", best_sell_pair)


    # Optionally save results to CSV
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f'grid_search_results_{current_time}.csv'

    with open(file_name, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Short MA', 'Long MA', 'Overall Performance'])
        for row in best_sell_pair:
            writer.writerow(row)

if __name__ == "__main__":
    main()
