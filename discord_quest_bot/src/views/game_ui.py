import json
from pathlib import Path
from typing import Any, cast

import discord
from discord import ButtonStyle


class DirectionView(discord.ui.View):
    """Вибір напрямку руху."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Ліворуч", style=cast(Any, ButtonStyle.primary))
    async def left(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_message("Ви вирушили ліворуч до диму...")
        self.stop()

    @discord.ui.button(label="Прямо", style=cast(Any, ButtonStyle.primary))
    async def straight(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_message("Ви пішли прямо стежкою до лісу...")
        self.stop()

    @discord.ui.button(label="Праворуч", style=cast(Any, ButtonStyle.primary))
    async def right(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_message("Ви піднімаєтесь праворуч до руїн...")
        self.stop()


class ClassView(discord.ui.View):
    """Вибір класу персонажа."""

    def __init__(self, nickname: str, gender: str):
        super().__init__(timeout=None)
        self.nickname = nickname
        self.gender = gender

    async def send_next_part(self, interaction: discord.Interaction):
        base_path = Path(__file__).resolve().parent.parent  # Повертаємось до src/
        resources_path = base_path / "resources"

        msg_file = resources_path / "messages" / "wai_2.txt"
        img_file = resources_path / "images" / "wai_2.png"

        content = "Ви зробили свій вибір. Що далі?"
        file_to_send = None

        if msg_file.exists():
            content = msg_file.read_text(encoding="utf-8")
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
        players_dir = base_path / "players"
        players_dir.mkdir(exist_ok=True)

        player_file = players_dir / f"{interaction.user.id}.json"

        with open(template_path, "r", encoding="utf-8") as f:
            stats = json.load(f)

        player_data = {
            "nickname": self.nickname,
            "gender": self.gender,
            "user_id": interaction.user.id,
            "stats": stats
        }

        with open(player_file, "w", encoding="utf-8") as f:
            json.dump(player_data, f, ensure_ascii=False, indent=4)

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