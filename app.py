import os
import time
import threading
from flask import Flask
import requests
from curl_cffi import requests as cffi_requests

app = Flask(__name__)

PROXY_URL = os.getenv("PROXY_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

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

def fetch_and_scan_odds():
    try:
        print("Scanning markets via Bright Data ISP Proxy + curl_cffi...")
        
        # 1xBet API / Endpoint request
        # resp_1xbet = cffi_requests.get("YOUR_1XBET_ENDPOINT", proxies=proxies, impersonate="chrome", timeout=10)
        
        # Pinnacle API / Endpoint request
        # resp_pinnacle = cffi_requests.get("YOUR_PINNACLE_ENDPOINT", proxies=proxies, impersonate="chrome", timeout=10)
        
        # TODO: Yahan JSON parse karke Total, Handicap aur O/U ke odds nikalenge
        # Arbitrage formula: (1 / Odds_1xBet) + (1 / Odds_Pinnacle) < 1
        
        surebet_found = False  # Jab profit > 0 hoga tab ye True hoga
        
        if surebet_found:
            alert_text = (
                "🚨 **SureBet Found!** 🚨\n\n"
                "⚽ **Match:** Team A vs Team B\n"
                "📊 **Market:** Total / Handicap / O/U\n"
                "🔥 **1xBet vs Pinnacle**\n"
                "💰 **Profit:** +2.3%\n"
                "⚡ *Secured via ISP Proxy & TLS Bypass*"
            )
            send_telegram_alert(alert_text)
            
    except Exception as e:
        print(f"Error during odds fetching: {e}")

def background_scanner():
    print("Arbitrage Scanner Background Loop Started!")
    send_telegram_alert(
        "🚀 **Arbitrage Scanner Fully Active!**\n\n"
        "🔥 ISP Proxy & TLS Fingerprint Connected.\n"
        "🎯 Ready for Live Market Data Processing..."
    )
    
    while True:
        try:
            fetch_and_scan_odds()
            time.sleep(10)  # Scan interval
        except Exception as e:
            print(f"Scanner loop error: {e}")
            time.sleep(10)

@app.route("/")
def home():
    return "Arbitrage Scanner Bot is Live and Ready for Data Parsing!"

if __name__ == "__main__":
    scanner_thread = threading.Thread(target=background_scanner)
    scanner_thread.daemon = True
    scanner_thread.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
    
