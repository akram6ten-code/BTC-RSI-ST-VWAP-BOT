import time
import requests
import pandas as pd
from datetime import datetime, timedelta

# ========== CONFIG - Yahan apni keys daal de ==========
DELTA_API_KEY = "QpsoKOJgYw1VaDyg8evzwfPQowkPoB"
DELTA_API_SECRET = "cprr4BdyjK5BY3XJLBABlIYp0OKgIBQ4GXRzM1iiTzf2Ahkak3THrwhsPzzO"
TELEGRAM_BOT_TOKEN = "8470029646:AAHuy2_FeSA4DZRz6L25n0LvSJgX-r9OiAU"
TELEGRAM_CHAT_ID = "6107508649"

LEVERAGE = 150
SYMBOL = "BTCUSD"  # Underlying for signal

# ========== INDICATORS ==========
def get_rsi(close, period=14):
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_supertrend(df, period=10, multiplier=3):
    hl2 = (df['high'] + df['low']) / 2
    atr = (df['high'] - df['low']).rolling(period).mean()
    upper = hl2 + (multiplier * atr)
    lower = hl2 - (multiplier * atr)
    # Simple logic
    df['st_dir'] = 1
    df.loc[df['close'] < lower, 'st_dir'] = -1
    return df

def get_vwap(df):
    df['vwap'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
    return df

# ========== DELTA FUNCTIONS ==========
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})

def get_btc_data():
    # Delta se BTCUSD 5min candle lega signal ke liye
    url = "https://api.delta.exchange/v2/history/candles"
    params = {"resolution": "5", "symbol": "BTCUSD", "start": int((datetime.now() - timedelta(days=1)).timestamp())}
    r = requests.get(url, params=params).json()
    df = pd.DataFrame(r['result'])
    df.columns = ['time','open','high','low','close','volume']
    df['close'] = df['close'].astype(float)
    return df

def place_option_order(strike_type="CALL"):
    # Yahan Next Day Expiry wala contract auto find karega
    # Demo order logic
    send_telegram(f"🚀 SIGNAL MILA - {strike_type} SELL\nStrike: Auto Next Day\nLeverage: {LEVERAGE}x Isolated\nTime: {datetime.now()}")
    print("ORDER PLACED")

# ========== MAIN LOOP ==========
send_telegram(f"🚀 BOT RESTARTED\nLeverage: {LEVERAGE}x Isolated\nStrategy: RSI+ST+VWAP+TrendMagic\nFilter: Next Day Expiry")

while True:
    try:
        df = get_btc_data()
        df['rsi'] = get_rsi(df['close'])
        df = get_supertrend(df)
        df = get_vwap(df)
        
        last = df.iloc[-1]
        print(f"Checking... RSI:{last['rsi']:.2f} | Close:{last['close']} | VWAP:{last['vwap']:.2f} | ST:{last['st_dir']}")

        # SELL CALL CONDITION
        if last['rsi'] > 65 and last['close'] < last['vwap'] and last['st_dir'] == -1:
            place_option_order("CALL")
            time.sleep(300) # 5 min rukega ek order ke baad

        # SELL PUT CONDITION
        if last['rsi'] < 35 and last['close'] > last['vwap'] and last['st_dir'] == 1:
            place_option_order("PUT")
            time.sleep(300)

        time.sleep(60)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(10)
