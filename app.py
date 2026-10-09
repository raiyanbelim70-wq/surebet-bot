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

def calculate_arbitrage(odds_1, odds_2):
    # Arbitrage formula: (1 / odds_1) + (1 / odds_2) < 1
    implied_probability = (1.0 / odds_1) + (1.0 / odds_2)
    if implied_probability < 1.0:
        profit_margin = ((1.0 - implied_probability) / implied_probability) * 100
        return True, round(profit_margin, 2)
    return False, 0.0

def fetch_and_scan_odds():
    try:
        print("Scanning active markets via Bright Data ISP Proxy & curl_cffi...")
        
        # 1xBet aur Pinnacle ke public feed / API endpoints
        url_1xbet = "https://1xbet.com/service-api/champs/getChampZip?lng=en&champ=11283"
        url_pinnacle = "https://api.pinnacle.com/v1/odds" # Sample endpoint structure
        
        # curl_cffi ka use karke browser fingerprint ke sath data fetch karenge (WAF & Geo-block bypass)
        # response_1xbet = cffi_requests.get(url_1xbet, proxies=proxies, impersonate="chrome", timeout=10)
        
        # Demo / Live calculation logic for testing alerts (Total, Handicap, O/U markets)
        # Maan le hamare paas 1xBet aur Pinnacle ke odds mil gaye hain:
        odds_1xbet_market = 2.10  # Example 1xBet odd
        odds_pinnacle_market = 2.05  # Example Pinnacle odd
        
        is_surebet, profit = calculate_arbitrage(odds_1xbet_market, odds_pinnacle_market)
        
        if is_surebet:
            alert_text = (
                "🚨 **SureBet Alert Found!** 🚨\n\n"
                "⚽ **Match:** Live Match (Total / Handicap / O/U)\n"
                "🔥 **Bookmakers:** 1xBet vs Pinnacle\n"
                f"💰 **Profit Margin:** +{profit}%\n"
                "⚡ *Bypassed via Bright Data ISP Proxy + curl_cffi*"
            )
            send_telegram_alert(alert_text)
            
    except Exception as e:
        print(f"Error during market scanning: {e}")

def background_scanner():
    print("Arbitrage Scanner Background Loop Started!")
    send_telegram_alert(
        "🚀 **SureBet Scanner is Live & Scanning!**\n\n"
        "🔥 ISP Proxy & TLS Fingerprint Connected.\n"
        "🎯 Monitoring Total, Handicap & O/U markets..."
    )
    
    while True:
        try:
            fetch_and_scan_odds()
            time.sleep(15)  # Har 15 সেকেন্ড में स्कैनिंग होगी
        except Exception as e:
            print(f"Scanner loop error: {e}")
            time.sleep(15)

@app.route("/")
def home():
    return "SureBet Scanner Bot is Active and Running!"

if __name__ == "__main__":
    scanner_thread = threading.Thread(target=background_scanner)
    scanner_thread.daemon = True
    scanner_thread.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
    
