import pytest
import pandas as pd
from project import fetch_data, calculate_moving_average, summarize_trend, calculate_rsi, calculate_macd

# ------------------------
# TESTING fetch_data()
# ------------------------
def test_fetch_data():
    """
    Test that fetch_data returns a non-empty DataFrame with a 'Close' column.
    """
    df = fetch_data("AAPL", "5d")
    assert isinstance(df, pd.DataFrame), "Expected a pandas DataFrame"
    assert not df.empty, "DataFrame should not be empty"
    assert "Close" in df.columns, "Expected 'Close' column in DataFrame"

# ------------------------
# TESTING calculate_moving_average()
# ------------------------
def test_calculate_moving_average():
    """
    Test that the moving average returns correct length and NaN handling.
    """
    data = pd.DataFrame({"Close": [100, 102, 104, 106, 108]})
    result = calculate_moving_average(data, window=2)
    assert len(result) == len(data), "Output should be same length as input"
    assert result.isnull().sum() == 1, "Expected 1 NaN due to window=2"

# ------------------------
# TESTING summarize_trend()
# ------------------------
def test_summarize_trend_increase():
    """
    Test summary for increasing trend.
    """
    data = pd.DataFrame({"Close": [100, 110]})
    result = summarize_trend(data)
    assert "increased" in result.lower()

def test_summarize_trend_decrease():
    """
    Test summary for decreasing trend.
    """
    data = pd.DataFrame({"Close": [110, 100]})
    result = summarize_trend(data)
    assert "decreased" in result.lower()

def test_summarize_trend_constant():
    """
    Test summary when stock price stays the same.
    """
    data = pd.DataFrame({"Close": [100, 100]})
    result = summarize_trend(data)
    assert "constant" in result.lower() or "same" in result.lower()
    
def test_calculate_rsi():a
    mock_data = pd.DataFrame({'Close': [100, 102, 101, 105, 107, 106, 108]})
    rsi = calculate_rsi(mock_data, period=3)
    assert len(rsi) == 7
    # Assert that the first few rows are calculated (or NaN handled)
    assert rsi is not None

def test_calculate_macd():
    mock_data = pd.DataFrame({'Close': [100, 102, 101, 105, 107, 106, 108]})
    macd, signal = calculate_macd(mock_data, fast=3, slow=5, signal=2)
    
    # Assert both the MACD line and Signal line are returned as Pandas Series
    assert len(macd) == 7
    assert len(signal) == 7
