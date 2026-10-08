import os
import time
import threading
from datetime import datetime, timezone
import requests
from flask import Flask

app = Flask(__name__)

TOKEN = "6001955104:AAFJAN8mFHNW9pMs8DLETR-K1E5dWn50tdd"
CHAT_ID = "5292910962"
ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")

ALLOWED_BOOKMAKERS = {
    "pinnacle": {"name": "Pinnacle", "base_url": "https://www.pinnacle.com"},
    "onexbet": {"name": "1xBet", "base_url": "https://1xbet.com"},
    "dafabet": {"name": "Dafabet", "base_url": "https://www.dafabet.com"},
    "mostbet": {"name": "Mostbet", "base_url": "https://mostbet.com"},
    "stake": {"name": "Stake", "base_url": "https://stake.com"},
    "parimatch": {"name": "Parimatch", "base_url": "https://parimatch.com"},
    "melbet": {"name": "Melbet", "base_url": "https://melbet.com"}
}

# Duniya bhar ki sabhi mukhya leagues aur sports ki massive list
SPORTS_TO_SCAN = [
    # Football / Soccer (Global Leagues)
    {"key": "soccer_epl", "name": "Football", "league": "English Premier League"},
    {"key": "soccer_spain_la_liga", "name": "Football", "league": "Spain La Liga"},
    {"key": "soccer_italy_serie_a", "name": "Football", "league": "Italy Serie A"},
    {"key": "soccer_germany_bundesliga", "name": "Football", "league": "Germany Bundesliga"},
    {"key": "soccer_france_ligue_one", "name": "Football", "league": "France Ligue 1"},
    {"key": "soccer_uefa_champs_league", "name": "Football", "league": "UEFA Champions League"},
    {"key": "soccer_uefa_europa_league", "name": "Football", "league": "UEFA Europa League"},
    {"key": "soccer_netherlands_eredivisie", "name": "Football", "league": "Netherlands Eredivisie"},
    {"key": "soccer_portugal_primeira_liga", "name": "Football", "league": "Portugal Primeira Liga"},
    {"key": "soccer_turkey_super_league", "name": "Football", "league": "Turkey Super Lig"},
    {"key": "soccer_greece_super_league", "name": "Football", "league": "Greece Super League"},
    {"key": "soccer_brazil_campeonato", "name": "Football", "league": "Brazil Serie A"},
    {"key": "soccer_argentina_primera_division", "name": "Football", "league": "Argentina Primera Division"},
    {"key": "soccer_mexico_ligamx", "name": "Football", "league": "Mexico Liga MX"},
    {"key": "soccer_japan_j_league", "name": "Football", "league": "Japan J League"},
    {"key": "soccer_korea_kleague1", "name": "Football", "league": "South Korea K League 1"},
    {"key": "soccer_australia_aleague", "name": "Football", "league": "Australia A-League"},

    # Basketball
    {"key": "basketball_nba", "name": "Basketball", "league": "NBA"},
    {"key": "basketball_euroleague", "name": "Basketball", "league": "Euroleague"},
    {"key": "basketball_ncaab", "name": "Basketball", "league": "NCAA College Basketball"},
    {"key": "basketball_australia_nbl", "name": "Basketball", "league": "Australia NBL"},
    {"key": "basketball_italy_lega_basket", "name": "Basketball", "league": "Italy Lega Basket"},
    {"key": "basketball_spain_acb", "name": "Basketball", "league": "Spain ACB"},

    # Tennis (ATP & WTA)
    {"key": "tennis_atp_aus_open", "name": "Tennis", "league": "ATP Australian Open"},
    {"key": "tennis_wta_aus_open", "name": "Tennis", "league": "WTA Australian Open"},
    {"key": "tennis_atp_french_open", "name": "Tennis", "league": "ATP French Open"},
    {"key": "tennis_wta_french_open", "name": "Tennis", "league": "WTA French Open"},
    {"key": "tennis_atp_wimbledon", "name": "Tennis", "league": "ATP Wimbledon"},
    {"key": "tennis_wta_wimbledon", "name": "Tennis", "league": "WTA Wimbledon"},
    {"key": "tennis_atp_us_open", "name": "Tennis", "league": "ATP US Open"},
    {"key": "tennis_wta_us_open", "name": "Tennis", "league": "WTA US Open"},

    # Cricket
    {"key": "cricket_ipl", "name": "Cricket", "league": "Indian Premier League (IPL)"},
    {"key": "cricket_international_t20", "name": "Cricket", "league": "International T20"},
    {"key": "cricket_odi", "name": "Cricket", "league": "ODI Matches"},
    {"key": "cricket_test_match", "name": "Cricket", "league": "Test Matches"},
    {"key": "cricket_big_bash", "name": "Cricket", "league": "Big Bash League (BBL)"},
    {"key": "cricket_psl", "name": "Cricket", "league": "Pakistan Super League (PSL)"},

    # Ice Hockey
    {"key": "icehockey_nhl", "name": "Ice Hockey", "league": "NHL"},
    {"key": "icehockey_sweden_hockey_league", "name": "Ice Hockey", "league": "Sweden Hockey League"},
    {"key": "icehockey_khl", "name": "Ice Hockey", "league": "KHL"}
]

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

def get_match_status_and_color(commence_time_str):
    try:
        match_time = datetime.fromisoformat(commence_time_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        diff_hours = (match_time - now).total_seconds() / 3600
        
        if diff_hours <= 0:
            return "🔴 LIVE", diff_hours
        elif diff_hours <= 48:
            return "🟢 UPCOMING", diff_hours
    except Exception as e:
        print(f"Time parse error: {e}")
    return None, 999

def get_real_matches_from_api():
    if not ODDS_API_KEY:
        return []

    all_opportunities = []
    markets_str = "h2h,spreads,totals"

    for sport in SPORTS_TO_SCAN:
        sport_key = sport["key"]
        sport_name = sport["name"]
        league_name = sport["league"]

        url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={ODDS_API_KEY}&regions=eu,us,uk,au&markets={markets_str}"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                api_data = response.json()
                print(f"Scanned {sport_key}: Found {len(api_data)} matches")
                
                for item in api_data:
                    commence_time = item.get("commence_time")
                    if not commence_time:
                        continue

                    status_label, diff_hours = get_match_status_and_color(commence_time)
                    if not status_label or diff_hours >= 48 or diff_hours < -4:
                        continue

                    home_team = item.get("home_team")
                    away_team = item.get("away_team")
                    match_query = f"{home_team} vs {away_team}".replace(" ", "+")

                    bookmakers_markets = {}

                    for bookie in item.get("bookmakers", []):
                        b_key = bookie.get("key")
                        if b_key in ALLOWED_BOOKMAKERS:
                            b_info = ALLOWED_BOOKMAKERS[b_key]
                            b_title = b_info["name"]
                            b_base = b_info["base_url"]

                            if b_title == "1xBet":
                                direct_link = f"https://1xbet.com/en/search?query={match_query}"
                            elif b_title == "Pinnacle":
                                direct_link = f"https://www.pinnacle.com/en/search?query={match_query}"
                            elif b_title == "Stake":
                                direct_link = f"https://stake.com/sports/search?query={match_query}"
                            elif b_title == "Dafabet":
                                direct_link = f"https://www.dafabet.com/en/sports/search?query={match_query}"
                            elif b_title == "Mostbet":
                                direct_link = f"https://mostbet.com/search?query={match_query}"
                            elif b_title == "Parimatch":
                                direct_link = f"https://parimatch.com/en/search?query={match_query}"
                            elif b_title == "Melbet":
                                direct_link = f"https://melbet.com/en/search?query={match_query}"
                            else:
                                direct_link = b_base

                            for m in bookie.get("markets", []):
                                n_key = m.get("key")
                                outcomes = m.get("outcomes", [])

                                if n_key == "h2h" and len(outcomes) == 2:
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
                                            "link": direct_link
                                        }

                                elif n_key == "spreads" and len(outcomes) == 2:
                                    o1, o2 = outcomes[0], outcomes[1]
                                    p1, p2 = o1.get("point"), o2.get("point")
                                    market_id = f"Handicap ({o1.get('name')} {p1})"

                                    if market_id not in bookmakers_markets:
                                        bookmakers_markets[market_id] = {}
                                    bookmakers_markets[market_id][b_title] = {
                                        "bet1_odds": o1.get("price"),
                                        "bet1_desc": f"{o1.get('name')} ({p1})",
                                        "bet2_odds": o2.get("price"),
                                        "bet2_desc": f"{o2.get('name')} ({p2})",
                                        "link": direct_link
                                    }

                                elif n_key == "totals" and len(outcomes) == 2:
                                    o1, o2 = outcomes[0], outcomes[1]
                                    point = o1.get("point")
                                    market_id = f"Totals Over/Under ({point})"

                                    if market_id not in bookmakers_markets:
                                        bookmakers_markets[market_id] = {}
                                    
                                    over_item = next((o for o in outcomes if o.get("name") == "Over"), None)
                                    under_item = next((o for o in outcomes if o.get("name") == "Under"), None)

                                    if over_item and under_item:
                                        bookmakers_markets[market_id][b_title] = {
                                            "bet1_odds": over_item.get("price"),
                                            "bet1_desc": f"Over ({point})",
                                            "bet2_odds": under_item.get("price"),
                                            "bet2_desc": f"Under ({point})",
                                            "link": direct_link
                                        }

                    for market_type, bookies_dict in bookmakers_markets.items():
                        b_names = list(bookies_dict.keys())
                        if len(b_names) < 2:
                            continue

                        for i in range(len(b_names)):
                            for j in range(i + 1, len(b_names)):
                                b1, b2 = b_names[i], b_names[j]
                                data1, data2 = bookies_dict[b1], bookies_dict[b2]

                                odds1 = data1["bet1_odds"]
                                odds2 = data2["bet2_odds"]

                                if not odds1 or not odds2:
                                    continue

                                implied_prob = (1 / odds1) + (1 / odds2)
                                if implied_prob < 1.0:
                                    profit_percentage = ((1 / implied_prob) - 1) * 100
                                    if profit_percentage >= 1.0:
                                        total_budget = 100.0
                                        stake1 = (total_budget / (odds1 * implied_prob))
                                        stake2 = (total_budget / (odds2 * implied_prob))

                                        unique_alert_key = f"{item['id']}_{market_type}_{b1}_{b2}"

                                        all_opportunities.append({
                                            "alert_key": unique_alert_key,
                                            "match_status": status_label,
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
            else:
                print(f"API Error for {sport_key}: Status {response.status_code}")
        except Exception as e:
            print(f"Error scanning sport {sport_key}: {e}")

    return all_opportunities

def sure_bet_scanner_loop():
    print("Ultimate Master Sure Bet Scanner started successfully...")
    send_telegram_alert("🚀 *Ultimate Master Sure Bet Bot Active:* Duniya bhar ki saari leagues aur 7 authorized bookmakers ke sath scanner live ho gaya hai!")
    
    while True:
        try:
            print("Scanning global leagues and matches for Sure Bets...")
            opportunities = get_real_matches_from_api()
            print(f"Scan complete. Total Sure Bets found in this cycle: {len(opportunities)}")
            
            for opp in opportunities:
                if opp["alert_key"] in sent_alerts:
                    continue

                message = (
                    f"💰 **New {opp['market_type']} Sure Bet!** ({opp['match_status']})\n"
                    f"🏆 **Sport:** {opp['sport']} | **League:** {opp['league']}\n"
                    f"⚔️ **Event:** {opp['match']}\n"
                    f"📈 **Profit:** {opp['profit']:.2f}%\n"
                    f"⏰ **Time:** {opp['start_time']}\n\n"
                    f"🔹 **{opp['b1_name']}**:\n"
                    f"▫️ {opp['b1_bet']} -> {opp['b1_odds']}\n"
                    f"💵 **Stake:** {opp['b1_stake']:.1f} €\n"
                    f"🔗 [Direct Match Page]({opp['b1_link']})\n\n"
                    f"🔹 **{opp['b2_name']}**:\n"
                    f"▫️ {opp['b2_bet']} -> {opp['b2_odds']}\n"
                    f"💵 **Stake:** {opp['b2_stake']:.1f} €\n"
                    f"🔗 [Direct Match Page]({opp['b2_link']})"
                )

                send_telegram_alert(message)
                sent_alerts.add(opp["alert_key"])

        except Exception as e:
            print(f"Loop error: {e}")
        
        time.sleep(60)

@app.route('/')
def home():
    return "Ultimate Master Sure Bet Bot is running 24/7 on Render!"

if __name__ == '__main__':
    t = threading.Thread(target=sure_bet_scanner_loop)
    t.daemon = True
    t.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
        
