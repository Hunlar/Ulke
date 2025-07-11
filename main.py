import os
import random
import asyncio
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

# Oyun durumu
katilim_listesi = set()
oyuncu_rolleri = {}
chat_lang = {}
oylama_turu = 0
oylama_aktif = False
oylama_katilimcilar = set()
oy_kayitlari = {}

ozel_guc_kullanilabilir = set()
guc_kullanimi_yapildi = {}

# Roller ve güçleri
roles = {
    "Osmanlı İmparatorluğu": "2 oylamada 1 ülkeyi saf dışı bırakabilir (aynı oylamada 2 değil).",
    "German İmparatorluğu": "2 oylamada 1 kez kaos çıkartır, sadece kendisi oy kullanabilir.",
    "Biritanya": "Bir ülkenin oylama tercihlerini manipüle edebilir.",
    "Renkli Dünya": "Kimse ne olduğunu bilmez, meydan okur ve meydan okur.",
    # Diğer ülkeler burada...
}

# Destek & geliştirici linkleri
DESTEK_LINK = "https://t.me/kizilsancaktr"
GELISTIRICI_LINK = "https://t.me/ZeydBinhalit"

# Metinler - sadece Türkçe örnek
TEXTS = {
    "start": (
        "3. Dünya Savaşı'nda kader seni nereye götürecek, "
        "alman mı olacaksın Osmanlı mı yoksa pembe dünyayı seçen bir zavallı mı? "
        "Kader sana hangi rolü verecek?"
    ),
    "welcome": "👋 Ülke Savaşları Botuna hoşgeldin!\n🎮 Oyuna katılmak için /katil komutunu kullanabilirsin.",
    "join_prompt": "Oyuna katılmak için aşağıdaki butona tıklayın. Katılım 2 dakika sürecek.",
    "already_joined": "Zaten oyuna katıldınız.",
    "joined_success": "Başarıyla katıldınız! Toplam oyuncu: {}",
    "not_enough_players": "Oyuna başlamak için en az 6 oyuncu gerekli!",
    "game_explain": (
        "🎲 Oyun Nasıl Oynanır?\n"
        "1. /katil ile oyuna katılın.\n"
        "2. /baslat ile oyun başlatılır ve roller rastgele dağıtılır.\n"
        "3. Oylama turları ile oyuncular elenir.\n"
        "4. Özel güçlerinizi kullanarak rakiplerinizi saf dışı bırakın.\n"
        "5. Son hayatta kalan kazanır!"
    ),
    "vote_no_active": "Şu anda oylama aktif değil.",
    "vote_received": "Oyunuz alındı: {}",
    "no_role": "Henüz rolünüz atanmamış veya oyuna katılmamışsınız.",
    "vote_already_done": "Zaten oy kullandınız.",
    "all_votes_in": "Tüm oylar alındı, oylama kapanıyor...",
    "guc_no_access": "Şu anda özel güç kullanma hakkınız yok veya zaten kullandınız.",
    "guc_used": "Özel gücünüz başarıyla kullanıldı!",
    "guc_prompt_osmanli": "Osmanlı, saf dışı bırakmak istediğin ülkeyi seç:",
    "guc_prompt_german": "German İmparatorluğu, kaos çıkarmak için onayla:",
}

# --- KOMUTLAR ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📝 Katıl", callback_data="join_game")],
        [InlineKeyboardButton("📜 Komutlar", callback_data="show_commands")],
        [InlineKeyboardButton("🎲 Oyun Nasıl Oynanır?", callback_data="game_explain")],
        [
            InlineKeyboardButton("Destek Grubu", url=DESTEK_LINK),
            InlineKeyboardButton("Geliştirici", url=GELISTIRICI_LINK)
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(TEXTS["start"], reply_markup=reply_markup)


async def katil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global katilim_listesi

    user_id = update.effective_user.id

    if user_id in katilim_listesi:
        await update.message.reply_text(TEXTS["already_joined"])
        return

    katilim_listesi.add(user_id)
    await update.message.reply_text(TEXTS["joined_success"].format(len(katilim_listesi)))


async def roller_listesi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mesaj = "🎭 Oyundaki Roller ve Güçleri:\n"
    for rol, guc in roles.items():
        mesaj += f"\n- {rol}: {guc}"
    await update.message.reply_text(mesaj)


async def rol_goster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    rol = oyuncu_rolleri.get(user_id)
    if rol:
        await update.message.reply_text(f"🎭 Rolünüz: {rol}\n🧠 Gücünüz: {roles[rol]}")
    else:
        await update.message.reply_text(TEXTS["no_role"])


async def oyun_baslat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global oylama_turu, oylama_aktif, oy_kayitlari, oylama_katilimcilar, ozel_guc_kullanilabilir, guc_kullanimi_yapildi

    if len(katilim_listesi) < 6:
        await update.message.reply_text(TEXTS["not_enough_players"])
        return

    await update.message.reply_text("🎲 Oyun başlatılıyor, roller dağıtılıyor...")

    # Roller rastgele dağıt
    roller = random.sample(list(roles.keys()), len(katilim_listesi))
    oyuncu_rolleri.clear()
    for user_id, rol in zip(katilim_listesi, roller):
        oyuncu_rolleri[user_id] = rol
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🎭 Rolünüz: {rol}\n🧠 Gücünüz: {roles[rol]}"
            )
        except:
            # DM kapalıysa ya da hata varsa atla
            pass

    await update.message.reply_text("🎭 Roller özel mesaj ile oyunculara gönderildi!")

    # İlk oylama turu başlat
    oylama_turu = 1
    oylama_aktif = True
    oy_kayitlari.clear()
    oylama_katilimcilar = set(katilim_listesi)
    ozel_guc_kullanilabilir.clear()
    guc_kullanimi_yapildi.clear()

    # Oylama için oylama ve özel güç butonlarını gönder
    await oylama_butonu_gonder(context)


async def oylama_butonu_gonder(context: ContextTypes.DEFAULT_TYPE):
    global oylama_turu, ozel_guc_kullanilabilir, guc_kullanimi_yapildi

    for user_id in oylama_katilimcilar:
        # Oylama butonları: rakip roller listesi (kendisini hariç tut)
        rakipler = [rol for uid, rol in oyuncu_rolleri.items() if uid != user_id]
        if not rakipler:
            continue
        keyboard_oy = [
            [InlineKeyboardButton(r, callback_data=f"oy_{r}")]
            for r in rakipler
        ]
        oy_markup = InlineKeyboardMarkup(keyboard_oy)

        # Özel güç kullanımı 2 oylamada bir aktif (örnek)
        guc_markup = None
        if oylama_turu % 2 == 0:
            rol = oyuncu_rolleri.get(user_id)
            if rol in ["Osmanlı İmparatorluğu", "German İmparatorluğu"]:
                ozel_guc_kullanilabilir.add(user_id)
                guc_kullanimi_yapildi[user_id] = False
                if rol == "Osmanlı İmparatorluğu":
                    guc_markup = InlineKeyboardMarkup([[
                        InlineKeyboardButton("Özel Gücünü Kullan (Saf Dışı Bırak)", callback_data="guc_osmanli")
                    ]])
                elif rol == "German İmparatorluğu":
                    guc_markup = InlineKeyboardMarkup([[
                        InlineKeyboardButton("Özel Gücünü Kullan (Kaos Çıkart)", callback_data="guc_german")
                    ]])

        # Mesajları gönder
        try:
            await context.bot.send_message(user_id, "Lütfen oyunu kullanınız:", reply_markup=oy_markup)
            if guc_markup:
                await context.bot.send_message(user_id, "Özel gücünüz aktif! Kullanmak ister misiniz?", reply_markup=guc_markup)
        except:
            pass


async def oylama_bitir(context: ContextTypes.DEFAULT_TYPE):
    global oylama_aktif, katilim_listesi, oyuncu_rolleri, oy_kayitlari, oylama_katilimcilar

    oylama_aktif = False

    sayim = {}
    for oy in oy_kayitlari.values():
        sayim[oy] = sayim.get(oy, 0) + 1

    if not sayim:
        sonuc_mesaji = "Oylama yapılmadı."
    else:
        max_oy = max(sayim.values())
        elenenler = [ulke for ulke, oy_sayisi in sayim.items() if oy_sayisi == max_oy]

        sonuc_mesaji = "🗳️ Oylama Sonuçları:\n"
        for ulke, oy_sayisi in sayim.items():
            sonuc_mesaji += f"{ulke}: {oy_sayisi} oy\n"

        sonuc_mesaji += "\n❌ Elenen ülke(ler): " + ", ".join(elenenler)

        # Elenen oyuncuları oyundan çıkar
        elenen_kullanicilar = [uid for uid, rol in oyuncu_rolleri.items() if rol in elenenler]
        for uid in elenen_kullanicilar:
            oyuncu_rolleri.pop(uid, None)
            katilim_listesi.discard(uid)

    # Grup sohbet ID ayarlanmalı (/setgroup komutuyla)
    group_chat_id = context.bot_data.get("group_chat_id")
    if group_chat_id:
        await context.bot.send_message(chat_id=group_chat_id, text=sonuc_mesaji)
    else:
        print("Grup chat ID ayarlanmadı, sonuç mesajı gönderilemedi.")

    # Oylama sonrası resetler
    oy_kayitlari.clear()
    oylama_katilimcilar.clear()

    # Sonraki turu başlatabiliriz (opsiyonel)
    global oylama_turu
    oylama_turu += 1
    oylama_aktif = True
    oylama_katilimcilar = set(katilim_listesi)
    await oylama_butonu_gonder(context)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global oylama_aktif, oylama_katilimcilar, oy_kayitlari, ozel_guc_kullanilabilir, guc_kullanimi_yapildi

    query = update.callback_query
    data = query.data
    user_id = query.from_user.id

    await query.answer()

    if data == "join_game":
        if user_id in katilim_listesi:
            await query.answer(TEXTS["already_joined"], show_alert=True)
        else:
            katilim_listesi.add(user_id)
            await query.edit_message_text(TEXTS["joined_success"].format(len(katilim_listesi)))

    elif data == "show_commands":
        komutlar = (
            "/start - Başlat\n"
            "/katil - Oyuna katıl\n"
            "/baslat - Oyunu başlat (Yönetici)\n"
            "/roles - Roller ve güçler\n"
            "/rol - Rolünü göster\n"
            "/setgroup - Grup chat ID ayarla (admin komutu)\n"
        )
        await query.edit_message_text(komutlar)

    elif data == "game_explain":
        await query.edit_message_text(TEXTS["game_explain"])

    elif data.startswith("oy_"):
        if not oylama_aktif:
            await query.answer(TEXTS["vote_no_active"], show_alert=True)
            return
        if user_id not in oylama_katilimcilar:
            await query.answer("Oylamaya katılmıyorsunuz veya oy kullandınız.", show_alert=True)
            return

        if user_id in oy_kayitlari:
            await query.answer(TEXTS["vote_already_done"], show_alert=True)
            return

        secilen = data[3:]
        oy_kayitlari[user_id] = secilen
        oylama_katilimcilar.remove(user_id)
        await query.edit_message_text(TEXTS["vote_received"].format(secilen))

        if not oylama_katilimcilar:
            await oylama_bitir(context)

    elif data.startswith("guc_"):
        if user_id not in ozel_guc_kullanilabilir:
            await query.answer(TEXTS["guc_no_access"], show_alert=True)
            return
        if guc_kullanimi_yapildi.get(user_id, True):
            await query.answer("Zaten özel gücünüzü kullandınız.", show_alert=True)
            return

        guc_kullanimi_yapildi[user_id] = True
        rol = oyuncu_rolleri.get(user_id)

        if data == "guc_osmanli":
            # Saf dışı bırakılacak ülkeyi seçtirmek için butonlar gönder
            rakipler = [r for r in oyuncu_rolleri.values() if r != rol]
            if not rakipler:
                await query.edit_message_text("Rakip ülke yok.")
                return
            keyboard = [
                [InlineKeyboardButton(r, callback_data=f"guc_osmanli_sec_{r}")]
                for r in rakipler
            ]
            await query.edit_message_text(TEXTS["guc_prompt_osmanli"], reply_markup=InlineKeyboardMarkup(keyboard))

        elif data == "guc_german":
            # Kaos çıkartma onayı verildi, oy kullanma haklarını değiştir
            await query.edit_message_text("Kaos çıkartıldı, sadece siz oy kullanabilirsiniz bu tur!")
            # Burada oy kullanma izinlerini güncelle (örnek: oylama_katilimcilar = {user_id})
            oylama_katilimcilar.clear()
            oylama_katilimcilar.add(user_id)

    elif data.startswith("guc_osmanli_sec_"):
        if user_id not in ozel_guc_kullanilabilir or guc_kullanimi_yapildi.get(user_id, False) == False:
            await query.answer(TEXTS["guc_no_access"], show_alert=True)
            return

        secilen_ulke = data[len("guc_osmanli_sec_"):]
        # Rakibi saf dışı bırak (oyun durumundan çıkar)
        elenen_kullanicilar = [uid for uid, rol in oyuncu_rolleri.items() if rol == secilen_ulke]
        for uid in elenen_kullanicilar:
            oyuncu_rolleri.pop(uid, None)
            katilim_listesi.discard(uid)
            if uid in oylama_katilimcilar:
                oylama_katilimcilar.discard(uid)

        await query.edit_message_text(f"Özel güç kullanıldı: {secilen_ulke} saf dışı bırakıldı!")
        # Güç kullandın işaretle (zaten True)
        # Oyun devam eder

    else:
        await query.answer("Bilinmeyen işlem.", show_alert=True)


async def grup_chat_ayarla(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in ("group", "supergroup"):
        context.bot_data["group_chat_id"] = update.effective_chat.id
        await update.message.reply_text("Grup sohbet ID'si ayarlandı.")
    else:
        await update.message.reply_text("Bu komut sadece grup sohbetinde kullanılabilir.")


def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN tanımlı değil!")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("katil", katil))
    app.add_handler(CommandHandler("roles", roller_listesi))
    app.add_handler(CommandHandler("rol", rol_goster))
    app.add_handler(CommandHandler("baslat", oyun_baslat))
    app.add_handler(CommandHandler("setgroup", grup_chat_ayarla))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot çalışıyor...")
    import asyncio
    asyncio.run(app.run_polling())


if __name__ == "__main__":
    main()
