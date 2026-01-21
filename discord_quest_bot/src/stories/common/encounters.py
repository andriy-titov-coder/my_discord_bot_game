import discord
from discord import ButtonStyle
from typing import Any, cast
from ...utils import update_player, get_text, get_image

class OldmanFinalView(discord.ui.View):
    def __init__(self, next_encounter_func=None):
        super().__init__(timeout=None)
        self.next_encounter_func = next_encounter_func

    @discord.ui.button(label="Повернутися до розвилки", style=cast(Any, ButtonStyle.primary))
    async def go_back(self, interaction: discord.Interaction, _: discord.ui.Button):
        # Оскільки DirectionView імпортується циклічно, ми зробимо локальний імпорт або 
        # передамо необхідну логіку зовні. Для універсальності краще передавати callback.
        from ..who_am_i.levels import DirectionView
        
        content = get_text("wai_3")
        img_file = get_image("wai_2")
        view = DirectionView(disable_left=True)

        if img_file.exists():
            await interaction.response.send_message(content, file=discord.File(str(img_file)), view=view)
        else:
            await interaction.response.send_message(content, view=view)
        self.stop()

    @discord.ui.button(label="Йти далі", style=cast(Any, ButtonStyle.success))
    async def go_forward(self, interaction: discord.Interaction, _: discord.ui.Button):
        if self.next_encounter_func:
            await self.next_encounter_func(interaction)
        self.stop()

class OldmanQuizView(discord.ui.View):
    def __init__(self, step: int, next_encounter_func=None):
        super().__init__(timeout=None)
        self.step = step
        self.next_encounter_func = next_encounter_func

    async def send_question(self, interaction: discord.Interaction):
        q_text = get_text(f"wai_oldman_question_{self.step}", folder="oldman")
        q_img = get_image(f"wai_oldman_question_{self.step}", folder="oldman")

        file = discord.File(str(q_img)) if q_img.exists() else None
        if interaction.response.is_done():
            await interaction.followup.send(q_text, file=file, view=self)
        else:
            await interaction.response.send_message(q_text, file=file, view=self)

    @discord.ui.button(label="1", style=cast(Any, ButtonStyle.secondary))
    async def opt1(self, interaction, _):
        status = ""
        if self.step == 1:
            update_player(interaction.user.id, {"health": 20}, "Капелюх")
            status = "✨ +20 HP, Капелюх"
        elif self.step == 2:
            update_player(interaction.user.id, {"strength": 10}, "Рукавиці воїна")
            status = "✨ +10 Сили, Рукавиці"
        elif self.step == 3:
            update_player(interaction.user.id, {"health": 15}, "Знак довіри")
            status = "✨ +15 HP, Знак довіри"
        await self.show_react(interaction, status)

    @discord.ui.button(label="2", style=cast(Any, ButtonStyle.secondary))
    async def opt2(self, interaction, _):
        status = ""
        if self.step == 1:
            update_player(interaction.user.id, {"health": -10})
            status = "💔 -10 HP"
        elif self.step == 2:
            update_player(interaction.user.id, {"health": 15, "magic": 5})
            status = "✨ +15 HP, +5 Магії"
        elif self.step == 3:
            update_player(interaction.user.id, {"health": -5, "magic": 15})
            status = "✨ +15 Магії, -5 HP"
        await self.show_react(interaction, status)

    @discord.ui.button(label="3", style=cast(Any, ButtonStyle.secondary))
    async def opt3(self, interaction, _):
        status = ""
        if self.step == 1:
            update_player(interaction.user.id, {"magic": 10}, "Намисто")
            status = "✨ +10 Магії, Намисто"
        elif self.step == 3:
            update_player(interaction.user.id, item="Зламаний кубик")
            status = "🎲 Зламаний кубик"
        await self.show_react(interaction, status)

    @discord.ui.button(label="4", style=cast(Any, ButtonStyle.secondary))
    async def opt4(self, interaction, _):
        status = ""
        if self.step == 1:
            update_player(interaction.user.id, item="Ключ")
            status = "🗝️ Ключ"
        elif self.step == 2:
            update_player(interaction.user.id, {"health": 20}, "Потертий амулет")
            status = "✨ +20 HP, Амулет"
        await self.show_react(interaction, status)

    async def show_react(self, interaction, status):
        react_text = get_text(f"wai_oldman_react_{self.step}", folder="oldman")
        full_msg = f"{react_text}\n\n{status}" if status else react_text
        img = get_image(f"wai_oldman_react_{self.step}", folder="oldman")

        await interaction.response.send_message(full_msg, file=discord.File(str(img)) if img.exists() else None)
        self.stop()

        if self.step < 3:
            await OldmanQuizView(step=self.step + 1, next_encounter_func=self.next_encounter_func).send_question(interaction)
        else:
            close_txt = get_text("wai_oldman_close", folder="oldman")
            close_img = get_image("wai_oldman_close", folder="oldman")
            await interaction.followup.send(close_txt,
                                            file=discord.File(str(close_img)) if close_img.exists() else None,
                                            view=OldmanFinalView(next_encounter_func=self.next_encounter_func))

class NPCView(discord.ui.View):
    def __init__(self, next_encounter_func=None):
        super().__init__(timeout=None)
        self.next_encounter_func = next_encounter_func

    @discord.ui.button(label="Погодитися", style=cast(Any, ButtonStyle.success))
    async def ok(self, interaction, _):
        txt = get_text("wai_oldman_start", folder="oldman")
        img = get_image("wai_oldman_start", folder="oldman")
        await interaction.response.send_message(txt, file=discord.File(str(img)) if img.exists() else None)
        await OldmanQuizView(step=1, next_encounter_func=self.next_encounter_func).send_question(interaction)
        self.stop()

    @discord.ui.button(label="Відмовитися", style=cast(Any, ButtonStyle.danger))
    async def no(self, interaction, _):
        from ..who_am_i.levels import DirectionView
        await interaction.response.send_message("Ви повернулися.", view=DirectionView(disable_left=True))
        self.stop()
