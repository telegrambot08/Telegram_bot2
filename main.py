import os
import yt_dlp
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

user_lang = {}
search_results = {}

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🇺🇿 Uzbek", callback_data="lang_uz"),
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        ]
    ]
    await update.message.reply_text(
        "O‘zingizga qulay tilni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= LANGUAGE =================

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = query.data.split("_")[1]
    user_lang[query.from_user.id] = lang

    text = {
        "uz": "🎬 Video havolasini yoki musiqa nomini yozing:",
        "ru": "🎬 Отправьте ссылку на видео или название песни:",
        "en": "🎬 Send video link or song name:"
    }

    keyboard = [
        [
            InlineKeyboardButton("ℹ️ Haqida", callback_data="about"),
            InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel")
        ]
    ]

    await query.edit_message_text(
        text[lang],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= ABOUT & CANCEL =================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "about":
        await query.edit_message_text("🎵 Bu bot YouTube dan musiqa va video yuklaydi.")
    elif query.data == "cancel":
        await query.edit_message_text("❌ Bekor qilindi.")

# ================= SEARCH =================

async def search_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_text = update.message.text
    user_id = update.message.from_user.id

    ydl_opts = {
        "quiet": True,
        "noplaylist": True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(
                f"ytsearch5:{query_text}",
                download=False
            ).get("entries", [])

        if not results:
            await update.message.reply_text("❌ Hech narsa topilmadi.")
            return

        search_results[user_id] = results

        text = "🎵 Topilgan qo‘shiqlar:\n\n"
        keyboard = []
        row = []

        for i, video in enumerate(results):
            text += f"{i+1}. {video['title']}\n"
            row.append(
                InlineKeyboardButton(str(i+1), callback_data=f"select_{i}")
            )
            if len(row) == 5:
                keyboard.append(row)
                row = []

        if row:
            keyboard.append(row)

        keyboard.append([
            InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel")
        ])

        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception:
        await update.message.reply_text("❌ Xatolik yuz berdi.")

# ================= SELECT VIDEO =================

async def select_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    index = int(query.data.split("_")[1])
    video = search_results[user_id][index]

    url = video["webpage_url"]

    keyboard = [
        [
            InlineKeyboardButton("🎵 Musiqani yuklab olish", callback_data=f"audio_{index}"),
            InlineKeyboardButton("➕ Guruhga qo‘shish", url="https://t.me/YOUR_BOT_USERNAME?startgroup=true")
        ]
    ]

    await query.message.reply_video(
        video=url,
        caption=video["title"],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= DOWNLOAD AUDIO =================

async def download_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    index = int(query.data.split("_")[1])
    video = search_results[user_id][index]

    filename = f"{user_id}_song.%(ext)s"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": filename,
        "quiet": True,
        "noplaylist": True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video["webpage_url"]])

        for file in os.listdir():
            if file.startswith(f"{user_id}_song"):
                await query.message.reply_audio(
                    audio=open(file, "rb"),
                    title=video["title"]
                )
                os.remove(file)
                break

    except Exception:
        await query.message.reply_text("❌ Yuklab bo‘lmadi.")

# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(
        os.environ.get("BOT_TOKEN")
    ).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(set_language, pattern="lang_"))
    app.add_handler(CallbackQueryHandler(buttons, pattern="about|cancel"))
    app.add_handler(CallbackQueryHandler(select_video, pattern="select_"))
    app.add_handler(CallbackQueryHandler(download_audio, pattern="audio_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_music))

    app.run_polling()

if __name__ == "__main__":
    main()
