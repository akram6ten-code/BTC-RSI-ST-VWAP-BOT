import requests, time
from datetime import datetime

print("Bot Started")

while True:
    try:
        r = requests.get("https://api.india.delta.exchange/v2/tickers/BTCUSD").json()
        price = r['result']['mark_price']
        print(f"BTC Price: {price} - Time: {datetime.now()}")
        print("Checking RSI + SuperTrend + VWAP...")
    except Exception as e:
        print(e)
    time.sleep(60)
