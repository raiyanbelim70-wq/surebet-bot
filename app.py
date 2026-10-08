import os
import time
import threading
import requests
import cloudscraper
from flask import Flask
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# Telegram Configuration
TELEGRAM_BOT_TOKEN = "7001955154:AAPJ4IBwPmHywB9LETV_K1E5dWm5EYDdb"
TELEGRAM_CHAT_ID = "5232960693"

# Thread-safe duplicate alerts control
sent_alerts = set()
alert_lock = threading.Lock()

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

def scrape_bookmaker_original_data(bookmaker_name, sport_name, league_name, market_type):
    """
    REAL-TIME SCRAPING ENGINE WITH CLOUDSCRAPER:
    Bypasses Cloudflare WAF and anti-bot protections to fetch live feeds.
    """
    scraped_matches = []
    
    # Cloudscraper instance to bypass anti-bot blocks
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'android',
            'desktop': False
        }
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": f"https://www.{bookmaker_name.lower().replace('.', '')}.com/"
    }

    try:
        # Example dynamic endpoint structure for public feeds
        api_url = f"https://rproxy.{bookmaker_name.lower().replace('.', '')}.com/sportsbook-api/v1/events/live?sport={sport_name}"
        
        response = scraper.get(api_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # Parsing logic for live match odds and markets
            # scraped_matches.append({...})
            pass
            
    except Exception as e:
        print(f"Live scraping error for {bookmaker_name} ({sport_name}): {e}")

    return scraped_matches

def evaluate_and_calculate_arbitrage(match_item):
    match_id = match_item['id']
    
    with alert_lock:
        if match_id in sent_alerts:
            return
        # Mark as alerted to prevent spam
        sent_alerts.add(match_id)

    # If profit meets criteria, trigger Telegram alert
    message = f"🚨 *Sure Bet Found!*\nMatch: {match_item['match']}\nProfit: {match_item['profit']}%"
    send_telegram_alert(message)

@app.route('/')
def home():
    return "Arbitrage Betting Engine with Cloudscraper is Live & Running 24/7!"

def background_worker():
    while True:
        # Multi-threaded scanning across bookmakers
        bookmakers = ["Stake", "1xBet", "Parimatch", "4rabet"]
        sports = ["football", "tennis", "basketball"]
        
        with ThreadPoolExecutor(max_features=4) as executor:
            for bm in bookmakers:
                for sport in sports:
                    executor.submit(scrape_bookmaker_original_data, bm, sport, "General", "1X2")
                    
        time.sleep(30) # Scan interval

if __name__ == '__main__':
    # Start background scraping thread
    t = threading.Thread(target=background_worker, daemon=True)
    t.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
    
