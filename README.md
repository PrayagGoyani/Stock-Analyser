# 📈 Stock Price Analyzer

A web application for analyzing stock prices with interactive charts and moving averages.

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the App

1. Start the server:
```bash
python app.py
```

2. Open your browser and go to:
```
localhost provided by running app.py
```

## Usage

1. Enter a stock symbol (e.g., AAPL, TSLA, MSFT)
2. Select a time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y)
3. Set the moving average window (default: 5)
4. Click "Analyze Stock"

## Features

- Relative Strength Index (RSI - 14 Period)
- Moving Average Convergence Divergence (MACD - 12, 26, 9)
- Intelligently fetches 1 month of background data for short timeframes (1d, 5d) so RSI/MACD mathematical calculations do not fail.
- Uses thread-safe Object-Oriented Matplotlib (`FigureCanvasAgg`) to generate 3 stacked subplots in a single image without crashing the Flask server.
- Stock statistics (min, max, average, latest price)
- Trend analysis with percentage change
- Download data as CSV
- Download charts as PNG

## Requirements

- Python 3.8+
- Flask
- yfinance
- pandas
- matplotlib
- colorama
- numpy
- pytest

## Project Structure

```
├── app.py              # Flask backend
├── project.py          # Core functions
├── test_project.py     # Unit tests for core functions
├── requirements.txt
├── templates/
│   └── index.html     # Frontend
└── static/
    ├── style.css      # Styling
    └── script.js      # JavaScript
```
