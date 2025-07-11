import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)

TOKEN = os.getenv("BOT_TOKEN")

katilim_listesi = set()
chat_lang = {}  # chat_id -> 'tr' veya 'az'


# Metinler
TEXTS = {
    "welcome": {
        "tr": "👋 Ülke Savaşları Botuna hoşgeldin!\n🎮 Oyuna katılmak için /katil komutunu kullanabilirsin.",
        "az": "👋 Ölkə Müharibəsi Botuna xoş gəlmisiniz!\n🎮 Oyuna qoşulmaq üçün /katil əmri verə bilərsiniz.",
    },
    "join_prompt": {
        "tr": "Oyuna katılmak için aşağıdaki butona tıklayın. Katılım 2 dakika sürecek.",
        "az": "Oyuna qoşulmaq üçün aşağıdakı düyməni basın. Qeydiyyat 2 dəqiqə davam edəcək.",
    },
    "already_joined": {
        "tr": "Zaten oyuna katıldınız.",
        "az": "Artıq oyuna qoşulmusunuz.",
    },
    "joined_success": {
        "tr": "Başarıyla katıldınız! Toplam oyuncu: {}",
        "az": "Uğurla qoşuldunuz! Ümumi oyunçu sayı: {}",
    },
    "choose_lang": {
        "tr": "Lütfen dilinizi seçin / Zəhmət olmasa dilinizi seçin",
        "az": "Lütfen dilinizi seçin / Zəhmət olmasa dilinizi seçin",
    },
    "game_explain": {
        "tr": (
            "🎲 **Oyun Nasıl Oynanır?**\n"
            "1. /katil ile oyuna katılın.\n"
            "2. Roller rastgele dağıtılır.\n"
            "3. Oylama turları ile oyuncular elenir.\n"
            "4. Özel güçlerinizi kullanarak rakiplerinizi saf dışı bırakın.\n"
            "5. Son hayatta kalan kazanır!"
        ),
        "az": (
            "🎲 **Oyun Necə Oynanır?**\n"
            "1. /katil ilə oyuna qoşulun.\n"
            "2. Rollar təsadüfi paylanır.\n"
            "3. Səsvermə turları ilə oyunçular çıxarılır.\n"
            "4. Xüsusi güclərinizi istifadə edərək rəqiblərinizi aradan qaldırın.\n"
            "5. Son sağ qalan qalib olur!"
        ),
    },
    "support_dev": {
        "tr": "Destek Grubu: t.me/kizilsancaktr\nGeliştirici: t.me/ZeydBinhalit",
        "az": "Dəstək Qrupu: t.me/kizilsancaktr\nİnkişaf etdirici: t.me/ZeydBinhalit",
    },
}

GIF_WELCOME = "https://media.giphy.com/media/3o7aD4n3dSlzDzpEsg/giphy.gif"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    keyboard = [
        [
            InlineKeyboardButton("Türkçe 🇹🇷", callback_data="lang_tr"),
            InlineKeyboardButton("Azərbaycanca 🇦🇿", callback_data="lang_az"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_animation(chat_id=chat_id, animation=GIF_WELCOME)
    await update.message.reply_text(TEXTS["choose_lang"]["tr"], reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    chat_id = query.message.chat.id
    user_id = query.from_user.id

    await query.answer()

    if data == "lang_tr":
        chat_lang[chat_id] = "tr"
        await query.edit_message_text(TEXTS["welcome"]["tr"], reply_markup=main_menu_keyboard("tr"))
    elif data == "lang_az":
        chat_lang[chat_id] = "az"
        await query.edit_message_text(TEXTS["welcome"]["az"], reply_markup=main_menu_keyboard("az"))

    elif data == "join_game":
        if user_id in katilim_listesi:
            await query.answer(TEXTS["already_joined"][chat_lang.get(chat_id, "tr")], show_alert=True)
        else:
            katilim_listesi.add(user_id)
            await query.edit_message_text(
                TEXTS["joined_success"][chat_lang.get(chat_id, "tr")].format(len(katilim_listesi)),
                reply_markup=main_menu_keyboard(chat_lang.get(chat_id, "tr"))
            )
    elif data == "game_explain":
        lang = chat_lang.get(chat_id, "tr")
        await query.edit_message_text(TEXTS["game_explain"][lang], parse_mode="Markdown", reply_markup=main_menu_keyboard(lang))


def main_menu_keyboard(lang):
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📝 Katıl", callback_data="join_game")],
            [InlineKeyboardButton("🎲 Oyun Nasıl Oynanır?", callback_data="game_explain")],
            [
                InlineKeyboardButton("Destek Grubu", url="https://t.me/kizilsancaktr"),
                InlineKeyboardButton("Geliştirici", url="https://t.me/ZeydBinhalit"),
            ],
        ]
    )


async def katil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    lang = chat_lang.get(chat_id, "tr")
    await update.message.reply_text(TEXTS["join_prompt"][lang], reply_markup=main_menu_keyboard(lang))


def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN ayarlanmalı!")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("katil", katil))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot çalışıyor...")
    app.run_polling()


if __name__ == "__main__":
    main()
