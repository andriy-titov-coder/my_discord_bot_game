import json
import random
from pathlib import Path
from typing import Any, cast

import discord
from discord import ButtonStyle

# Базовий шлях до ресурсів
BASE_RES = Path(__file__).resolve().parent.parent.parent / "resources"


class OldmanFinalView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Повернутися до розвилки", style=cast(Any, ButtonStyle.primary))
    async def go_back(self, interaction: discord.Interaction, _: discord.ui.Button):
        msg_file = BASE_RES / "messages" / "wai_3.txt"
        img_file = BASE_RES / "images" / "wai_2.png"

        content = msg_file.read_text(encoding="utf-8") if msg_file.exists() else "Ви повернулися."
        view = DirectionView(disable_left=True)

        if img_file.exists():
            await interaction.response.send_message(content, file=discord.File(str(img_file)), view=view)
        else:
            await interaction.response.send_message(content, view=view)
        self.stop()

    @discord.ui.button(label="Йти далі", style=cast(Any, ButtonStyle.success))
    async def go_forward(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_message("Ви рушили далі вглиб берега...")
        self.stop()


class OldmanQuizView(discord.ui.View):
    def __init__(self, step: int):
        super().__init__(timeout=None)
        self.step = step

    async def send_question(self, interaction: discord.Interaction):
        q_text = (BASE_RES / "messages" / "oldman" / f"wai_oldman_question_{self.step}.txt").read_text(encoding="utf-8")
        q_img = BASE_RES / "images" / "oldman" / f"wai_oldman_question_{self.step}.png"

        file = discord.File(str(q_img)) if q_img.exists() else None
        if interaction.response.is_done():
            await interaction.followup.send(q_text, file=file, view=self)
        else:
            await interaction.response.send_message(q_text, file=file, view=self)

    async def update_player(self, user_id: int, stat_change: dict = None, item: str = None):
        player_file = BASE_RES.parent / "players" / f"{user_id}.json"
        with open(player_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if stat_change:
            for stat, val in stat_change.items(): data["stats"][stat] += val
        if item and item not in data.get("inventory", []):
            data.setdefault("inventory", []).append(item)
        with open(player_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    @discord.ui.button(label="1", style=cast(Any, ButtonStyle.secondary))
    async def opt1(self, interaction, _):
        status = ""
        if self.step == 1:
            await self.update_player(interaction.user.id, {"health": 20}, "Капелюх")
            status = "✨ +20 HP, Капелюх"
        elif self.step == 2:
            await self.update_player(interaction.user.id, {"strength": 10}, "Рукавиці воїна")
            status = "✨ +10 Сили, Рукавиці"
        elif self.step == 3:
            await self.update_player(interaction.user.id, {"health": 15}, "Знак довіри")
            status = "✨ +15 HP, Знак довіри"
        await self.show_react(interaction, status)

    @discord.ui.button(label="2", style=cast(Any, ButtonStyle.secondary))
    async def opt2(self, interaction, _):
        status = ""
        if self.step == 1:
            await self.update_player(interaction.user.id, {"health": -10})
            status = "💔 -10 HP"
        elif self.step == 2:
            await self.update_player(interaction.user.id, {"health": 15, "magic": 5})
            status = "✨ +15 HP, +5 Магії"
        elif self.step == 3:
            await self.update_player(interaction.user.id, {"health": -5, "magic": 15})
            status = "✨ +15 Магії, -5 HP"
        await self.show_react(interaction, status)

    @discord.ui.button(label="3", style=cast(Any, ButtonStyle.secondary))
    async def opt3(self, interaction, _):
        status = ""
        if self.step == 1:
            await self.update_player(interaction.user.id, {"magic": 10}, "Намисто")
            status = "✨ +10 Магії, Намисто"
        elif self.step == 3:
            await self.update_player(interaction.user.id, item="Зламаний кубик")
            status = "🎲 Зламаний кубик"
        await self.show_react(interaction, status)

    @discord.ui.button(label="4", style=cast(Any, ButtonStyle.secondary))
    async def opt4(self, interaction, _):
        status = ""
        if self.step == 1:
            await self.update_player(interaction.user.id, item="Ключ")
            status = "🗝️ Ключ"
        elif self.step == 2:
            await self.update_player(interaction.user.id, {"health": 20}, "Потертий амулет")
            status = "✨ +20 HP, Амулет"
        await self.show_react(interaction, status)

    async def show_react(self, interaction, status):
        base = BASE_RES / "messages" / "oldman"
        react_text = (base / f"wai_oldman_react_{self.step}.txt").read_text(encoding="utf-8")
        full_msg = f"{react_text}\n\n{status}" if status else react_text
        img = BASE_RES / "images" / "oldman" / f"wai_oldman_react_{self.step}.png"

        await interaction.response.send_message(full_msg, file=discord.File(str(img)) if img.exists() else None)
        self.stop()

        if self.step < 3:
            await OldmanQuizView(step=self.step + 1).send_question(interaction)
        else:
            close_txt = (base / "wai_oldman_close.txt").read_text(encoding="utf-8")
            close_img = BASE_RES / "images" / "oldman" / "wai_oldman_close.png"
            await interaction.followup.send(close_txt,
                                            file=discord.File(str(close_img)) if close_img.exists() else None,
                                            view=OldmanFinalView())


class NPCView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.button(label="Погодитися", style=cast(Any, ButtonStyle.success))
    async def ok(self, interaction, _):
        txt = (BASE_RES / "messages" / "oldman" / "wai_oldman_start.txt").read_text(encoding="utf-8")
        img = BASE_RES / "images" / "oldman" / "wai_oldman_start.png"
        await interaction.response.send_message(txt, file=discord.File(str(img)) if img.exists() else None)
        await OldmanQuizView(step=1).send_question(interaction)
        self.stop()

    @discord.ui.button(label="Відмовитися", style=cast(Any, ButtonStyle.danger))
    async def no(self, interaction, _):
        await interaction.response.send_message("Ви повернулися.", view=DirectionView(disable_left=True))
        self.stop()


class DiceView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Кинути кубик 🎲", style=cast(Any, ButtonStyle.success))
    async def roll(self, interaction, _):
        res = random.randint(1, 24)
        if 1 <= res <= 8:
            await self.weapon(interaction, res)
        elif 9 <= res <= 16:
            await self.npc(interaction, res)
        else:
            await self.empty(interaction, res)
        self.stop()

    async def weapon(self, interaction, res):
        p_file = BASE_RES.parent / "players" / f"{interaction.user.id}.json"
        with open(p_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        cls = data["stats"]["class_name"]
        w_map = {"Воїн": ("wai_sword", "strength", "Меч"), "Маг": ("wai_staff", "magic", "Посох"),
                 "Лучник": ("wai_bow", "agility", "Лук")}
        prefix, stat, name = w_map.get(cls, w_map["Воїн"])

        if name not in data.get("inventory", []):
            data.setdefault("inventory", []).append(name)
            data["stats"][stat] += 10
            with open(p_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            status = f"✨ Отримано {name} (+10 {stat})"
        else:
            status = f"У вас вже є {name}."

        txt = (BASE_RES / "messages" / f"{prefix}.txt").read_text(encoding="utf-8")
        img = BASE_RES / "images" / f"{prefix}.png"
        await interaction.response.send_message(f"🎲 {res}\n\n{txt}\n\n{status}",
                                                file=discord.File(str(img)) if img.exists() else None)

    async def npc(self, interaction, res):
        txt = (BASE_RES / "messages" / "wai_oldman.txt").read_text(encoding="utf-8")
        img = BASE_RES / "images" / "wai_oldman.png"
        await interaction.response.send_message(f"🎲 {res}\n\n{txt}",
                                                file=discord.File(str(img)) if img.exists() else None, view=NPCView())

    async def empty(self, interaction, res):
        txt = (BASE_RES / "messages" / "wai_nothing.txt").read_text(encoding="utf-8")
        img = BASE_RES / "images" / "wai_nothing.png"
        await interaction.response.send_message(f"🎲 {res}\n\n{txt}",
                                                file=discord.File(str(img)) if img.exists() else None,
                                                view=DirectionView(disable_left=True))


class DirectionView(discord.ui.View):
    def __init__(self, disable_left=False):
        super().__init__(timeout=None)
        if disable_left: self.remove_item(self.left)

    @discord.ui.button(label="Ліворуч", style=cast(Any, ButtonStyle.primary))
    async def left(self, interaction, _):
        img = BASE_RES / "images" / "wai_dice.png"
        chance_msg = (
            "Ви йдете на дим і бачите старе вогнище... Ваша доля вирішиться кидком кубика (1-24):\n\n"
            "🎲 **1-8**: Ви знайдете цінну зброю свого класу (+10 до основної характеристики).\n"
            "🎲 **9-16**: Ви зустрінете таємничу постать, що запропонує випробування.\n"
            "🎲 **17-24**: Ви знайдете лише попіл і порожнечу (доведеться повернутися)."
        )

        
        file = discord.File(str(img)) if img.exists() else None
        await interaction.response.send_message(chance_msg, file=file, view=DiceView())
        self.stop()

    @discord.ui.button(label="Прямо", style=cast(Any, ButtonStyle.primary))
    async def straight(self, interaction, _):
        await interaction.response.send_message("Ви пішли до лісу...")
        self.stop()

    @discord.ui.button(label="Праворуч", style=cast(Any, ButtonStyle.primary))
    async def right(self, interaction, _):
        await interaction.response.send_message("Ви пішли до руїн...")
        self.stop()