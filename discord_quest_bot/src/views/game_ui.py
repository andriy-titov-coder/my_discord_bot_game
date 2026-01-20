import json
import random
from pathlib import Path
from typing import Any, cast

import discord
from discord import ButtonStyle


class DiceView(discord.ui.View):
    """Кнопка для кидка кубика."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Кинути кубик 🎲", style=cast(Any, ButtonStyle.success))
    async def roll(self, interaction: discord.Interaction, _: discord.ui.Button):
        result = random.randint(1, 24)
        base_path = Path(__file__).resolve().parent.parent
        resources_path = base_path / "resources"

        if 1 <= result <= 8:
            await self.handle_weapon(interaction, resources_path, result)
        elif 9 <= result <= 16:
            await self.handle_npc(interaction, resources_path, result)
        else:
            await self.handle_empty(interaction, resources_path, result)
        self.stop()

    async def handle_weapon(self, interaction: discord.Interaction, res_path: Path, result: int):
        player_file = res_path.parent / "players" / f"{interaction.user.id}.json"
        with open(player_file, "r", encoding="utf-8") as f:
            player_data = json.load(f)

        class_name = player_data["stats"]["class_name"]

        weapon_map = {
            "Воїн": ("wai_sword", "strength", "Меч"),
            "Маг": ("wai_staff", "magic", "Посох"),
            "Лучник": ("wai_bow", "agility", "Лук")
        }

        file_prefix, stat_to_up, weapon_name = weapon_map.get(class_name, ("wai_sword", "strength", "Меч"))

        player_data["stats"][stat_to_up] += 10
        with open(player_file, "w", encoding="utf-8") as f:
            json.dump(player_data, f, ensure_ascii=False, indent=4)

        content = (res_path / "messages" / f"{file_prefix}.txt").read_text(encoding="utf-8")
        image = discord.File(str(res_path / "images" / f"{file_prefix}.png"), filename="weapon.png")

        await interaction.response.send_message(
            f"🎲 Ви викинули {result}!\n\n{content}\n\n✨ Ваша характеристика {stat_to_up} збільшена на 10!",
            file=image
        )

    async def handle_npc(self, interaction: discord.Interaction, res_path: Path, result: int):
        content = (res_path / "messages" / "wai_oldman.txt").read_text(encoding="utf-8")
        image = discord.File(str(res_path / "images" / "wai_oldman.png"), filename="npc.png")

        view = NPCView()

        await interaction.response.send_message(
            f"🎲 Ви викинули {result}!\n\n{content}\n\nВи згодні відповісти на загадку?",
            file=image,
            view=view
        )

    async def handle_empty(self, interaction: discord.Interaction, res_path: Path, result: int):
        content = (res_path / "messages" / "wai_nothing.txt").read_text(encoding="utf-8")
        image = discord.File(str(res_path / "images" / "wai_nothing.png"), filename="nothing.png")

        view = DirectionView(disable_left=True)
        await interaction.response.send_message(
            f"🎲 Ви викинули {result}!\n\n{content}\n\nТут нічого немає. Доведеться повернутися.",
            file=image,
            view=view
        )


class NPCView(discord.ui.View):
    """Логіка взаємодії з NPC (старим)."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Погодитися", style=cast(Any, ButtonStyle.success))
    async def accept(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_message(
            "Старий посміхається: 'Чудово... Слухай мою першу загадку...'",
            ephemeral=False
        )
        # Тут згодом додамо виклик загадок
        self.stop()

    @discord.ui.button(label="Відмовитися", style=cast(Any, ButtonStyle.danger))
    async def decline(self, interaction: discord.Interaction, _: discord.ui.Button):
        view = DirectionView(disable_left=True)
        await interaction.response.send_message(
            "Ви вирішили не ризикувати і повернулися на берег.",
            view=view
        )
        self.stop()

class DirectionView(discord.ui.View):
    """Вибір напрямку руху."""

    def __init__(self, disable_left: bool = False):
        super().__init__(timeout=None)
        if disable_left:
            self.remove_item(self.left)

    @discord.ui.button(label="Ліворуч", style=cast(Any, ButtonStyle.primary))
    async def left(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_message(
            "Ви йдете на дим і бачите старе вогнище... Здається, ваша доля вирішиться кидком кубика.",
            view=DiceView()
        )
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
        base_path = Path(__file__).resolve().parent.parent
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