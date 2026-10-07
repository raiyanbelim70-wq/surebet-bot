
import os
import time
import threading
from datetime import datetime, timedelta
import requests
from flask import Flask

app = Flask(__name__)

# Telegram Credentials
TOKEN = "8001955184:AAFJ4NbmFHwVhpWB9LETM_K1ESdRWS8YDd8"
CHAT_ID = "5292908963"

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

def get_matches():
    today = datetime.now()
    today_str = today.strftime("%d %b")
    
    # Sabhi major sports ke matches aur unke bookmakers ka automatic setup
    matches = [
        {
            "id": "match_football_01",
            "match_status": "🟢 PRE-MATCH",
            "match": "Real Madrid - Barcelona",
            "sport": "Football",
            "league": "Spain. La Liga",
            "start_time": f"{today_str} 21:00 UTC",
            "market_type": "1X2 Match Winner",
            "bookmakers": {
                "Pinnacle": {"odds": 2.10, "bet": "Home (1)", "link": "https://www.pinnacle.com"},
                "1xBet": {"odds": 2.15, "bet": "Away (2)", "link": "https://1xbet.com"},
                "Dafabet": {"odds": 2.08, "bet": "Home (1)", "link": "https://dafabet.com"},
                "Mostbet": {"odds": 2.12, "bet": "Away (2)", "link": "https://mostbet.com"}
            }
        },
        {
            "id": "match_tennis_02",
            "match_status": "🔴 LIVE MATCH",
            "match": "Novak Djokovic - Carlos Alcaraz",
            "sport": "Tennis",
            "league": "ATP Masters",
            "start_time": "Live Now (Set 2)",
            "market_type": "Match Winner",
            "bookmakers": {
                "Pinnacle": {"odds": 1.95, "bet": "Djokovic", "link": "https://www.pinnacle.com"},
                "Stake": {"odds": 2.05, "bet": "Alcaraz", "link": "https://stake.com"},
                "Parimatch": {"odds": 2.00, "bet": "Alcaraz", "link": "https://parimatch.com"}
            }
        },
        {
            "id": "match_cricket_03",
            "match_status": "🟢 PRE-MATCH",
            "match": "India - Australia",
            "sport": "Cricket",
            "league": "International T20",
            "start_time": f"{today_str} 14:30 UTC",
            "market_type": "Match Winner",
            "bookmakers": {
                "1xBet": {"odds": 1.85, "bet": "India", "link": "https://1xbet.com"},
                "Mostbet": {"odds": 2.08, "bet": "Australia", "link": "https://mostbet.com"},
                "Melbet": {"odds": 1.90, "bet": "India", "link": "https://melbet.com"}
            }
        },
        {
            "id": "match_basketball_04",
            "match_status": "🔴 LIVE MATCH",
            "match": "L.A. Lakers - Boston Celtics",
            "sport": "Basketball",
            "league": "NBA",
            "start_time": "Live Now (Q4)",
            "market_type": "Asian Handicap",
            "bookmakers": {
                "Pinnacle": {"odds": 1.97, "bet": "AH2(+5.5)", "link": "https://www.pinnacle.com"},
                "Stake": {"odds": 1.95, "bet": "AH2(+5.5)", "link": "https://stake.com"},
                "4rabet": {"odds": 2.02, "bet": "AH1(-5.5)", "link": "https://4rabet.com"}
            }
        },
        {
            "id": "match_esports_05",
            "match_status": "🟢 PRE-MATCH",
            "match": "Natus Vincere - FaZe Clan",
            "sport": "eSports",
            "league": "CS2 Major",
            "start_time": f"{today_str} 18:00 UTC",
            "market_type": "Map Winner",
            "bookmakers": {
                "1xBet": {"odds": 1.91, "bet": "NaVi", "link": "https://1xbet.com"},
                "Parimatch": {"odds": 2.04, "bet": "FaZe", "link": "https://parimatch.com"},
                "Dafabet": {"odds": 1.95, "bet": "NaVi", "link": "https://dafabet.com"}
            }
        },
        {
            "id": "match_hockey_06",
            "match_status": "🟢 PRE-MATCH",
            "match": "Toronto Maple Leafs - Montreal Canadiens",
            "sport": "Ice Hockey",
            "league": "NHL",
            "start_time": f"{today_str} 23:00 UTC",
            "market_type": "Winner (Incl. OT)",
            "bookmakers": {
                "Pinnacle": {"odds": 1.88, "bet": "Leafs", "link": "https://www.pinnacle.com"},
                "Mostbet": {"odds": 2.05, "bet": "Canadiens", "link": "https://mostbet.com"}
            }
        },
        {
            "id": "match_tabletennis_07",
            "match_status": "🔴 LIVE MATCH",
            "match": "Ma Long - Fan Zhendong",
            "sport": "Table Tennis",
            "league": "TT Elite Series",
            "start_time": "Live Now (Game 3)",
            "market_type": "Winner",
            "bookmakers": {
                "1xBet": {"odds": 1.98, "bet": "Ma Long", "link": "https://1xbet.com"},
                "Melbet": {"odds": 2.01, "bet": "Fan Zhendong", "link": "https://melbet.com"}
            }
        },
        {
            "id": "match_volleyball_08",
            "match_status": "🟢 PRE-MATCH",
            "match": "Italy - Brazil",
            "sport": "Volleyball",
            "league": "World Championship",
            "start_time": f"{today_str} 19:30 UTC",
            "market_type": "Set Handicap",
            "bookmakers": {
                "Stake": {"odds": 1.93, "bet": "Italy", "link": "https://stake.com"},
                "Dafabet": {"odds": 2.02, "bet": "Brazil", "link": "https://dafabet.com"}
            }
        }
    ]
    return matches

def surebet_scanner_loop():
    print("Multi-Sport Universal Surebet Bot started in background...")
    send_telegram_alert("🚀 *Universal Surebet Bot* (All Sports Enabled) is now running 24/7 on Render!")
    
    while True:
        try:
            matches_to_check = get_matches()
            
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
                
                # Sabhi bookmakers ke odds ko aapas mein compare karna
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
                            
                            # Stake Distribution (Total Budget = 100 €)
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
            
        time.sleep(30)

@app.route('/')
def home():
    return "Universal All-Sports Surebet Bot is active and running 24/7 on Render!"

if __name__ == '__main__':
    t = threading.Thread(target=surebot_scanner_loop)
    t.daemon = True
    t.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
    
