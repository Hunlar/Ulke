import logging
import json
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    CallbackQueryHandler
)
from game_manager import GameManager  # Daha önce hazırlanmış oyun mantığı

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "BOT_TOKEN_HERE"

game = None
joined_users = set()
language_map = {}

# Mesajlar ve butonlar
MESSAGES = {
    "tr": {
        "welcome_text": "3. Dünya Savaşı'nda kader seni nereye götürecek, alman mı olacaksın Osmanlı mı yoksa pembe dünyayı seçen bir zavallı mı? Kader sana hangi rolü verecek.",
        "welcome_buttons": [
            [InlineKeyboardButton("Dil: Türkçe", callback_data="lang_tr"),
             InlineKeyboardButton("Dil: Azerbaycan", callback_data="lang_az")],
            [InlineKeyboardButton("Oyunu Anlat", callback_data="game_info")],
            [InlineKeyboardButton("Oyuna Katıl", callback_data="join_game")],
            [InlineKeyboardButton("Roller", callback_data="show_roles")],
        ],
        "game_info": "Oyun, her oyuncuya rastgele bir ülke rolü dağıtır. Oyuncular özel güçlerini kullanabilir ve oy kullanarak diğerlerini saf dışı bırakabilirler. Özel güçler DM'den buton ile kullanılır.",
        "already_joined": "Zaten oyuna katıldınız.",
        "joined_success": "Oyuna başarıyla katıldınız!",
        "min_players": "Oyuna başlamanız için en az 6 oyuncu gerekiyor.",
        "roles_header": "Oyundaki Ülkeler ve Güçleri:",
        "roles_list_format": "• {role}: {desc}",
        "not_in_game": "Oyunda değilsiniz.",
        "power_not_available": "Özel gücünüzü şu an kullanamazsınız.",
        "power_used": "Özel gücünüz başarıyla kullanıldı!",
        "vote_prompt": "Lütfen oylama yapınız:",
        "vote_recorded": "Oyunuz kaydedildi.",
        "vote_already": "Zaten oy kullandınız.",
        "vote_invalid": "Geçersiz oy tercihi.",
        "game_started": "Oyun başladı! Roller ve özel güçler DM olarak gönderildi.",
        "game_already_started": "Oyun zaten devam ediyor.",
        "not_enough_players": "Yeterli oyuncu yok, oyun başlatılamıyor.",
        "game_cancelled": "Oyun iptal edildi.",
        "help_text": "Komutlar:\n/start - Başlat\n/join - Oyuna katıl\n/roles - Roller\n/cancel - Oyunu iptal et"
    },
    "az": {
        "welcome_text": "3-cü Dünya Müharibəsində taleyin səni hara aparacaq? Alman olacaqsan, Osmanlı, yoxsa çəhrayı dünyanı seçən zavallı? Taleyin sənə hansı rol verəcək.",
        "welcome_buttons": [
            [InlineKeyboardButton("Dil: Türkçe", callback_data="lang_tr"),
             InlineKeyboardButton("Dil: Azerbaycan", callback_data="lang_az")],
            [InlineKeyboardButton("Oyunu Anlat", callback_data="game_info")],
            [InlineKeyboardButton("Oyuna Katıl", callback_data="join_game")],
            [InlineKeyboardButton("Roller", callback_data="show_roles")],
        ],
        "game_info": "Oyun, hər oyunçuya təsadüfi ölkə rolu verir. Oyunçular xüsusi güclərini istifadə edə bilər və səs verərək digər oyunçuları xaric edə bilərlər. Xüsusi güclər DM vasitəsilə buton ilə istifadə olunur.",
        "already_joined": "Artıq oyuna qatıldınız.",
        "joined_success": "Oyuna uğurla qatıldınız!",
        "min_players": "Oyuna başlamaq üçün ən az 6 oyunçu lazımdır.",
        "roles_header": "Oyundakı Ölkələr və Gücləri:",
        "roles_list_format": "• {role}: {desc}",
        "not_in_game": "Oyunda deyilsiniz.",
        "power_not_available": "Xüsusi gücünüz hazırda istifadə edilə bilməz.",
        "power_used": "Xüsusi gücünüz uğurla istifadə edildi!",
        "vote_prompt": "Zəhmət olmasa səs verin:",
        "vote_recorded": "Səsiniz qeydə alındı.",
        "vote_already": "Artıq səs vermisiniz.",
        "vote_invalid": "Yanlış səs seçimi.",
        "game_started": "Oyun başladı! Rollar və xüsusi güclər DM vasitəsilə göndərildi.",
        "game_already_started": "Oyun artıq davam edir.",
        "not_enough_players": "Kifayət qədər oyunçu yoxdur, oyun başlatmaq mümkün deyil.",
        "game_cancelled": "Oyun ləğv edildi.",
        "help_text": "Əmrlər:\n/start - Başla\n/join - Oyuna qoşul\n/roles - Rollar\n/cancel - Oyunu ləğv et"
    }
}

MIN_PLAYERS = 6
MAX_PLAYERS = 20

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    language_map[user_id] = "tr"
    msg = MESSAGES["tr"]["welcome_text"]
    buttons = InlineKeyboardMarkup(MESSAGES["tr"]["welcome_buttons"])
    await update.message.reply_text(msg, reply_markup=buttons)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    data = query.data
    lang = language_map.get(user_id, "tr")

    global game

    # Dil seçimi
    if data == "lang_tr":
        language_map[user_id] = "tr"
        await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(MESSAGES["tr"]["welcome_buttons"]))
        await query.message.edit_text(MESSAGES["tr"]["welcome_text"])
        return
    elif data == "lang_az":
        language_map[user_id] = "az"
        await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(MESSAGES["az"]["welcome_buttons"]))
        await query.message.edit_text(MESSAGES["az"]["welcome_text"])
        return

    # Oyunu anlat
    if data == "game_info":
        await query.message.reply_text(MESSAGES[lang]["game_info"])
        return

    # Oyuna katıl
    if data == "join_game":
        if user_id in joined_users:
            await query.message.reply_text(MESSAGES[lang]["already_joined"])
        else:
            joined_users.add(user_id)
            await query.message.reply_text(MESSAGES[lang]["joined_success"])
        return

    # Roller listesi
    if data == "show_roles":
        roles_text = MESSAGES[lang]["roles_header"] + "\n\n"
        with open('roles.json', 'r', encoding='utf-8') as f:
            roles = json.load(f)
        for role, info in roles.items():
            roles_text += MESSAGES[lang]["roles_list_format"].format(role=role, desc=info["power_description"]) + "\n"
        await query.message.reply_text(roles_text)
        return

    # Oyunu başlat (admin veya bot sahibi /startgame komutu yerine buton istersen ekleriz)
    if data == "start_game":
        if game is not None:
            await query.message.reply_text(MESSAGES[lang]["game_already_started"])
            return
        if len(joined_users) < MIN_PLAYERS:
            await query.message.reply_text(MESSAGES[lang]["min_players"])
            return
        game = GameManager()
        assigned = game.assign_roles(list(joined_users))
        # Rolleri ve özel güçleri DM at
        for uid, info in assigned.items():
            try:
                role = info["role"]
                power_desc = game.roles[role]["power_description"]
                power_gif = game.roles[role].get("power_use_gif")
                keyboard = InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Özel Gücümü Kullan", callback_data="power_use")]]
                )
                await context.bot.send_message(chat_id=uid, text=f"Rolünüz: {role}\nGücünüz: {power_desc}", reply_markup=keyboard)
                if power_gif:
                    await context.bot.send_animation(chat_id=uid, animation=power_gif)
            except Exception as e:
                logger.warning(f"DM gönderilemedi {uid}: {e}")
        await query.message.reply_text(MESSAGES[lang]["game_started"])
        return

    # Özel güç kullanımı
    if data == "power_use":
        if game is None:
            await query.message.reply_text("Oyun başlamadı.")
            return
        result, message = game.use_power(user_id)
        if result:
            msg, gif = message
            await query.message.reply_text(msg)
            if gif:
                await context.bot.send_animation(chat_id=user_id, animation=gif)
        else:
            await query.answer(message, show_alert=True)
        return

    # Oylama butonları, örn data = vote_<hedef>
    if data.startswith("vote_"):
        if game is None:
            await query.message.reply_text("Oyun başlamadı.")
            return
        target = data.split("_", 1)[1]
        result, message = game.cast_vote(user_id, target)
        if result:
            await query.answer(message)
            # Oy kullandıktan sonra butonları kaldırabiliriz:
            await query.message.edit_reply_markup(reply_markup=None)
        else:
            await query.answer(message, show_alert=True)
        return

async def cancel_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = language_map.get(user_id, "tr")
    global game, joined_users
    if game is None:
        await update.message.reply_text("Şu anda aktif oyun yok.")
        return
    game = None
    joined_users.clear()
    await update.message.reply_text(MESSAGES[lang]["game_cancelled"])

async def join_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = language_map.get(user_id, "tr")
    if user_id in joined_users:
        await update.message.reply_text(MESSAGES[lang]["already_joined"])
    else:
        joined_users.add(user_id)
        await update.message.reply_text(MESSAGES[lang]["joined_success"])

async def roles_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = language_map.get(user_id, "tr")
    roles_text = MESSAGES[lang]["roles_header"] + "\n\n"
    with open('roles.json', 'r', encoding='utf-8') as f:
        roles = json.load(f)
    for role, info in roles.items():
        roles_text += MESSAGES[lang]["roles_list_format"].format(role=role, desc=info["power_description"]) + "\n"
    await update.message.reply_text(roles_text)

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("join", join_command))
    application.add_handler(CommandHandler("roles", roles_command))
    application.add_handler(CommandHandler("cancel", cancel_game))
    application.add_handler(CallbackQueryHandler(button_handler))

    application.run_polling()

if __name__ == "__main__":
    main()
