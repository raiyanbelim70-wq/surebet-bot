import os
import time
import threading
from flask import Flask
from curl_cffi import requests as curl_requests
import requests
from difflib import get_close_matches

app = Flask(__name__)

PROXY_URL = os.getenv("PROXY_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if PROXY_URL:
    PROXY_URL = PROXY_URL.strip().strip('"').strip("'")

proxies_dict = {
    "http": PROXY_URL,
    "https": PROXY_URL
} if PROXY_URL else {}

sent_alerts_cache = set()

def send_telegram_alert(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram tokens missing!", flush=True)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=8)
        if response.status_code != 200:
            print(f"Telegram error response: {response.text}", flush=True)
    except Exception as e:
        print(f"Telegram connection error: {e}", flush=True)

def calculate_arbitrage(odds1, odds2):
    if odds1 <= 0 or odds2 <= 0:
        return False, 0.0
    implied_probability = (1.0 / odds1) + (1.0 / odds2)
    if implied_probability < 1.0:
        profit_percentage = round((1.0 - implied_probability) * 100, 2)
        return True, profit_percentage
    return False, 0.0

def fetch_pinnacle_odds(session):
    try:
        # Pinnacle public guest feed endpoint
        url = "https://guest.api.pinnacle.com/0.1/sports/29/markets/straight"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }
        resp = session.get(url, headers=headers, proxies=proxies_dict, impersonate="chrome110", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"Pinnacle fetch error: {e}", flush=True)
    return {}

def fetch_1xbet_odds(session):
    try:
        # 1xBet live feed endpoint structure for soccer/major sports
        url = "https://1xbet.moe/service-api/LiveFeed/GetChampZip?lng=en&id=1"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            "Referer": "https://1xbet.com/"
        }
        resp = session.get(url, headers=headers, proxies=proxies_dict, impersonate="chrome110", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"1xBet fetch error: {e}", flush=True)
    return {}

def parse_pinnacle(data):
    parsed = {}
    try:
        events = data.get('events', [])
        for ev in events:
            match_name = f"{ev.get('home')} vs {ev.get('away')}"
            periods = ev.get('periods', [])
            for p in periods:
                if p.get('number') == 0:  # Full time match
                    ml = p.get('moneyline', {})
                    home_price = ml.get('home')
                    away_price = ml.get('away')
                    if home_price and away_price:
                        parsed[match_name.lower()] = {
                            'home': home_price,
                            'away': away_price,
                            'raw_title': match_name
                        }
    except Exception as e:
        print(f"Error parsing Pinnacle data: {e}", flush=True)
    return parsed

def parse_1xbet(data):
    parsed = {}
    try:
        value_list = data.get('Value', [])
        if isinstance(value_list, list):
            games = value_list
        else:
            games = data.get('Value', {}).get('G', [])
            
        for game in games:
            home = game.get('O1')
            away = game.get('O2')
            if home and away:
                match_name = f"{home} vs {away}"
                # Extracting 1X2 odds or moneyline structure from 1xBet block
                odds_events = game.get('E', [])
                if len(odds_events) >= 2:
                    # Taking home and away decimal odds roughly
                    home_price = float(odds_events[0].get('V', 0))
                    away_price = float(odds_events[1].get('V', 0))
                    if home_price > 1 and away_price > 1:
                        parsed[match_name.lower()] = {
                            'home': home_price,
                            'away': away_price,
                            'raw_title': match_name
                        }
    except Exception as e:
        print(f"Error parsing 1xBet data: {e}", flush=True)
    return parsed

def scan_direct_markets():
    print("-> Direct scraper & matching cycle started...", flush=True)
    try:
        session = curl_requests.Session()
        
        pin_raw = fetch_pinnacle_odds(session)
        xbet_raw = fetch_1xbet_odds(session)
        
        pin_markets = parse_pinnacle(pin_raw)
        xbet_markets = parse_1xbet(xbet_raw)
        
        print(f"Parsed {len(pin_markets)} Pinnacle matches and {len(xbet_markets)} 1xBet matches.", flush=True)
        
        # Match mapping using fuzzy matching
        pin_keys = list(pin_markets.keys())
        for xbet_key, xbet_val in xbet_markets.items():
            matches = get_close_matches(xbet_key, pin_keys, n=1, cutoff=0.6)
            if matches:
                matched_pin_key = matches[0]
                pin_val = pin_markets[matched_pin_key]
                
                # Check Arbitrage between Home(1xBet) vs Away(Pinnacle) and vice versa
                # Option 1: Back Home on 1xBet, Away on Pinnacle
                is_arb1, profit1 = calculate_arbitrage(xbet_val['home'], pin_val['away'])
                alert_key1 = f"{xbet_val['raw_title']}_arb1"
                
                if is_arb1 and alert_key1 not in sent_alerts_cache:
                    sent_alerts_cache.add(alert_key1)
                    msg = (
                        f"🔥 *REAL SUREBET FOUND!* 🔥\n\n"
                        f"⚔️ *Match:* {xbet_val['raw_title']}\n"
                        f"💰 *Profit Margin:* `+{profit1}%`\n"
                        f"▫️ *1xBet (Home):* `{xbet_val['home']}`\n"
                        f"▫️ *Pinnacle (Away):* `{pin_val['away']}`\n\n"
                        f"⚡ *Source: Direct Scraper + ISP Proxy*"
                    )
                    send_telegram_alert(msg)
                
                # Option 2: Back Away on 1xBet, Home on Pinnacle
                is_arb2, profit2 = calculate_arbitrage(xbet_val['away'], pin_val['home'])
                alert_key2 = f"{xbet_val['raw_title']}_arb2"
                
                if is_arb2 and alert_key2 not in sent_alerts_cache:
                    sent_alerts_cache.add(alert_key2)
                    msg = (
                        f"🔥 *REAL SUREBET FOUND!* 🔥\n\n"
                        f"⚔️ *Match:* {xbet_val['raw_title']}\n"
                        f"💰 *Profit Margin:* `+{profit2}%`\n"
                        f"▫️ *1xBet (Away):* `{xbet_val['away']}`\n"
                        f"▫️ *Pinnacle (Home):* `{pin_val['home']}`\n\n"
                        f"⚡ *Source: Direct Scraper + ISP Proxy*"
                    )
                    send_telegram_alert(msg)

    except Exception as e:
        print(f"Error in direct scraping & matching cycle: {e}", flush=True)

def background_scanner():
    print("Direct Scraper Background Thread Initialized!", flush=True)
    time.sleep(2)
    send_telegram_alert("🚀 *Direct 1xBet & Pinnacle Arbitrage Scanner is Active!*")
    
    while True:
        try:
            scan_direct_markets()
        except Exception as e:
            print(f"Scanner loop error: {e}", flush=True)
        time.sleep(30)

@app.route("/")
def home():
    return "Direct 1xBet & Pinnacle Match-Mapping Scraper is Active!"

if __name__ == "__main__":
    scanner_thread = threading.Thread(target=background_scanner)
    scanner_thread.daemon = True
    scanner_thread.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
    
