import os
import time
import threading
import requests
from flask import Flask

app = Flask(__name__)

API_KEY = "1f05a6b3d359e7a23fdca322cb0f3007"
TARGET_BOOKMAKERS = ["1xbet", "parimatch", "pinnacle", "stake"]

# Telegram Credentials
TELEGRAM_BOT_TOKEN = "8001955184:AAFs9js7ilyVYFsXMQuepSwBbXAQzZRMbw"
TELEGRAM_CHAT_ID = "5292908963"

def send_telegram_alert(message):
    """Telegram par alert bhejne ka function"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload, timeout=10)
        print(f"Telegram Response: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Telegram Error: {e}")

def calculate_surebet(odds_list):
    best_home_odd = 0
    best_away_odd = 0
    best_home_bm = ""
    best_away_bm = ""
    
    for bm, outcomes in odds_list.items():
        if len(outcomes) >= 2:
            home_odd = outcomes[0].get('price', 0)
            away_odd = outcomes[1].get('price', 0)
            
            if home_odd > best_home_odd:
                best_home_odd = home_odd
                best_home_bm = bm
            if away_odd > best_away_odd:
                best_away_odd = away_odd
                best_away_bm = bm

    if best_home_odd > 0 and best_away_odd > 0:
        implied_probability = (1 / best_home_odd) + (1 / best_away_odd)
        if implied_probability < 1:
            profit_margin = (1 - implied_probability) * 100
            return True, profit_margin, best_home_bm, best_home_odd, best_away_bm, best_away_odd
            
    return False, 0, "", 0, "", 0

def scan_all_sports():
    time.sleep(5)  # Thoda wait karte hain taaki server fully stable ho jaye
    send_telegram_alert("🚀 *Surebet Scanner Bot is Live & Scanning!* (1xBet, Parimatch, Pinnacle, Stake)")
    
    while True:
        print("\n--- Starting Full Speed Multi-Sport Scan ---")
        try:
            sports_url = "https://api.the-odds-api.com/v4/sports/"
            sports_response = requests.get(sports_url, params={'api_key': API_KEY}, timeout=15)
            
            if sports_response.status_code == 200:
                sports_data = sports_response.json()
                active_sports = [s['key'] for s in sports_data if s.get('active', False)]
                print(f"Total Active Sports Found: {len(active_sports)}")
                
                for sport_key in active_sports:
                    odds_url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
                    params = {
                        'api_key': API_KEY,
                        'regions': 'eu,us',
                        'markets': 'h2h',
                        'oddsFormat': 'decimal',
                        'bookmakers': ','.join(TARGET_BOOKMAKERS)
                    }
                    
                    try:
                        odds_resp = requests.get(odds_url, params=params, timeout=10)
                        if odds_resp.status_code == 200:
                            matches = odds_resp.json()
                            for match in matches:
                                match_title = f"{match.get('home_team')} vs {match.get('away_team')}"
                                bookmakers_data = match.get('bookmakers', [])
                                
                                odds_dict = {}
                                for bm in bookmakers_data:
                                    bm_key = bm['key']
                                    if bm_key in TARGET_BOOKMAKERS:
                                        for m in bm.get('markets', []):
                                            if m['key'] == 'h2h':
                                                odds_dict[bm_key] = m.get('outcomes', [])
                                                
                                if len(odds_dict) >= 2:
                                    is_sure, profit, bm1, odd1, bm2, odd2 = calculate_surebet(odds_dict)
                                    if is_sure:
                                        alert_msg = (
                                            f"🔥 *SUREBET FOUND!* 🔥\n\n"
                                            f"🏆 *Sport:* {sport_key.upper()}\n"
                                            f"⚔️ *Match:* {match_title}\n"
                                            f"💰 *Profit:* `{profit:.2f}%`\n\n"
                                            f"👉 *Bet 1:* {bm1.upper()} ({odd1})\n"
                                            f"👉 *Bet 2:* {bm2.upper()} ({odd2})"
                                        )
                                        print(alert_msg)
                                        send_telegram_alert(alert_msg)
                                        
                        time.sleep(0.5)
                    except Exception:
                        continue
            else:
                print(f"Error fetching sports list: {sports_response.status_code}")
                
        except Exception as e:
            print(f"Scanner Error: {e}")
            
        print("--- Scan Cycle Completed. Restarting in 60 seconds ---")
        time.sleep(60)

def start_background_scanner():
    thread = threading.Thread(target=scan_all_sports, daemon=True)
    thread.start()

start_background_scanner()

@app.route('/')
def home():
    return "🚀 Full-Speed Telegram Surebet Scanner is Live and Running!"

@app.route('/test-telegram')
def test_telegram():
    send_telegram_alert("🧪 *Test Alert:* Telegram integration is working perfectly!")
    return "Test message sent to Telegram!"
    
