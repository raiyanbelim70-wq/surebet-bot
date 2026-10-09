import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from flask import Flask

app = Flask(__name__)

# Telegram Configuration
TELEGRAM_BOT_TOKEN = "8001955184:AAH_k7XKzU6aJhg8MoAeECsra06SYqEJZFs"
TELEGRAM_CHAT_ID = "5232960693"

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
        # Direct network use for Telegram (No proxy needed)
        requests.post(url, json=payload, proxies={"http": None, "https": None}, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}", flush=True)

def fetch_mobile_api(bm, endpoint, bookmaker_urls):
    bookie_results = {}
    try:
        # Mobile app headers to bypass browser-based WAF/Cloudflare
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-S918B Build/TP1A.220624.014) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/112.0.5615.135 Mobile Safari/537.36 1xBetClient/15.0(4250)",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate",
            "X-Requested-With": "org.xbet.client",
            "Connection": "keep-alive"
        }
        
        response = requests.get(endpoint, headers=headers, timeout=8)
        print(f"DEBUG Mobile API -> Bookmaker: {bm} | Status Code: {response.status_code}", flush=True)
        
        if response.status_code == 200:
            try:
                data = response.json()
            except Exception:
                print(f"DEBUG Error -> {bm}: Non-JSON response received", flush=True)
                return bm, bookie_results

            events_list = []
            if isinstance(data, dict):
                events_list = data.get("result", data.get("Value", data.get("data", [])))
            elif isinstance(data, list):
                events_list = data

            if isinstance(events_list, list):
                for event in events_list:
                    match_name = event.get("name", event.get("matchName", event.get("C1", "") + " vs " + event.get("C2", "")))
                    odds_list = event.get("odds", event.get("prices", event.get("E", [])))
                    
                    extracted_odds = []
                    if isinstance(odds_list, list) and len(odds_list) > 0:
                        for odd in odds_list:
                            if isinstance(odd, dict):
                                val = odd.get("C", odd.get("value", 0))
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
        else:
            print(f"DEBUG Error -> {bm}: HTTP Status {response.status_code}", flush=True)
            
    except Exception as e:
        print(f"DEBUG Error -> {bm}: {str(e)}", flush=True)
        
    return bm, bookie_results

def fetch_odds_from_bookmakers(sport, market):
    live_matches_cache = {}

    # Mobile API Endpoints (Direct JSON Gateways)
    bookmaker_endpoints = {
        "1xBet": f"https://1xbet.com/service-api/live/getEvents?sport={sport}&market={market}",
        "Pinnacle": f"https://api.pinnacle.com/v1/odds?sport={sport}&market={market}"
    }

    bookmaker_urls = {
        "1xBet": "https://1xbet.com",
        "Pinnacle": "https://www.pinnacle.com"
    }

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(fetch_mobile_api, bm, endpoint, bookmaker_urls): bm 
            for bm, endpoint in bookmaker_endpoints.items()
        }
        
        for future in as_completed(futures):
            try:
                bm, bookie_results = future.result()
                for match_name, info in bookie_results.items():
                    if match_name not in live_matches_cache:
                        live_matches_cache[match_name] = {}
                    live_matches_cache[match_name][bm] = info
            except Exception as e:
                print(f"ThreadPool Future Error: {e}", flush=True)

    return live_matches_cache

def evaluate_surebet_and_alert(match_name, sport, market, odds_dictionary):
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
            
            message = (
                f"🚨 *100% PROFITABLE ARBITRAGE FOUND!* 🚨\n\n"
                f"🔴 *LIVE SURE BET SIGNAL*\n"
                f"🏆 *Sport:* {sport}\n"
                f"⚔️ *Match:* {match_name}\n"
                f"📊 *Market:* {market}\n"
                f"💰 *Guaranteed Profit:* `{profit_percentage}%`\n\n"
                f"👉 *Leg 1:* [{bookie_1}]({link_1}) @ **{best_odd_1}**\n"
                f"👉 *Leg 2:* [{bookie_2}]({link_2}) @ **{best_odd_2}**\n\n"
                f"🔥 *Click bookmaker names above to open site directly!*"
            )
            send_telegram_alert(message)

@app.route('/')
def home():
    return "Mobile API Emulated Arbitrage Scanner is Active!"

def background_worker():
    startup_msg = "🟢 *Mobile API Scanner Started Successfully!*\n\nBypassing browser WAF using mobile client headers."
    send_telegram_alert(startup_msg)
    print("Background worker started with mobile emulation!", flush=True)

    sports_list = ["Cricket", "Football", "Tennis", "Basketball"]
    markets_list = ["1X2", "Totals"]

    while True:
        try:
            for sport in sports_list:
                for market in markets_list:
                    live_cache = fetch_odds_from_bookmakers(sport, market)
                    for match_name, odds_dict in live_cache.items():
                        evaluate_surebet_and_alert(match_name, sport, market, odds_dict)
        except Exception as e:
            print(f"Background Loop Error: {e}", flush=True)
            
        time.sleep(5)

t = threading.Thread(target=background_worker, daemon=True)
t.start()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
    
