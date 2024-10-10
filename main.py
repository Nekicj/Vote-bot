import telebot
from config import API_TOKEN, ADMIN_ID, UPLOAD_FOLDER
from db import init_db
from handlers import start_handlers

bot = telebot.TeleBot(API_TOKEN, parse_mode='Markdown')

# Инициализация базы данных
init_db()

# Регистрация обработчиков
start_handlers(bot)

# Запуск бота
bot.polling(none_stop=True)
