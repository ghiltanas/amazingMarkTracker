import os
import requests
from bs4 import BeautifulSoup
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")
URL = "https://www.amazon.it/dp/B0DRPSF34T"
HEADERS = {"User-Agent": "Mozilla/5.0"}
SOGLIA = float(os.getenv("SOGLIA", 370))  # valore soglia configurabile
CHAT_ID = os.getenv("CHAT_ID")  # il tuo ID per invii automatici

def estrai_info():
    res = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(res.content, 'html.parser')

    try:
        titolo = soup.select_one("#productTitle").text.strip()
        prezzo_elem = soup.select_one("span.a-price span.a-offscreen")
        img_elem = soup.select_one("#imgTagWrapperId img")
        
        prezzo_str = prezzo_elem.text.replace("€", "").replace(",", ".").strip()
        prezzo = float(prezzo_str)
        immagine = img_elem['src'] if img_elem else ""
        return titolo, prezzo, immagine
    except Exception as e:
        print("Errore:", e)
        return None, None, None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Benvenuto! Usa /check per controllare il prezzo.")

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    titolo, prezzo, img = estrai_info()
    if not prezzo:
        await update.message.reply_text("❌ Errore nel recupero del prezzo.")
        return

    messaggio = f"💻 <b>{titolo}</b>\n\n💰 Prezzo attuale: <b>{prezzo}€</b>\n\n🔗 <a href=\"{URL}\">Vai su Amazon</a>"
    
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=img,
        caption=messaggio,
        parse_mode="HTML"
    )

    if prezzo < SOGLIA:
        await update.message.reply_text(f"⚠️ Il prezzo è sotto la soglia di {SOGLIA}€!")

async def check_auto():
    titolo, prezzo, img = estrai_info()
    if not prezzo or not CHAT_ID:
        return

    if prezzo < SOGLIA:
        messaggio = f"📉 <b>{titolo}</b>\n\n💰 Nuovo prezzo: <b>{prezzo}€</b>\nSotto la soglia di {SOGLIA}€!\n\n🔗 <a href=\"{URL}\">Vai su Amazon</a>"
        bot = Bot(token=TOKEN)
        await bot.send_photo(chat_id=CHAT_ID, photo=img, caption=messaggio, parse_mode="HTML")

async def id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Il tuo chat ID è: {update.effective_chat.id}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("id", id))
    app.run_polling()
