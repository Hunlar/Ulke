"" import logging import os import json from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaAnimation from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler

Logging ayarları

logging.basicConfig( format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO )

Ortamdan TOKEN al

TOKEN = os.environ.get("BOT_TOKEN")

Sabit bağlantılar

DESTEK_GRUBU = "https://t.me/kizilsancaktr" GELISTIRICI = "https://t.me/ZeydBinhalit" BOT_LINK = "https://t.me/ZeydOyunbot"

Roller dosyasını oku

def load_roles(): with open("roles.json", encoding="utf-8") as f: return json.load(f)

Komutlar mesajı

def get_command_list(): return ( "<b>✨ Komutlar:</b>\n" "/start - Başlangıç\n" "/katil - Oyuna katıl\n" "/roles - Tüm ülkeleri gör\n" "/iptal - Oyunu iptal et (yönetici)" )

Start komutu

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): keyboard = [ [ InlineKeyboardButton("🇹🇷 Türkçe", callback_data='lang_tr'), InlineKeyboardButton("🇦🇿 Azərbaycan", callback_data='lang_az') ], [ InlineKeyboardButton("🗺 Komutlar", callback_data='commands'), InlineKeyboardButton("📜 Roller", callback_data='roles') ], [ InlineKeyboardButton("🎮 Katıl", url=BOT_LINK) ] ] reply_markup = InlineKeyboardMarkup(keyboard)

await context.bot.send_animation(
    chat_id=update.effective_chat.id,
    animation="https://media.tenor.com/hQzEJZ_gJfoAAAAC/world-war-3-ww3.gif",
    caption=(
        "<b>3. Dünya Savaşı'nda kader seni nereye götürecek?</b>\n"
        "Alman mı olacaksın, Osmanlı mı yoksa pembe dünyayı seçen bir zavallı mı?\n"
        "Kader sana hangi rolü verecek?\n\n"
        f"🔗 <b>Destek Grubu:</b> <a href='{DESTEK_GRUBU}'>kizilsancaktr</a>\n"
        f"🤝 <b>Geliştirici:</b> <a href='{GELISTIRICI}'>ZeydBinhalit</a>"
    ),
    parse_mode="HTML",
    reply_markup=reply_markup
)

Callback button handler

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE): query = update.callback_query await query.answer()

if query.data == "lang_tr":
    await query.edit_message_media(
        media=InputMediaAnimation(
            media="https://media.tenor.com/qEKjTO4_4v0AAAAC/recep-tayyip-erdo%C4%9Fan-%C3%A7ay.gif"
        ),
        reply_markup=query.message.reply_markup
    )
elif query.data == "lang_az":
    await query.edit_message_media(
        media=InputMediaAnimation(
            media="https://media.tenor.com/WddwdQ2Og_gAAAAd/ilham-aliyev.gif"
        ),
        reply_markup=query.message.reply_markup
    )
elif query.data == "commands":
    await query.edit_message_caption(
        caption=get_command_list(),
        parse_mode="HTML"
    )
elif query.data == "roles":
    roles = load_roles()
    text = "<b>Ülkeler ve Özel Güçler:</b>\n"
    for role in roles:
        text += f"\n<b>{role['name']}</b>: {role['power']}"
    await query.edit_message_caption(caption=text, parse_mode="HTML")

/roles komutu

async def roles_command(update: Update, context: ContextTypes.DEFAULT_TYPE): if update.effective_chat.type != "private": await update.message.reply_text("Bu komutu botun özel mesajında kullanmalısın! @ZeydOyunbot") return

roles = load_roles()
text = "<b>Ülkeler ve Özel Güçler:</b>\n"
for role in roles:
    text += f"\n<b>{role['name']}</b>: {role['power']}"
await update.message.reply_text(text, parse_mode="HTML")

/katil komutu – PM kontrolü ile

async def katil(update: Update, context: ContextTypes.DEFAULT_TYPE): if update.effective_chat.type != "private": await update.message.reply_text("Katılmak için botun özeline gel! @ZeydOyunbot") return await update.message.reply_text("Katılım başladı! Rolüne hazır ol...")

/iptal sadece grup ve admin kontrolü

async def iptal(update: Update, context: ContextTypes.DEFAULT_TYPE): if update.effective_chat.type == "private": await update.message.reply_text("Bu komut sadece grup içinde kullanılabilir.") return member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id) if member.status not in ["administrator", "creator"]: await update.message.reply_text("Sadece yöneticiler oyunu iptal edebilir!") return await update.message.reply_text("Oyun iptal edildi.")

Ana fonksiyon

def main(): app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(CommandHandler("roles", roles_command))
app.add_handler(CommandHandler("katil", katil))
app.add_handler(CommandHandler("iptal", iptal))

app.run_polling()

if name == "main": main()

