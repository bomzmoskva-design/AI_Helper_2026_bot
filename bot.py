import os
import json
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote


# ============================================================
# НАСТРОЙКИ
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Минимальный зазор, при котором присылаем объявление
MIN_MARGIN = 5000

# Резерв на торг/мелкие расходы
RESERVE = 2000

# Файл с уже просмотренными объявлениями
SEEN_FILE = "seen.json"


# ============================================================
# МОДЕЛИ ТЕЛЕФОНОВ
# ============================================================

MODELS = {

    "iPhone 11": {
        "sell": 20000,
        "max_buy": 15000
    },

    "iPhone 11 Pro": {
        "sell": 25000,
        "max_buy": 19000
    },

    "iPhone 11 Pro Max": {
        "sell": 28000,
        "max_buy": 22000
    },

    "iPhone 12": {
        "sell": 24000,
        "max_buy": 18000
    },

    "iPhone 12 Pro": {
        "sell": 28000,
        "max_buy": 22000
    },

    "iPhone 12 Pro Max": {
        "sell": 33000,
        "max_buy": 26000
    },

    "iPhone 13": {
        "sell": 28000,
        "max_buy": 22000
    },

    "iPhone 13 Pro": {
        "sell": 35000,
        "max_buy": 28000
    },

    "iPhone 13 Pro Max": {
        "sell": 40000,
        "max_buy": 32000
    },

    "iPhone 14": {
        "sell": 32000,
        "max_buy": 25000
    },

    "iPhone 14 Pro": {
        "sell": 43000,
        "max_buy": 35000
    },

    "iPhone 14 Pro Max": {
        "sell": 50000,
        "max_buy": 41000
    },

    "iPhone 15": {
        "sell": 43000,
        "max_buy": 35000
    },

    "iPhone 15 Pro": {
        "sell": 55000,
        "max_buy": 45000
    },

    "iPhone 15 Pro Max": {
        "sell": 65000,
        "max_buy": 54000
    },

    "iPhone 16": {
        "sell": 55000,
        "max_buy": 45000
    },

    "iPhone 16 Pro": {
        "sell": 65000,
        "max_buy": 55000
    },

    "iPhone 16 Pro Max": {
        "sell": 75000,
        "max_buy": 63000
    }
}


# ============================================================
# TELEGRAM
# ============================================================

def send_telegram(message):

    if not BOT_TOKEN:
        print("ОШИБКА: BOT_TOKEN не найден")
        return False

    if not CHAT_ID:
        print("ОШИБКА: CHAT_ID не найден")
        return False

    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/sendMessage"
    )

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

        if response.status_code == 200:
            return True

        print(
            "Ответ Telegram:",
            response.text
        )

        return False

    except Exception as e:

        print(
            "Ошибка Telegram:",
            e
        )

        return False


# ============================================================
# ПРОВЕРКА TELEGRAM
# ============================================================

def telegram_test():

    print("Проверяем Telegram...")

    message = (
        "🤖 <b>Avito Monitor запущен!</b>\n\n"
        "📍 Москва\n"
        "📱 Мониторинг телефонов\n"
        "🔎 Начинаю поиск выгодных объявлений."
    )

    return send_telegram(message)


# ============================================================
# СОХРАНЁННЫЕ ОБЪЯВЛЕНИЯ
# ============================================================

def load_seen():

    try:

        with open(
            SEEN_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

            if isinstance(data, list):
                return set(data)

    except Exception:
        pass

    return set()


def save_seen(seen):

    try:

        # Оставляем последние 5000
        data = list(seen)[-5000:]

        with open(
            SEEN_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2
            )

    except Exception as e:

        print(
            "Ошибка сохранения seen.json:",
            e
        )


# ============================================================
# ОПРЕДЕЛЕНИЕ МОДЕЛИ
# ============================================================

def detect_model(title):

    title_lower = title.lower()

    # Сначала длинные названия
    # чтобы Pro Max не определился как Pro

    models = sorted(
        MODELS.keys(),
        key=len,
        reverse=True
    )

    for model in models:

        if model.lower() in title_lower:

            return model

    return None


# ============================================================
# ИЗВЛЕЧЕНИЕ ЦЕНЫ
# ============================================================

def extract_price(text):

    if not text:
        return None

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

            except Exception:
                pass

    return None


# ============================================================
# ПОИСК AVITO
# ============================================================

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
            "ru-RU,ru;q=0.9",

        "Accept":
            "text/html,application/xhtml+xml"
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

        links = soup.find_all(
            "a",
            href=True
        )

        for link in links:

            href = link.get(
                "href",
                ""
            )

            if "/moskva/" not in href:
                continue

            if not (
                "/telefony/" in href
                or "/iphone/" in href
            ):
                continue

            title = link.get_text(
                " ",
                strip=True
            )

            if not title:
                continue

            # Получаем текст родительского блока

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

            if len(results) >= 30:
                break

        return results

    except Exception as e:

        print(
            "Ошибка поиска:",
            e
        )

        return []


# ============================================================
# РАСЧЁТ ЗАЗОРА
# ============================================================

def calculate_deal(item):

    model = item["model"]

    if model not in MODELS:
        return None

    settings = MODELS[model]

    buy_price = item["price"]

    sell_price = settings["sell"]

    max_buy = settings["max_buy"]

    # Цена покупки не должна быть
    # выше нашего лимита

    if buy_price > max_buy:
        return None

    margin = (
        sell_price
        - buy_price
        - RESERVE
    )

    # Минимальный зазор

    if margin < MIN_MARGIN:
        return None

    return {

        "model": model,

        "title": item["title"],

        "buy": buy_price,

        "sell": sell_price,

        "reserve": RESERVE,

        "margin": margin,

        "url": item["url"]
    }


# ============================================================
# ФОРМИРОВАНИЕ СООБЩЕНИЯ
# ============================================================

def make_message(deal):

    margin = deal["margin"]

    if margin >= 10000:
        icon = "🔥"

    elif margin >= 7000:
        icon = "🟢"

    else:
        icon = "🟡"

    title = (
        deal["title"]
        .replace("<", "")
        .replace(">", "")
    )

    title = title[:180]

    return (
        f"{icon} <b>ВЫГОДНОЕ ОБЪЯВЛЕНИЕ</b>\n\n"

        f"📱 <b>{deal['model']}</b>\n\n"

        f"📝 {title}\n\n"

        f"💰 Покупка: "
        f"<b>{deal['buy']:,} ₽</b>\n"

        f"📈 Продажа: "
        f"<b>~{deal['sell']:,} ₽</b>\n"

        f"💸 Резерв: "
        f"<b>{deal['reserve']:,} ₽</b>\n\n"

        f"💵 <b>ЗАЗОР: "
        f"{deal['margin']:,} ₽</b>\n\n"

        f"📍 Москва\n\n"

        f"🔗 <a href=\"{deal['url']}\">"
        f"ОТКРЫТЬ ОБЪЯВЛЕНИЕ"
        f"</a>"
    ).replace(",", " ")


# ============================================================
# ОСНОВНАЯ ПРОВЕРКА
# ============================================================

def main():

    print()
    print("=" * 50)
    print("AVITO PHONE MONITOR")
    print("Москва")
    print("=" * 50)
    print()

    # Проверяем переменные

    if not BOT_TOKEN:

        print("❌ BOT_TOKEN отсутствует")
        return

    if not CHAT_ID:

        print("❌ CHAT_ID отсутствует")
        return

    # Тест Telegram

    if not telegram_test():

        print(
            "❌ Telegram не отвечает."
        )

        return

    print(
        "✅ Telegram работает"
    )

    # Загружаем просмотренные объявления

    seen = load_seen()

    total = 0

    profitable = 0

    print()

    # Проверяем модели

    for model in MODELS:

        print(
            "🔎 Проверяю:",
            model
        )

        listings = search_avito(
            model
        )

        print(
            "   Найдено:",
            len(listings)
        )

        for item in listings:

            total += 1

            listing_id = item["url"]

            # Уже видели
            if listing_id in seen:
                continue

            seen.add(
                listing_id
            )

            deal = calculate_deal(
                item
            )

            if not deal:
                continue

            profitable += 1

            print()
            print(
                "🔥 НАЙДЕН ЗАЗОР!"
            )

            print(
                deal["model"]
            )

            print(
                "Покупка:",
                deal["buy"]
            )

            print(
                "Зазор:",
                deal["margin"]
            )

            send_telegram(
                make_message(deal)
            )

            time.sleep(1)

    # Сохраняем просмотренные

    save_seen(seen)

    print()
    print("=" * 50)
    print("ПРОВЕРКА ЗАВЕРШЕНА")
    print("=" * 50)

    print(
        "Всего объявлений:",
        total
    )

    print(
        "Выгодных:",
        profitable
    )

    print("=" * 50)


# ============================================================
# ЗАПУСК
# ============================================================

if __name__ == "__main__":

    main()
