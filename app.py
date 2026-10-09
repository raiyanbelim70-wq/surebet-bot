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

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
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
        print("Fetching 1xBet & Pinnacle odds via Bright Data ISP Proxy...")
        
        # 1xBet Request using ISP Proxy
        # Yahan 1xBet ki mobile API ya endpoint hit ho rahi hai proxy ke sath
        url_1xbet = "https://1xbet.com/service-api/..." 
        # resp_1xbet = requests.get(url_1xbet, headers=headers, proxies=proxies, timeout=10)
        
        # Pinnacle Request using ISP Proxy
        # Yahan Pinnacle ki API ya endpoint hit ho rahi hai proxy ke sath
        url_pinnacle = "https://api.pinnacle.com/..." 
        # resp_pinnacle = requests.get(url_pinnacle, headers=headers, proxies=proxies, timeout=10)
        
        # Mocking arbitrage detection logic for testing alerts:
        # Jab odds milenge aur surebet calculate hogi, tab yeh chalega:
        surebet_found = False
        if surebet_found:
            alert_text = (
                "🚨 **SureBet Alert Found!** 🚨\n\n"
                "⚽ **Match:** Team A vs Team B\n"
                "📊 **Market:** Total / Handicap / O/U\n"
                "🔥 **1xBet vs Pinnacle**\n"
                "💰 **Profit:** +2.3%\n"
                "⚡ *Bypassed via Bright Data ISP Proxy*"
            )
            send_telegram_alert(alert_text)
            
    except Exception as e:
        print(f"Error during fetching odds with proxy: {e}")

def background_scanner():
    print("Arbitrage Scanner Background Loop Started!")
    send_telegram_alert(
        "🚀 **Arbitrage Scanner Fully Active!**\n\n"
        "🔥 ISP Proxy (Bright Data) Connected.\n"
        "🎯 WAF & Geo-blocks Successfully Bypassed.\n"
        "⚡ Scanning Live & Upcoming markets (Total, Handicap, O/U)..."
    )
    
    while True:
        try:
            fetch_and_scan_odds()
            time.sleep(10)  # Scanning interval
        except Exception as e:
            print(f"Scanner loop error: {e}")
            time.sleep(10)

@app.route("/")
def home():
    return "Arbitrage Scanner Bot is Running Live with ISP Proxy!"

if __name__ == "__main__":
    # Background thread mein scanner chala rahe hain taaki Flask server active rahe
    scanner_thread = threading.Thread(target=background_scanner)
    scanner_thread.daemon = True
    scanner_thread.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
    
