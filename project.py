import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from colorama import init, Fore, Style

# Initialize colorama to automatically reset color after each print
init(autoreset=True)

def fetch_data(symbol: str, period: str = "1mo") -> pd.DataFrame:
    """
    Fetch historical stock data for a given symbol and period.
    """
    ticker = yf.Ticker(symbol)
    return ticker.history(period=period)

def calculate_moving_average(data: pd.DataFrame, window: int = 5) -> pd.Series:
    """
    Calculate the moving average of the closing prices.
    """
    return data['Close'].rolling(window=window).mean()

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

            ma = calculate_moving_average(data, window)

            # Show key statistics
            print(Fore.BLUE + f"\nQuick Stats:")
            print(Fore.BLUE + f"Min Closing Price: {data['Close'].min():.2f}")
            print(Fore.BLUE + f"Max Closing Price: {data['Close'].max():.2f}")
            print(Fore.BLUE + f"Average Closing Price: {data['Close'].mean():.2f}\n")

            # Save CSV
            csv_filename = f"{symbol}_{period}.csv"
            data.to_csv(csv_filename)
            print(Fore.GREEN + f"Stock data saved as {csv_filename}")

            # Create and save plot
            plt.figure(figsize=(10, 5))
            plt.plot(data.index, data['Close'], label='Closing Price', linewidth=2)
            plt.plot(data.index, ma, label=f'{window}-Day Moving Average', linestyle='--', color='orange')
            plt.title(f"{symbol} Stock Price ({period})")
            plt.xlabel("Date")
            plt.ylabel("Price")
            plt.legend()
            plt.grid(True)
            plt.tight_layout()

            plot_filename = f"{symbol}_{period}_plot.png"
            plt.savefig(plot_filename)
            plt.close()
            print(Fore.GREEN + f"Graph saved as {plot_filename}\n")

        except Exception as e:
            print(Fore.RED + f"Something went wrong: {e}\nPlease try again. 🙏")

if __name__ == "__main__":
    main()
