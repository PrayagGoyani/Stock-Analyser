from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import numpy as np
import io
import base64
import os

# Use Object-Oriented Matplotlib for Thread Safety in Flask
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

# Import your functions from project.py
from project import fetch_data, calculate_moving_average, summarize_trend, calculate_rsi, calculate_macd

app = Flask(__name__)

def clean_trend_summary(summary: str) -> str:
    """Remove colorama formatting from trend summary."""
    import re
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', summary)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        symbol = data.get('symbol', '').upper().strip()
        period = data.get('period', '1mo')
        window = int(data.get('window', 5))
        
        if not symbol or not symbol.isalpha() or len(symbol) > 5:
            return jsonify({'error': 'Invalid stock symbol.'}), 400
        
        valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"]
        if period not in valid_periods:
            return jsonify({'error': 'Invalid period selected.'}), 400
        
        # Pad short timeframes with "3mo" so MACD (26-day EMA) has enough data
        fetch_period = "3mo" if period in ["1d", "5d", "1mo"] else period
        
        stock_data = fetch_data(symbol, fetch_period)
        if stock_data.empty:
            return jsonify({'error': 'No data found for this symbol.'}), 404
        
        # Calculate Indicators on the padded data
        ma = calculate_moving_average(stock_data, window)
        stock_data[f'{window}d_MA'] = ma
        stock_data['RSI'] = calculate_rsi(stock_data)
        macd, signal_line = calculate_macd(stock_data)
        stock_data['MACD'] = macd
        stock_data['MACD_Signal'] = signal_line
        
        # Slice the dataframe down to the requested timeframe
        if period == "1d":
            stock_data = stock_data.tail(1)
        elif period == "5d":
            stock_data = stock_data.tail(5)
        elif period == "1mo":
            stock_data = stock_data.tail(21)  # Approx 21 trading days in a month
            
        trend_summary = clean_trend_summary(summarize_trend(stock_data))
        
        start = stock_data['Close'].iloc[0]
        end = stock_data['Close'].iloc[-1]
        change = ((end - start) / start) * 100
        
        # Replace Pandas NaN with Python None (becomes JSON null) for JS rendering
        dates = [date.strftime('%Y-%m-%d') for date in stock_data.index]
        closing_prices = stock_data['Close'].tolist()
        moving_avg = stock_data[f'{window}d_MA'].replace({np.nan: None}).tolist()
        rsi_list = stock_data['RSI'].replace({np.nan: None}).tolist()
        macd_list = stock_data['MACD'].replace({np.nan: None}).tolist()
        macd_sig_list = stock_data['MACD_Signal'].replace({np.nan: None}).tolist()
        
        stats = {
            'latest_price': float(stock_data['Close'].iloc[-1]),
            'min_price': float(stock_data['Close'].min()),
            'max_price': float(stock_data['Close'].max()),
            'avg_price': float(stock_data['Close'].mean()),
            'change_percent': float(change)
        }
        
        # Thread-Safe Matplotlib Rendering
        fig = Figure(figsize=(12, 12))
        ax1, ax2, ax3 = fig.subplots(3, 1, sharex=True)
        
        # Ax1: Price and MA
        ax1.plot(stock_data.index, stock_data['Close'], label='Closing Price', color='#2563eb')
        ax1.plot(stock_data.index, stock_data[f'{window}d_MA'], label=f'{window}d MA', linestyle='--', color='#f59e0b')
        ax1.set_title(f"{symbol} Stock Price & Indicators ({period})", fontsize=16, fontweight='bold')
        ax1.set_ylabel("Price ($)", fontsize=12)
        ax1.legend(loc="upper left")
        ax1.grid(True, alpha=0.3)

        # Ax2: RSI
        ax2.plot(stock_data.index, stock_data['RSI'], label='RSI (14)', color='purple')
        ax2.axhline(70, linestyle='--', alpha=0.5, color='red')
        ax2.axhline(30, linestyle='--', alpha=0.5, color='green')
        ax2.set_ylabel("RSI", fontsize=12)
        ax2.legend(loc="upper left")
        ax2.grid(True, alpha=0.3)

        # Ax3: MACD
        ax3.plot(stock_data.index, stock_data['MACD'], label='MACD', color='black')
        ax3.plot(stock_data.index, stock_data['MACD_Signal'], label='Signal Line', color='red')
        ax3.bar(stock_data.index, stock_data['MACD'] - stock_data['MACD_Signal'], color='gray', alpha=0.3)
        ax3.set_ylabel("MACD", fontsize=12)
        ax3.set_xlabel("Date", fontsize=12)
        ax3.legend(loc="upper left")
        ax3.grid(True, alpha=0.3)
        
        fig.tight_layout()
        
        canvas = FigureCanvas(fig)
        img_buffer = io.BytesIO()
        fig.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
        img_buffer.seek(0)
        plot_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        
        csv_data = stock_data.to_csv()
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'period': period,
            'trend_summary': trend_summary,
            'stats': stats,
            'dates': dates,
            'closing_prices': closing_prices,
            'moving_avg': moving_avg,
            'rsi': rsi_list,
            'macd': macd_list,
            'macd_signal': macd_sig_list,
            'plot': plot_base64,
            'csv_data': csv_data
        })
        
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/download_csv', methods=['POST'])
def download_csv():
    try:
        data = request.json
        csv_data = data.get('csv_data', '')
        symbol = data.get('symbol', 'STOCK')
        period = data.get('period', '1mo')
        
        output = io.BytesIO()
        output.write(csv_data.encode('utf-8'))
        output.seek(0)
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f"{symbol}_{period}.csv"
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
