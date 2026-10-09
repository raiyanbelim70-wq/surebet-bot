import os
import time
import threading
from flask import Flask
from curl_cffi import requests as curl_requests
import requests

app = Flask(__name__)

API_KEY = os.getenv("API_KEY", "1f05a6b3d359e7a23fdca322cb0f3007")
PROXY_URL = os.getenv("PROXY_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

proxies_dict = {
    "http": PROXY_URL,
    "https": PROXY_URL
}

# India-accessible bookmakers target list
TARGET_BOOKMAKERS = ["1xbet", "parimatch", "pinnacle", "stake"]
sent_alerts_cache = set()

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
        response = requests.post(url, json=payload, timeout=8)
        if response.status_code != 200:
            print(f"Telegram error response: {response.text}")
    except Exception as e:
        print(f"Telegram connection error: {e}")

def calculate_arbitrage(outcomes_dict):
    prices = [v['price'] for v in outcomes_dict.values()]
    if len(prices) < 2:
        return False, 0.0
    
    implied_probability = sum(1.0 / p for p in prices if p > 0)
    if implied_probability < 1.0:
        profit_percentage = round((1.0 - implied_probability) * 100, 2)
        return True, profit_percentage
    return False, 0.0

def fetch_and_scan_live_markets():
    try:
        session = curl_requests.Session()
        
        # Fetch active sports list
        sports_url = "https://api.the-odds-api.com/v4/sports/"
        params = {'api_key': API_KEY}
        
        resp = session.get(sports_url, params=params, proxies=proxies_dict, impersonate="chrome110", timeout=12)
        if resp.status_code != 200:
            print(f"Failed to fetch sports list: {resp.status_code}")
            return
            
        sports_data = resp.json()
        active_sports = [s['key'] for s in sports_data if s.get('active', False)]
        print(f"Scanning {len(active_sports)} active sports across India-friendly bookmakers...")
        
        for sport_key in active_sports:
            odds_url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
            odds_params = {
                'api_key': API_KEY,
                'regions': 'uk,us,eu,au',
                'markets': 'h2h,spreads,totals',
                'oddsFormat': 'decimal',
                'bookmakers': ','.join(TARGET_BOOKMAKERS)
            }
            
            odds_resp = session.get(odds_url, params=odds_params, proxies=proxies_dict, impersonate="chrome110", timeout=10)
            if odds_resp.status_code == 200:
                matches = odds_resp.json()
                for match in matches:
                    match_id = match.get('id')
                    match_title = f"{match.get('home_team')} vs {match.get('away_team')}"
                    commence_time = match.get('commence_time', 'Live/Upcoming')
                    bookmakers_data = match.get('bookmakers', [])
                    
                    market_outcomes_map = {'h2h': {}, 'spreads': {}, 'totals': {}}
                    
                    for bm in bookmakers_data:
                        bm_key = bm['key']
                        if bm_key in TARGET_BOOKMAKERS:
                            for m in bm.get('markets', []):
                                m_key = m['key']
                                if m_key in market_outcomes_map:
                                    for outcome in m.get('outcomes', []):
                                        name = outcome.get('name')
                                        price = outcome.get('price', 0)
                                        point = outcome.get('point', '')
                                        outcome_key = f"{name}_{point}"
                                        
                                        if outcome_key not in market_outcomes_map[m_key] or price > market_outcomes_map[m_key][outcome_key]['price']:
                                            market_outcomes_map[m_key][outcome_key] = {
                                                'price': price,
                                                'bookmaker': bm_key,
                                                'point': point,
                                                'name': name
                                            }

                    for market_name, outcomes_dict in market_outcomes_map.items():
                        if len(outcomes_dict) >= 2:
                            is_arb, profit = calculate_arbitrage(outcomes_dict)
                            unique_alert_key = f"{match_id}_{market_name}"
                            
                            if is_arb and unique_alert_key not in sent_alerts_cache:
                                sent_alerts_cache.add(unique_alert_key)
                                
                                total_investment = 100.0
                                prices_list = [v['price'] for v in outcomes_dict.values()]
                                implied_prob_sum = sum(1.0 / p for p in prices_list)
                                
                                details_str = ""
                                for k, v in outcomes_dict.items():
                                    stake = round((total_investment / v['price']) / implied_prob_sum, 2)
                                    details_str += f"▫️ *{v['bookmaker'].upper()}* -> {v['name']} (Line: {v['point']}) @ `{v['price']}` | Stake: `{stake}€`\n"
                                
                                alert_text = (
                                    f"🔥 *VERIFIED SUREBET FOUND!* 🔥\n\n"
                                    f"🏆 *Sport:* `{sport_key.upper()}`\n"
                                    f"⚔️ *Match:* {match_title}\n"
                                    f"📊 *Market:* `{market_name.upper()}`\n"
                                    f"⏰ *Time:* `{commence_time}`\n"
                                    f"💰 *Profit Margin:* `+{profit}%`\n\n"
                                    f"{details_str}\n"
                                    f"⚡ *Secured via ISP Proxy + curl_cffi*"
                                )
                                send_telegram_alert(alert_text)
                                
            time.sleep(0.3)
            
    except Exception as e:
        print(f"Error during live market scan: {e}")

def background_scanner():
    print("Production Live Arbitrage Background Loop Started!")
    time.sleep(2)
    send_telegram_alert("🚀 *Production SureBet Scanner is Live with Real API + Proxy!*")
    
    while True:
        try:
            fetch_and_scan_live_markets()
        except Exception as e:
            print(f"Scanner loop error: {e}")
        time.sleep(20)

@app.route("/")
def home():
    return "Production Real-Data SureBet Scanner Bot is Active!"

if __name__ == "__main__":
    scanner_thread = threading.Thread(target=background_scanner)
    scanner_thread.daemon = True
    scanner_thread.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
    
