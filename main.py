from flask import Flask
import threading
import os
import time
import requests
from datetime import datetime, timedelta
import pytz

# --- Flask server for Render Port Fix ---
app = Flask(__name__)
@app.route('/')
def home():
    return "BTC-RSI-ST-VWAP-BOT is LIVE! 150x | Next Day Expiry | Premium>50"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask, daemon=True).start()
# -----------------------------------------

# --- BOT CONFIG - FINAL ---
DELTA_API_KEY = os.getenv("DELTA_API_KEY")
DELTA_API_SECRET = os.getenv("DELTA_API_SECRET")
LEVERAGE = 150  # 150x as per your demand
MIN_PREMIUM = 50  # 50 se neeche sell nahi hoga
SYMBOL = "BTCUSD"

ist = pytz.timezone('Asia/Kolkata')

print(f"Bot Started... LEVERAGE={LEVERAGE}x | MIN_PREMIUM={MIN_PREMIUM}", flush=True)

def send_telegram(msg):
    try:
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if token and chat_id:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            requests.post(url, data={"chat_id": chat_id, "text": msg})
    except Exception as e:
        print(f"Telegram error: {e}")

def get_next_day_expiry_str():
    now = datetime.now(ist)
    next_day = now + timedelta(days=1)
    # Delta format: 14SEP, 15SEP etc
    return next_day.strftime("%d%b").upper()

def get_premium(product_symbol):
    # Yahan tera Delta API se LTP lene ka logic ayega
    # Example: api.get_ticker(product_symbol)
    # Abhi ke liye dummy
    try:
        # return float(api_response['last_price'])
        return 0 # yahan real LTP ayega
    except:
        return 0

def place_sell_order(product_symbol, premium):
    print(f"SELL ORDER -> {product_symbol} | Premium={premium} | Leverage={LEVERAGE}x Isolated", flush=True)
    send_telegram(f"✅ SELL: {product_symbol}\nPremium: {premium}\nLeverage: {LEVERAGE}x\nExpiry: {get_next_day_expiry_str()}")
    # Yahan Delta pe order lagane ka code ayega
    # leverage set: set_leverage(product_id, 150, isolated=True)

# --- MAIN STRATEGY LOOP ---
send_telegram(f"🚀 Bot LIVE! {LEVERAGE}x | Next Day Expiry | Premium>{MIN_PREMIUM}")

while True:
    try:
        now_ist = datetime.now(ist)
        next_expiry = get_next_day_expiry_str()
        
        print(f"[{now_ist.strftime('%d-%m %H:%M:%S')}] Scanning... Next Expiry: {next_expiry} | Min Premium: {MIN_PREMIUM}", flush=True)

        # --- EXAMPLE: Maan le tere RSI+ST+VWAP se signal mila aur product select hua ---
        # selected_product = "BTC-14SEP24-65000-CE"  # ye Delta se ayega
        # premium = get_premium(selected_product)
        
        # --- 3 FILTERS ---
        # 1. Next Day Expiry Check
        # if next_expiry not in selected_product:
        #     print(f"Skip: Current day expiry hai, {next_expiry} chahiye", flush=True)
        #     time.sleep(60)
        #     continue
        
        # 2. Premium Check - 50 se kam ka nahi bechna
        # if premium < MIN_PREMIUM:
        #     print(f"Skip: Premium {premium} < {MIN_PREMIUM}, brokerage kha jayega", flush=True)
        #     time.sleep(60)
        #     continue

        # 3. Entry allowed
        # if rsi_signal and supertrend_signal and vwap_signal:
        #     place_sell_order(selected_product, premium)

        time.sleep(60)

    except Exception as e:
        print(f"Loop Error: {e}", flush=True)
        time.sleep(10)
