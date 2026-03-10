import discord
from discord.ext import commands
from discord.ui import View, Select, Button
from dotenv import load_dotenv
import os
import datetime

load_dotenv()
TOKEN = os.getenv("TOKEN")

CATEGORY_ID = 1480796146510332120
LOG_CHANNEL = 1480796145608556691

YETKILI_ROLLER = [
1480796145608556685,
1480796145600172131,
1480796145600172130
]

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


# TICKET SELECT MENU

class TicketSelect(Select):
    def __init__(self):

        options = [
            discord.SelectOption(label="Partner Başvuru", emoji="🤝"),
            discord.SelectOption(label="Yardım", emoji="🆘"),
            discord.SelectOption(label="Ekip Alım", emoji="👥"),
            discord.SelectOption(label="Şikayet", emoji="⚠️"),
        ]

        super().__init__(
            placeholder="Bir kategori seç...",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):

        guild = interaction.guild
        category = guild.get_channel(CATEGORY_ID)

        name = f"ticket-{interaction.user.name}".lower()

        for c in guild.channels:
            if c.name == name:
                await interaction.response.send_message("Zaten açık ticketın var.", ephemeral=True)
                return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        for role_id in YETKILI_ROLLER:
            role = guild.get_role(role_id)
            overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(name=name, category=category, overwrites=overwrites)

        embed = discord.Embed(
            title="🎫 Ticket Açıldı",
            description=f"{interaction.user.mention} destek talebi oluşturdu.",
            color=0x2b2d31
        )

        embed.add_field(name="Kategori", value=self.values[0])
        embed.set_footer(text="Yetkililer sizinle ilgilenecek.")

        await channel.send(
            content=f"{interaction.user.mention}",
            embed=embed,
            view=TicketButtons()
        )

        await interaction.response.send_message(
            f"Ticket oluşturuldu: {channel.mention}",
            ephemeral=True
        )


class TicketPanel(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


# BUTTONS

class TicketButtons(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Ticket Kapat", emoji="🔒", style=discord.ButtonStyle.red)
    async def close(self, interaction: discord.Interaction, button: Button):

        await interaction.channel.send("Ticket 5 saniye içinde kapanacak.")
        await discord.utils.sleep_until(datetime.datetime.utcnow() + datetime.timedelta(seconds=5))
        await interaction.channel.edit(name="closed-ticket")


    @discord.ui.button(label="Ticket Sil", emoji="🧹", style=discord.ButtonStyle.gray)
    async def delete(self, interaction: discord.Interaction, button: Button):

        log = interaction.guild.get_channel(LOG_CHANNEL)

        messages = []
        async for msg in interaction.channel.history(limit=None, oldest_first=True):
            messages.append(f"{msg.author}: {msg.content}")

        transcript = "\n".join(messages)

        file = discord.File(
            fp=bytes(transcript, "utf-8"),
            filename="transcript.txt"
        )

        embed = discord.Embed(
            title="📁 Ticket Log",
            description=f"Ticket silindi\nKanal: {interaction.channel.name}",
            color=discord.Color.red()
        )

        await log.send(embed=embed, file=file)

        await interaction.channel.delete()


# SLASH COMMAND

@bot.tree.command(name="ticketpanel", description="Ticket paneli oluşturur")
async def ticketpanel(interaction: discord.Interaction):

    embed = discord.Embed(
        title="🎫 Klan Destek Merkezi",
        description="""
Aşağıdaki menüden destek kategorisini seçerek ticket oluşturabilirsiniz.

**Kategoriler**
🤝 Partner Başvuru  
🆘 Yardım  
👥 Ekip Alım  
⚠️ Şikayet  

⚠️ Gereksiz ticket açmayın.
""",
        color=0x5865F2
    )

    embed.set_footer(text="Destek ekibi en kısa sürede ilgilenecektir.")

    await interaction.response.send_message(
        embed=embed,
        view=TicketPanel()
    )


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot aktif: {bot.user}")


bot.run(TOKEN)
