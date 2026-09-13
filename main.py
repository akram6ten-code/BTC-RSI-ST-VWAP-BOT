# --- YE FIX HAI, ISKO SABSE UPAR DAL DE ---
import os
from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def health_check():
    return "BOT IS LIVE - 100 LOT - 150x - OK", 200

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# Flask ko background me chalao
threading.Thread(target=run_web_server, daemon=True).start()
# --- FIX KHATAM ---

# Iske neeche se tera asli bot ka code start hoga
import time
import requests
# ... baki tera code ...import time, requests, pandas as pd
from datetime import datetime, timedelta

DELTA_API_KEY = "QpsoKOJgYw1VaDyg8evzwfPQowkPoB"
DELTA_API_SECRET = "cprr4BdyjK5BY3XJLBABlIYp0OKgIBQ4GXRzM1iiTzf2Ahkak3THrwhsPzzO"
TELEGRAM_BOT_TOKEN = "8470029646:AAHuy2_FeSA4DZRz6L25n0LvSJgX-r9OiAU"
TELEGRAM_CHAT_ID = "6107508649"

def get_rsi(c, p=14):
    d = c.diff()
    g = (d.where(d > 0, 0)).rolling(p).mean()
    l = (-d.where(d < 0, 0)).rolling(p).mean()
    r = g / l
    return 100 - (100 / (1 + r))

def get_supertrend(df, p=10, m=3):
    hl2 = (df['high'] + df['low']) / 2
    atr = (df['high'] - df['low']).rolling(p).mean()
    lo = hl2 - (m * atr)
    df['st_dir'] = 1
    df.loc[df['close'] < lo, 'st_dir'] = -1
    return df

def get_vwap(df):
    df['vwap'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
    return df

def send_telegram(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", data={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=5)
    except: pass

def get_btc_data():
    url = "https://api.delta.exchange/v2/history/candles"
    par = {"resolution": "5", "symbol": "BTCUSD", "start": int((datetime.now() - timedelta(days=1)).timestamp())}
    r = requests.get(url, params=par, timeout=10).json()
    df = pd.DataFrame(r['result'])
    df.columns = ['time','open','high','low','close','volume']
    for c in ['open','high','low','close','volume']: df[c] = df[c].astype(float)
    return df

send_telegram("BOT RESTARTED - Premium Filter Removed - 150x")

while True:
    try:
        df = get_btc_data()
        df['rsi'] = get_rsi(df['close'])
        df = get_supertrend(df)
        df = get_vwap(df)
        last = df.iloc[-1]
        print(f"RSI:{last['rsi']:.1f} ST:{last['st_dir']}")

        if last['rsi'] > 65 and last['close'] < last['vwap'] and last['st_dir'] == -1:
            send_telegram(f"CALL SELL SIGNAL {datetime.now()}")
            time.sleep(300)
        if last['rsi'] < 35 and last['close'] > last['vwap'] and last['st_dir'] == 1:
            send_telegram(f"PUT SELL SIGNAL {datetime.now()}")
            time.sleep(300)
        time.sleep(60)
    except Exception as e:
        print(e)
        time.sleep(10)
