
import yfinance as yf
import pandas as pd
import sys

# 표준 출력을 파일로 리다이렉션
with open('debug_output.txt', 'w', encoding='utf-8') as f:
    sys.stdout = f
    
    ticker = yf.Ticker("AAPL")
    
    print("--- Major Holders (Raw) ---")
    try:
        mh = ticker.major_holders
        print(mh)
        print("\nColumns:", mh.columns)
        print("Index:", mh.index)
        print("Values:\n", mh.values)
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n--- Institutional Holders (Raw) ---")
    try:
        ih = ticker.institutional_holders
        if ih is not None:
            print(ih.head())
            print("\nColumns:", ih.columns)
            print("Dtypes:", ih.dtypes)
    except Exception as e:
        print(f"Error: {e}")
