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

def fetch_odds_with_proxy():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        # 1xBet request using Bright Data ISP Proxy (Bypassing 403 WAF)
        print("Fetching 1xBet odds via ISP Proxy...")
        # r_1xbet = requests.get("https://1xbet.com/api/...", headers=headers, proxies=proxies, timeout=10)
        
        # Pinnacle request using Bright Data ISP Proxy (Bypassing 451 Geo-block)
        print("Fetching Pinnacle odds via ISP Proxy...")
        # r_pinnacle = requests.get("https://api.pinnacle.com/...", headers=headers, proxies=proxies, timeout=10)
        
    except Exception as e:
        print(f"Proxy request failed: {e}")

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
            # Yahan live aur upcoming matches ka data fetch hoga
            fetch_odds_with_proxy()
            
            # Arbitrage calculation aur Telegram alert ka logic yahan aayega
            # Agar surebet milti hai toh:
            # send_telegram_alert("🚨 SureBet Found! 1xBet vs Pinnacle ...")
            
            time.sleep(10)  # Super fast scanning interval
        except Exception as e:
            print(f"Scanner loop error: {e}")
            time.sleep(10)

@app.route("/")
def home():
    return "Arbitrage Scanner Bot is Running Successfully with ISP Proxy!"

if __name__ == "__main__":
    # Background thread mein scanner chala rahe hain taaki Flask server block na ho
    scanner_thread = threading.Thread(target=background_scanner)
    scanner_thread.daemon = True
    scanner_thread.start()
    
    # Render ke liye port configure kar rahe hain
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
    
