import os
import time
import threading
import requests
from flask import Flask, request

app = Flask(__name__)

# Telegram Bot Configurations
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID")

# IPRoyal Proxy Integration
PROXY_HOST = "geo.iproyal.com"
PROXY_PORT = "12321"
PROXY_USER = "HwySPyYCdCrpOQD9"
PROXY_PASS = "ayUXZGame10E4bIN"

proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
proxies = {
    "http": proxy_url,
    "https": proxy_url,
}

# Data-Saving Manual Switch
BOT_RUNNING = False

SPORTS_LIST = ["Cricket", "Football", "Tennis", "Basketball", "Hockey"]
MARKET_TYPES = ["Match Odds", "Under/Over", "Total Goals/Runs", "Handicap"]

@app.route("/")
def home():
    return "Ultimate Multi-Sport Arbitrage Bot is Running via IPRoyal Proxy!"

@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    global BOT_RUNNING
    update = request.get_json()
    if update and "message" in update:
        text = update["message"].get("text", "")
        chat_id = update["message"]["chat"]["id"]

        if text == "/start":
            BOT_RUNNING = True
            send_telegram_msg(chat_id, "🚀 **Bot Started!** Scanning Cricket, Football, Tennis, Basketball, Hockey & all markets.")
        elif text == "/stop":
            BOT_RUNNING = False
            send_telegram_msg(chat_id, "🛑 **Bot Stopped!** Data consumption paused to save your proxy GB.")
    return "OK", 200

def send_telegram_msg(chat_id, text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=10
        )
    except Exception as e:
        print(f"Telegram Error: {e}")

# Background Scanner Thread
def background_scanner():
    global BOT_RUNNING
    while True:
        if BOT_RUNNING:
            try:
                for sport in SPORTS_LIST:
                    for market in MARKET_TYPES:
                        if not BOT_RUNNING:
                            break
                        
                        # Simulated Surebet detection
                        surebet_found = False 
                        if surebet_found:
                            status = "LIVE 🔴"
                            league = f"{sport} Elite Tour"
                            match_name = "Team Alpha vs Team Beta"
                            profit_margin = "3.8%"
                            link_bm1 = "https://www.example-bookmaker.com/match/1"
                            link_bm2 = "https://www.example-bookmaker.com/match/2"

                            alert_message = (
                                f"🔥 **SUREBET ALERT ({sport.upper()})** 🔥\n\n"
                                f"🏆 **League:** {league}\n"
                                f"⏱ **Status:** {status}\n"
                                f"📊 **Market:** {market}\n"
                                f"🆚 **Match:** {match_name}\n\n"
                                f"💰 **Profit:** +{profit_margin}\n\n"
                                f"👉 **Direct Bet Links:**\n"
                                f"• [Open Bookmaker 1]({link_bm1})\n"
                                f"• [Open Bookmaker 2]({link_bm2})"
                            )
                            send_telegram_msg(TELEGRAM_CHAT_ID, alert_message)
            except Exception as e:
                print(f"Scanning Error with Proxy: {e}")
        time.sleep(10)

if __name__ == "__main__":
    scanner_thread = threading.Thread(target=background_scanner, daemon=True)
    scanner_thread.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    
