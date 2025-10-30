import os
import telebot
from telebot import types
import time
import threading
from flask import Flask
import logging
import requests

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

# ================== АВТО-ПИНГ ДЛЯ RENDER ==================
def keep_alive():
    """Каждые 10 минут отправляет запрос чтобы Render не уснул"""
    while True:
        try:
            # Получаем URL нашего приложения
            render_url = os.environ.get('RENDER_URL')
            if not render_url:
                # Если URL не указан, пробуем определить автоматически
                service_name = os.environ.get('RENDER_SERVICE_NAME')
                if service_name:
                    render_url = f"https://{service_name}.onrender.com"
            
            if render_url:
                response = requests.get(f"{render_url}/health", timeout=10)
                logging.info(f"✅ Пинг отправлен: {response.status_code}")
            else:
                logging.info("✅ Бот активен (пинг пропущен - URL не настроен)")
                
        except Exception as e:
            logging.warning(f"⚠️ Пинг не удался: {e}")
        
        # Ждем 10 минут до следующего пина
        time.sleep(600)

# Запускаем авто-пинг в отдельном потоке
ping_thread = threading.Thread(target=keep_alive)
ping_thread.daemon = True
ping_thread.start()
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
        
        bot.send_message(message.chat.id, agent_info)
        logger.info(f"✅ Выдан агент {agent['name']} пользователю {message.chat.id}")
        
        current_agent_index = (current_agent_index + 1) % len(agents)
        
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке номера агента: {e}")
        bot.send_message(
            message.chat.id,
            "⚠️ Произошла временная ошибка. Пожалуйста, попробуйте снова.",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(
                types.KeyboardButton("📞 Получить номер агента")
            )
        )

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

# Запуск бота
if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("🚀 БОТ ЗАПУСКАЕТСЯ НА RENDER")
    logger.info("✅ Flask сервер запущен")
    logger.info("✅ Авто-пинг активирован")
    logger.info("=" * 50)
    
    while True:
        try:
            logger.info("🔄 Запуск polling...")
            bot.infinity_polling(timeout=90, long_polling_timeout=90)
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            logger.info("♻️ Перезапуск через 15 секунд...")
            time.sleep(15)


