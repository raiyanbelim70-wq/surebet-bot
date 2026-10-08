import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import cloudscraper
from flask import Flask

app = Flask(__name__)

# Telegram Configuration
TELEGRAM_BOT_TOKEN = "7001955154:AAPJ4IBwPmHywB9LETV_K1E5dWm5EYDdb"
TELEGRAM_CHAT_ID = "5232960693"

# IPRoyal Paid Proxy Configuration
PROXY_URL = os.environ.get("PROXY_URL", "http://HwySPyYCdCrpOQD9:ayUXZQamc10E4blN@geo.iproyal.com:12321")

sent_alerts = set()
alert_lock = threading.Lock()

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

def fetch_single_bookmaker(bm, endpoint, bookmaker_urls):
    proxies = {
        "http": PROXY_URL,
        "https": PROXY_URL
    } if PROXY_URL else None
    
    scraper = cloudscraper.create_scraper()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.google.com/"
    }
    
    bookie_results = {}
    try:
        response = scraper.get(endpoint, proxies=proxies, headers=headers, timeout=6)
        print(f"[{bm}] Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            
            events_list = []
            if isinstance(data, dict):
                events_list = data.get("result", data.get("data", data.get("events", data.get("Value", []))))
                if not events_list and "sports" in data:
                    events_list = data["sports"]
            elif isinstance(data, list):
                events_list = data

            if isinstance(events_list, list):
                for event in events_list:
                    match_name = event.get("name", event.get("matchName", event.get("homeTeam", "") + " vs " + event.get("awayTeam", "")))
                    odds_list = event.get("odds", event.get("prices", event.get("markets", [])))
                    
                    extracted_odds = []
                    if isinstance(odds_list, list) and len(odds_list) > 0:
                        for odd in odds_list:
                            if isinstance(odd, dict):
                                val = odd.get("C", odd.get("price", odd.get("value", 0)))
                                try:
                                    if val: 
                                        extracted_odds.append(float(val))
                                except:
                                    pass
                            elif isinstance(odd, (int, float)):
                                extracted_odds.append(float(odd))

                    if match_name and len(extracted_odds) >= 2:
                        bm_link = bookmaker_urls.get(bm, "https://google.com")
                        bookie_results[match_name] = {
                            "prices": [extracted_odds[0], extracted_odds[1]],
                            "link": bm_link
                        }
    except Exception as e:
        print(f"[{bm}] Error: {e}")
        
    return bm, bookie_results

def fetch_odds_from_bookmakers(sport, market, status):
    live_matches_cache = {}
    type_path = "live" if status == "LIVE" else "line"
    stake_query = "query" + status.capitalize() + "Events{" + sport + "}"

    # Only 4 core bookmakers focused on India
    bookmaker_endpoints = {
        "1xBet": f"https://1xbet.com/service-api/{type_path}/getEvents?sport={sport}&market={market}",
        "Parimatch": f"https://parimatch.com/api/v4/{type_path}/events?sport={sport}&market={market}",
        "Pinnacle": f"https://api.pinnacle.com/v1/odds?sport={sport}&market={market}&period={status.lower()}",
        "Stake": f"https://stake.com/_api/graphql?query={stake_query}"
    }

    bookmaker_urls = {
        "1xBet": "https://1xbet.com",
        "Parimatch": "https://parimatch.com",
        "Pinnacle": "https://www.pinnacle.com",
        "Stake": "https://stake.com"
    }

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(fetch_single_bookmaker, bm, endpoint, bookmaker_urls): bm 
            for bm, endpoint in bookmaker_endpoints.items()
        }
        
        for future in as_completed(futures):
            bm, bookie_results = future.result()
            for match_name, info in bookie_results.items():
                if match_name not in live_matches_cache:
                    live_matches_cache[match_name] = {}
                live_matches_cache[match_name][bm] = info

    return live_matches_cache

def evaluate_surebet_and_alert(match_name, sport, market, status, odds_dictionary):
    if len(odds_dictionary) < 2:
        return

    best_odd_1, bookie_1, link_1 = 0.0, "", ""
    best_odd_2, bookie_2, link_2 = 0.0, "", ""

    for bm, info in odds_dictionary.items():
        prices = info["prices"]
        bm_link = info["link"]
        
        if len(prices) >= 2:
            if prices[0] > best_odd_1:
                best_odd_1 = prices[0]
                bookie_1 = bm
                link_1 = bm_link
            if prices[1] > best_odd_2:
                best_odd_2 = prices[1]
                bookie_2 = bm
                link_2 = bm_link

    if best_odd_1 > 0 and best_odd_2 > 0 and bookie_1 != bookie_2:
        implied_probability = (1.0 / best_odd_1) + (1.0 / best_odd_2)
        
        if implied_probability < 1.0:
            profit_percentage = round((1.0 - implied_probability) * 100, 2)
            alert_id = f"{match_name}_{best_odd_1}_{best_odd_2}_{market}"
            
            with alert_lock:
                if alert_id in sent_alerts:
                    return
                sent_alerts.add(alert_id)

            status_tag = "🔴 *LIVE SURE BET SIGNAL (IN-PLAY)*" if status == "LIVE" else "⏳ *PRE-MATCH / UPCOMING SURE BET SIGNAL*"
            
            message = (
                f"🚨 *100% PROFITABLE ARBITRAGE FOUND!* 🚨\n\n"
                f"{status_tag}\n"
                f"🏆 *Sport:* {sport}\n"
                f"⚔️ *Match:* {match_name}\n"
                f"📊 *Market:* {market}\n"
                f"💰 *Guaranteed Profit:* `{profit_percentage}%`\n\n"
                f"👉 *Leg 1:* [{bookie_1}]({link_1}) @ **{best_odd_1}**\n"
                f"👉 *Leg 2:* [{bookie_2}]({link_2}) @ **{best_odd_2}**\n\n"
                f"🔥 *Click bookmaker names above to open site directly and place bets!*"
            )
            send_telegram_alert(message)

@app.route('/')
def home():
    return "Targeted 4-Bookmaker Arbitrage Scanner is Running 24/7!"

def background_worker():
    sports_list = ["Cricket", "Football", "Soccer", "Tennis"]
    markets_list = ["1X2", "Over/Under"]
    statuses = ["LIVE", "UPCOMING"]

    while True:
        try:
            for sport in sports_list:
                for market in markets_list:
                    for status in statuses:
                        live_cache = fetch_odds_from_bookmakers(sport, market, status)
                        for match_name, odds_dict in live_cache.items():
                            evaluate_surebet_and_alert(match_name, sport, market, status, odds_dict)
        except Exception as e:
            print(f"Background Loop Error: {e}")
            
        time.sleep(2)

if __name__ == '__main__':
    t = threading.Thread(target=background_worker, daemon=True)
    t.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
    
