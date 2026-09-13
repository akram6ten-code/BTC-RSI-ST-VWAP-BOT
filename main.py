from flask import Flask
import threading
import os
import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz

# --- 1. RENDER KE LIYE FLASK SERVER (Isse mat cherna) ---
app = Flask(__name__)
@app.route('/')
def home():
    return "BTC-RSI-ST-VWAP-BOT LIVE | 150x | Next Day Expiry | Premium > 50"
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
threading.Thread(target=run_flask, daemon=True).start()

# --- 2. CONFIG - FINAL JUJU DEMAND ---
LEVERAGE = 150
MIN_PREMIUM = 50
SYMBOL = "BTCUSD" # Delta Perpetual for signal
TIMEFRAME = "5m"
IST = pytz.timezone('Asia/Kolkata')

# Delta Credentials Render Env se lega
DELTA_API_KEY = os.getenv("DELTA_API_KEY")
DELTA_API_SECRET = os.getenv("DELTA_API_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(msg):
    try:
        if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=5)
    except: pass

print(f"BOT STARTED | LEVERAGE={LEVERAGE}x | MIN_PREMIUM={MIN_PREMIUM} | NEXT DAY EXPIRY", flush=True)
send_telegram(f"🚀 BOT RESTARTED\nLeverage: {LEVERAGE}x Isolated\nFilter: Next Day Expiry\nMin Premium: > {MIN_PREMIUM}")

# --- 3. INDICATORS ---
def calculate_rsi(df, period=14):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_supertrend(df, period=10, multiplier=3.0):
    hl2 = (df['high'] + df['low']) / 2
    atr = (df['high'] - df['low']).rolling(period).mean()
    upper_band = hl2 + (multiplier * atr)
    lower_band = hl2 - (multiplier * atr)
    # Simplified ST Logic
    df['st_dir'] = np.where(df['close'] > upper_band.shift(1), 1, -1)
    return df

def calculate_vwap(df):
    df['vwap'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
    return df

# --- 4. DELTA API FUNCTIONS (Tumhara purana logic yahin tha) ---
# NOTE: Yahan tujhe apna asli Delta API wala function rakhna hai
# Main dummy structure de raha hu taki premium check aur expiry check sahi chale

def get_btc_candles():
    # Yahan Delta se BTCUSD ke candles lana
    # For now dummy return
    # Tu apna purana get_candles wala code yahan paste kar sakta hai
    url = "https://api.delta.exchange/v2/history/candles"
    params = {"resolution": "5m", "symbol": "BTCUSD", "start": int((datetime.now()-timedelta(days=1)).timestamp()), "end": int(datetime.now().timestamp())}
    try:
        r = requests.get(url, params=params, timeout=10).json()
        df = pd.DataFrame(r['result'])
        df.rename(columns={'open':'open','high':'high','low':'low','close':'close','volume':'volume'}, inplace=True)
        return df
    except:
        return pd.DataFrame()

def get_next_day_expiry_products():
    # Delta se saare BTC options lao aur kal ki expiry filter karo
    now = datetime.now(IST)
    next_day = now + timedelta(days=1)
    next_day_str1 = next_day.strftime("%d%b%y").upper() # 14SEP24
    next_day_str2 = next_day.strftime("%d-%b-%y").upper()
    next_day_str3 = next_day.strftime("%d%b").upper() # 14SEP

    url = "https://api.delta.exchange/v2/products"
    try:
        r = requests.get(url, timeout=10).json()
        all_products = r['result']
        filtered = []
        for p in all_products:
            if p['contract_type'] == 'call_options' or p['contract_type'] == 'put_options':
                # Check if symbol contains next day expiry
                sym = p['symbol'] # ex: C-BTC-65000-140924
                if next_day_str3 in sym or next_day.strftime("%d%m%y") in sym or next_day.strftime("%d-%m-%y") in sym:
                    # Aur sirf BTC ke options
                    if "BTC" in sym:
                        filtered.append(p)
        return filtered
    except Exception as e:
        print(f"Product fetch error: {e}", flush=True)
        return []

def get_premium(product_id):
    url = f"https://api.delta.exchange/v2/tickers/{product_id}"
    try:
        r = requests.get(url, timeout=5).json()
        return float(r['result']['last_price'])
    except:
        return 0

# --- 5. MAIN LOOP ---
while True:
    try:
        now_ist = datetime.now(IST)
        print(f"[{now_ist.strftime('%d-%m %H:%M:%S')}] Scanning...", flush=True)

        df = get_btc_candles()
        if df.empty or len(df) < 20:
            print("Candle wait...", flush=True)
            time.sleep(60)
            continue

        df['rsi'] = calculate_rsi(df)
        df = calculate_supertrend(df)
        df = calculate_vwap(df)

        last = df.iloc[-1]
        rsi = last['rsi']
        close = last['close']
        vwap = last['vwap']
        st_dir = last['st_dir']

        print(f"Price: {close} | RSI: {rsi:.2f} | VWAP: {vwap:.2f} | ST_Dir: {st_dir}", flush=True)

        # --- SIGNAL LOGIC ---
        # Example: RSI < 35 + Price < VWAP + Supertrend Bearish = PUT SELL
        # Tu apna original signal yahan rakhe
        signal = False
        option_type = None # "P" or "C"

        if rsi < 35 and close < vwap and st_dir == -1:
            signal = True
            option_type = "P" # Oversold but trend down -> Put sell ka soch
        elif rsi > 65 and close > vwap and st_dir == 1:
            signal = True
            option_type = "C"

        if not signal:
            time.sleep(60)
            continue

        # --- FILTER 1: NEXT DAY EXPIRY ---
        products = get_next_day_expiry_products()
        if not products:
            print("Next day expiry product nahi mila, wait...", flush=True)
            time.sleep(60)
            continue

        # --- FILTER 2: PREMIUM > 50 & 150x ---
        # ATM se 2 OTM nikalna hai
        products = sorted(products, key=lambda x: abs(float(x.get('strike_price',0)) - close))

        selected = None
        for prod in products:
            # Sirf C ya P jo signal me hai
            if option_type == "P" and "-P-" not in prod['symbol'] and prod['symbol'][0]!= 'P':
                if "put" not in prod['contract_type'].lower(): continue
            if option_type == "C" and "-C-" not in prod['symbol'] and prod['symbol'][0]!= 'C':
                if "call" not in prod['contract_type'].lower(): continue

            premium = get_premium(prod['symbol'])
            print(f"Checking {prod['symbol']} | Premium: {premium}", flush=True)

            # YAHI TERA MAIN FILTER HAI JUJU
            if premium < MIN_PREMIUM:
                print(f"SKIP: Premium {premium} < {MIN_PREMIUM}", flush=True)
                continue
            else:
                selected = prod
                selected_premium = premium
                break

        if not selected:
            print(f"Koi product {MIN_PREMIUM} se upar nahi mila", flush=True)
            time.sleep(60)
            continue

        # --- FINAL ORDER ---
        print(f"✅ FINAL ENTRY: {selected['symbol']} | Premium {selected_premium} | Lev {LEVERAGE}x", flush=True)
        send_telegram(f"✅ ENTRY FOUND\n{selected['symbol']}\nPremium: {selected_premium}\nLeverage: {LEVERAGE}x Isolated\nNext Day Expiry: YES")

        # YAHAN TERA REAL SELL ORDER CODE AYEGA
        # set_leverage(selected['id'], LEVERAGE, isolated=True)
        # place_order(product_id=selected['id'], size=..., side='sell')

        time.sleep(300) # Ek baar entry ke baad 5 min ruko

    except Exception as e:
        print(f"Loop Error: {e}", flush=True)
        time.sleep(10)
