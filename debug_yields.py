
import yfinance as yf

# Tickers to check
tickers = ["^FVX", "^TNX", "^TYX"]
print(f"Fetching {tickers}...")

data = yf.download(tickers, period="1d", progress=False)

if not data.empty:
    print("\nRaw Data Columns:", data.columns)
    try:
        # Access Close
        closes = data['Close'].iloc[-1]
        print("\nLatest Close Values:")
        print(closes)
    except Exception as e:
        print(f"Error accessing close: {e}")
        print(data)
else:
    print("No data returned.")
