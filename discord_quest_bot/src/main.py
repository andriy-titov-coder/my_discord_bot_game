import asyncio
from pathlib import Path
from typing import Any, cast

import discord
from discord import ButtonStyle
from discord.ext import commands

# Імпортуємо наші нові View
from views.game_ui import GenderView

# Спробуємо імпортувати конфіг відносно розташування файлу
try:
    from config import DISCORD_TOKEN
except ImportError:
    from discord_quest_bot.src.config import DISCORD_TOKEN

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


class StoryView(discord.ui.View):
    """Головне меню історій."""

    def __init__(self):
        super().__init__(timeout=None)

    @staticmethod
    async def start_story(interaction: discord.Interaction, story_name: str):
        # Переконаємось, що команда запущена в гільдії
        guild = interaction.guild
        user = interaction.user

        if guild is None:
            await interaction.response.send_message(  # type: ignore
                "Цю команду потрібно виконувати на сервері (не в приватних повідомленнях).",
                ephemeral=True,
            )
            return

        # Перевірка прав бота у гільдії
        bot_member = guild.me or guild.get_member(bot.user.id)
        if bot_member is None:
            await interaction.response.send_message(  # type: ignore
                "Не вдалося визначити учасника бота у гільдії.", ephemeral=True
            )
            return

        if not bot_member.guild_permissions.manage_channels:
            await interaction.response.send_message(  # type: ignore
                "Помилка: У бота немає дозволу 'Керування каналами'.",
                ephemeral=True,
            )
            return

        # Налаштування приватності каналу
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            bot_member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        # Спроба створити приватний канал у тій же категорії (якщо є)
        category = None
        if interaction.channel is not None:
            category = interaction.channel.category

        try:
            channel = await guild.create_text_channel(
                name=f"квест-{user.name}",
                overwrites=overwrites,
                category=category,
                reason=f"Створено приватний квест-канал для {user}",
            )
        except discord.Forbidden:
            await interaction.response.send_message(  # type: ignore
                "Помилка: Бот не має прав для створення каналів.", ephemeral=True
            )
            return
        except discord.HTTPException as exc:
            await interaction.response.send_message(  # type: ignore
                f"Помилка Discord API при створенні каналу: {exc}", ephemeral=True
            )
            return

        await interaction.response.send_message(  # type: ignore
            f"Пригода чекає на тебе тут: {channel.mention}", ephemeral=True
        )

        # Визначаємо шляхи до ресурсів відносно файлу
        base_path = Path(__file__).resolve().parent
        resources_path = base_path / "resources"

        content = f"Ви обрали історію: **{story_name}**."
        file_to_send = None

        if story_name == "Хто я":
            msg_file = resources_path / "messages" / "who_am_i.txt"
            img_file = resources_path / "images" / "who_am_i.png"

            if msg_file.exists():
                try:
                    content = msg_file.read_text(encoding="utf-8")
                except OSError:
                    # Якщо не вдалось прочитати файл через права доступу або іншу системну помилку
                    pass

            if img_file.exists():
                try:
                    file_to_send = discord.File(str(img_file), filename="story.png")
                except (OSError, discord.DiscordException):
                    # Лог для дебагу, якщо файл пошкоджено або він недоступний
                    print(f"DEBUG: Не вдалося створити discord.File з {img_file}")

        # Надсилаємо контент (без file=None)
        if file_to_send:
            await channel.send(content, file=file_to_send)
        else:
            await channel.send(content)

        await channel.send("Спробуйте пригадати як вас звуть:")

        def check(m: discord.Message) -> bool:
            return m.author == user and m.channel == channel

        try:
            msg = await bot.wait_for("message", check=check, timeout=300)
            nickname = msg.content.strip()
            if not nickname:
                await channel.send("Ім'я не може бути пустим. Спробуйте ще раз.")
                return

            await channel.send(
                f"Чудове ім'я, **{nickname}**! Тепер обери свою стать:",
                view=GenderView(nickname),
            )
        except asyncio.TimeoutError:
            await channel.send(
                "Час очікування вийшов. Спробуй ще раз, натиснувши кнопку в головному каналі."
            )

    @discord.ui.button(label="Хто я", style=cast(Any, ButtonStyle.success))
    async def story_1(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self.start_story(interaction, "Хто я")

    @discord.ui.button(label="Історія 2", style=cast(Any, ButtonStyle.success))
    async def story_2(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self.start_story(interaction, "Історія 2")

    @discord.ui.button(label="Історія 3", style=cast(Any, ButtonStyle.success))
    async def story_3(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self.start_story(interaction, "Історія 3")


@bot.tree.command(name="choice_story", description="Почати вибір історії")
async def setup(interaction: discord.Interaction):
    await interaction.response.send_message(  # type: ignore
        "Оберіть свою історію:", view=StoryView(), ephemeral=True
    )


@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        print("Slash-команди синхронізовано!")
    except discord.HTTPException as e:
        print(f"Помилка синхронізації: {e}")
    print(f'Бот {bot.user.name} запущений!')


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
