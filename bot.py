import os
import json
import logging
import telebot

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ==============================
# НАСТРОЙКИ
# ==============================

TOKEN = os.getenv("BOT_TOKEN")

REGISTRATION_URL = "https://ya.cc/t/xNoOHAItAyyVVL"

STATS_FILE = "stats.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

if not TOKEN:
    raise RuntimeError(
        "Не найден BOT_TOKEN. Добавьте токен в GitHub Secrets."
    )

bot = telebot.TeleBot(TOKEN)


# ==============================
# СТАТИСТИКА
# ==============================

def load_stats():
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"users": []}


def save_stats(stats):
    with open(STATS_FILE, "w", encoding="utf-8") as file:
        json.dump(stats, file, ensure_ascii=False, indent=2)


def register_user(user_id):
    stats = load_stats()

    if user_id not in stats["users"]:
        stats["users"].append(user_id)
        save_stats(stats)
        logging.info("Новый пользователь: %s", user_id)


def get_user_count():
    return len(load_stats()["users"])


# ==============================
# КЛАВИАТУРЫ
# ==============================

def main_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton(
            "🚀 Зарегистрироваться курьером",
            url=REGISTRATION_URL
        ),
        InlineKeyboardButton(
            "📋 Как устроиться на работу",
            callback_data="how_to"
        ),
        InlineKeyboardButton(
            "📊 Информация о работе",
            callback_data="info"
        )
    )

    return keyboard


def back_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(
            "⬅️ Главное меню",
            callback_data="main_menu"
        )
    )
    return keyboard


# ==============================
# КОМАНДА START
# ==============================

@bot.message_handler(commands=["start"])
def start(message):
    register_user(message.from_user.id)

    text = (
        "👋 Здравствуйте!\n\n"
        "Добро пожаловать в бот для желающих работать "
        "курьерами Яндекс Еды в Москве.\n\n"
        "Здесь вы можете перейти к регистрации и узнать, "
        "с чего начать.\n\n"
        "Выберите нужный пункт меню 👇"
    )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=main_menu()
    )


# ==============================
# КОМАНДА HELP
# ==============================

@bot.message_handler(commands=["help"])
def help_command(message):
    bot.send_message(
        message.chat.id,
        "ℹ️ Помощь\n\n"
        "Нажмите /start, чтобы открыть главное меню.\n"
        "Для регистрации используйте кнопку "
        "«Зарегистрироваться курьером»."
    )


# ==============================
# ОБРАБОТКА КНОПОК
# ==============================

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "how_to":
        text = (
            "📋 Как начать работать курьером\n\n"
            "1. Нажмите кнопку регистрации.\n"
            "2. Перейдите по ссылке и заполните необходимые данные.\n"
            "3. Следуйте инструкциям на странице регистрации.\n"
            "4. Дождитесь дальнейших инструкций.\n\n"
            "Требования и условия уточняйте на официальной "
            "странице регистрации."
        )

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=back_menu()
        )

    elif call.data == "info":
        text = (
            "📊 Информация о работе\n\n"
            "Условия сотрудничества, требования, "
            "доступность заказов и выплаты зависят от "
            "условий подключения.\n\n"
            "Подробности доступны на странице регистрации."
        )

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=back_menu()
        )

    elif call.data == "main_menu":
        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            "🏠 Главное меню\n\nВыберите нужный пункт:",
            reply_markup=main_menu()
        )


# ==============================
# СТАТИСТИКА ДЛЯ ВЛАДЕЛЬЦА
# ==============================

@bot.message_handler(commands=["stats"])
def stats_command(message):
    # Здесь нужно будет указать ваш Telegram ID.
    # Пока команда доступна всем, поэтому не используйте её
    # для приватной статистики до настройки ADMIN_ID.
    count = get_user_count()

    bot.send_message(
        message.chat.id,
        f"📊 Всего пользователей: {count}"
    )


# ==============================
# ЗАПУСК БОТА
# ==============================

if __name__ == "__main__":
    logging.info("Бот запускается...")

    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=30
    )
