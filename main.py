import logging
import json
import random
import asyncio
from telegram import Update, ForceReply
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# LOG Ayarları
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global değişkenler
TOKEN = "BOT_TOKENINIZI_BURAYA_YAZIN"

# Oyuncu listesi ve roller
players = []
player_roles = {}
game_active = False

# Dil dosyasını yükle
with open("languages/tr.json", "r", encoding="utf-8") as f:
    texts = json.load(f)

# Roller dosyası
with open("roles.json", "r", encoding="utf-8") as f:
    roles = json.load(f)


async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global game_active, players, player_roles

    if game_active:
        await update.message.reply_text("Bir oyun zaten devam ediyor!")
        return

    players = []
    player_roles = {}
    game_active = True

    await update.message.reply_text(texts["oyun_basladi"])
    await asyncio.sleep(120)  # 2 dakika katılım süresi

    if len(players) < 6:
        await update.message.reply_text("Yeterli oyuncu toplanamadı. Oyun iptal edildi.")
        game_active = False
        return

    await update.message.reply_text(texts["oyun_baslatiliyor"])
    assign_roles()
    await send_roles(context)


def assign_roles():
    global player_roles
    available_roles = list(roles.keys())
    random.shuffle(available_roles)

    for i, player in enumerate(players):
        role_key = available_roles[i % len(available_roles)]
        player_roles[player] = role_key


async def send_roles(context: ContextTypes.DEFAULT_TYPE):
    for player_id, role_key in player_roles.items():
        role = roles[role_key]
        text = texts["rol_dm"].format(rol_adi=role["ad"], guc=role["guc"])
        try:
            await context.bot.send_message(chat_id=player_id, text=text)
        except Exception as e:
            logger.error(f"{player_id} kullanıcısına rol gönderilemedi: {e}")


async def join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global players, game_active

    if not game_active:
        await update.message.reply_text("Şu anda aktif bir oyun yok. /oyun komutunu kullanarak yeni oyun başlatabilirsiniz.")
        return

    user_id = update.message.from_user.id
    if user_id in players:
        await update.message.reply_text(texts["zaten_katildin"])
        return

    players.append(user_id)
    await update.message.reply_text(texts["katilan_oyuncu"].format(kullanici=update.message.from_user.first_name))
    await update.message.reply_text(texts["oyuncu_sayisi"].format(sayi=len(players)))


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "/oyun - Yeni oyun başlat\n"
        "/katıl - Oyuna katıl\n"
        "/yardım - Bu mesajı göster\n"
    )
    await update.message.reply_text(help_text)


def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("oyun", start_game))
    application.add_handler(CommandHandler("katıl", join_game))
    application.add_handler(CommandHandler("yardım", help_command))

    application.run_polling()


if __name__ == '__main__':
    main()
