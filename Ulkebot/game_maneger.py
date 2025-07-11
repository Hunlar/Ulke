import json
import random
import asyncio

class GameManager:
    def __init__(self, roles_file='roles.json'):
        with open(roles_file, 'r', encoding='utf-8') as f:
            self.roles = json.load(f)
        self.players = {}  # user_id: { "role": role_name, "cooldown": 0 }
        self.active_votes = {}
        self.vote_results = {}
        self.round_number = 0

    def assign_roles(self, user_ids):
        roles_list = list(self.roles.keys())
        random.shuffle(roles_list)

        assigned = {}
        for i, user_id in enumerate(user_ids):
            role = roles_list[i % len(roles_list)]
            assigned[user_id] = {
                "role": role,
                "cooldown": 0,
                "power_used_this_round": False
            }
        self.players = assigned
        return assigned

    def get_player_role(self, user_id):
        return self.players.get(user_id, {}).get("role")

    def can_use_power(self, user_id):
        player = self.players.get(user_id)
        if not player:
            return False
        role = player["role"]
        cooldown = player["cooldown"]
        return cooldown == 0 and not player.get("power_used_this_round", False)

    def use_power(self, user_id):
        player = self.players.get(user_id)
        if not player:
            return False, "Oyuncu bulunamadı."
        role = player["role"]
        if self.can_use_power(user_id):
            cd = self.roles[role]["power_cooldown"]
            player["cooldown"] = cd
            player["power_used_this_round"] = True
            message = self.roles[role]["power_use_message"]
            gif = self.roles[role].get("power_use_gif")
            return True, (message, gif)
        else:
            return False, "Özel güç kullanım hakkınız yok ya da bekleme süreniz devam ediyor."

    def reduce_cooldowns(self):
        for user_id, info in self.players.items():
            if info["cooldown"] > 0:
                info["cooldown"] -= 1
            # Her yeni turda özel güç kullanımını sıfırla
            info["power_used_this_round"] = False

    def start_vote(self, vote_type, candidates):
        # vote_type: örn "eliminate", "manipulate", vb.
        self.active_votes = {
            "type": vote_type,
            "candidates": candidates,
            "votes": {}  # user_id: vote_choice
        }

    def cast_vote(self, voter_id, vote_choice):
        if voter_id not in self.players:
            return False, "Oyuncu bulunamadı."
        if voter_id in self.active_votes["votes"]:
            return False, "Zaten oy kullandınız."
        if vote_choice not in self.active_votes["candidates"]:
            return False, "Geçersiz oy tercihi."
        self.active_votes["votes"][voter_id] = vote_choice
        return True, "Oy kaydedildi."

    def tally_votes(self):
        counts = {}
        for choice in self.active_votes["votes"].values():
            counts[choice] = counts.get(choice, 0) + 1
        self.vote_results = counts
        return counts

    def get_vote_winner(self):
        if not self.vote_results:
            return None
        winner = max(self.vote_results.items(), key=lambda x: x[1])
        return winner[0]

    def remove_player(self, user_id):
        if user_id in self.players:
            del self.players[user_id]

    # Ek fonksiyonlar oyun gereksinimlerine göre eklenebilir
