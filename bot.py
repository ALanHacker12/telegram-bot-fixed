import os
import telebot
from telebot import types
import time
import threading
from flask import Flask

# ================== ОБМАНКА ДЛЯ RENDER ==================
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Telegram Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False)

flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()
# =======================================================

BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден!")
    exit(1)

print("✅ BOT_TOKEN загружен успешно")
bot = telebot.TeleBot(BOT_TOKEN)

agents = [
    {"name": "@SamoletPlus113", "status": "свободен"},
    {"name": "@qwils", "status": "свободен"},
    {"name": "Денис", "phone": "+7 963 891 5555", "status": "свободен"}
]

current_agent_index = 0

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_agent = types.KeyboardButton("📞 Получить номер агента")
    markup.add(button_agent)
    
    welcome_text = """
🤖 Добро пожаловать в службу поддержки!

Нажмите кнопку «Получить номер агента», чтобы связаться со специалистом.
    """
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)
    print(f"✅ Пользователь {message.chat.id} запустил бота")

@bot.message_handler(func=lambda message: message.text == "📞 Получить номер агента")
def send_agent_number(message):
    global current_agent_index
    agent = agents[current_agent_index]
    
    agent_info = f"""
✅ Ваш персональный агент:

👨‍💼 Имя: {agent['name']}
📞 Телефон: {agent['phone']}
🟢 Статус: {agent['status']}
    """
    
    bot.send_message(message.chat.id, agent_info)
    current_agent_index = (current_agent_index + 1) % len(agents)
    print(f"✅ Выдан агент {agent['name']} пользователю {message.chat.id}")

@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    bot.send_message(
        message.chat.id, 
        "Для получения номера агента нажмите кнопку ниже 👇",
        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(
            types.KeyboardButton("📞 Получить номер агента")
        )
    )

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 БОТ ЗАПУСКАЕТСЯ НА RENDER")
    print("=" * 50)
    print("✅ Flask сервер запущен в фоне")
    print("✅ Бот начинает работу...")
    
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("♻️ Перезапуск через 10 секунд...")
        time.sleep(10)
