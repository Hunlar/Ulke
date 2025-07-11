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

# Global değişkenler
katilim_listesi = set()
chat_lang = {}  # chat_id -> 'tr' veya 'az'

oy_kayitlari = {}  # user_id -> oy verdiği kişi/ülke id
oylama_aktif = False
oylama_katilimcilar = set()

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
    "vote_prompt": {
        "tr": "Lütfen oyunu kullanmak için aşağıdaki butonlardan birine tıklayın:",
        "az": "Zəhmət olmasa aşağıdakı düymələrdən birinə basaraq səs verin:",
    },
    "vote_received": {
        "tr": "Oyunuz alındı: {}",
        "az": "Səsiniz qeydə alındı: {}",
    },
    "vote_closed": {
        "tr": "Oylama kapandı!",
        "az": "Səsvermə bitdi!",
    },
    "vote_no_active": {
        "tr": "Şu anda oylama aktif değil.",
        "az": "Hal-hazırda səsvermə aktiv deyil.",
    }
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


async def main_menu_keyboard(lang):
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
    await update.message.reply_text(TEXTS["join_prompt"][lang], reply_markup=await main_menu_keyboard(lang))


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global oylama_aktif
    query = update.callback_query
    data = query.data
    chat_id = query.message.chat.id
    user_id = query.from_user.id

    await query.answer()

    if data == "lang_tr":
        chat_lang[chat_id] = "tr"
        await query.edit_message_text(TEXTS["welcome"]["tr"], reply_markup=await main_menu_keyboard("tr"))
    elif data == "lang_az":
        chat_lang[chat_id] = "az"
        await query.edit_message_text(TEXTS["welcome"]["az"], reply_markup=await main_menu_keyboard("az"))

    elif data == "join_game":
        if user_id in katilim_listesi:
            await query.answer(TEXTS["already_joined"][chat_lang.get(chat_id, "tr")], show_alert=True)
        else:
            katilim_listesi.add(user_id)
            await query.edit_message_text(
                TEXTS["joined_success"][chat_lang.get(chat_id, "tr")].format(len(katilim_listesi)),
                reply_markup=await main_menu_keyboard(chat_lang.get(chat_id, "tr")),
            )

    elif data == "game_explain":
        lang = chat_lang.get(chat_id, "tr")
        await query.edit_message_text(TEXTS["game_explain"][lang], parse_mode="Markdown", reply_markup=await main_menu_keyboard(lang))

    elif data.startswith("oy_"):
        if not oylama_aktif:
            await query.answer(TEXTS["vote_no_active"][chat_lang.get(chat_id, "tr")], show_alert=True)
            return
        secilen = data[3:]
        oy_kayitlari[user_id] = secilen
        await query.edit_message_text(TEXTS["vote_received"][chat_lang.get(chat_id, "tr")].format(secilen))

    else:
        await query.answer("Bilinmeyen komut.", show_alert=True)


async def start_vote(context: ContextTypes.DEFAULT_TYPE):
    global oylama_aktif, oy_kayitlari, oylama_katilimcilar
    oylama_aktif = True
    oy_kayitlari = {}
    oylama_katilimcilar = katilim_listesi.copy()

    for user_id in oylama_katilimcilar:
        secenekler = [str(uid) for uid in oylama_katilimcilar if uid != user_id]
        keyboard = [[InlineKeyboardButton(f"Ülke {uid}", callback_data=f"oy_{uid}")] for uid in secenekler]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=user_id,
            text=TEXTS["vote_prompt"][chat_lang.get(user_id, "tr")],
            reply_markup=reply_markup,
        )

    # Örnek: 40 saniye sonra oylama bitirilsin
    context.job_queue.run_once(end_vote, 40, context=None)


async def end_vote(context: ContextTypes.DEFAULT_TYPE):
    global oylama_aktif
    oylama_aktif = False

    # Oyları say
    oy_sayaci = {}
    for oy in oy_kayitlari.values():
        oy_sayaci[oy] = oy_sayaci.get(oy, 0) + 1

    # En çok oyu alan
    if not oy_sayaci:
        mesaj = "Kimse oy kullanmadı."
    else:
        max_oy = max(oy_sayaci.values())
        kazananlar = [k for k, v in oy_sayaci.items() if v == max_oy]
        mesaj = f"Oylama kapandı! En çok oy alanlar: {', '.join(kazananlar)}"

    # Tüm katılımcılara mesaj gönder
    for user_id in oylama_katilimcilar:
        try:
            await context.bot.send_message(chat_id=user_id, text=mesaj)
        except Exception:
            pass


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
