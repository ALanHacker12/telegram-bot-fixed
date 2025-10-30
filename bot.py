import os
import telebot
from telebot import types
import time
import threading
from flask import Flask
import logging

# ================== ОБМАНКА ДЛЯ RENDER ==================
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Telegram Bot is running!"

@app.route('/health')
def health():
    return "OK"

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False)

flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()
# =======================================================

# Настраиваем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем токен бота
BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не найден!")
    exit(1)

logger.info("✅ BOT_TOKEN загружен успешно")
bot = telebot.TeleBot(BOT_TOKEN)

# Список агентов
agents = [
    {"name": "Алан", "phone": "+7 (996) 882-57-34", "status": "свободен"},
    {"name": "Рустам", "phone": "+7 (995) 943-14-07", "status": "свободен"},
    {"name": "Денис", "phone": "+7 (963) 891-55-55", "status": "свободен"}
]

current_agent_index = 0

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
        button_agent = types.KeyboardButton("📞 Получить номер агента")
        markup.add(button_agent)
        
        welcome_text = """
🤖 Добро пожаловать в службу поддержки!

Нажмите кнопку «Получить номер агента», чтобы связаться со специалистом.
        """
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup)
        logger.info(f"✅ Пользователь {message.chat.id} запустил бота")
    except Exception as e:
        logger.error(f"❌ Ошибка в send_welcome: {e}")

@bot.message_handler(func=lambda message: message.text == "📞 Получить номер агента")
def send_agent_number(message):
    global current_agent_index
    try:
        agent = agents[current_agent_index]
        
        agent_info = f"""
✅ Ваш персональный агент:

👨‍💼 Имя: {agent['name']}
📞 Телефон: {agent['phone']}
🟢 Статус: {agent['status']}

💡 Позвоните или напишите в WhatsApp для консультации.
        """
        
        # Отправляем сообщение с защитой от ошибок
        sent_message = bot.send_message(message.chat.id, agent_info)
        logger.info(f"✅ Выдан агент {agent['name']} пользователю {message.chat.id}")
        
        # Переходим к следующему агенту
        current_agent_index = (current_agent_index + 1) % len(agents)
        
        # Отправляем подтверждение
        time.sleep(1)
        bot.send_message(
            message.chat.id,
            "✅ Номер агента успешно выдан! Для получения следующего агента нажмите кнопку снова.",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(
                types.KeyboardButton("📞 Получить номер агента")
            )
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке номера агента: {e}")
        try:
            bot.send_message(
                message.chat.id,
                "⚠️ Произошла временная ошибка. Пожалуйста, попробуйте снова через несколько секунд.",
                reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(
                    types.KeyboardButton("📞 Получить номер агента")
                )
            )
        except:
            pass

@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    try:
        if message.text and message.text != "📞 Получить номер агента":
            bot.send_message(
                message.chat.id, 
                "Для получения номера агента нажмите кнопку ниже 👇",
                reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(
                    types.KeyboardButton("📞 Получить номер агента")
                )
            )
    except Exception as e:
        logger.error(f"❌ Ошибка в handle_other_messages: {e}")

# Обработчик ошибок бота
@bot.message_handler(content_types=['text', 'contact', 'location'])
def handle_all_messages(message):
    try:
        if message.text == "📞 Получить номер агента":
            send_agent_number(message)
        elif message.text and not message.text.startswith('/'):
            handle_other_messages(message)
    except Exception as e:
        logger.error(f"❌ Ошибка в handle_all_messages: {e}")

# Запуск бота с улучшенной обработкой ошибок
if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("🚀 БОТ ЗАПУСКАЕТСЯ НА RENDER")
    logger.info("=" * 50)
    
    max_retries = 5
    retry_delay = 10
    
    for attempt in range(max_retries):
        try:
            logger.info(f"♻️ Попытка запуска {attempt + 1}/{max_retries}")
            bot.infinity_polling(timeout=90, long_polling_timeout=90)
        except Exception as e:
            logger.error(f"❌ Ошибка на попытке {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                logger.info(f"⏳ Перезапуск через {retry_delay} секунд...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Увеличиваем задержку с каждой попыткой
            else:
                logger.error("💥 Достигнут лимит попыток перезапуска")

