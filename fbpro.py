import yfinance as yf
import matplotlib.pyplot as plt
from prophet import Prophet
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import TimeSeriesSplit
import numpy as np

# Define the ticker symbol
ticker = 'SPY'

# Download historical data
data = yf.download(ticker, start='2000-01-01')

# Prepare the data for Prophet
data = data[['Close']]
data.reset_index(inplace=True)  
data.columns = ['ds', 'y']
data.loc[:, 'MA'] = data['y'].rolling(window=200).mean()
data.loc[:, 'Indicator'] = np.where(data['y'] > data['MA'], 'Buy', 'Sell')

# Define custom scoring function
def score_func(y_true, y_pred):
    return mean_absolute_error(y_true, y_pred)

# Initialize the TimeSeriesSplit object
tscv = TimeSeriesSplit(n_splits=5)

# Initialize an empty list to store the scores
scores = []

# Iterate through the splits of the data
for train_index, test_index in tscv.split(data):
    # Get the training and testing data for this split
    train_data = data.iloc[train_index]
    test_data = data.iloc[test_index]

    # Fit the model on the training data
    m = Prophet(yearly_seasonality=True)
    m.fit(train_data)

    # Make predictions on the test data
    future = m.make_future_dataframe(periods=365 * 5)
    forecast = m.predict(future)
    test_predictions = forecast.iloc[-len(test_data):][['yhat']]

    # Calculate the score for this split
    score = score_func(test_data[['y']], test_predictions)

    # Append the score to the scores list
    scores.append(score)

# Calculate the mean score
mean_score = sum(scores) / len(scores)

# Fit the model with all the data
m = Prophet(yearly_seasonality=True)
m.fit(data)

# Create a dataframe to hold predictions
future = m.make_future_dataframe(periods=365 * 5)
forecast = m.predict(future)

# Plot the forecast
plt.figure(figsize=(15, 8))
fig1 = m.plot(forecast)

# Add labels and a title to the graph
plt.xlabel('Date')
plt.ylabel('Price')
plt.title('Stock Price with Buy and Sell Indicators')

# Add gridlines to the graph
plt.grid(True)

# Print the mean score
print("Cross Validation Score : ", mean_score)

# Show the plot
plt.show()