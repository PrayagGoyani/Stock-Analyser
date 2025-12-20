from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import io
import base64
from project import fetch_data, calculate_moving_average, summarize_trend
import os

app = Flask(__name__)

def clean_trend_summary(summary: str) -> str:
    """Remove colorama formatting from trend summary."""
    # Remove ANSI color codes
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
        
        # Validate symbol
        if not symbol or not symbol.isalpha() or len(symbol) > 5:
            return jsonify({'error': 'Invalid stock symbol. Please enter a valid symbol (e.g., AAPL, TSLA)'}), 400
        
        # Validate period
        valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"]
        if period not in valid_periods:
            return jsonify({'error': f'Invalid period. Please choose from: {", ".join(valid_periods)}'}), 400
        
        # Fetch data
        stock_data = fetch_data(symbol, period)
        if stock_data.empty:
            return jsonify({'error': 'No data found for this symbol and period. Please try again.'}), 404
        
        # Calculate moving average
        ma = calculate_moving_average(stock_data, window)
        
        # Get trend summary
        trend_summary = clean_trend_summary(summarize_trend(stock_data))
        
        # Extract percentage change
        start = stock_data['Close'].iloc[0]
        end = stock_data['Close'].iloc[-1]
        change = ((end - start) / start) * 100
        
        # Prepare data for JSON response
        dates = [date.strftime('%Y-%m-%d') for date in stock_data.index]
        closing_prices = stock_data['Close'].tolist()
        moving_avg = ma.fillna(0).tolist()  # Replace NaN with 0 for JSON serialization
        
        # Statistics
        stats = {
            'latest_price': float(stock_data['Close'].iloc[-1]),
            'min_price': float(stock_data['Close'].min()),
            'max_price': float(stock_data['Close'].max()),
            'avg_price': float(stock_data['Close'].mean()),
            'change_percent': float(change)
        }
        
        # Create plot
        plt.figure(figsize=(12, 6))
        plt.plot(stock_data.index, stock_data['Close'], label='Closing Price', linewidth=2, color='#2563eb')
        plt.plot(stock_data.index, ma, label=f'{window}-Day Moving Average', linestyle='--', color='#f59e0b', linewidth=2)
        plt.title(f"{symbol} Stock Price ({period})", fontsize=16, fontweight='bold')
        plt.xlabel("Date", fontsize=12)
        plt.ylabel("Price ($)", fontsize=12)
        plt.legend(fontsize=11)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Convert plot to base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
        img_buffer.seek(0)
        plot_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        plt.close()
        
        # Prepare CSV data
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
            'plot': plot_base64,
            'csv_data': csv_data
        })
        
    except Exception as e:
        return jsonify({'error': f'Something went wrong: {str(e)}'}), 500

@app.route('/download_csv', methods=['POST'])
def download_csv():
    try:
        data = request.json
        csv_data = data.get('csv_data', '')
        symbol = data.get('symbol', 'STOCK')
        period = data.get('period', '1mo')
        
        # Create in-memory file
        output = io.BytesIO()
        output.write(csv_data.encode('utf-8'))
        output.seek(0)
        
        filename = f"{symbol}_{period}.csv"
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

