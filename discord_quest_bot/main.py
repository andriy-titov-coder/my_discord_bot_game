import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

# Завантажуємо змінні з .env файлу
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


# --- Вибір класу ---
class ClassView(discord.ui.View):
    def __init__(self, gender):
        super().__init__(timeout=None)
        self.gender = gender

    @discord.ui.button(label="Воїн", style=discord.ButtonStyle.secondary)
    async def warrior(self, interaction: discord.Interaction, button: discord.ui.Button):
        msg = "Ти став могутнім Воїном!" if self.gender == "male" else "Ти стала могутньою Воїтелькою!"
        await interaction.response.send_message(f"{msg}\nТвій шлях починається тут...")
        self.stop()

    @discord.ui.button(label="Маг", style=discord.ButtonStyle.secondary)
    async def mage(self, interaction: discord.Interaction, button: discord.ui.Button):
        msg = "Ти став мудрим Магом!" if self.gender == "male" else "Ти стала мудрою Магинею!"
        await interaction.response.send_message(f"{msg}\nТвоя магія прокидається...")
        self.stop()

    @discord.ui.button(label="Лучник", style=discord.ButtonStyle.secondary)
    async def archer(self, interaction: discord.Interaction, button: discord.ui.Button):
        msg = "Ти став влучним Лучником!" if self.gender == "male" else "Ти стала влучною Лучницею!"
        await interaction.response.send_message(f"{msg}\nТвоя стріла завжди знайде ціль...")
        self.stop()


# --- Вибір статі ---
class GenderView(discord.ui.View):
    def __init__(self, nickname):
        super().__init__(timeout=None)
        self.nickname = nickname

    @discord.ui.button(label="Чоловіча", style=discord.ButtonStyle.primary)
    async def male(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"Вітаю, {self.nickname}! Оберіть свій клас:", view=ClassView("male"))
        self.stop()

    @discord.ui.button(label="Жіноча", style=discord.ButtonStyle.danger)
    async def female(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"Вітаю, {self.nickname}! Оберіть свій клас:", view=ClassView("female"))
        self.stop()


# --- Головне меню історій ---
class StoryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def start_story(self, interaction: discord.Interaction, story_name: str):
        guild = interaction.guild
        user = interaction.user

        # Створення приватного каналу
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        channel = await guild.create_text_channel(
            name=f"квест-{user.name}",
            overwrites=overwrites,
            category=interaction.channel.category  # Створити в тій же категорії
        )

        await interaction.response.send_message(f"Пригода чекає на тебе тут: {channel.mention}", ephemeral=True)

        await channel.send(f"Ви обрали історію: **{story_name}**.\nДля початку, напиши свій ігровий нікнейм у цей чат:")

        def check(m):
            return m.author == user and m.channel == channel

        try:
            msg = await bot.wait_for('message', check=check, timeout=300)
            nickname = msg.content
            await channel.send(f"Чудове ім'я, **{nickname}**! Тепер обери свою стать:", view=GenderView(nickname))
        except asyncio.TimeoutError:
            await channel.send("Час очікування вийшов. Спробуй ще раз, натиснувши кнопку в головному каналі.")

    @discord.ui.button(label="Хто я", style=discord.ButtonStyle.success)
    async def story_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.start_story(interaction, "Хто я")

    @discord.ui.button(label="Історія 2", style=discord.ButtonStyle.success)
    async def story_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.start_story(interaction, "Історія 2")

    @discord.ui.button(label="Історія 3", style=discord.ButtonStyle.success)
    async def story_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.start_story(interaction, "Історія 3")


# Команда для ініціалізації кнопок у каналі
@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    await ctx.send("Оберіть свою історію:", view=StoryView())


@bot.event
async def on_ready():
    print(f'Бот {bot.user.name} запущений!')


bot.run(TOKEN)