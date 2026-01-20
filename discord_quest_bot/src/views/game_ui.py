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

        if weapon_name not in player_data.get("inventory", []):
            player_data.setdefault("inventory", []).append(weapon_name)
            player_data["stats"][stat_to_up] += 10

            with open(player_file, "w", encoding="utf-8") as f:
                json.dump(player_data, f, ensure_ascii=False, indent=4)

            status_msg = f"✨ Ви отримали **{weapon_name}**! Ваша характеристика {stat_to_up} збільшена на 10!"
        else:
            status_msg = f"У вас вже є **{weapon_name}**, ви просто міцніше стиснули його в руках."

        content = (res_path / "messages" / f"{file_prefix}.txt").read_text(encoding="utf-8")
        image = discord.File(str(res_path / "images" / f"{file_prefix}.png"), filename="weapon.png")

        await interaction.response.send_message(
            f"🎲 Ви викинули {result}!\n\n{content}\n\n{status_msg}",
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
        base_path = Path(__file__).resolve().parent.parent
        res_path = base_path / "resources"

        start_text = (res_path / "messages" / "oldman" / "wai_oldman_start.txt").read_text(encoding="utf-8")
        start_img = res_path / "images" / "oldman" / "wai_oldman_start.png"

        if start_img.exists():
            file = discord.File(str(start_img), filename="start.png")
            await interaction.response.send_message(start_text, file=file)
        else:
            await interaction.response.send_message(start_text)

        # Запускаємо першу загадку
        view = OldmanQuizView(step=1)
        await view.send_question(interaction)
        self.stop()

    @discord.ui.button(label="Відмовитися", style=cast(Any, ButtonStyle.danger))
    async def decline(self, interaction: discord.Interaction, _: discord.ui.Button):
        view = DirectionView(disable_left=True)
        await interaction.response.send_message(
            "Ви вирішили не ризикувати і повернулися на берег.",
            view=view
        )
        self.stop()


class OldmanQuizView(discord.ui.View):
    """Почергові загадки старого."""

    def __init__(self, step: int):
        super().__init__(timeout=None)
        self.step = step

    async def send_question(self, interaction: discord.Interaction):
        base_path = Path(__file__).resolve().parent.parent
        res_path = base_path / "resources"

        q_text = (res_path / "messages" / "oldman" / f"wai_oldman_question_{self.step}.txt").read_text(encoding="utf-8")
        q_img = res_path / "images" / "oldman" / f"wai_oldman_question_{self.step}.png"

        file_to_send = None
        if q_img.exists():
            file_to_send = discord.File(str(q_img), filename=f"question_{self.step}.png")

        if interaction.response.is_done():
            await interaction.followup.send(q_text, file=file_to_send, view=self)
        else:
            await interaction.response.send_message(q_text, file=file_to_send, view=self)

    async def update_player(self, user_id: int, stat_change: dict = None, item: str = None):
        base_path = Path(__file__).resolve().parent.parent
        player_file = base_path / "players" / f"{user_id}.json"

        with open(player_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if stat_change:
            for stat, value in stat_change.items():
                data["stats"][stat] += value

        if item and item not in data.get("inventory", []):
            data.setdefault("inventory", []).append(item)

        with open(player_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    @discord.ui.button(label="1", style=cast(Any, ButtonStyle.secondary))
    async def option_1(self, interaction: discord.Interaction, _: discord.ui.Button):
        status = ""
        if self.step == 1:
            await self.update_player(interaction.user.id, stat_change={"health": 20}, item="Капелюх")
            status = "✨ Ви отримали **Капелюх** та **+20 HP**"
        elif self.step == 2:
            await self.update_player(interaction.user.id, stat_change={"strength": 10}, item="Рукавиці воїна")
            status = "✨ Ви отримали **Рукавиці воїна** та **+10 Сили**"
        elif self.step == 3:
            await self.update_player(interaction.user.id, stat_change={"health": 15}, item="Знак довіри")
            status = "✨ Ви отримали **Знак довіри** та **+15 HP**"

        await self.show_react(interaction, self.step, status)

    @discord.ui.button(label="2", style=cast(Any, ButtonStyle.secondary))
    async def option_2(self, interaction: discord.Interaction, _: discord.ui.Button):
        status = ""
        if self.step == 1:
            await self.update_player(interaction.user.id, stat_change={"health": -10})
            status = "💔 Ви втратили **10 HP**"
        elif self.step == 2:
            await self.update_player(interaction.user.id, stat_change={"health": 15, "magic": 5})
            status = "✨ Ви отримали **+15 HP** та **+5 Магії**"
        elif self.step == 3:
            await self.update_player(interaction.user.id, stat_change={"health": -5, "magic": 15})
            status = "✨ Ви отримали **+15 Магії**, але втратили **5 HP**"

        await self.show_react(interaction, self.step, status)

    @discord.ui.button(label="3", style=cast(Any, ButtonStyle.secondary))
    async def option_3(self, interaction: discord.Interaction, _: discord.ui.Button):
        status = ""
        if self.step == 1:
            await self.update_player(interaction.user.id, stat_change={"magic": 10}, item="Намисто")
            status = "✨ Ви отримали **Намисто** та **+10 Магії**"
        elif self.step == 2:
            status = "🌿 Старий просто кивнув вам..."
        elif self.step == 3:
            await self.update_player(interaction.user.id, item="Зламаний кубик")
            status = "🎲 Ви отримали **Зламаний кубик** (стане у пригоді для повторного кидка!)"

        await self.show_react(interaction, self.step, status)

    @discord.ui.button(label="4", style=cast(Any, ButtonStyle.secondary))
    async def option_4(self, interaction: discord.Interaction, _: discord.ui.Button):
        status = ""
        if self.step == 1:
            await self.update_player(interaction.user.id, item="Ключ")
            status = "🗝️ Ви отримали **Дивний Ключ**"
        elif self.step == 2:
            await self.update_player(interaction.user.id, stat_change={"health": 20}, item="Потертий амулет")
            status = "✨ Ви отримали **Потертий амулет** та **+20 HP**"
        elif self.step == 3:
            status = "🛡️ Старий дав вам цінну пораду... але про Пентагон промовчав."

        await self.show_react(interaction, self.step, status)

    async def show_react(self, interaction: discord.Interaction, step: int, status_msg: str = ""):
        base_path = Path(__file__).resolve().parent.parent
        res_path = base_path / "resources"

        react_text = (res_path / "messages" / "oldman" / f"wai_oldman_react_{step}.txt").read_text(encoding="utf-8")

        # Додаємо інформацію про отримані речі/стати до тексту старого
        if status_msg:
            full_content = f"{react_text}\n\n{status_msg}"
        else:
            full_content = react_text

        react_img = res_path / "images" / "oldman" / f"wai_oldman_react_{step}.png"

        file_to_send = None
        if react_img.exists():
            file_to_send = discord.File(str(react_img), filename=f"react_{step}.png")

        if file_to_send:
            await interaction.response.send_message(full_content, file=file_to_send)
        else:
            await interaction.response.send_message(full_content)

        self.stop()

        # Логіка для переходу до наступної загадки
        if self.step < 3:
            next_view = OldmanQuizView(step=self.step + 1)
            await next_view.send_question(interaction)
        else:
            # Фінал діалогу
            base_path = Path(__file__).resolve().parent.parent
            close_file = base_path / "resources" / "messages" / "oldman" / "wai_oldman_close.txt"
            close_img = base_path / "resources" / "images" / "oldman" / "wai_oldman_close.png"
        
            close_text = close_file.read_text(encoding="utf-8") if close_file.exists() else "Старий зникає в тумані..."
        
            view = OldmanFinalView()
            if close_img.exists():
                file = discord.File(str(close_img), filename="close.png")
                await interaction.followup.send(close_text, file=file, view=view)
            else:
                await interaction.followup.send(close_text, view=view)


class OldmanFinalView(discord.ui.View):
    """Вибір після завершення всіх загадок."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Повернутися до розвилки", style=cast(Any, ButtonStyle.primary))
    async def go_back(self, interaction: discord.Interaction, _: discord.ui.Button):
        base_path = Path(__file__).resolve().parent.parent
        res_path = base_path / "resources"
        
        # Завантажуємо текст та картинку розвилки
        msg_file = res_path / "messages" / "wai_2.txt"
        img_file = res_path / "images" / "wai_2.png"
        
        content = "Ви повернулися на берег, де шлях розходиться. Тепер ви знаєте, що було ліворуч."
        if msg_file.exists():
            content = msg_file.read_text(encoding="utf-8")
            
        view = DirectionView(disable_left=True)
        
        if img_file.exists():
            file = discord.File(str(img_file), filename="wai_2.png")
            await interaction.response.send_message(content, file=file, view=view)
        else:
            await interaction.response.send_message(content, view=view)
            
        self.stop()

    @discord.ui.button(label="Йти далі", style=cast(Any, ButtonStyle.success))
    async def go_forward(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_message(
            "Ви вирішили не повертатися і рушили вглиб узбережжя, за вогнище старого..."
        )
        # Тут згодом додамо логіку продовження шляху за старим
        self.stop()


class DirectionView(discord.ui.View):
    """Вибір напрямку руху."""

    def __init__(self, disable_left: bool = False):
        super().__init__(timeout=None)
        if disable_left:
            self.remove_item(self.left)

    @discord.ui.button(label="Ліворуч", style=cast(Any, ButtonStyle.primary))
    async def left(self, interaction: discord.Interaction, _: discord.ui.Button):
        base_path = Path(__file__).resolve().parent.parent
        img_path = base_path / "resources" / "images" / "wai_dice.png"

        chance_msg = (
            "Ви йдете на дим і бачите старе вогнище... Ваша доля вирішиться кидком кубика (1-24):\n\n"
            "🎲 **1-8**: Ви знайдете цінну зброю свого класу (+10 до основної характеристики).\n"
            "🎲 **9-16**: Ви зустрінете таємничу постать, що запропонує випробування.\n"
            "🎲 **17-24**: Ви знайдете лише попіл і порожнечу (доведеться повернутися)."
        )

        if img_path.exists():
            file = discord.File(str(img_path), filename="dice.png")
            await interaction.response.send_message(chance_msg, file=file, view=DiceView())
        else:
            await interaction.response.send_message(chance_msg, view=DiceView())

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
            "stats": stats,
            "inventory": []  # Додаємо порожній інвентар
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