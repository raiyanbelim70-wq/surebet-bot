import os
import time
import threading
import requests
from flask import Flask

app = Flask(__name__)

# Telegram Credentials
TELEGRAM_BOT_TOKEN = "8001955184:AAFJ4NbmFHwVhpWB9LETM_K1ESdRWS8YDd8"
TELEGRAM_CHAT_ID = "5292908963"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Error sending message: {e}")

def surebet_scanner_loop():
    print("Surebet Scanner Bot started in background...")
    send_telegram_message("🚀 *Surebet Scanner Bot* is now running 24/7 on Render!")
    
    while True:
        try:
            print("Scanning bookmakers for surebets...")
        except Exception as e:
            print(f"Error in scanner loop: {e}")
            
        time.sleep(60)

@app.route('/')
def home():
    return "Surebet Bot is active and running 24/7!"

if __name__ == '__main__':
    t = threading.Thread(target=surebet_scanner_loop)
    t.daemon = True
    t.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
  
