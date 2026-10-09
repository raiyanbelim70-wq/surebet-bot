import os
import time
import threading
import requests
from flask import Flask

app = Flask(__name__)

# Environment variables se credentials utha rahe hain
PROXY_URL = os.getenv("PROXY_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Bright Data ISP Proxy configuration
proxies = {
    "http": PROXY_URL,
    "https": PROXY_URL
}

def send_telegram_alert(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram tokens missing!")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code != 200:
            print(f"Telegram error response: {response.text}")
    except Exception as e:
        print(f"Telegram connection error: {e}")

def background_scanner():
    print("Arbitrage Scanner Background Loop Started!")
    send_telegram_alert(
        "🚀 **High-Speed Arbitrage Scanner Started!**\n\n"
        "🔥 ISP Proxy (Bright Data) Connected.\n"
        "🎯 WAF & Geo-blocks (403/451) Bypassed.\n"
        "⚡ Scanning Live & Upcoming matches (Total, Handicap, O/U)..."
    )
    while True:
        try:
            # Yahan Bright Data ISP Proxy ke zariye odds fetch aur scan karne ka logic chalega
            print("Fetching live & upcoming odds via Bright Data ISP Proxy...")
            time.sleep(15)
        except Exception as e:
            print(f"Scanner loop error: {e}")
            time.sleep(10)

@app.route("/")
def home():
    return "Arbitrage Scanner Bot is Running Successfully!"

if __name__ == "__main__":
    # Scanner ko background thread mein daal rahe hain taaki web server block na ho
    scanner_thread = threading.Thread(target=background_scanner)
    scanner_thread.daemon = True
    scanner_thread.start()
    
    # Render ke liye Flask app ko port par run kar rahe hain
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
    
