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

# --- Roller ve özel güçleri ---
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
    "Fransa": {
        "power_desc": "Güçlü diplomasiyle rakiplerini etkileyebilir.",
        "power_key": "fransa_diplomasi",
    },
    "Rusya": {
        "power_desc": "Soğuk savaş gücüyle rakiplerin oylarını azaltabilir.",
        "power_key": "rusya_soguk_savas",
    },
    "Çin": {
        "power_desc": "Ekonomik baskı ile rakiplerin kararlarını etkiler.",
        "power_key": "cin_ekonomi",
    },
    "Japonya": {
        "power_desc": "Hızlı saldırı yaparak bir tur koruma sağlar.",
        "power_key": "japonya_saldiri",
    },
    "İtalya": {
        "power_desc": "Stratejik hamlelerle kendi oylarını artırır.",
        "power_key": "italya_strateji",
    },
    "İspanya": {
        "power_desc": "Gizli anlaşmalarla rakipleri zayıflatır.",
        "power_key": "ispanya_anlasma",
    },
    "Hindistan": {
        "power_desc": "Kitle desteği ile oylama gücünü artırır.",
        "power_key": "hindistan_kitle",
    },
    "Brezilya": {
        "power_desc": "Sürpriz saldırı yapabilir.",
        "power_key": "brezilya_saldiri",
    },
    "Mısır": {
        "power_desc": "Stratejik savunma yapar, bir tur korunur.",
        "power_key": "misir_savunma",
    },
    "Yunanistan": {
        "power_desc": "Rakiplerin güçlerini geçici azaltır.",
        "power_key": "yunanistan_zayiflat",
    },
    "Türkiye": {
        "power_desc": "Hem saldırı hem savunma yapabilir.",
        "power_key": "turkiye_karma",
    },
    "Kanada": {
        "power_desc": "Oylama süresini kısaltabilir.",
        "power_key": "kanada_hiz",
    },
    "Avustralya": {
        "power_desc": "Müttefik desteği alır, güç artışı sağlar.",
        "power_key": "avustralya_destek",
    },
    "Güney Afrika": {
        "power_desc": "Zorunlu barış talebinde bulunabilir.",
        "power_key": "güneyafrika_barış",
    },
}

# --- GLOBAL DURUM ---
katilim_listesi = set()
oyuncu_rolleri = {}
oylama_turu = 0
oylama_aktif = False
oylama_katilimcilar = set()
oy_kayitlari = {}
ozel_guc_kullanilabilir = set()
guc_kullanimi_yapildi = {}

# Grup chat ID oyundaki sonuçlar için
group_chat_id = None

# --- MESAJLAR ---

TEXTS = {
    "start": "3. Dünya Savaşı'nda kader seni nereye götürecek, alman mı olacaksın Osmanlı mı yoksa pembe dünyayı seçen bir zavallı mı? Kader sana hangi rolü verecek?",
    "welcome": "👋 Ülke Savaşları Botuna hoşgeldin!\n🎮 Oyuna katılmak için /katil komutunu kullanabilirsin.",
    "already_joined": "Zaten oyuna katıldınız.",
    "joined_success": "Başarıyla katıldınız! Toplam oyuncu: {}",
    "not_enough_players": "Oyuna başlamak için en az 6 oyuncu gerekli!",
    "game_explain": "🎲 Oyun Nasıl Oynanır?\n"
                    "1. /katil ile oyuna katılın.\n"
                    "2. /baslat ile oyun başlatılır ve roller rastgele dağıtılır.\n"
                    "3. Oylama turları ile oyuncular elenir.\n"
                    "4. Özel güçlerinizi kullanarak rakiplerinizi saf dışı bırakın.\n"
                    "5. Son hayatta kalan kazanır!",
    "vote_no_active": "Şu anda oylama aktif değil.",
    "vote_received": "Oyunuz alındı: {}",
    "no_role": "Henüz rolünüz atanmamış veya oyuna katılmamışsınız.",
    "vote_already_done": "Zaten oy kullandınız.",
    "all_votes_in": "Tüm oylar alındı, oylama kapanıyor...",
    "guc_no_access": "Şu anda özel güç kullanma hakkınız yok veya zaten kullandınız.",
    "guc_used": "Özel gücünüz başarıyla kullanıldı!",
    "guc_prompt": "Özel gücünüzü kullanmak ister misiniz?",
    "guc_prompt_select": "Özel güç için hedef seçin:",
    "guc_cant_last6": "Son 6 oyuncuda özel güç kullanılamaz.",
    "guc_used_already": "Özel gücünüzü zaten kullandınız bu tur.",
    "game_end": "Oyun sona erdi! Kazanan: {}",
    "commands": "/start - Başlat\n/katil - Oyuna katıl\n/baslat - Oyunu başlat\n/roles - Roller ve güçler\n/rol - Rolünü göster\n/setgroup - Grup chat ID ayarla (admin)\n",
}

START_GIF = "https://media.giphy.com/media/3o6Zt481isNVuQI1l6/giphy.gif"  # savaş temalı gif

# --- KOMUTLAR ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📝 Katıl", callback_data="join_game")],
        [InlineKeyboardButton("📜 Komutlar", callback_data="show_commands")],
        [InlineKeyboardButton("🎲 Oyun Nasıl Oynanır?", callback_data="game_explain")],
        [
            InlineKeyboardButton("Destek Grubu", url="https://t.me/kizilsancaktr"),
            InlineKeyboardButton("Geliştirici", url="https://t.me/ZeydBinhalit")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # GIF ile mesaj gönder
    if update.message:
        await update.message.reply_animation(animation=START_GIF, caption=TEXTS["start"], reply_markup=reply_markup)
    else:
        # CallbackQuery olabilir
        await update.callback_query.edit_message_media(
            media=None,  # GIF değiştirme vb. zor olabilir, bu durumda sadece metin + buton gösterilebilir
            reply_markup=reply_markup
        )

async def katil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in katilim_listesi:
        await update.message.reply_text(TEXTS["already_joined"])
        return
    katilim_listesi.add(user_id)
    await update.message.reply_text(TEXTS["joined_success"].format(len(katilim_listesi)))

async def roller_listesi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mesaj = "🎭 Oyundaki Roller ve Güçleri:\n"
    for rol, detay in roles.items():
        mesaj += f"\n- {rol}: {detay['power_desc']}"
    await update.message.reply_text(mesaj)

async def rol_goster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    rol = oyuncu_rolleri.get(user_id)
    if rol:
        detay = roles.get(rol, {})
        await update.message.reply_text(f"🎭 Rolünüz: {rol}\n🧠 Gücünüz: {detay.get('power_desc', '')}")
    else:
        await update.message.reply_text(TEXTS["no_role"])

async def oyun_baslat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global oylama_turu, oylama_aktif, oy_kayitlari, oylama_katilimcilar, ozel_guc_kullanilabilir, guc_kullanimi_yapildi

    if len(katilim_listesi) < 6:
        await update.message.reply_text(TEXTS["not_enough_players"])
        return

    await update.message.reply_text("🎲 Oyun başlatılıyor, roller dağıtılıyor...")

    roller_secimi = random.sample(list(roles.keys()), len(katilim_listesi))
    oyuncu_rolleri.clear()
    for user_id, rol in zip(katilim_listesi, roller_secimi):
        oyuncu_rolleri[user_id] = rol
        try:
            await context.bot.send_message(user_id, f"🎭 Rolünüz: {rol}\n🧠 Gücünüz: {roles[rol]['power_desc']}")
        except:
            pass

    await update.message.reply_text("🎭 Roller özel mesaj ile oyunculara gönderildi!")

    oylama_turu = 1
    oylama_aktif = True
    oy_kayitlari.clear()
    oylama_katilimcilar = set(katilim_listesi)
    ozel_guc_kullanilabilir.clear()
    guc_kullanimi_yapildi.clear()

    # Oyuncu sayısına göre son 6 için özel güç engellemesi uygulanacak (ilk turda herkes aktif)
    await oylama_butonu_gonder(context)

async def oylama_butonu_gonder(context: ContextTypes.DEFAULT_TYPE):
    global oylama_turu, ozel_guc_kullanilabilir, guc_kullanimi_yapildi

    # Son 6 oyuncu özel güç kullanamaz
    oyuncular_siralama = list(oyuncu_rolleri.keys())
    son_6_oyuncu = set(oyuncular_siralama[-6:])

    for user_id in oylama_katilimcilar:
        rol = oyuncu_rolleri.get(user_id)
        if not rol:
            continue

        # Rakip roller (kendisi hariç)
        rakipler = [r for uid, r in oyuncu_rolleri.items() if uid != user_id]
        if not rakipler:
            continue

        oy_butonlari = [[InlineKeyboardButton(r, callback_data=f"oy_{r}")] for r in rakipler]
        oy_markup = InlineKeyboardMarkup(oy_butonlari)

        # Özel güç butonu 2 oylamada bir ve son 6 oyuncuda devre dışı
        guc_markup = None
        if (oylama_turu % 2 == 0) and (user_id not in son_6_oyuncu):
            if not guc_kullanimi_yapildi.get(user_id, False):
                guc_key = roles[rol]["power_key"]
                guc_buton_text = "Özel Gücünü Kullan"
                guc_markup = InlineKeyboardMarkup(
                    [[InlineKeyboardButton(guc_buton_text, callback_data=f"guc_{guc_key}")]]
                )
                ozel_guc_kullanilabilir.add(user_id)
            else:
                ozel_guc_kullanilabilir.discard(user_id)
        else:
            ozel_guc_kullanilabilir.discard(user_id)

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
            if uid in oylama_katilimlar:
                oylama_katilimlar.discard(uid)

    global group_chat_id
    if group_chat_id:
        await context.bot.send_message(chat_id=group_chat_id, text=sonuc_mesaji)
    else:
        print("Grup chat ID ayarlanmadı, sonuç mesajı gönderilemedi.")

    oy_kayitlari.clear()
    oylama_katilimlar.clear()

    # Oyuncu sayısı 1 ise oyun sonu
    if len(katilim_listesi) <= 1:
        kazanan_rol = None
        if katilim_listesi:
            kazanan_rol = oyuncu_rolleri.get(list(katilim_listesi)[0], "Bilinmiyor")
        await context.bot.send_message(chat_id=group_chat_id, text=TEXTS["game_end"].format(kazanan_rol))
        return

    global oylama_turu
    oylama_turu += 1
    oylama_aktif = True
    oylama_katilimlar = set(katilim_listesi)
    await oylama_butonu_gonder(context)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global oylama_aktif, oylama_katilimlar, oy_kayitlari, ozel_guc_kullanilabilir, guc_kullanimi_yapildi

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
        await query.edit_message_text(TEXTS["commands"])

    elif data == "game_explain":
        await query.edit_message_text(TEXTS["game_explain"])

    elif data.startswith("oy_"):
        if not oylama_aktif:
            await query.answer(TEXTS["vote_no_active"], show_alert=True)
            return
        if user_id not in oylama_katilimlar:
            await query.answer("Oylamaya katılmıyorsunuz veya oy kullandınız.", show_alert=True)
            return
        if user_id in oy_kayitlari:
            await query.answer(TEXTS["vote_already_done"], show_alert=True)
            return
        secilen = data[3:]
        oy_kayitlari[user_id] = secilen
        oylama_katilimlar.remove(user_id)
        await query.edit_message_text(TEXTS["vote_received"].format(secilen))

        if not oylama_katilimlar:
            await oylama_bitir(context)

    elif data.startswith("guc_"):
        if user_id not in ozel_guc_kullanilabilir:
            await query.answer(TEXTS["guc_no_access"], show_alert=True)
            return
        if guc_kullanimi_yapildi.get(user_id, False):
            await query.answer(TEXTS["guc_used_already"], show_alert=True)
            return

        guc_kullanimi_yapildi[user_id] = True
        rol = oyuncu_rolleri.get(user_id)
        guc_key = data[4:]

        # Örnek: Osmanlı özel güç kullanımı (saf dışı bırakma)
    if guc_key == "osmanli_el":
            # Osmanlı'nın özel gücü: 1 ülkeyi saf dışı bırakabilir.
            # Kullanıcıya rakip ülkeler DM ile listelenir, seçmesi istenir.
            # Burada basit örnek, hemen rastgele saf dışı bırakılıyor.
            rakipler = [r for uid, r in oyuncu_rolleri.items() if uid != user_id]
            if not rakipler:
                await query.answer("Rakip yok.", show_alert=True)
                return
            eleneni = random.choice(rakipler)

            # Elenen oyuncuları oyundan çıkar
            elenen_kullanicilar = [uid for uid, rol in oyuncu_rolleri.items() if rol == eleneni]
            for uid in elenen_kullanicilar:
                oyuncu_rolleri.pop(uid, None)
                katilim_listesi.discard(uid)
                if uid in oylama_katilimlar:
                    oylama_katilimlar.discard(uid)

            await query.edit_message_text(f"Osmanlı özel gücü kullanıldı! {eleneni} ülkesi saf dışı bırakıldı.")
            return

        elif guc_key == "german_kaos":
            # Alman İmparatorluğu kaos çıkarır, sadece kendisi oy kullanabilir
            # Oylama katılımcıları sadece kullanıcı olacak
            oylama_katilimlar.clear()
            oylama_katilimlar.add(user_id)
            await query.edit_message_text("German İmparatorluğu kaos çıkardı, sadece sen oy kullanabilirsin!")
            return

        elif guc_key == "biritanya_manipulasyon":
            # Biritanya istediği ülkenin oylarını manipüle eder.
            # Burada basitçe seçilen ülke oy kullanırken Biritanya'nın seçimini seçer.
            # Örnek olarak random seçim yapıyoruz.
            await query.edit_message_text("Biritanya özel gücü etkinleştirildi. (Manipülasyon örnek)")

        elif guc_key == "renkli_dunya_meydan":
            await query.edit_message_text("Pembe Dünya Direnişçileri meydan okuyor!")

        else:
            await query.edit_message_text(f"Özel güç {guc_key} henüz uygulanmadı.")

    else:
        await query.answer("Bilinmeyen komut.", show_alert=True)

async def setgroup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global group_chat_id
    user = update.effective_user
    chat = update.effective_chat

    if not user or not chat:
        return

    # Sadece adminler bu komutu kullanabilir
    member = await chat.get_member(user.id)
    if not member.status in ("administrator", "creator"):
        await update.message.reply_text("Bu komutu sadece grup yöneticileri kullanabilir.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Kullanım: /setgroup <grup_chat_id>")
        return

    try:
        gid = int(context.args[0])
        group_chat_id = gid
        await update.message.reply_text(f"Grup chat ID başarıyla ayarlandı: {gid}")
    except:
        await update.message.reply_text("Geçerli bir sayı giriniz.")

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("katil", katil))
    application.add_handler(CommandHandler("roles", roller_listesi))
    application.add_handler(CommandHandler("rol", rol_goster))
    application.add_handler(CommandHandler("baslat", oyun_baslat))
    application.add_handler(CommandHandler("setgroup", setgroup))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Bot çalışıyor...")
    application.run_polling()

if __name__ == "__main__":
    main()
