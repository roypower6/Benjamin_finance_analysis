
import yfinance as yf
import pandas as pd

ticker = yf.Ticker("AAPL")

print("--- Major Holders ---")
try:
    mh = ticker.major_holders
    print(mh)
except Exception as e:
    print(e)

print("\n--- Institutional Holders ---")
try:
    ih = ticker.institutional_holders
    print(ih.head())
    print(ih.columns)
except Exception as e:
    print(e)

print("\n--- Mutual Fund Holders ---")
try:
    mf = ticker.mutualfund_holders
    print(mf.head())
except Exception as e:
    print(e)

