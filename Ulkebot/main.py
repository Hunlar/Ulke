import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = "ZeydOyunbot"  # Güncel bot kullanıcı adı

ERDOGAN_GIF_URL = "https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif"
ILHAM_ALIYEV_GIF_URL = "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Dil: Türkçe 🇹🇷", callback_data="lang_tr"),
            InlineKeyboardButton("Dil: Azərbaycan 🇦🇿", callback_data="lang_az"),
        ],
        [InlineKeyboardButton("Oyun Nasıl Oynanır?", callback_data="game_explain")],
        [InlineKeyboardButton("Komutlar", callback_data="commands")],
        [InlineKeyboardButton("Katıl", url=f"https://t.me/{BOT_USERNAME}")],
        [
            InlineKeyboardButton("Destek Grubu", url="https://t.me/kizilsancaktr"),
            InlineKeyboardButton("Geliştirici", url="https://t.me/ZeydBinhalit"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_animation(chat_id=update.effective_chat.id, animation=ERDOGAN_GIF_URL)

    await update.message.reply_text(
        "3. Dünya Savaşı'nda kader seni nereye götürecek, alman mı olacaksın Osmanlı mı yoksa pembe dünyayı seçen bir zavallı mı? Kader sana hangi rolü verecek?",
        reply_markup=reply_markup,
    )

async def katil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.effective_chat.type
    if chat_type != "private":
        await update.message.reply_text("Lütfen bu komutu bana özel mesajda kullanınız.")
        return
    user = update.effective_user
    # Burada katılım işlemlerini yapacaksın
    await update.message.reply_text(f"{user.first_name}, oyuna katıldın! Katılım süreci devam ediyor...")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "lang_tr":
        await query.edit_message_text("Dil Türkçe olarak ayarlandı.")
    elif query.data == "lang_az":
        await context.bot.send_animation(chat_id=query.message.chat.id, animation=ILHAM_ALIYEV_GIF_URL)
        await query.edit_message_text("Dil Azərbaycan olaraq ayarlandı.")
    elif query.data == "game_explain":
        await query.edit_message_text(
            "Oyun Nasıl Oynanır?\n"
            "1. /katil ile katıl\n"
            "2. /baslat ile başlat\n"
            "3. Oylama ve özel güçler"
        )
    elif query.data == "commands":
        await query.edit_message_text(
            "/start - Botu başlatır\n"
            "/katil - Oyuna katılır\n"
            "/baslat - Oyunu başlatır\n"
            "/iptal - Oyunu iptal eder\n"
            "/roles - Roller ve güçler hakkında bilgi verir\n"
            "/rol - Kendi rolünü gösterir\n"
            "/vote <ülke> - Oy verir\n"
            "/ozelguc <ülke> - Özel gücünü kullanır\n"
        )
    else:
        await query.edit_message_text("Bilinmeyen komut.")

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("katil", katil))
    application.add_handler(CallbackQueryHandler(button_handler))

    application.run_polling()

if __name__ == "__main__":
    main()
