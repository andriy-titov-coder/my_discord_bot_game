import json
import random
from pathlib import Path
from typing import Any, cast

import discord
from discord import ButtonStyle

try:
    from utils import save_player, get_text, get_image
except ImportError:
    from discord_quest_bot.src.utils import save_player, get_text, get_image




class ClassView(discord.ui.View):
    """Вибір класу персонажа."""

    def __init__(self, nickname: str, gender: str):
        super().__init__(timeout=None)
        self.nickname = nickname
        self.gender = gender

    async def send_next_part(self, interaction: discord.Interaction):
        # Використовуємо повний шлях до модуля
        try:
            from stories.who_am_i.levels import DirectionView
        except ImportError:
            from discord_quest_bot.src.stories.who_am_i.levels import DirectionView
        
        content = get_text("wai_2")
        img_file = get_image("wai_2")

        file_to_send = None

        if img_file.exists():
            file_to_send = discord.File(str(img_file), filename="wai_2.png")

        view = DirectionView()
        if file_to_send:
            await interaction.followup.send(content, file=file_to_send, view=view)
        else:
            await interaction.followup.send(content, view=view)

    async def create_player_file(self, interaction: discord.Interaction, class_key: str):
        base_path = Path(__file__).resolve().parent.parent
        template_path = base_path / "resources" / "classes" / f"{class_key}.json"

        with open(template_path, "r", encoding="utf-8") as f:
            stats = json.load(f)

        player_data = {
            "nickname": self.nickname,
            "gender": self.gender,
            "user_id": interaction.user.id,
            "stats": stats,
            "inventory": []  # Додаємо порожній інвентар
        }

        save_player(interaction.user.id, player_data)

        return stats

    @discord.ui.button(label="Воїн", style=cast(Any, ButtonStyle.secondary))
    async def warrior(self, interaction: discord.Interaction, _: discord.ui.Button):
        stats = await self.create_player_file(interaction, "warrior")
        msg = "Ти став могутнім Воїном!" if self.gender == "male" else "Ти стала могутньою Воїтелькою!"
        await interaction.response.send_message(f"{msg}\nЖиття: {stats['health']}, Сила: {stats['strength']}")
        await self.send_next_part(interaction)
        self.stop()

    @discord.ui.button(label="Маг", style=cast(Any, ButtonStyle.secondary))
    async def mage(self, interaction: discord.Interaction, _: discord.ui.Button):
        stats = await self.create_player_file(interaction, "mage")
        msg = "Ти став мудрим Магом!" if self.gender == "male" else "Ти стала мудрою Магинею!"
        await interaction.response.send_message(f"{msg}\nМагія: {stats['magic']}, Життя: {stats['health']}")
        await self.send_next_part(interaction)
        self.stop()

    @discord.ui.button(label="Лучник", style=cast(Any, ButtonStyle.secondary))
    async def archer(self, interaction: discord.Interaction, _: discord.ui.Button):
        stats = await self.create_player_file(interaction, "archer")
        msg = "Ти став влучним Лучником!" if self.gender == "male" else "Ти стала влучною Лучницею!"
        await interaction.response.send_message(f"{msg}\nСпритність: {stats['agility']}, Життя: {stats['health']}")
        await self.send_next_part(interaction)
        self.stop()


class GenderView(discord.ui.View):
    def __init__(self, nickname: str):
        super().__init__(timeout=None)
        self.nickname = nickname

    @discord.ui.button(label="Чоловіча", style=cast(Any, ButtonStyle.primary))
    async def male(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_message(f"Вітаю, {self.nickname}! Оберіть клас:",
                                                view=ClassView(self.nickname, "male"))
        self.stop()

    @discord.ui.button(label="Жіноча", style=cast(Any, ButtonStyle.danger))
    async def female(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_message(f"Вітаю, {self.nickname}! Оберіть клас:",
                                                view=ClassView(self.nickname, "female"))
        self.stop()