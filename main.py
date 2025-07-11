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

roles = {
    "Osmanlı İmparatorluğu": {
        "power_desc": "2 oylamada 1 ülkeyi saf dışı bırakabilir (aynı oylamada 2 değil).",
        "power_key": "osmanli_el",
    },
    "German İmparatorluğu": {
        "power_desc": "2 oylamada 1 kez kaos çıkartır, sadece kendisi oy kullanabilir.",
        "power_key": "german_kaos",
    },
    "Biritanya": {
        "power_desc": "Bir ülkenin oylama tercihlerini manipüle edebilir.",
        "power_key": "biritanya_manipulasyon",
    },
    "Renkli Dünya": {
        "power_desc": "Kimse ne olduğunu bilmez, meydan okur.",
        "power_key": "renkli_dunya_meydan",
    },
    # Diğer ülkeler eklenmeli burada...
}

katilim_listesi = set()
oyuncu_rolleri = {}
oylama_turu = 0
oylama_aktif = False
oylama_katilimlar = set()
oy_kayitlari = {}
ozel_guc_kullanilabilir = set()
guc_kullanimi_yapildi = {}

TEXTS = {
    "start": "3. Dünya Savaşı'nda kader seni nereye götürecek, alman mı olacaksın Osmanlı mı yoksa pembe dünyayı seçen bir zavallı mı? Kader sana hangi rolü verecek?",
    "welcome": "Ülke Savaşları Botuna hoşgeldin! /katil ile oyuna katılabilirsin.",
    "already_joined": "Zaten oyuna katıldınız.",
    "joined_success": "Başarıyla katıldınız! Toplam oyuncu: {}",
    "not_enough_players": "Oyuna başlamak için en az 6 oyuncu gerekli!",
    "game_explain": "Oyun Nasıl Oynanır?\n1. /katil ile katıl\n2. /baslat ile başlat\n3. Oylama ve özel güçler",
    "vote_no_active": "Şu anda oylama aktif değil.",
    "vote_received": "Oyunuz alındı: {}",
    "no_role": "Henüz rolünüz yok.",
    "vote_already_done": "Zaten oy kullandınız.",
    "all_votes_in": "Tüm oylar alındı, oylama kapanıyor...",
    "guc_no_access": "Özel güç kullanma hakkınız yok veya kullandınız.",
    "guc_used_already": "Özel gücünüzü zaten kullandınız.",
    "game_end": "Oyun sona erdi! Kazanan: {}",
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Dil: Türkçe 🇹🇷", callback_data="lang_tr"),
            InlineKeyboardButton("Dil: Azərbaycan 🇦🇿", callback_data="lang_az"),
        ],
        [InlineKeyboardButton("Oyun Nasıl Oynanır?", callback_data="game_explain")],
        [InlineKeyboardButton("Komutlar", callback_data="commands")],
        [
            InlineKeyboardButton("Destek Grubu", url="https://t.me/kizilsancaktr"),
            InlineKeyboardButton("Geliştirici", url="https://t.me/ZeydBinhalit"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(TEXTS["start"], reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "lang_tr":
        await query.edit_message_text("Dil Türkçe olarak ayarlandı.")
    elif query.data == "lang_az":
        await query.edit_message_text("Dil Azərbaycan olaraq ayarlandı.")
    elif query.data == "game_explain":
        await query.edit_message_text(TEXTS["game_explain"])
    elif query.data == "commands":
        komutlar = (
            "/start - Başlat\n"
            "/katil - Oyuna Katıl\n"
            "/baslat - Oyunu Başlat\n"
            "/roles - Roller ve Güçler\n"
            "/rol - Kendi Rolünü Gör\n"
            "/vote <ülke> - Oy Ver\n"
            "/ozelguc <ülke> - Özel Gücünü Kullan\n"
        )
        await query.edit_message_text(komutlar)
    else:
        await query.edit_message_text("Bilinmeyen komut.")

async def katil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in katilim_listesi:
        await update.message.reply_text(TEXTS["already_joined"])
    else:
        katilim_listesi.add(user_id)
        await update.message.reply_text(TEXTS["joined_success"].format(len(katilim_listesi)))
        async def roles_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rol_metni = "🎭 Oyundaki Roller ve Güçleri:\n\n"
    for rol, detay in roles.items():
        rol_metni += f"• {rol}: {detay['power_desc']}\n"
    await update.message.reply_text(rol_metni)

async def rol_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in oyuncu_rolleri:
        await update.message.reply_text(TEXTS["no_role"])
        return
    rol = oyuncu_rolleri[user_id]
    desc = roles[rol]["power_desc"]
    await update.message.reply_text(f"Senin rolün: {rol}\nGücün: {desc}")

async def baslat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global oylama_aktif, oylama_turu, oylama_katilimlar, oy_kayitlari, oyuncu_rolleri, ozel_guc_kullanilabilir, guc_kullanimi_yapildi

    if len(katilim_listesi) < 6:
        await update.message.reply_text(TEXTS["not_enough_players"])
        return

    oyuncular = list(katilim_listesi)
    random.shuffle(oyuncular)
    roller = list(roles.keys())
    random.shuffle(roller)

    oyuncu_rolleri = {}
    for i, oyuncu in enumerate(oyuncular):
        oyuncu_rolleri[oyuncu] = roller[i % len(roller)]

    oylama_aktif = False
    oylama_turu = 1
    oylama_katilimlar = set()
    oy_kayitlari = {}
    guc_kullanimi_yapildi = {}
    ozel_guc_kullanilabilir = set(oyuncular[:-6])  # Son 6 oyuncu özel güç kullanamaz

    metin = "🎉 Oyun başladı! Roller dağıtıldı.\n"
    for oyuncu in oyuncular:
        rol = oyuncu_rolleri[oyuncu]
        desc = roles[rol]["power_desc"]
        metin += f"- {rol}: {desc}\n"
    await update.message.reply_text(metin)

    for oyuncu in oyuncular:
        try:
            await context.bot.send_message(chat_id=oyuncu, text=f"Rolün: {oyuncu_rolleri[oyuncu]}\nGücün: {roles[oyuncu_rolleri[oyuncu]]['power_desc']}")
        except Exception as e:
            print(f"DM gönderilemedi: {e}")

async def vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global oylama_aktif, oylama_katilimlar, oy_kayitlari

    if not oylama_aktif:
        await update.message.reply_text(TEXTS["vote_no_active"])
        return

    user_id = update.message.from_user.id
    if user_id not in katilim_listesi:
        await update.message.reply_text("Oyuna katılmadınız.")
        return

    if user_id in oylama_katilimlar:
        await update.message.reply_text(TEXTS["vote_already_done"])
        return

    args = context.args
    if not args:
        await update.message.reply_text("Lütfen oy vermek istediğiniz ülkeyi yazınız.")
        return

    hedef_rol = " ".join(args).strip()
    if hedef_rol not in roles:
        await update.message.reply_text("Geçersiz ülke adı.")
        return

    oy_kayitlari[user_id] = hedef_rol
    oylama_katilimlar.add(user_id)
    await update.message.reply_text(TEXTS["vote_received"].format(hedef_rol))

    if len(oylama_katilimlar) == len(katilim_listesi):
        await update.message.reply_text(TEXTS["all_votes_in"])
        # Oylama sonuçları hesaplanacak, oy kullanma ve özel güç işlemleri burada yapılacak
        async def ozel_guc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in katilim_listesi or user_id not in ozel_guc_kullanilabilir:
        await update.message.reply_text(TEXTS["guc_no_access"])
        return

    if guc_kullanimi_yapildi.get(user_id, False):
        await update.message.reply_text(TEXTS["guc_used_already"])
        return

    rol = oyuncu_rolleri.get(user_id)
    if not rol:
        await update.message.reply_text(TEXTS["no_role"])
        return

    await update.message.reply_text(f"Özel gücünüzü kullanmak için hedefinizi belirtin. Örnek: /ozelguc <ülke adı>")
    guc_kullanimi_yapildi[user_id] = True


async def ozelguc_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in katilim_listesi or user_id not in ozel_guc_kullanilabilir:
        await update.message.reply_text(TEXTS["guc_no_access"])
        return

    args = context.args
    if not args:
        await update.message.reply_text("Lütfen özel gücünüz için hedef ülkeyi yazınız.")
        return

    hedef_rol = " ".join(args).strip()
    if hedef_rol not in roles:
        await update.message.reply_text("Geçersiz ülke adı.")
        return

    await update.message.reply_text(f"Özel gücünüz {hedef_rol} üzerine kullanıldı!")

    guc_kullanimi_yapildi[user_id] = True
    # Burada özel güç kullanımının oyuna etkileri işlenmeli


async def setgroup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global group_chat_id
    if update.effective_chat.type in ["group", "supergroup"]:
        group_chat_id = update.effective_chat.id
        await update.message.reply_text(f"Grup sohbet ID'si ayarlandı: {group_chat_id}")
    else:
        await update.message.reply_text("Bu komut sadece grup sohbetinde kullanılabilir.")


def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(CommandHandler("katil", katil))
    application.add_handler(CommandHandler("roles", roles_command))
    application.add_handler(CommandHandler("rol", rol_command))
    application.add_handler(CommandHandler("baslat", baslat))
    application.add_handler(CommandHandler("vote", vote))
    application.add_handler(CommandHandler("ozelguc", ozel_guc))
    application.add_handler(CommandHandler("ozelguc_target", ozelguc_target))
    application.add_handler(CommandHandler("setgroup", setgroup))

    application.run_polling()


if __name__ == "__main__":
    main()
