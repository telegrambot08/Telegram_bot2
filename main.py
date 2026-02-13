from flask import Flask
from threading import Thread
import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ================= KEEP ALIVE =================
flask_app = Flask("")

@flask_app.route("/")
def home():
    return "Bot 24/7 ishlayapti"

def run():
    flask_app.run(host="0.0.0.0", port=8080)

Thread(target=run).start()

# ================= TEXTS =================
TEXTS = {
    "uz": {
        "start": "🇺 Uzbekistan",
        "welcome": "🎬 Send a video link or 🎵 song name",
        "error": "❌ No results found",
        "searching": "🔎 Searching...",
        "done": "Downloaded via @yourbot",
    }
}

# ================= /START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🇺🇿 Choose your language"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇺🇿 O‘zb", callback_data="lang_uz")]
    ])
    await update.message.reply_text(text, reply_markup=kb)

# ================= MAIN HANDLER =================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    lang = context.user_data.get("lang", "uz")
    await update.message.reply_text(TEXTS[lang]["searching"])

    ydl_opts = {"quiet": True, "extract_flat": True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(f"ytsearch10:{text}", download=False)
    except:
        await update.message.reply_text(TEXTS[lang]["error"])
        return

    entries = result.get("entries", [])[:10]
    if not entries:
        await update.message.reply_text(TEXTS[lang]["error"])
        return

    context.user_data["songs"] = entries

    msg = "Choose a song\n\n"
    buttons = []

    for i, e in enumerate(entries):
        msg += f"{i+1}. {e.get('title', 'Unknown')}\n"
        buttons.append(InlineKeyboardButton(str(i+1), callback_data=f"song_{i}"))

    keyboard = [buttons[i:i+5] for i in range(0, len(buttons), 5)]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

# ================= SONG DOWNLOAD =================
async def download_song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    lang = context.user_data.get("lang", "uz")
    index = int(q.data.split("_")[1])
    songs = context.user_data.get("songs")

    if not songs or index >= len(songs):
        await q.message.reply_text(TEXTS[lang]["error"])
        return

    song = songs[index]
    url = song["url"]

    await q.message.reply_text(TEXTS[lang]["searching"])

    ydl_opts = {
        "format": "bestaudio",
        "outtmpl": "song_%(id)s.%(ext)s",
        "quiet": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "128",
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = f"song_{info['id']}.mp3"

    await q.message.reply_audio(audio=open(filename, "rb"), title=info.get("title"))
    os.remove(filename)

# ================= MAIN =================
def main():
    BOT_TOKEN = os.environ.get("8263979816:AAGHp-orHyAJ6WAarHcCrNmU-i0HwhKPabI")

    app = ApplicationBuilder().token(8263979816:AAGHp-orHyAJ6WAarHcCrNmU-i0HwhKPabI).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(download_song, pattern="^song_"))

    app.run_polling()

if __name__ == "__main__":
    main()
