from flask import Flask
import threading
import os
import time
import requests
from datetime import datetime

# --- Flask server for Render Port Fix ---
app = Flask(__name__)
@app.route('/')
def home():
    return "BTC-RSI-ST-VWAP-BOT is LIVE! 24/7 Running"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask, daemon=True).start()
# -----------------------------------------

# --- YOUR BOT CONFIG ---
DELTA_API_KEY = os.getenv("DELTA_API_KEY")
DELTA_API_SECRET = os.getenv("DELTA_API_SECRET")
LEVERAGE = 100
# Add your RSI+ST+VWAP logic below

print("RSI + SuperTrend + VWAP Bot Started...", flush=True)
print(f"Time: {datetime.now()}", flush=True)

# --- Example: Telegram notification ---
def send_telegram(msg):
    try:
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if token and chat_id:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            requests.post(url, data={"chat_id": chat_id, "text": msg})
    except Exception as e:
        print(f"Telegram error: {e}")

send_telegram("✅ BTC-RSI-ST-VWAP-BOT Deployed & Live on Render!")

# --- YOUR STRATEGY LOOP ---
# Yahan se teri purani strategy start hogi
# Main tera purana logic yahan chipka raha hu, tu apna original logic yahan paste kar dena agar ye alag lage

while True:
    try:
        print(f"[{datetime.now()}] Scanning BTC... RSI + ST + VWAP", flush=True)
        # TODO: Yahan apna RSI, SuperTrend, VWAP ka logic daal
        
        time.sleep(60) # har 1 min check
        
    except Exception as e:
        print(f"Error in loop: {e}", flush=True)
        time.sleep(10)
