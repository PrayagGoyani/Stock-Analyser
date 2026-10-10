import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from colorama import init, Fore, Style

# Initialize colorama to automatically reset color after each print
init(autoreset=True)

def fetch_data(symbol: str, period: str = "1mo") -> pd.DataFrame:
    ticker = yf.Ticker(symbol)
    
    # If the user asks for a very short timeframe, fetch 1 month to ensure math works
    fetch_period = period
    if period in ["1d", "5d"]:
        fetch_period = "1mo" 
        
    data = ticker.history(period=fetch_period)
    # Then at the very end of your calculations, slice it back if needed:
    if period == "1d":
        data = data.tail(1) # Keep only the last day
    elif period == "5d":
        data = data.tail(5) # Keep only the last 5 days
        
    return data
def calculate_moving_average(data: pd.DataFrame, window: int = 5) -> pd.Series:
    """
    Calculate the moving average of the closing prices.
    """
    return data['Close'].rolling(window=window).mean()

def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = delta.clip(lower=0).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(data, fast=12, slow=26, signal=9):
    ema_fast = data['Close'].ewm(span=fast, adjust=False).mean()
    ema_slow = data['Close'].ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line

def summarize_trend(data: pd.DataFrame) -> str:
    """
    Return a friendly summary of how the stock performed over time.
    """
    start = data['Close'].iloc[0]
    end = data['Close'].iloc[-1]
    change = ((end - start) / start) * 100
    if change > 0:
        return f"{Fore.GREEN}The stock has increased by {change:.2f}% over the selected period.{Style.RESET_ALL}"
    elif change < 0:
        return f"{Fore.RED}The stock has decreased by {abs(change):.2f}% over the selected period.{Style.RESET_ALL}"
    else:
        return f"{Fore.YELLOW}No change! The stock price stayed the same over this period.{Style.RESET_ALL}"

def main():
    print(Fore.MAGENTA + "\nWelcome to the Stock Price Analyzer! 📈")
    while True:
        user_input = input(Fore.CYAN + "\nEnter a stock symbol (e.g., AAPL, TSLA) or type 'exit' to quit: ")
        if user_input.lower() == 'exit':
            print(Fore.MAGENTA + "Thanks for using Stock Price Analyzer. Goodbye! 👋")
            break

        symbol = user_input.upper()

        if not symbol.isalpha() or len(symbol) > 5:
            print(Fore.RED + "Oops! That doesn't look like a valid stock symbol. Please try again.")
            continue

        period = input(Fore.CYAN + "Choose a time period (e.g., 1mo, 3mo, 6mo, 1y): ").strip()
        if period not in ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"]:
            print(Fore.RED + "Invalid period. Please pick one from: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y.")
            continue

        try:
            data = fetch_data(symbol, period)
            if data.empty:
                print(Fore.RED + "No data found. Maybe the symbol or period is incorrect. Try again!")
                continue

            print(Fore.YELLOW + f"\nLatest closing price for {symbol}: {data['Close'].iloc[-1]:.2f}")
            print(summarize_trend(data))

            window = input(Fore.CYAN + "Enter moving average window (e.g.5): ").strip()
            if not window.isdigit():
                print(Fore.YELLOW + "No valid number entered. Defaulting to 5.")
                window = 5
            else:
                window = int(window)

            # Apply indicators to the dataframe
            ma = calculate_moving_average(data, window)
            data[f'{window}d_MA'] = ma
            data['RSI'] = calculate_rsi(data)
            macd, signal_line = calculate_macd(data)
            data['MACD'] = macd
            data['MACD_Signal'] = signal_line

            # Show key statistics
            print(Fore.BLUE + f"\nQuick Stats:")
            print(Fore.BLUE + f"Min Closing Price: {data['Close'].min():.2f}")
            print(Fore.BLUE + f"Max Closing Price: {data['Close'].max():.2f}")
            print(Fore.BLUE + f"Average Closing Price: {data['Close'].mean():.2f}\n")

            # Save CSV
            csv_filename = f"{symbol}_{period}.csv"
            data.to_csv(csv_filename)
            print(Fore.GREEN + f"Stock data saved as {csv_filename}")

            # Create and save stacked subplots
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
            
            # Plot 1: Price
            ax1.plot(data.index, data['Close'], label='Closing Price', linewidth=2)
            ax1.plot(data.index, ma, label=f'{window}-Day Moving Average', linestyle='--', color='orange')
            ax1.set_title(f"{symbol} Stock Price & Indicators ({period})")
            ax1.set_ylabel("Price")
            ax1.legend(loc="upper left")
            ax1.grid(True)

            # Plot 2: RSI
            ax2.plot(data.index, data['RSI'], label='RSI (14)', color='purple')
            ax2.axhline(70, linestyle='--', alpha=0.5, color='red')
            ax2.axhline(30, linestyle='--', alpha=0.5, color='green')
            ax2.set_ylabel("RSI")
            ax2.legend(loc="upper left")
            ax2.grid(True)

            # Plot 3: MACD
            ax3.plot(data.index, data['MACD'], label='MACD', color='black')
            ax3.plot(data.index, data['MACD_Signal'], label='Signal', color='red')
            ax3.bar(data.index, data['MACD'] - data['MACD_Signal'], color='gray', alpha=0.3)
            ax3.set_ylabel("MACD")
            ax3.set_xlabel("Date")
            ax3.legend(loc="upper left")
            ax3.grid(True)

            plt.tight_layout()
            plot_filename = f"{symbol}_{period}_plot.png"
            plt.savefig(plot_filename)
            plt.close()
            print(Fore.GREEN + f"Graph saved as {plot_filename}\n")

        except Exception as e:
            print(Fore.RED + f"Something went wrong: {e}\nPlease try again. 🙏")

if __name__ == "__main__":
    main()
