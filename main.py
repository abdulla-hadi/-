import requests
from flask import Flask
import threading
import time
import os
import telebot

TOKEN = os.getenv("TELEGRAM_TOKEN")
USER_ID = int(os.getenv("USER_ID"))

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

def get_arbitrage():
    while True:
        try:
            url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=volume_desc&per_page=100&page=1"
            coins = requests.get(url).json()
            result = []
            for coin in coins:
                tickers = requests.get(f"https://api.coingecko.com/api/v3/coins/{coin['id']}/tickers").json()
                prices = {}
                for t in tickers.get("tickers", []):
                    price = t["converted_last"].get("usd")
                    volume = t["converted_volume"].get("usd", 0)
                    if price and volume > 10000:
                        prices[t["market"]["name"]] = price
                if len(prices) >= 2:
                    min_ex = min(prices, key=prices.get)
                    max_ex = max(prices, key=prices.get)
                    spread = (prices[max_ex] - prices[min_ex]) / prices[min_ex] * 100
                    if spread > 1:
                        result.append(f"{coin['symbol'].upper()} {spread:.2f}% | {min_ex} → {max_ex}")
            if result:
                bot.send_message(USER_ID, "\n".join(result[:10]))
        except Exception as e:
            print("Error:", e)
        time.sleep(10)

@bot.message_handler(commands=['start'])
def start_handler(message):
    if message.chat.id == USER_ID:
        bot.send_message(USER_ID, "Бот запущен!")

@bot.message_handler(commands=['price'])
def price_handler(message):
    if message.chat.id != USER_ID:
        return
    try:
        symbol = message.text.split()[1].lower()
        url = f"https://api.coingecko.com/api/v3/coins/{symbol}/tickers"
        data = requests.get(url).json()
        result = [f"{t['market']['name']}: ${t['converted_last']['usd']:.4f}" 
                  for t in data.get("tickers", []) if t.get("converted_last", {}).get("usd")]
        bot.send_message(USER_ID, "\n".join(result[:20]) or "Не найдено.")
    except:
        bot.send_message(USER_ID, "Ошибка. Используй: /price btc")

@app.route('/')
def home():
    return "Bot is running"

def run():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

threading.Thread(target=run).start()
threading.Thread(target=get_arbitrage).start()
bot.polling()
