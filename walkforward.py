#walkforward.py
'''
Define a range of short and long moving averages for optimization.
Divide the historical data into in-sample (training) and out-of-sample (testing) periods.
For each in-sample period, find the best moving average cross using grid search.
Apply the best moving average cross found in the in-sample period to the corresponding out-of-sample period.
Aggregate the results from all out-of-sample periods to evaluate the overall performance.

This script uses the functions provided in previous replies, such as grid_search(), moving_average_cross_strategy(),
calculate_performance(), and get_performance_metrics(). Make sure to include these functions in your script.

Please note that walk-forward optimization can be computationally intensive and may take a while to complete.
You can adjust the number of windows (num_windows) and the range of short and long moving averages to control
the optimization process's complexity.


'''
import pandas as pd
import yfinance as yf
import numpy as np
import csv
from datetime import datetime

# Import all required functions from previous replies or your existing code
# ...

def moving_average_cross_strategy(data, short_window, long_window):
    signals = pd.DataFrame(index=data.index)
    signals['signal'] = 0.0

    signals['short_mavg'] = data['Close'].rolling(window=short_window, min_periods=1, center=False).mean()
    signals['long_mavg'] = data['Close'].rolling(window=long_window, min_periods=1, center=False).mean()

    signals['signal'][short_window:] = np.where(signals['short_mavg'][short_window:] > signals['long_mavg'][short_window:], 1.0, 0.0)

    signals['positions'] = signals['signal'].diff()

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



def grid_search(data, short_ma_values, long_ma_values):
    best_performance = -np.inf
    best_pair = None
    results = []

    for short_ma in short_ma_values:
        for long_ma in long_ma_values:
            if long_ma > short_ma:
                signals = moving_average_cross_strategy(data, short_ma, long_ma)
                #signals = apply_sell_conditions(data, signals)
                portfolio = calculate_performance(data, signals, 4)
                performance_metrics = get_performance_metrics(portfolio, long_ma)

                current_performance = performance_metrics[1]  # Overall Performance (index 1)

                results.append((short_ma, long_ma, current_performance))

                if current_performance > best_performance:
                    best_performance = current_performance
                    best_pair = (short_ma, long_ma)

    return best_pair, results


def walk_forward_optimization(data, short_ma_values, long_ma_values, num_windows):
    # Split data into windows
    window_size = len(data) // num_windows
    windows = [(data.iloc[i * window_size:(i + 1) * window_size]) for i in range(num_windows)]

    out_of_sample_results = []

    for i in range(num_windows - 1):
        in_sample_data = windows[i]
        out_of_sample_data = windows[i + 1]

        # Find best moving average cross in the in-sample period
        best_buy_pair, _ = grid_search(in_sample_data, short_ma_values, long_ma_values)

        # Apply the best moving average cross to the out-of-sample period
        signals = moving_average_cross_strategy(out_of_sample_data, best_buy_pair[0], best_buy_pair[1])
        portfolio = calculate_performance(out_of_sample_data, signals, 4)
        performance_metrics = get_performance_metrics(portfolio, best_buy_pair[1])

        out_of_sample_results.append((best_buy_pair, performance_metrics))

    # Calculate average performance across all out-of-sample periods
    avg_performance = np.mean([result[1][1] for result in out_of_sample_results])

    return avg_performance, out_of_sample_results


def main():
    ticker = "SPY"
    start_date = "2003-01-01"
    end_date = "2023-03-01"
    prediction_start_date = "2023-03-01"
    prediction_end_date = "2023-06-01"

    data = yf.download(ticker, start=start_date, end=end_date)

    short_ma_values = range(3, 21)  # Define a range of short MA values for buying
    long_ma_values = range(22, 51)  # Define a range of long MA values for buying
    num_windows = 8  # Define the number of windows to use for walk-forward optimization

    avg_performance, out_of_sample_results = walk_forward_optimization(data, short_ma_values, long_ma_values, num_windows)

    print("Average performance across all out-of-sample periods:", avg_performance)

    # Fetch the data for the desired prediction time frame
    prediction_data = yf.download(ticker, start=prediction_start_date, end=prediction_end_date)

    # Get the most recent best-performing MA crossover pair
    most_recent_best_buy_pair, _ = out_of_sample_results[-1]

    # Apply the most recent best-performing MA crossover pair to the new data
    signals = moving_average_cross_strategy(prediction_data, most_recent_best_buy_pair[0], most_recent_best_buy_pair[1])

    # Print buy signals
    buy_signals = signals.loc[signals['signal'] == 1]
    print(f"Buy signals for the next 3 months using the most recent best MA crossover {most_recent_best_buy_pair}:\n{buy_signals}\n")

if __name__ == "__main__":
    main()


