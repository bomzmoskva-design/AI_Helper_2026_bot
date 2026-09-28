import os
import json
import re
import time
import html
from urllib.parse import quote_plus, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup


# ============================================================
# НАСТРОЙКИ
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

SEEN_FILE = "seen.json"

CITY = "Москва"

MODELS = {
    "iPhone 11": {
        "max_buy": 30000,
        "sell": 40000
    },
    "iPhone 11 Pro": {
        "max_buy": 35000,
        "sell": 48000
    },
    "iPhone 11 Pro Max": {
        "max_buy": 40000,
        "sell": 55000
    },
    "iPhone 12": {
        "max_buy": 35000,
        "sell": 48000
    },
    "iPhone 12 Pro": {
        "max_buy": 45000,
        "sell": 60000
    },
    "iPhone 12 Pro Max": {
        "max_buy": 50000,
        "sell": 70000
    },
    "iPhone 13": {
        "max_buy": 45000,
        "sell": 60000
    },
    "iPhone 13 Pro": {
        "max_buy": 55000,
        "sell": 75000
    },
    "iPhone 13 Pro Max": {
        "max_buy": 65000,
        "sell": 85000
    },
    "iPhone 14": {
        "max_buy": 55000,
        "sell": 70000
    },
    "iPhone 14 Pro": {
        "max_buy": 70000,
        "sell": 90000
    },
    "iPhone 14 Pro Max": {
        "max_buy": 80000,
        "sell": 105000
    },
    "iPhone 15": {
        "max_buy": 65000,
        "sell": 85000
    },
    "iPhone 15 Pro": {
        "max_buy": 80000,
        "sell": 105000
    },
    "iPhone 15 Pro Max": {
        "max_buy": 90000,
        "sell": 120000
    },
    "iPhone 16": {
        "max_buy": 75000,
        "sell": 95000
    },
    "iPhone 16 Pro": {
        "max_buy": 95000,
        "sell": 120000
    },
    "iPhone 16 Pro Max": {
        "max_buy": 110000,
        "sell": 140000
    }
}

RESERVE = 5000
MIN_MARGIN = 5000


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8"
}


# ============================================================
# TELEGRAM
# ============================================================

def send_telegram(message):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ BOT_TOKEN или CHAT_ID отсутствует")
        return False

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

        print("Telegram:", response.status_code)

        return response.status_code == 200

    except Exception as e:
        print("Ошибка Telegram:", e)
        return False


# ============================================================
# SEEN
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
        print("Ошибка seen.json:", e)


# ============================================================
# ЦЕНА
# ============================================================

def extract_price(text):
    if not text:
        return None

    text = text.replace("\xa0", " ")

    patterns = [
        r"(\d{1,3}(?:[\s]\d{3})+)\s*(?:₽|руб\.?|р\b)",
        r"(\d{4,6})\s*(?:₽|руб\.?|р\b)"
    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        for value in matches:

            value = re.sub(
                r"\s+",
                "",
                value
            )

            try:

                price = int(value)

                if 5000 <= price <= 500000:
                    return price

            except ValueError:
                pass

    return None


# ============================================================
# МОДЕЛЬ
# ============================================================

def detect_model(text):

    text_lower = text.lower()

    models = sorted(
        MODELS.keys(),
        key=len,
        reverse=True
    )

    for model in models:

        if model.lower() in text_lower:
            return model

    return None


# ============================================================
# URL
# ============================================================

def clean_url(url):

    if not url:
        return ""

    try:

        parsed = urlparse(url)

        params = parse_qs(
            parsed.query
        )

        if "uddg" in params:
            if params["uddg"]:
                url = params["uddg"][0]

    except Exception:
        pass

    return url


# ============================================================
# ПОИСК ЧЕРЕЗ BING
# ============================================================

def search_bing(model):

    query = (
        f'site:avito.ru/moskva/telefony '
        f'"{model}"'
    )

    url = (
        "https://www.bing.com/search?q="
        + quote_plus(query)
        + "&count=20"
    )

    print(
        "Bing запрос:",
        model
    )

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=25
        )

        print(
            "Bing HTTP:",
            response.status_code
        )

        if response.status_code != 200:
            return []

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        results = []

        for item in soup.select("li.b_algo"):

            link = item.select_one("h2 a")

            if not link:
                continue

            title = link.get_text(
                " ",
                strip=True
            )

            result_url = clean_url(
                link.get("href", "")
            )

            if "avito.ru" not in result_url:
                continue

            if "/moskva/" not in result_url:
                continue

            snippet = item.select_one(
                ".b_caption"
            )

            snippet_text = ""

            if snippet:
                snippet_text = snippet.get_text(
                    " ",
                    strip=True
                )

            full_text = (
                title
                + " "
                + snippet_text
            )

            price = extract_price(
                full_text
            )

            detected_model = detect_model(
                full_text
            )

            if not detected_model:
                detected_model = model

            results.append(
                {
                    "model": detected_model,
                    "title": title,
                    "price": price,
                    "url": result_url
                }
            )

        return results[:20]

    except Exception as e:

        print(
            "Ошибка Bing:",
            e
        )

        return []


# ============================================================
# ЗАПАСНОЙ ПОИСК — YANDEX
# ============================================================

def search_yandex(model):

    query = (
        f'site:avito.ru/moskva/telefony '
        f'"{model}"'
    )

    url = (
        "https://yandex.ru/search/?text="
        + quote_plus(query)
    )

    print(
        "Yandex запрос:",
        model
    )

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=25
        )

        print(
            "Yandex HTTP:",
            response.status_code
        )

        if response.status_code != 200:
            return []

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        results = []

        for item in soup.select(
            "li.serp-item"
        ):

            link = item.select_one(
                "a"
            )

            if not link:
                continue

            result_url = clean_url(
                link.get("href", "")
            )

            if "avito.ru" not in result_url:
                continue

            title_node = item.select_one(
                "h2"
            )

            if not title_node:
                continue

            title = title_node.get_text(
                " ",
                strip=True
            )

            full_text = item.get_text(
                " ",
                strip=True
            )

            price = extract_price(
                full_text
            )

            detected_model = detect_model(
                full_text
            )

            if not detected_model:
                detected_model = model

            results.append(
                {
                    "model": detected_model,
                    "title": title,
                    "price": price,
                    "url": result_url
                }
            )

        return results[:20]

    except Exception as e:

        print(
            "Ошибка Yandex:",
            e
        )

        return []


# ============================================================
# ПОИСК
# ============================================================

def search_listings(model):

    results = search_bing(model)

    if results:
        return results

    print(
        "Bing результатов нет."
    )

    results = search_yandex(model)

    return results


# ============================================================
# ПРОВЕРКА СДЕЛКИ
# ============================================================

def calculate_deal(item):

    model = item.get(
        "model"
    )

    price = item.get(
        "price"
    )

    if not model:
        return None

    if not price:
        return None

    if model not in MODELS:
        return None

    settings = MODELS[model]

    max_buy = settings["max_buy"]

    sell_price = settings["sell"]

    if price > max_buy:
        return None

    margin = (
        sell_price
        - price
        - RESERVE
    )

    if margin < MIN_MARGIN:
        return None

    return {
        "model": model,
        "title": item["title"],
        "buy": price,
        "sell": sell_price,
        "reserve": RESERVE,
        "margin": margin,
        "url": item["url"]
    }


# ============================================================
# TELEGRAM СООБЩЕНИЕ
# ============================================================

def make_message(deal):

    if deal["margin"] >= 10000:
        icon = "🔥"

    elif deal["margin"] >= 7000:
        icon = "🟢"

    else:
        icon = "🟡"

    title = html.escape(
        deal["title"][:180]
    )

    url = html.escape(
        deal["url"],
        quote=True
    )

    message = (
        f"{icon} "
        f"<b>ВЫГОДНОЕ ОБЪЯВЛЕНИЕ</b>\n\n"

        f"📱 <b>{html.escape(deal['model'])}</b>\n\n"

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

        f"🔗 "
        f'<a href="{url}">'
        f"ОТКРЫТЬ ОБЪЯВЛЕНИЕ"
        f"</a>"
    )

    return message.replace(
        ",",
        " "
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 50)

    print(
        "AVITO PHONE MONITOR"
    )

    print(
        "Москва"
    )

    print(
        "Поиск: Bing → Yandex"
    )

    print("=" * 50)

    if not BOT_TOKEN:

        print(
            "❌ BOT_TOKEN отсутствует"
        )

        return

    if not CHAT_ID:

        print(
            "❌ CHAT_ID отсутствует"
        )

        return

    started = send_telegram(
        "🤖 <b>Avito Monitor запущен!</b>\n\n"
        "📍 Москва\n"
        "📱 iPhone 11–16 Pro Max\n"
        "🔎 Новый поиск\n"
        "💰 Проверяю выгодные объявления..."
    )

    if not started:

        print(
            "❌ Telegram не работает"
        )

        return

    print(
        "✅ Telegram работает"
    )

    seen = load_seen()

    total = 0

    profitable = 0

    for model in MODELS:

        print()

        print(
            "🔎 Проверяю:",
            model
        )

        listings = search_listings(
            model
        )

        print(
            "   Результатов:",
            len(listings)
        )

        for item in listings:

            total += 1

            listing_id = item.get(
                "url"
            )

            if not listing_id:
                continue

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
                "Модель:",
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

    save_seen(
        seen
    )

    print()

    print("=" * 50)

    print(
        "ПРОВЕРКА ЗАВЕРШЕНА"
    )

    print(
        "Результатов:",
        total
    )

    print(
        "Выгодных:",
        profitable
    )

    print("=" * 50)

    send_telegram(
        "✅ <b>Проверка завершена</b>\n\n"
        f"📱 Результатов: <b>{total}</b>\n"
        f"🔥 Выгодных: <b>{profitable}</b>\n\n"
        "📍 Москва"
    )


if __name__ == "__main__":
    main()
