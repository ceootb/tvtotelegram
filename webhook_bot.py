from flask import Flask, request
import requests

app = Flask(__name__)

BOT_TOKEN = "7873749734:AAFFCqrcQrc57HGUZ6im_QNEjNQ3ZqRhJWg"
CHAT_ID = "1785396742"

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, data=payload)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    signal = data.get("signal")
    ticker = data.get("ticker", "EUR/USD")
    price = data.get("price")
    waktu = data.get("time")

    message = f"""📡 Sinyal dari TradingView

📈 Pair: {ticker}
📉 Sinyal: {signal}
💰 Harga: {price}
🕒 Waktu: {waktu}

🎯 TP: +30 pips
🛑 SL: -50 pips
"""
    send_to_telegram(message)
    return "OK", 200
