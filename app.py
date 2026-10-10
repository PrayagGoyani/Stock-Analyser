from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import io
import base64
# Added calculate_rsi and calculate_macd to the import list
from project import fetch_data, calculate_moving_average, summarize_trend, calculate_rsi, calculate_macd
import os

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
        
        # Calculate moving average & Indicators
        ma = calculate_moving_average(stock_data, window)
        stock_data[f'{window}d_MA'] = ma
        
        stock_data['RSI'] = calculate_rsi(stock_data)
        macd, signal_line = calculate_macd(stock_data)
        stock_data['MACD'] = macd
        stock_data['MACD_Signal'] = signal_line
        
        # Get trend summary
        trend_summary = clean_trend_summary(summarize_trend(stock_data))
        
        # Extract percentage change
        start = stock_data['Close'].iloc[0]
        end = stock_data['Close'].iloc[-1]
        change = ((end - start) / start) * 100
        
        # Prepare data for JSON response
        dates = [date.strftime('%Y-%m-%d') for date in stock_data.index]
        closing_prices = stock_data['Close'].tolist()
        moving_avg = ma.fillna(0).tolist()  # Replace NaN with 0
        rsi_list = stock_data['RSI'].fillna(0).tolist()
        macd_list = stock_data['MACD'].fillna(0).tolist()
        macd_sig_list = stock_data['MACD_Signal'].fillna(0).tolist()
        
        # Statistics
        stats = {
            'latest_price': float(stock_data['Close'].iloc[-1]),
            'min_price': float(stock_data['Close'].min()),
            'max_price': float(stock_data['Close'].max()),
            'avg_price': float(stock_data['Close'].mean()),
            'change_percent': float(change)
        }
        
        # Create Stacked Plot
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 12), sharex=True)
        
        # Ax1: Price and MA
        ax1.plot(stock_data.index, stock_data['Close'], label='Closing Price', linewidth=2, color='#2563eb')
        ax1.plot(stock_data.index, ma, label=f'{window}-Day Moving Average', linestyle='--', color='#f59e0b', linewidth=2)
        ax1.set_title(f"{symbol} Stock Price & Indicators ({period})", fontsize=16, fontweight='bold')
        ax1.set_ylabel("Price ($)", fontsize=12)
        ax1.legend(fontsize=11, loc="upper left")
        ax1.grid(True, alpha=0.3)

        # Ax2: RSI
        ax2.plot(stock_data.index, stock_data['RSI'], label='RSI (14)', color='purple', linewidth=1.5)
        ax2.axhline(70, linestyle='--', alpha=0.5, color='red')
        ax2.axhline(30, linestyle='--', alpha=0.5, color='green')
        ax2.set_ylabel("RSI", fontsize=12)
        ax2.legend(fontsize=11, loc="upper left")
        ax2.grid(True, alpha=0.3)

        # Ax3: MACD
        ax3.plot(stock_data.index, stock_data['MACD'], label='MACD', color='black', linewidth=1.5)
        ax3.plot(stock_data.index, stock_data['MACD_Signal'], label='Signal Line', color='red', linewidth=1.5)
        ax3.bar(stock_data.index, stock_data['MACD'] - stock_data['MACD_Signal'], color='gray', alpha=0.3)
        ax3.set_ylabel("MACD", fontsize=12)
        ax3.set_xlabel("Date", fontsize=12)
        ax3.legend(fontsize=11, loc="upper left")
        ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Convert plot to base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
        img_buffer.seek(0)
        plot_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        plt.close()
        
        # Prepare CSV data (Automatically includes RSI and MACD now!)
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
