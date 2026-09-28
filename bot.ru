import os
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
AI_API_KEY = os.environ["AI_API_KEY"]

async def ask_ai(text):
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {AI_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": "Ты полезный русскоязычный ИИ-помощник."
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        },
        timeout=60
    )

    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    try:
        answer = await ask_ai(text)
        await update.message.reply_text(answer)
    except Exception:
        await update.message.reply_text(
            "Произошла ошибка при обращении к ИИ."
        )


app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
)

app.run_polling()
