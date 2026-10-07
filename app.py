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

# The Odds API Key (Render environment variables se aayegi)
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

# Scan karne ke liye alag-alag sports ki list (The Odds API keys)
SPORTS_TO_SCAN = [
    {"key": "soccer_epl", "name": "Football", "league": "English Premier League"},
    {"key": "soccer_spain_la_liga", "name": "Football", "league": "Spain. La Liga"},
    {"key": "cricket_ipl", "name": "Cricket", "league": "Indian Premier League"},
    {"key": "cricket_international_t20", "name": "Cricket", "league": "International T20"},
    {"key": "tennis_atp_aus_open", "name": "Tennis", "league": "ATP Masters"},
    {"key": "basketball_nba", "name": "Basketball", "league": "NBA"},
    {"key": "icehockey_nhl", "name": "Ice Hockey", "league": "NHL"}
]

# Duplicate alerts ko rokne ke liye set
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
        print("ODDS_API_KEY missing hai! Render environment variables me key add karein.")
        return []

    all_matches = []

    for sport in SPORTS_TO_SCAN:
        sport_key = sport["key"]
        sport_name = sport["name"]
        league_name = sport["league"]

        url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={ODDS_API_KEY}&regions=eu,uk&markets=h2h"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                api_data = response.json()
                
                for item in api_data:
                    match_id = item.get("id")
                    home_team = item.get("home_team")
                    away_team = item.get("away_team")
                    commence_time = item.get("commence_time")
                    
                    bookmakers_dict = {}
                    for bookie in item.get("bookmakers", []):
                        b_key = bookie.get("key")
                        
                        if b_key in ALLOWED_BOOKMAKERS:
                            b_info = ALLOWED_BOOKMAKERS[b_key]
                            b_title = b_info["name"]
                            b_domain = b_info["domain"]
                            
                            markets = bookie.get("markets", [])
                            for m in markets:
                                if m.get("key") == "h2h":
                                    outcomes = m.get("outcomes", [])
                                    for outcome in outcomes:
                                        name = outcome.get("name")
                                        price = outcome.get("price")
                                        
                                        if name == home_team:
                                            bet_label = f"Home ({home_team})"
                                        elif name == away_team:
                                            bet_label = f"Away ({away_team})"
                                        else:
                                            bet_label = name
                                            
                                        bookmakers_dict[b_title] = {
                                            "odds": price,
                                            "bet": bet_label,
                                            "link": f"https://www.{b_domain}"
                                        }
                    
                    if len(bookmakers_dict) >= 2:
                        all_matches.append({
                            "id": match_id,
                            "match_status": "🟢 LIVE / UPCOMING",
                            "match": f"{home_team} - {away_team}",
                            "sport": sport_name,
                            "league": league_name,
                            "start_time": commence_time,
                            "market_type": "1X2 / Match Winner",
                            "bookmakers": bookmakers_dict
                        })
        except Exception as e:
            print(f"Error fetching odds for {sport_key}: {e}")

    return all_matches

def surebot_scanner_loop():
    print("Multi-Sport Universal Surebet Bot started with All Sports & Custom Bookmakers...")
    send_telegram_alert("🚀 *Universal Surebet Bot* ab Saare Sports aur Custom Bookmakers ke sath 24/7 live ho gaya hai!")
    
    while True:
        try:
            matches_to_check = get_real_matches_from_api()
            
            for item in matches_to_check:
                match_id = item["id"]
                
                if match_id in sent_alerts:
                    continue
                    
                match_status = item["match_status"]
                match_name = item["match"]
                sport = item["sport"]
                league = item["league"]
                start_time = item["start_time"]
                market_type = item["market_type"]
                bookmakers = item["bookmakers"]
                
                bookie_names = list(bookmakers.keys())
                
                for i in range(len(bookie_names)):
                    for j in range(i + 1, len(bookie_names)):
                        b1_name = bookie_names[i]
                        b2_name = bookie_names[j]
                        
                        b1_data = bookmakers[b1_name]
                        b2_data = bookmakers[b2_name]
                        
                        odds1 = b1_data["odds"]
                        odds2 = b2_data["odds"]
                        
                        implied_prob = (1 / odds1) + (1 / odds2)
                        
                        if implied_prob < 1.0:
                            profit_percentage = ((1 / implied_prob) - 1) * 100
                            
                            total_budget = 100.0
                            stake1 = (total_budget / (odds1 * implied_prob))
                            stake2 = (total_budget / (odds2 * implied_prob))
                            
                            message = (
                                f"💰 **New surebet found!** ({match_status})\n"
                                f"**Sport:** {sport}\n"
                                f"**League:** {league}\n"
                                f"**Event:** {match_name}\n"
                                f"**Profit:** {profit_percentage:.2f}%\n"
                                f"**Time:** {start_time}\n"
                                f"**Market:** {market_type}\n\n"
                                f"🔹 **{b1_name}**:\n"
                                f"▫️ {b1_data['bet']} -> {odds1}\n"
                                f"💵 **Stake:** {stake1:.1f} €\n"
                                f"🔗 [Direct Match Entry]({b1_data['link']})\n\n"
                                f"🔹 **{b2_name}**:\n"
                                f"▫️ {b2_data['bet']} -> {odds2}\n"
                                f"💵 **Stake:** {stake2:.1f} €\n"
                                f"🔗 [Direct Match Entry]({b2_data['link']})"
                            )
                            
                            send_telegram_alert(message)
                            sent_alerts.add(match_id)
                            print(f"Surebet found for {sport} - {match_name} ({profit_percentage:.2f}%)")
                            break
        except Exception as e:
            print(f"Error in scanner loop: {e}")
            
        time.sleep(60)

@app.route('/')
def home():
    return "All-Sports Custom Surebet Bot is running 24/7 on Render!"

if __name__ == '__main__':
    t = threading.Thread(target=surebot_scanner_loop)
    t.daemon = True
    t.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
