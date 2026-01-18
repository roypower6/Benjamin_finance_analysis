import yfinance as yf
import pandas as pd

# AAPL은 2020년 8월 31일에 4:1 액면분할을 함. 
# 2019년 9월(회계연도 말) 기준 Diluted EPS는 원래 약 $2.97 (분할 후 기준) 또는 $11.89 (분할 전 기준).
# yfinance가 어떤 값을 주는지 확인.

ticker = yf.Ticker("AAPL")
fin = ticker.financials
q_fin = ticker.quarterly_financials

print("=== Annual Diluted EPS (Recent 5 years) ===")
try:
    if 'Diluted EPS' in fin.index:
        print(fin.loc['Diluted EPS'])
    elif 'Basic EPS' in fin.index:
        print(fin.loc['Basic EPS'])
    else:
        print("EPS not found in Annual")
except Exception as e:
    print(e)

print("\n=== Splits ===")
print(ticker.splits)
