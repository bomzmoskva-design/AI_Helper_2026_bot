import os
import json
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote


# =========================
# НАСТРОЙКИ
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Минимальный желаемый зазор
MIN_MARGIN = 5000

# Сколько новых объявлений проверять по каждой модели
MAX_RESULTS = 30

SEEN_FILE = "seen.json"


# =========================
# МОДЕЛИ И ЦЕНЫ
# =========================
#
# sell_price = ориентировочная цена продажи
# max_buy    = максимальная цена покупки
#
# Эти значения потом можно изменить.
#

MODELS = {
    "iPhone 11": {
        "sell_price": 20000,
        "max_buy": 15000
    },

    "iPhone 11 Pro": {
        "sell_price": 25000,
        "max_buy": 19000
    },

    "iPhone 11 Pro Max": {
        "sell_price": 28000,
        "max_buy": 22000
    },

    "iPhone 12": {
        "sell_price": 24000,
        "max_buy": 18000
    },

    "iPhone 12 Pro": {
        "sell_price": 28000,
        "max_buy": 22000
    },

    "iPhone 12 Pro Max": {
        "sell_price": 33000,
        "max_buy": 26000
    },

    "iPhone 13": {
        "sell_price": 28000,
        "max_buy": 22000
    },

    "iPhone 13 Pro": {
        "sell_price": 35000,
        "max_buy": 28000
    },

    "iPhone 13 Pro Max": {
        "sell_price": 40000,
        "max_buy": 32000
    },

    "iPhone 14": {
        "sell_price": 32000,
        "max_buy": 25000
    },

    "iPhone 14 Pro": {
        "sell_price": 43000,
        "max_buy": 35000
    },

    "iPhone 14 Pro Max": {
        "sell_price": 50000,
        "max_buy": 41000
    },

    "iPhone 15": {
        "sell_price": 43000,
        "max_buy": 35000
    },

    "iPhone 15 Pro": {
        "sell_price": 55000,
        "max_buy": 45000
    },

    "iPhone 15 Pro Max": {
        "sell_price": 65000,
        "max_buy": 54000
    },

    "iPhone 16": {
        "sell_price": 55000,
        "max_buy": 45000
    },

    "iPhone 16 Pro": {
        "sell_price": 65000,
        "max_buy": 55000
    },

    "iPhone 16 Pro Max": {
        "sell_price": 75000,
        "max_buy": 63000
    }
}


# =========================
# TELEGRAM
# =========================

def send_telegram(message):

    if not BOT_TOKEN:
        print("ОШИБКА: BOT_TOKEN не указан")
        return

    if not CHAT_ID:
        print("ОШИБКА: CHAT_ID не указан")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }

    try:

        response = requests.post(
            url,
            data=data,
            timeout=20
        )

        print(
            "Telegram:",
            response.status_code
        )

    except Exception as e:

        print(
            "Ошибка Telegram:",
            e
        )


# =========================
# СОХРАНЁННЫЕ ОБЪЯВЛЕНИЯ
# =========================

def load_seen():

    try:

        with open(
            SEEN_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return set(
                json.load(file)
            )

    except:

        return set()


def save_seen(seen):

    # Не даём файлу расти бесконечно

    data = list(seen)[-5000:]

    with open(
        SEEN_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False
        )


# =========================
# ОПРЕДЕЛЯЕМ МОДЕЛЬ
# =========================

def detect_model(title):

    title_lower = title.lower()

    # Сначала проверяем Pro Max,
    # чтобы он не определился как обычный Pro

    models = sorted(
        MODELS.keys(),
        key=len,
        reverse=True
    )

    for model in models:

        if model.lower() in title_lower:

            return model

    return None


# =========================
# ИЩЕМ ЦЕНУ
# =========================

def extract_price(text):

    if not text:
        return None

    # Убираем HTML-пробелы

    text = text.replace(
        "\xa0",
        " "
    )

    patterns = [
        r'(\d[\d\s]{2,})\s*(?:₽|руб|р\b)',
        r'(\d{4,6})\s*(?:₽|руб|р\b)'
    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        for value in matches:

            value = value.replace(
                " ",
                ""
            )

            try:

                price = int(value)

                if 5000 <= price <= 500000:

                    return price

            except:

                pass

    return None


# =========================
# ПОИСК AVITO
# =========================

def search_avito(model):

    query = quote(model)

    url = (
        "https://www.avito.ru/moskva/telefony"
        "?q=" + query
    )

    headers = {

        "User-Agent":
            "Mozilla/5.0 "
            "(Linux; Android 12) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/120.0 Mobile Safari/537.36",

        "Accept-Language":
            "ru-RU,ru;q=0.9"
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=30
        )

        print(
            model,
            "HTTP:",
            response.status_code
        )

        if response.status_code != 200:

            return []

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        results = []

        # Ищем ссылки на объявления

        for link in soup.find_all(
            "a",
            href=True
        ):

            href = link.get(
                "href",
                ""
            )

            if "/moskva/" not in href:

                continue

            if not any(
                part in href
                for part in [
                    "/telefony/",
                    "/iphone/"
                ]
            ):

                continue

            title = link.get_text(
                " ",
                strip=True
            )

            if not title:

                continue

            # Получаем ближайший блок
            # с текстом объявления

            parent = link

            for _ in range(5):

                if parent.parent:

                    parent = parent.parent

            block_text = parent.get_text(
                " ",
                strip=True
            )

            price = extract_price(
                block_text
            )

            if not price:

                continue

            if href.startswith("/"):

                href = (
                    "https://www.avito.ru"
                    + href
                )

            results.append({

                "title": title,

                "price": price,

                "url": href,

                "model": model

            })

            if len(results) >= MAX_RESULTS:

                break

        return results

    except Exception as e:

        print(
            "Ошибка Avito:",
            e
        )

        return []


# =========================
# РАСЧЁТ ЗАЗОРА
# =========================

def calculate_deal(item):

    model = item["model"]

    if model not in MODELS:

        return None

    settings = MODELS[model]

    buy_price = item["price"]

    sell_price = settings[
        "sell_price"
    ]

    max_buy = settings[
        "max_buy"
    ]

    # Резерв на торг,
    # мелкие расходы и риск

    reserve = 2000

    # Чистый предполагаемый зазор

    margin = (
        sell_price
        - buy_price
        - reserve
    )

    # Если цена покупки выше
    # нашего лимита — пропускаем

    if buy_price > max_buy:

        return None

    # Если зазор маленький —
    # тоже пропускаем

    if margin < MIN_MARGIN:

        return None

    return {

        "model": model,

        "title": item["title"],

        "buy": buy_price,

        "sell": sell_price,

        "reserve": reserve,

        "margin": margin,

        "url": item["url"]
    }


# =========================
# TELEGRAM СООБЩЕНИЕ
# =========================

def make_message(deal):

    margin = deal["margin"]

    if margin >= 10000:

        icon = "🔥"

    elif margin >= 7000:

        icon = "🟢"

    else:

        icon = "🟡"

    title = deal["title"][:180]

    return f"""
{icon} <b>НАЙДЕН ВЫГОДНЫЙ ТЕЛЕФОН</b>

📱 <b>{deal["model"]}</b>

📝 {title}

💰 Покупка:
<b>{deal["buy"]:,} ₽</b>

📈 Продажа:
<b>~{deal["sell"]:,} ₽</b>

💸 Резерв:
<b>{deal["reserve"]:,} ₽</b>

💵 ЗАЗОР:
<b>{deal["margin"]:,} ₽</b>

📍 Москва

🔗 <a href="{deal["url"]}">ОТКРЫТЬ ОБЪЯВЛЕНИЕ</a>
""".replace(",", " ")


# =========================
# ОСНОВНАЯ ПРОВЕРКА
# =========================

def main():

    print()
    print(
        "================================"
    )
    print(
        " AVITO PHONE MONITOR"
    )
    print(
        " Москва"
    )
    print(
        "================================"
    )
    print()

    if not BOT_TOKEN:

        print(
            "Нет BOT_TOKEN"
        )

        return

    if not CHAT_ID:

        print(
            "Нет CHAT_ID"
        )

        return

    seen = load_seen()

    total = 0

    deals = 0

    # Проверяем каждую модель

    for model in MODELS:

        print(
            "Проверяю:",
            model
        )

        listings = search_avito(
            model
        )

        print(
            "Объявлений:",
            len(listings)
        )

        for item in listings:

            total += 1

            # URL использу
