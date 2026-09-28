import os
import json
import re
import time
import html
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlparse, parse_qs


# ============================================================
# НАСТРОЙКИ
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

MIN_MARGIN = 5000
RESERVE = 2000
SEEN_FILE = "seen.json"


# ============================================================
# МОДЕЛИ IPHONE
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
# HTTP
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    ),

    "Accept-Language":
        "ru-RU,ru;q=0.9,en;q=0.8",

    "Accept":
        "text/html,application/xhtml+xml"
}


# ============================================================
# TELEGRAM
# ============================================================

def send_telegram(message):

    if not BOT_TOKEN:
        print("❌ BOT_TOKEN отсутствует")
        return False

    if not CHAT_ID:
        print("❌ CHAT_ID отсутствует")
        return False

    url = (
        "https://api.telegram.org/"
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

        if response.status_code != 200:

            print(
                response.text[:500]
            )

        return response.status_code == 200

    except Exception as e:

        print(
            "Ошибка Telegram:",
            e
        )

        return False


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
            "Ошибка seen.json:",
            e
        )


# ============================================================
# ЦЕНА
# ============================================================

def extract_price(text):

    if not text:
        return None

    text = text.replace(
        "\xa0",
        " "
    )

    patterns = [

        r"(\d{1,3}(?:[\s\u00a0]\d{3})+)"
        r"\s*(?:₽|руб\.?|р\b)",

        r"(\d{4,6})"
        r"\s*(?:₽|руб\.?|р\b)"
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
# ОПРЕДЕЛЕНИЕ МОДЕЛИ
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
# ОЧИСТКА ССЫЛКИ
# ============================================================

def clean_result_url(url):

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
# ПОИСК
# ============================================================

def search_duckduckgo(model):

    query = (
        f'site:avito.ru/moskva/telefony '
        f'"{model}" "₽"'
    )

    url = (
        "https://html.duckduckgo.com/html/?q="
        + quote_plus(query)
    )

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=25
        )

        print(
            model,
            "DDG HTTP:",
            response.status_code
        )

        if response.status_code != 200:

            return []

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        results = []

        items = soup.select(
            ".result"
        )

        for item in items:

            link = item.select_one(
                ".result__a"
            )

            snippet = item.select_one(
                ".result__snippet"
            )

            if not link:
                continue

            title = link.get_text(
                " ",
                strip=True
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

            result_url = clean_result_url(
                link.get("href", "")
            )

            if "avito.ru" not in result_url:
                continue

            if "/moskva/" not in result_url:
                continue

            price = extract_price(
                full_text
            )

            if not price:
                continue

            detected_model = detect_model(
                full_text
            )

            if not detected_model:

                detected_model = model

            results.append({

                "model":
                    detected_model,

                "title":
                    title,

                "price":
                    price,

                "url":
                    result_url
            })

        return results[:10]

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

    if buy_price > max_buy:

        return None

    margin = (
        sell_price
        - buy_price
        - RESERVE
    )

    if margin < MIN_MARGIN:

        return None

    return {

        "model":
            model,

        "title":
            item["title"],

        "buy":
            buy_price,

        "sell":
            sell_price,

        "reserve":
            RESERVE,

        "margin":
            margin,

        "url":
            item["url"]
    }


# ============================================================
# TELEGRAM-СООБЩЕНИЕ
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

        f"📱 <b>"
        f"{html.escape(deal['model'])}"
        f"</b>\n\n"

        f"📝 {title}\n\n"

        f"💰 Покупка: "
        f"<b>{deal['buy']:,} ₽</b>\n"

        f"📈 Продажа: "
        f"<b>~{deal['sell']:,} ₽</b>\n"

        f"💸 Резерв: "
        f"<b>{deal['reserve']:,} ₽</b>\n\n"

        f"💵 <b>ЗАЗОР: "
        f"{deal['margin']:,} ₽"
        f"</b>\n\n"

        f"📍 Москва\n\n"

        f"🔗 <a href=\"{url}\">"
        f"ОТКРЫТЬ ОБЪЯВЛЕНИЕ"
        f"</a>"
    )

    return message.replace(
        ",",
        " "
    )


# ============================================================
# ОСНОВНАЯ ФУНКЦИЯ
# ============================================================

def main():

    print(
        "=" * 50
    )

    print(
        "AVITO PHONE MONITOR"
    )

    print(
        "Москва"
    )

    print(
        "Поиск через поисковую выдачу"
    )

    print(
        "=" * 50
    )

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

    # --------------------------------------------------------
    # TELEGRAM TEST
    # --------------------------------------------------------

    started = send_telegram(

        "🤖 <b>Avito Monitor запущен!</b>\n\n"

        "📍 Москва\n"

        "📱 iPhone 11–16 Pro Max\n"

        "🔎 Поиск через поисковую выдачу\n"

        "💰 Проверяю зазор..."
    )

    if not started:

        print(
            "❌ Telegram не работает"
        )

        return

    print(
        "✅ Telegram работает"
    )

    # --------------------------------------------------------
    # БАЗА
    # --------------------------------------------------------

    seen = load_seen()

    total = 0

    profitable = 0

    # --------------------------------------------------------
    # ПОИСК
    # --------------------------------------------------------

    for model in MODELS:

        print()

        print(
            "🔎 Проверяю:",
            model
        )

        listings = search_duckduckgo(
            model
        )

        print(
            "   Результатов:",
            len(listings)
        )

        for item in listings:

            total += 1

            listing_id = item["url"]

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

        time.sleep(2)

    # --------------------------------------------------------
    # СОХРАНЕНИЕ
    # --------------------------------------------------------

    save_seen(
        seen
    )

    # --------------------------------------------------------
    # ИТОГ
    # --------------------------------------------------------

    print()

    print(
        "=" * 50
    )

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

    print(
        "=" * 50
    )

    send_telegram(

        "✅ <b>Проверка завершена</b>\n\n"

        f"📱 Результатов: "
        f"<b>{total}</b>\n"

        f"🔥 Выгодных: "
        f"<b>{profitable}</b>\n\n"

        "📍 Москва"
    )


# ============================================================
# ЗАПУСК
# ============================================================

if __name__ == "__main__":

    main()
