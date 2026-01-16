
import yfinance as yf
import pandas as pd

ticker = yf.Ticker("AAPL")

print("--- Major Holders (Raw) ---")
try:
    mh = ticker.major_holders
    print(mh)
    print("Columns:", mh.columns)
    print("Index:", mh.index)
    print("Values:\n", mh.values)
except Exception as e:
    print(f"Error: {e}")

print("\n--- Institutional Holders (Raw) ---")
try:
    ih = ticker.institutional_holders
    if ih is not None:
        print(ih.head())
        print("Columns:", ih.columns)
        print("Dtypes:", ih.dtypes)
except Exception as e:
    print(f"Error: {e}")
