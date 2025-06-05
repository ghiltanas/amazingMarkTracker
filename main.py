import os
import requests
from bs4 import BeautifulSoup
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")
URL = "https://www.amazon.it/dp/B0DRPSF34T"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
}
PREZZO_FILE = "prezzo_attuale.txt"
SOGLIA = float(os.getenv("SOGLIA", 800))
CHAT_ID = os.getenv("CHAT_ID")  # per uso automatico

def estrai_info():
    try:
        res = requests.get(URL, headers=HEADERS)
        soup = BeautifulSoup(res.content, 'html.parser')

        titolo_elem = soup.select_one("#productTitle")
        prezzo_elem = soup.select_one("span.a-price span.a-offscreen")
        img_elem = soup.select_one("#imgTagWrapperId img")

        if not (titolo_elem and prezzo_elem):
            return None, None, None

        titolo = titolo_elem.text.strip()
        prezzo = float(prezzo_elem.text.replace("€", "").replace(",", ".").strip())
        immagine = img_elem['src'] if img_elem else None

        return titolo, prezzo, immagine

    except Exception as e:
        print("Errore:", e)
        return None, None, None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Benvenuto! Usa /check per controllare il prezzo.")

async def id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Il tuo chat ID è: {update.effective_chat.id}")

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    titolo, prezzo, immagine = estrai_info()
    if prezzo is None:
        await update.message.reply_text("❌ Errore nel recupero del prezzo.")
        return

    if not os.path.exists(PREZZO_FILE):
        with open(PREZZO_FILE, "w") as f:
            f.write(str(prezzo))

    else:
        with open(PREZZO_FILE) as f:
            vecchio = float(f.read())

        if prezzo < vecchio:
            with open(PREZZO_FILE, "w") as f:
                f.write(str(prezzo))

    messaggio = (
        f"💻 <b>{titolo}</b>\n\n"
        f"💰 Prezzo attuale: <b>{prezzo}€</b>\n"
        f"🔗 <a href=\"{URL}\">Vai su Amazon</a>"
    )

    if immagine:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=immagine,
            caption=messaggio,
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(messaggio, parse_mode="HTML")

    if prezzo < SOGLIA:
        await update.message.reply_text(f"⚠️ Prezzo sotto la soglia di {SOGLIA}€!")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("check", check))
app.add_handler(CommandHandler("id", id))

app.run_polling()
