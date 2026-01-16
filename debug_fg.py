import requests
import json

try:
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers, timeout=5)
    data = response.json()
    print("Keys:", data.keys())
    if 'fear_and_greed' in data:
        print("F&G Keys:", data['fear_and_greed'].keys())
except Exception as e:
    print(e)
