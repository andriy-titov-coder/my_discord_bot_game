import json
import random
from pathlib import Path
from typing import Any, cast

import discord
from discord import ButtonStyle

from ...utils import update_player, load_player, save_player, get_text, get_image
from ..common.encounters import NPCView


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
        data = load_player(interaction.user.id)
        if not data:
            return
            
        cls = data["stats"]["class_name"]
        w_map = {"Воїн": ("wai_sword", "strength", "Меч"), "Маг": ("wai_staff", "magic", "Посох"),
                 "Лучник": ("wai_bow", "agility", "Лук")}
        prefix, stat, name = w_map.get(cls, w_map["Воїн"])

        if name not in data.get("inventory", []):
            update_player(interaction.user.id, {stat: 10}, name)
            status = f"✨ Отримано {name} (+10 {stat})"
        else:
            status = f"У вас вже є {name}."

        txt = get_text(prefix)
        img = get_image(prefix)
        
        await interaction.response.send_message(f"🎲 {res}\n\n{txt}\n\n{status}",
                                                file=discord.File(str(img)) if img.exists() else None)
        
        # Перехід до циклопа після отримання зброї
        await start_cyclops_encounter(interaction)

    async def npc(self, interaction, res):
        txt = get_text("wai_oldman")
        img = get_image("wai_oldman")
        await interaction.response.send_message(f"🎲 {res}\n\n{txt}",
                                                file=discord.File(str(img)) if img.exists() else None, 
                                                view=NPCView(next_encounter_func=start_cyclops_encounter))

    async def empty(self, interaction, res):
        txt = get_text("wai_nothing")
        img = get_image("wai_nothing")
        await interaction.response.send_message(f"🎲 {res}\n\n{txt}",
                                                file=discord.File(str(img)) if img.exists() else None,
                                                view=DirectionView(disable_left=True))


async def start_cyclops_encounter(interaction: discord.Interaction):
    """Початок зустрічі з Циклопом."""
    content = get_text("wai_cyclops_start")
    img_file = get_image("wai_cyclops")
    
    img = discord.File(str(img_file)) if img_file.exists() else None
    
    # Використовуємо followup, бо interaction вже міг бути використаний
    if interaction.response.is_done():
        await interaction.followup.send(content, file=img)
    else:
        await interaction.response.send_message(content, file=img)

class DirectionView(discord.ui.View):
    def __init__(self, disable_left=False):
        super().__init__(timeout=None)
        if disable_left: self.remove_item(self.left)

    @discord.ui.button(label="Ліворуч", style=cast(Any, ButtonStyle.primary))
    async def left(self, interaction, _):
        img = get_image("wai_dice")
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