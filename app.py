import os
import time
import threading
from datetime import datetime
import requests
from flask import Flask

app = Flask(__name__)

# Telegram Credentials
TOKEN = "8001955184:AAFJ4NbmFHwVhpWB9LETM_K1ESdRWS8YDd8"
CHAT_ID = "5292908963"

# The Odds API Key
ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")

# Aapke pasandida bookmakers ki mapping
ALLOWED_BOOKMAKERS = {
    "pinnacle": {"name": "Pinnacle", "domain": "pinnacle.com"},
    "onexbet": {"name": "1xBet", "domain": "1xbet.com"},
    "dafabet": {"name": "Dafabet", "domain": "dafabet.com"},
    "mostbet": {"name": "Mostbet", "domain": "mostbet.com"},
    "stake": {"name": "Stake", "domain": "stake.com"},
    "parimatch": {"name": "Parimatch", "domain": "parimatch.com"},
    "melbet": {"name": "Melbet", "domain": "melbet.com"}
}

# Scan karne ke liye sports (Football, Tennis, Basketball, Cricket etc.)
SPORTS_TO_SCAN = [
    {"key": "soccer_epl", "name": "Football", "league": "English Premier League"},
    {"key": "soccer_spain_la_liga", "name": "Football", "league": "Spain. La Liga"},
    {"key": "tennis_atp_aus_open", "name": "Tennis", "league": "ATP Masters"},
    {"key": "basketball_nba", "name": "Basketball", "league": "NBA"},
    {"key": "cricket_ipl", "name": "Cricket", "league": "IPL / T20"}
]

# Duplicate alerts rokne ke liye set
sent_alerts = set()

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Telegram Error: {e}")

def get_real_matches_from_api():
    if not ODDS_API_KEY:
        print("ODDS_API_KEY missing hai!")
        return []

    all_opportunities = []

    # Hum yahan h2h (Match Winner), spreads (Handicap), aur totals (Over/Under) teeno markets fetch karenge
    markets_str = "h2h,spreads,totals"

    for sport in SPORTS_TO_SCAN:
        sport_key = sport["key"]
        sport_name = sport["name"]
        league_name = sport["league"]

        url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={ODDS_API_KEY}&regions=eu,uk&markets={markets_str}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                api_data = response.json()
                
                for item in api_data:
                    match_id = item.get("id")
                    home_team = item.get("home_team")
                    away_team = item.get("away_team")
                    commence_time = item.get("commence_time")
                    
                    # Har bookmaker ke liye markets ka data collect karenge
                    bookmakers_markets = {} # Format: {bookie_name: {market_key_subtype: {data}}}
                    
                    for bookie in item.get("bookmakers", []):
                        b_key = bookie.get("key")
                        if b_key in ALLOWED_BOOKMAKERS:
                            b_info = ALLOWED_BOOKMAKERS[b_key]
                            b_title = b_info["name"]
                            b_domain = b_info["domain"]
                            
                            for m in bookie.get("markets", []):
                                m_key = m.get("key")
                                outcomes = m.get("outcomes", [])
                                
                                # 1. H2H Market (2-Way only to avoid Draw error)
                                if m_key == "h2h" and len(outcomes) == 2:
                                    b_outcomes = {}
                                    for outcome in outcomes:
                                        name = outcome.get("name")
                                        price = outcome.get("price")
                                        if name == home_team:
                                            b_outcomes["home"] = {"odds": price, "desc": f"Home ({home_team})"}
                                        elif name == away_team:
                                            b_outcomes["away"] = {"odds": price, "desc": f"Away ({away_team})"}
                                    
                                    if "home" in b_outcomes and "away" in b_outcomes:
                                        market_id = "Match Winner (H2H)"
                                        if market_id not in bookmakers_markets:
                                            bookmakers_markets[market_id] = {}
                                        bookmakers_markets[market_id][b_title] = {
                                            "bet1_odds": b_outcomes["home"]["odds"],
                                            "bet1_desc": b_outcomes["home"]["desc"],
                                            "bet2_odds": b_outcomes["away"]["odds"],
                                            "bet2_desc": b_outcomes["away"]["desc"],
                                            "link": f"https://www.{b_domain}"
                                        }

                                # 2. Spreads (Handicap) Market
                                elif m_key == "spreads" and len(outcomes) == 2:
                                    # Spreads mein point bhi hota hai (jaise -1.5 ya +1.5)
                                    o1, o2 = outcomes[0], outcomes[1]
                                    # Dono ka point same hona chahiye valid comparison ke liye
                                    if o1.get("point") == -o2.get("point") or o1.get("point") == o2.get("point"):
                                        p1, p2 = o1.get("point"), o2.get("point")
                                        market_id = f"Handicap ({o1.get('name')} {p1})"
                                        
                                        if b_title not in bookmakers_markets.get(market_id, {}):
                                            if market_id not in bookmakers_markets:
                                                bookmakers_markets[market_id] = {}
                                            
                                            bookmakers_markets[market_id][b_title] = {
                                                "bet1_odds": o1.get("price"),
                                                "bet1_desc": f"{o1.get('name')} (Handicap {p1})",
                                                "bet2_odds": o2.get("price"),
                                                "bet2_desc": f"{o2.get('name')} (Handicap {p2})",
                                                "link": f"https://www.{b_domain}"
                                            }

                                # 3. Totals (Over/Under) Market
                                elif m_key == "totals" and len(outcomes) == 2:
                                    o1, o2 = outcomes[0], outcomes[1] # Over aur Under
                                    point = o1.get("point")
                                    market_id = f"Totals Over/Under ({point})"
                                    
                                    if market_id not in bookmakers_markets:
                                        bookmakers_markets[market_id] = {}
                                        
                                    over_item = next((o for o in outcomes if o.get("name") == "Over"), None)
                                    under_item = next((o for o in outcomes if o.get("name") == "Under"), None)
                                    
                                    if over_item and under_item:
                                        bookmakers_markets[market_id][b_title] = {
                                            "bet1_odds": over_item.get("price"),
                                            "bet1_desc": f"Over {point}",
                                            "bet2_odds": under_item.get("price"),
                                            "bet2_desc": f"Under {point}",
                                            "link": f"https://www.{b_domain}"
                                        }

                    # Har market ke liye surebet check karna
                    for market_type, bookies_dict in bookmakers_markets.items():
                        b_names = list(bookies_dict.keys())
                        if len(b_names) >= 2:
                            for i in range(len(b_names)):
                                for j in range(len(b_names)):
                                    if i == j:
                                        continue
                                    
                                    b1, b2 = b_names[i], b_names[j]
                                    data1 = bookies_dict[b1]
                                    data2 = bookies_dict[b2]
                                    
                                    # Bet 1 (e.g. Home/Over) aur Bet 2 (e.g. Away/Under)
                                    odds1 = data1["bet1_odds"]
                                    odds2 = data2["bet2_odds"]
                                    
                                    if not odds1 or not odds2:
                                        continue
                                        
                                    implied_prob = (1 / odds1) + (1 / odds2)
                                    
                                    if implied_prob < 1.0:
                                        profit_percentage = ((1 / implied_prob) - 1) * 100
                                        total_budget = 100.0
                                        stake1 = (total_budget / (odds1 * implied_prob))
                                        stake2 = (total_budget / (odds2 * implied_prob))
                                        
                                        unique_alert_key = f"{match_id}_{market_type}_{b1}_{b2}"
                                        
                                        all_opportunities.append({
                                            "alert_key": unique_alert_key,
                                            "match_status": "🟢 LIVE / UPCOMING",
                                            "match": f"{home_team} - {away_team}",
                                            "sport": sport_name,
                                            "league": league_name,
                                            "start_time": commence_time,
                                            "market_type": market_type,
                                            "b1_name": b1,
                                            "b1_bet": data1["bet1_desc"],
                                            "b1_odds": odds1,
                                            "b1_stake": stake1,
                                            "b1_link": data1["link"],
                                            "b2_name": b2,
                                            "b2_bet": data2["bet2_desc"],
                                            "b2_odds": odds2,
                                            "b2_stake": stake2,
                                            "b2_link": data2["link"],
                                            "profit": profit_percentage
                                        })
        except Exception as e:
            print(f"Error fetching data for {sport_key}: {e}")

    return all_opportunities

def surebot_scanner_loop():
    print("Multi-Market Surebet Bot started (H2H, Handicaps, Totals)...")
    send_telegram_alert("🚀 *Multi-Market Surebet Bot* active ho gaya hai! (Match Winner, Handicaps & Totals saare markets included)")
    
    while True:
        try:
            opportunities = get_real_matches_from_api()
            
            for opp in opportunities:
                alert_key = opp["alert_key"]
                
                if alert_key in sent_alerts:
                    continue
                    
                message = (
                    f"💰 **New {opp['market_type']} Surebet!** ({opp['match_status']})\n"
                    f"**Sport:** {opp['sport']} | {opp['league']}\n"
                    f"**Event:** {opp['match']}\n"
                    f"**Profit:** {opp['profit']:.2f}%\n"
                    f"**Time:** {opp['start_time']}\n\n"
                    f"🔹 **{opp['b1_name']}**:\n"
                    f"▫️ {opp['b1_bet']} -> {opp['b1_odds']}\n"
                    f"💵 **Stake:** {opp['b1_stake']:.1f} €\n"
                    f"🔗 [Direct Match Entry]({opp['b1_link']})\n\n"
                    f"🔹 **{opp['b2_name']}**:\n"
                    f"▫️ {opp['b2_bet']} -> {opp['b2_odds']}\n"
                    f"💵 **Stake:** {opp['b2_stake']:.1f} €\n"
                    f"🔗 [Direct Match Entry]({opp['b2_link']})"
                )
                
                send_telegram_alert(message)
                sent_alerts.add(alert_key)
                print(f"Alert sent for {opp['match']} - Profit: {opp['profit']:.2f}%")
                
        except Exception as e:
            print(f"Error in scanner loop: {e}")
            
        time.sleep(60)

@app.route('/')
def home():
    return "Multi-Market Surebet Bot is running 24/7 on Render!"

if __name__ == '__main__':
    t = threading.Thread(target=surebot_scanner_loop)
    t.daemon = True
    t.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
                                        
