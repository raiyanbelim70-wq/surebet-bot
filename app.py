import os
import time
import threading
import requests
from flask import Flask

app = Flask(__name__)

API_KEY = "1f05a6b3d359e7a23fdca322cb0f3007"
TARGET_BOOKMAKERS = ["1xbet", "parimatch", "pinnacle", "stake"]

# Naya Revoked Telegram Bot Token aur Chat ID
TELEGRAM_BOT_TOKEN = "8001955184:AAFKUnk0mrCkkdtHTk3c1g-SMzaXjgAdVMY"
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
        print(f"Telegram Response Status: {response.status_code}")
    except Exception as e:
        print(f"Telegram Error: {e}")

def check_market_arbitrage(outcomes, market_name, match_title, sport_key):
    """Generic function to find arbitrage across any 2-way or multi-way outcomes"""
    if len(outcomes) < 2:
        return
        
    # Simple 2-outcome market check (jaise H2H ya Over/Under)
    best_outcomes = {}
    for outcome in outcomes:
        name = outcome.get('name')
        price = outcome.get('price', 0)
        point = outcome.get('point', '') # Handicaps ya Totals ke liye point (jaise Over 2.5)
        
        key = f"{name}_{point}"
        if key not in best_outcomes or price > best_outcomes[key]['price']:
            best_outcomes[key] = {'price': price, 'bookmaker': outcome.get('bookmaker', '')}

    # Agar 2 ya zyada outcomes hain toh arb check karo
    if len(best_outcomes) >= 2:
        prices = [v['price'] for v in best_outcomes.values()]
        implied_prob = sum(1/p for p in prices if p > 0)
        
        if implied_prob > 0 and implied_prob < 1:
            profit_margin = (1 - implied_probability) * 100 if 'implied_probability' in locals() else (1 - implied_prob) * 100
            
            # Format alert message
            details = "\n".join([f"👉 *{k}:* `{v['price']}`" for k, v in best_outcomes.items()])
            alert_msg = (
                f"🔥 *SUREBET FOUND! ({market_name.upper()})* 🔥\n\n"
                f"🏆 *Sport:* {sport_key.upper()}\n"
                f"⚔️ *Match:* {match_title}\n"
                f"💰 *Profit:* `{profit_margin:.2f}%`\n\n"
                f"{details}"
            )
            print(alert_msg)
            send_telegram_alert(alert_msg)

def scan_all_sports():
    print("Background high-speed scanner started...")
    time.sleep(5)
    send_telegram_alert("🚀 *Surebet Scanner Bot is Live & Scanning!* (1xBet, Parimatch, Pinnacle, Stake - All Markets)")
    
    while True:
        print("\n--- Starting Full Speed Multi-Sport & Multi-Market Scan ---")
        try:
            sports_url = "https://api.the-odds-api.com/v4/sports/"
            sports_response = requests.get(sports_url, params={'api_key': API_KEY}, timeout=15)
            
            if sports_response.status_code == 200:
                sports_data = sports_response.json()
                active_sports = [s['key'] for s in sports_data if s.get('active', False)]
                print(f"Total Active Sports Found: {len(active_sports)}")
                
                # Sabhi major markets target kar rahe hain: H2H, Spreads (Handicap), Totals (Over/Under)
                markets_to_scan = "h2h,spreads,totals"
                
                for sport_key in active_sports:
                    odds_url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
                    params = {
                        'api_key': API_KEY,
                        'regions': 'eu,us',
                        'markets': markets_to_scan,
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
                                
                                # Market wise data collect karna
                                market_outcomes_map = {'h2h': {}, 'spreads': {}, 'totals': {}}
                                
                                for bm in bookmakers_data:
                                    bm_key = bm['key']
                                    if bm_key in TARGET_BOOKMAKERS:
                                        for m in bm.get('markets', []):
                                            m_key = m['key']
                                            if m_key in market_outcomes_map:
                                                for outcome in m.get('outcomes', []):
                                                    outcome['bookmaker'] = bm_key
                                                    # Grouping by point if totals/spreads exist
                                                    market_outcomes_map[m_key].setdefault(str(outcome.get('point', '')), []).append(outcome)

                                # Check arbitrage for each market type
                                for market_type, points_dict in market_outcomes_map.items():
                                    for point_val, outcomes_list in points_dict.items():
                                        # Group by bookmaker to find best odds across bookies
                                        bm_best = {}
                                        for out in outcomes_list:
                                            bm = out['bookmaker']
                                            # Simple check for multi-bookmaker availability
                                            pass
                                                
                                        # Fast arbitrage calculation across target bookmakers
                                        if len(outcomes_list) >= 2:
                                            check_market_arbitrage(outcomes_list, market_type, match_title, sport_key)
                                            
                        time.sleep(0.3)
                    except Exception:
                        continue
            else:
                print(f"Error fetching sports list: {sports_response.status_code}")
                
        except Exception as e:
            print(f"Scanner Error: {e}")
            
        print("--- Scan Cycle Completed. Restarting in 30 seconds ---")
        time.sleep(30)

scanner_thread = threading.Thread(target=scan_all_sports, daemon=True)
scanner_thread.start()

@app.route('/')
def home():
    return "🚀 High-Speed Multi-Market Surebet Scanner is Live and Running!"

@app.route('/test-telegram')
def test_telegram():
    send_telegram_alert("🧪 *Test Alert:* New Token is working perfectly with all markets!")
    return "Test message sent to Telegram!"
    
