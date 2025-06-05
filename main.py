import os
import re
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")
URL = "https://www.amazon.it/dp/B0DRPSF34T"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept-Language": "it-IT,it;q=0.9"
}
PREZZO_FILE = "prezzo_attuale.txt"

def estrai_info():
    try:
        res = requests.get(URL, headers=HEADERS)
        soup = BeautifulSoup(res.content, 'html.parser')

        titolo_elem = soup.select_one("#productTitle")
        img_elem = soup.select_one("#imgTagWrapperId img")
        titolo = titolo_elem.text.strip() if titolo_elem else "Prodotto Amazon"
        immagine = img_elem['src'] if img_elem else None

        prezzo = None
        venditore = "Non specificato"

        # 🔍 Cerca prezzo principale con Prime
        prime_price = soup.select_one("span.a-price span.a-offscreen")
        prime_badge = soup.select_one("i.a-icon-prime")

        if prime_price and prime_badge:
            prezzo = float(prime_price.text.replace("€", "").replace(",", ".").strip())

        # 🔁 Fallback: cerca altre offerte con "Prime"
        if not prezzo:
            alternative = soup.find_all("span", string=re.compile(r"da .*€.*Prime"))
            for alt in alternative:
                match = re.search(r"(\d+,\d{2})", alt.text)
                if match:
                    prezzo = float(match.group(1).replace(",", "."))
                    break

        # 📦 Recupera venditore, se disponibile
        venditore_elem = soup.select_one("#merchant-info")
        if venditore_elem:
            venditore = venditore_elem.text.strip()
            venditore = re.sub(r"\s+", " ", venditore)  # pulizia spazi

        return titolo, prezzo, immagine, venditore

    except Exception as e:
        print("❌ Errore estrazione:", e)
        return None, None, None, None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Usa /check per controllare se il prezzo è calato.")

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    titolo, prezzo, img, venditore = estrai_info()
    if prezzo is None:
        await update.message.reply_text("❌ Errore nel recupero del prezzo.")
        return

    if not os.path.exists(PREZZO_FILE):
        with open(PREZZO_FILE, "w") as f:
            f.write(str(prezzo))
        await update.message.reply_photo(
            photo=img,
            caption=f"📦 <b>{titolo}</b>\n\n💰 Prezzo attuale: <b>{prezzo}€</b>\n👤 Venditore: <i>{venditore}</i>\n\n🔗 <a href=\"{URL}\">Vai su Amazon</a>",
            parse_mode="HTML"
        )
        return

    with open(PREZZO_FILE) as f:
        vecchio = float(f.read())

    if prezzo < vecchio:
        with open(PREZZO_FILE, "w") as f:
            f.write(str(prezzo))
        await update.message.reply_photo(
            photo=img,
            caption=f"🎉 <b>Il prezzo è sceso!</b>\n\n💰 Da <s>{vecchio}€</s> a <b>{prezzo}€</b>\n👤 Venditore: <i>{venditore}</i>\n\n🔗 <a href=\"{URL}\">Vai su Amazon</a>",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_photo(
            photo=img,
            caption=f"🔍 <b>Nessuna variazione positiva</b>\n\n💰 Prezzo attuale: <b>{prezzo}€</b>\n👤 Venditore: <i>{venditore}</i>\n\n🔗 <a href=\"{URL}\">Vai su Amazon</a>",
            parse_mode="HTML"
        )

# ✅ Setup bot
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("check", check))
app.run_polling()