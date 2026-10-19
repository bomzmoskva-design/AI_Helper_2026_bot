
import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("BOT_TOKEN")

# Сюда позже добавим твою ссылку на регистрацию
REGISTRATION_URL = "https://example.com"

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=["start"])
def start(message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(
            "🚀 Зарегистрироваться курьером",
            url=REGISTRATION_URL
        )
    )

    bot.send_message(
        message.chat.id,
        "👋 Привет!\n\n"
        "Здесь ты можешь перейти к регистрации курьером.\n\n"
        "Нажми кнопку ниже:",
        reply_markup=keyboard
    )

bot.infinity_polling()
