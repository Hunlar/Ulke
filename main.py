import os
import random
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
oy_kayitlari = {}  # user_id -> oy verdiği kişi/ülke id
oylama_aktif = False
oylama_katilimcilar = set()
oyuncu_rolleri = {}

roles = {
    "Osmanlı İmparatorluğu": "2 ülkeyi saf dışı bırakabilir fakat aynı oylamada değil, her 2 oylamada bir 1 ülkeyi saf dışı bırakabilir.",
    "German İmparatorluğu": "2 oylamada bir kaos çıkartıp sadece kendisi oy kullanabilir.",
    "Biritanya": "İstediği ülkenin oylamada tercihlerini manipüle edebilir.",
    "Renkli Dünya": "Kimse ne olduğunu bilmez, meydan okur.",
    "Fransa": "Ekonomik sabotaj gücüne sahiptir, rakipleri zayıflatır.",
    "Rusya": "Güçlü askeri saldırı yapabilir, 1 tur boyunca çift oy kullanır.",
    "Çin": "Teknolojik üstünlük sağlar, rakip oylarını bloke eder.",
    "Japonya": "Hızlı saldırı yapar, oy verme süresini kısaltır.",
    "İtalya": "Diplomasi ile diğerlerini etkiler, oyları değiştirebilir.",
    "ABD": "Yüksek hava gücü ile 1 oylamada 2 ülkeyi etkisiz hale getirir.",
    "İspanya": "Gizli istihbarat toplar, diğer oyuncuların rollerini öğrenir.",
    "Hindistan": "Sosyal hareketler çıkarır, oylamayı etkiler.",
    "Brezilya": "Kaynakları kontrol eder, oy haklarını artırır.",
    "Mısır": "Tarihi etkisiyle rakiplerin oylarını azaltır.",
    "Yunanistan": "Savunma gücü yüksektir, 1 tur koruma sağlar.",
    "İsveç": "Nötr politikalar uygular, oylar tarafsızdır.",
    "Norveç": "Doğal engeller yaratır, rakip hareketlerini sınırlar.",
    "Kanada": "Uluslararası destek verir, ittifak kurar."
}

START_TEXT = (
    "3. Dünya Savaşı'nda kader seni nereye götürecek, "
    "alman mı olacaksın Osmanlı mı yoksa pembe dünyayı seçen bir zavallı mı? "
    "Kader sana hangi rolü verecek?"
)

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
        "tr": "Lütfen dilinizi seçin",
        "az": "Zəhmət olmasa dilinizi seçin",
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
    "vote_no_active": {
        "tr": "Şu anda oylama aktif değil.",
        "az": "Hal-hazırda səsvermə aktiv deyil.",
    },
    "vote_received": {
        "tr": "Oyunuz alındı: {}",
        "az": "Səsiniz qeydə alındı: {}",
    },
    "vote_prompt": {
        "tr": "Lütfen oy vermek için aşağıdaki butonlardan birine tıklayın:",
        "az": "Səs vermək üçün aşağıdakı düymələrdən birinə basın:",
    },
    "no_role": {
        "tr": "Henüz rolünüz atanmamış veya oyuna katılmamışsınız.",
        "az": "Hələ rolunuz təyin edilməyib və ya oyuna qoşulmamısınız.",
    },
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Türkçe 🇹🇷", callback_data="lang_tr"),
            InlineKeyboardButton("Azərbaycanca 🇦🇿", callback_data="lang_az"),
        ],
        [
            InlineKeyboardButton("📝 Katıl", callback_data="join_game"),
            InlineKeyboardButton("📜 Komutlar", callback_data="show_roles"),
        ],
        [
            InlineKeyboardButton("🎲 Oyun Nasıl Oynanır?", callback_data="game_explain"),
        ],
        [
            InlineKeyboardButton("Destek Grubu", url="https://t.me/kizilsancaktr"),
            InlineKeyboardButton("Geliştirici", url="https://t.me/ZeydBinhalit"),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # 1. GIF gönder
    gif_url = "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif"
    await context.bot.send_animation(
        chat_id=update.effective_chat.id,
        animation=gif_url
    )

    # 2. Butonlu mesajı ayrı gönder (buton tıklanma sorununu önlemek için)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=START_TEXT,
        reply_markup=reply_markup
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    chat_id = query.message.chat_id

    await query.answer()

    if data == "lang_tr":
        chat_lang[chat_id] = "tr"
        await query.edit_message_text(TEXTS["welcome"]["tr"])
    elif data == "lang_az":
        chat_lang[chat_id] = "az"
        await query.edit_message_text(TEXTS["welcome"]["az"])
    elif data == "join_game":
        if user_id in katilim_listesi:
            await query.answer(TEXTS["already_joined"][chat_lang.get(chat_id, "tr")], show_alert=True)
        else:
            katilim_listesi.add(user_id)
            await query.edit_message_text(TEXTS["joined_success"][chat_lang.get(chat_id, "tr")].format(len(katilim_listesi)))
    elif data == "show_roles":
        msg = "🎭 Oyundaki Roller:\n" + "\n".join(f"- {rol}" for rol in roles.keys())
        await query.edit_message_text(msg)
    elif data == "game_explain":
        lang = chat_lang.get(chat_id, "tr")
        await query.edit_message_text(TEXTS["game_explain"][lang], parse_mode="Markdown")
    elif data.startswith("oy_"):
        if not oylama_aktif:
            await query.answer(TEXTS["vote_no_active"][chat_lang.get(chat_id, "tr")], show_alert=True)
            return
        secilen = data[3:]
        oy_kayitlari[user_id] = secilen
        await query.edit_message_text(TEXTS["vote_received"][chat_lang.get(chat_id, "tr")].format(secilen))


async def katil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = chat_lang.get(update.effective_chat.id, "tr")
    await update.message.reply_text(TEXTS["join_prompt"][lang])


async def roller_listesi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mesaj = "🎭 Oyundaki Roller:\n" + "\n".join(f"- {rol}" for rol in roles.keys())
    await update.message.reply_text(mesaj)


async def rol_goster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    rol = oyuncu_rolleri.get(user_id)
    if rol:
        mesaj = f"🎭 Rolünüz: {rol}\nGüç: {roles[rol]}"
    else:
        mesaj = TEXTS["no_role"]["tr"]
    await update.message.reply_text(mesaj)


def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN tanımlı değil!")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("katil", katil))
    app.add_handler(CommandHandler("roles", roller_listesi))
    app.add_handler(CommandHandler("rol", rol_goster))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot çalışıyor...")
    app.run_polling()


if __name__ == "__main__":
    main()
