import os
import time
import threading
import requests
from flask import Flask

app = Flask(__name__)

API_KEY = "1f05a6b3d359e7a23fdca322cb0f3007"
TARGET_BOOKMAKERS = ["1xbet", "parimatch", "pinnacle", "stake"]

# Telegram Bot Token aur Chat ID
TELEGRAM_BOT_TOKEN = "8001955184:AAH_k7XKzU6aJhg8MoAeECsra06SYqEJZFs"
TELEGRAM_CHAT_ID = "5292908963"

# Paid Proxy Configuration (IPRoyal)
PROXY_HOST = "geo.iproyal.com"
PROXY_PORT = "12321"
PROXY_USER = "HwySPyYCdCrpOQD9"
PROXY_PASS = "ayUXZQamc10E4blN"

PROXY_URL = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
PROXIES = {
    "http": PROXY_URL,
    "https": PROXY_URL
}

def send_telegram_alert(message):
    """Telegram par ultra-fast alert bhejne ka function"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload, proxies=PROXIES, timeout=8)
        print(f"Telegram Status: {response.status_code}")
    except Exception as e:
        print(f"Telegram Error: {e}")

def check_market_arbitrage(outcomes, market_name, match_title, sport_key, commence_time):
    if len(outcomes) < 2:
        return
        
    best_outcomes = {}
    for outcome in outcomes:
        name = outcome.get('name')
        price = outcome.get('price', 0)
        point = outcome.get('point', '')
        
        # Unique key for every outcome including point/handicap/total line
        key = f"{name}_{point}"
        if key not in best_outcomes or price > best_outcomes[key]['price']:
            best_outcomes[key] = {
                'price': price, 
                'bookmaker': outcome.get('bookmaker', ''),
                'point': point
            }

    if len(best_outcomes) >= 2:
        prices = [v['price'] for v in best_outcomes.values()]
        implied_prob = sum(1/p for p in prices if p > 0)
        
        if 0 < implied_prob < 1:
            profit_margin = (1 - implied_prob) * 100
            
            details = "\n".join([f"👉 *{k}* (Line: {v['point']}): `{v['price']}` [{v['bookmaker'].upper()}]" for k, v in best_outcomes.items()])
            alert_msg = (
                f"🔥 *REAL SUREBET FOUND!* 🔥\n\n"
                f"🏆 *Sport:* `{sport_key.upper()}`\n"
                f"⚔️ *Match:* {match_title}\n"
                f"📊 *Market:* `{market_name.upper()}`\n"
                f"⏰ *Time:* `{commence_time}`\n"
                f"💰 *Profit Margin:* `+{profit_margin:.2f}%`\n\n"
                f"{details}"
            )
            print(alert_msg)
            send_telegram_alert(alert_msg)

def scan_all_sports():
    print("Ultra-fast global proxy scanner background thread started...")
    time.sleep(2)
    send_telegram_alert("🚀 *Global High-Speed Surebet Bot is Live!* (Scanning H2H, Spreads, Totals across Live & Upcoming via Paid Proxy)")
    
    while True:
        print("\n--- Starting High-Speed Global Multi-Sport & Multi-Market Scan ---")
        try:
            sports_url = "https://api.the-odds-api.com/v4/sports/"
            sports_response = requests.get(sports_url, params={'api_key': API_KEY}, proxies=PROXIES, timeout=12)
            
            if sports_response.status_code == 200:
                sports_data = sports_response.json()
                active_sports = [s['key'] for s in sports_data if s.get('active', False)]
                print(f"Total Active Sports Loaded: {len(active_sports)}")
                
                # Covering all essential markets: Moneyline/H2H, Handicaps/Spreads, Totals (Over/Under)
                markets_to_scan = "h2h,spreads,totals"
                
                for sport_key in active_sports:
                    odds_url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
                    params = {
                        'api_key': API_KEY,
                        'regions': 'uk,us,eu,au',  # Global coverage to never miss any odds
                        'markets': markets_to_scan,
                        'oddsFormat': 'decimal',
                        'bookmakers': ','.join(TARGET_BOOKMAKERS)
                    }
                    
                    try:
                        odds_resp = requests.get(odds_url, params=params, proxies=PROXIES, timeout=8)
                        if odds_resp.status_code == 200:
                            matches = odds_resp.json()
                            for match in matches:
                                match_title = f"{match.get('home_team')} vs {match.get('away_team')}"
                                commence_time = match.get('commence_time', 'Live/Upcoming')
                                bookmakers_data = match.get('bookmakers', [])
                                
                                market_outcomes_map = {'h2h': [], 'spreads': [], 'totals': []}
                                
                                for bm in bookmakers_data:
                                    bm_key = bm['key']
                                    if bm_key in TARGET_BOOKMAKERS:
                                        for m in bm.get('markets', []):
                                            m_key = m['key']
                                            if m_key in market_outcomes_map:
                                                for outcome in m.get('outcomes', []):
                                                    outcome['bookmaker'] = bm_key
                                                    market_outcomes_map[m_key].append(outcome)

                                for market_type, outcomes_list in market_outcomes_map.items():
                                    if len(outcomes_list) >= 2:
                                        check_market_arbitrage(outcomes_list, market_type, match_title, sport_key, commence_time)
                                            
                        time.sleep(0.1) # Minimized delay for blazing-fast execution
                    except Exception:
                        continue
            else:
                print(f"Error fetching sports list: {sports_response.status_code}")
                
        except Exception as e:
            print(f"Scanner Global Error: {e}")
            
        print("--- Scan Cycle Finished. Re-running instantly ---")
        time.sleep(10) # Quick restart loop for zero missed opportunities

scanner_thread = threading.Thread(target=scan_all_sports, daemon=True)
scanner_thread.start()

@app.route('/')
def home():
    return "🚀 Global High-Speed Proxy Surebet Scanner is Fully Active and Scanning Live & Upcoming Markets!"

@app.route('/test-alert')
def test_alert():
    send_telegram_alert("🧪 *System Operational Check:* Global proxy and multi-market scanner running at peak performance.")
    return "Operational check message sent!"
    
