import os
import asyncio
import random
import json
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from game_manager import kullan_rol_gucu

TOKEN = os.getenv("BOT_TOKEN")

players = []
game_started = False
player_roles = {}
languages = {}
roles = {}

KATILIM_SÜRESİ = 120  # saniye
OY_SÜRESİ = 40        # saniye
MIN_PLAYER = 6


def load_roles():
    global roles
    with open("roles.json", "r", encoding="utf-8") as f:
        roles = json.load(f)


def load_languages():
    global languages
    for lang in ["tr", "az"]:
        with open(f"languages/{lang}.json", "r", encoding="utf-8") as f:
            languages[lang] = json.load(f)


def get_text(lang, key):
    return languages.get(lang, {}).get(key, key)


def detect_lang(user):
    # Not: Daha gelişmiş kontrol yapılabilir
    return "tr" if user.language_code == "tr" else "az"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = detect_lang(update.effective_user)
    await update.message.reply_text(get_text(lang, "welcome"))


async def katil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global players, game_started
    lang = detect_lang(update.effective_user)

    if game_started:
        await update.message.reply_text(get_text(lang, "game_already_started"))
        return

    players = [update.effective_user.id]
    await update.message.reply_text(get_text(lang, "join_started"))

    async def wait_for_players():
        await asyncio.sleep(KATILIM_SÜRESİ)
        if len(players) < MIN_PLAYER:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=get_text(lang, "not_enough_players")
            )
            return

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=get_text(lang, "game_starting")
        )
        await baslat_oyun(context, update)

    asyncio.create_task(wait_for_players())


async def baslat_oyun(context, update):
    global game_started, player_roles
    game_started = True

    chat_id = update.effective_chat.id
    random.shuffle(players)
    selected_roles = random.sample(list(roles.keys()), len(players))
    player_roles = dict(zip(players, selected_roles))

    for user_id, rol_key in player_roles.items():
        rol = roles[rol_key]
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"Rolün: {rol['ad']}\nGüç: {rol['guc']}"
            )
        except Exception as e:
            print(f"DM gönderilemedi: {e}")

    await context.bot.send_message(chat_id=chat_id, text="🗳️ Oylama başlıyor...")

    await oylama_süreci(chat_id, context)


async def oylama_süreci(chat_id, context):
    await asyncio.sleep(OY_SÜRESİ)
    secilen = random.choice(players)
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"❌ {secilen} ID'li oyuncu elendi."
    )
    players.remove(secilen)

    # Elenenin özel gücü varsa çalıştır
    if secilen in player_roles:
        await kullan_rol_gucu(secilen, chat_id, context)

    if len(players) <= 1:
        await context.bot.send_message(
            chat_id=chat_id,
            text="🏁 Oyun bitti!"
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text="🗳️ Yeni oylama turu başlıyor..."
        )
        await oylama_süreci(chat_id, context)


def main():
    load_roles()
    load_languages()

    if not TOKEN:
        raise ValueError("BOT_TOKEN ortam değişkeni ayarlanmalı.")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("katil", katil))

    print("Bot çalışıyor...")
    app.run_polling()


if __name__ == "__main__":
    main()
