import random
import json
from telegram.ext import ContextTypes

# Roller dosyasını yükle (roles.json aynı klasörde olmalı)
with open("roles.json", "r", encoding="utf-8") as f:
    roles = json.load(f)

players = []          # Oyuncu user_id listesi
player_roles = {}     # {user_id: rol_key} formatında oyuncu rolleri


def set_players(player_list):
    global players
    players = player_list


def set_roles(role_mapping):
    global player_roles
    player_roles = role_mapping


async def kullan_rol_gucu(user_id: int, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """
    Oyuncunun rolüne göre özel gücünü uygular ve varsa GIF gönderir.
    """
    if user_id not in player_roles:
        return

    rol_key = player_roles[user_id]
    rol = roles.get(rol_key)

    if not rol:
        return

    # GIF varsa gönder
    gif_url = rol.get("gif")
    if gif_url:
        try:
            await context.bot.send_animation(
                chat_id=chat_id,
                animation=gif_url,
                caption=f"🎭 {rol['ad']} rolü harekete geçti!",
            )
        except Exception as e:
            print(f"[HATA] GIF gönderilemedi: {e}")

    # Rolün özel gücünü uygula
    if rol_key == "osmanli":
        hedefler = [p for p in players if p != user_id]
        if not hedefler:
            await context.bot.send_message(chat_id=chat_id, text="İnfaz edilecek kimse kalmadı.")
            return
        hedef = random.choice(hedefler)
        players.remove(hedef)
        await context.bot.send_message(chat_id=chat_id, text=f"🇹🇷 Osmanlı, oyuncu {hedef} kişisini infaz etti.")

    elif rol_key == "german":
        await context.bot.send_message(chat_id=chat_id, text="🇩🇪 German İmparatorluğu kaos çıkardı! Sadece kendisi oy kullanabilir.")

    elif rol_key == "biritanya":
        await context.bot.send_message(chat_id=chat_id, text="🇬🇧 Britanya başka ülkenin oylamasını manipüle etti.")

    elif rol_key == "pdm":
        await context.bot.send_message(
            chat_id=chat_id,
            text="🏳️‍🌈 Pembe Dünya Direnişçileri meydanda: *“Götümüz başımız ayrı oynuyor, biz ibneler buradayız!”*",
            parse_mode="Markdown"
        )

    else:
        await context.bot.send_message(chat_id=chat_id, text=f"{rol['ad']} özel gücünü kullandı.")
