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
AUTO_ROLE = 1480796145591648432

VALORANT_ROLE = 1480796145579200582
MINECRAFT_ROLE = 1480796145570676779

YETKILI_ROLLER = [
1480796145608556685,
1480796145600172131,
1480796145600172130
]

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


# -----------------------------
# MEMBER JOIN
# -----------------------------

@bot.event
async def on_member_join(member):

    role = member.guild.get_role(AUTO_ROLE)

    if role:
        await member.add_roles(role)

    channel = member.guild.system_channel

    if channel:

        embed = discord.Embed(
            title="👋 Sunucuya Hoş Geldin!",
            description=f"""
🎉 **Hoş geldin {member.mention}!**

🏰 **Towny Klan Sunucumuza katıldığın için mutluyuz.**

⚔️ Klan kurabilir ve savaşlara katılabilirsin  
🏠 Towny ile şehir kurabilirsin  
💰 Ekonomi sistemi ile gelişebilirsin  
🤝 Yeni arkadaşlar edinebilirsin
""",
            color=0x2ecc71
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        await channel.send(embed=embed)


# -----------------------------
# REACTION ROLE
# -----------------------------

class RoleButtons(View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Valorant", emoji="🎯", style=discord.ButtonStyle.red)
    async def valorant(self, interaction: discord.Interaction, button: Button):

        role = interaction.guild.get_role(VALORANT_ROLE)

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message("Valorant rolü kaldırıldı.", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("Valorant rolü verildi.", ephemeral=True)


    @discord.ui.button(label="Minecraft", emoji="⛏️", style=discord.ButtonStyle.green)
    async def minecraft(self, interaction: discord.Interaction, button: Button):

        role = interaction.guild.get_role(MINECRAFT_ROLE)

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message("Minecraft rolü kaldırıldı.", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("Minecraft rolü verildi.", ephemeral=True)


@bot.tree.command(name="roller", description="Rol alma paneli")
async def roller(interaction: discord.Interaction):

    embed = discord.Embed(
        title="🎭 Rol Seçimi",
        description="""
Aşağıdaki butonlara basarak rol alabilirsiniz.

🎯 Valorant  
⛏️ Minecraft
""",
        color=0x5865F2
    )

    await interaction.response.send_message(embed=embed, view=RoleButtons())


# -----------------------------
# MODERATION COMMANDS
# -----------------------------

@bot.tree.command(name="ban", description="Kullanıcıyı banlar")
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "Sebep belirtilmedi"):

    if not interaction.user.guild_permissions.ban_members:
        return await interaction.response.send_message("Yetkin yok.", ephemeral=True)

    await user.ban(reason=reason)

    await interaction.response.send_message(f"{user} banlandı.")


@bot.tree.command(name="kick", description="Kullanıcıyı atar")
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str = "Sebep belirtilmedi"):

    if not interaction.user.guild_permissions.kick_members:
        return await interaction.response.send_message("Yetkin yok.", ephemeral=True)

    await user.kick(reason=reason)

    await interaction.response.send_message(f"{user} sunucudan atıldı.")


@bot.tree.command(name="clear", description="Mesaj temizler")
async def clear(interaction: discord.Interaction, amount: int):

    if not interaction.user.guild_permissions.manage_messages:
        return await interaction.response.send_message("Yetkin yok.", ephemeral=True)

    await interaction.channel.purge(limit=amount)

    await interaction.response.send_message(f"{amount} mesaj silindi.", ephemeral=True)


# -----------------------------
# TICKET SYSTEM (Geliştirilmiş)
# -----------------------------

class TicketView(View):
    def __init__(self, user: discord.Member):
        super().__init__(timeout=None)
        self.user = user

        self.add_item(TicketSelect(user))

class TicketSelect(Select):
    def __init__(self, user: discord.Member):

        self.user = user
        options = [
            discord.SelectOption(label="Partner Başvuru", emoji="🤝"),
            discord.SelectOption(label="Yardım", emoji="🆘"),
            discord.SelectOption(label="Ekip Alım", emoji="👥"),
            discord.SelectOption(label="Şikayet", emoji="⚠️"),
        ]

        super().__init__(placeholder="Bir kategori seç...", options=options)

    async def callback(self, interaction: discord.Interaction):

        guild = interaction.guild
        category = guild.get_channel(CATEGORY_ID)

        name = f"ticket-{interaction.user.name}".lower()

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        for role_id in YETKILI_ROLLER:
            role = guild.get_role(role_id)
            overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(name=name, category=category, overwrites=overwrites)

        # Ticket açıldı mesajı
        yetkililer = " ".join([f"<@&{r}>" for r in YETKILI_ROLLER])
        embed = discord.Embed(
            title="🎫 Destek Talebi Açıldı",
            description=f"{interaction.user.mention} destek talebi oluşturdu.\n\n{yetkililer} buraya bakabilir.\n\nLütfen talebinizi açıklayıcı şekilde yazın.",
            color=0x2b2d31,
            timestamp=datetime.datetime.utcnow()
        )

        await channel.send(embed=embed, view=TicketButtons(user=interaction.user))
        await interaction.response.send_message(f"Ticket oluşturuldu: {channel.mention}", ephemeral=True)


class TicketButtons(View):
    def __init__(self, user: discord.Member):
        super().__init__(timeout=None)
        self.user = user

    @discord.ui.button(label="Talebi Devral", style=discord.ButtonStyle.primary, emoji="🛠️")
    async def claim(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(f"{interaction.user.mention} talebi devraldı.", ephemeral=False)

    @discord.ui.button(label="Ticket Kapat", style=discord.ButtonStyle.red, emoji="❌")
    async def close(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Ticket 5 saniye içinde kapatılacak...", ephemeral=True)
        await discord.utils.sleep_until(datetime.datetime.utcnow() + datetime.timedelta(seconds=5))
        await interaction.channel.delete()


class TicketPanel(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelectPlaceholder())

class TicketSelectPlaceholder(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Ticket Oluştur", emoji="🎫", description="Destek talebi oluştur")
        ]
        super().__init__(placeholder="Bir ticket oluştur...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Ticket oluşturmak için aşağıdaki menüden bir kategori seçmelisin.", ephemeral=True)


@bot.tree.command(name="ticketpanel", description="Ticket paneli oluşturur")
async def ticketpanel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎫 Klan Destek Merkezi",
        description="""
Aşağıdaki menüden destek kategorisini seçerek ticket oluşturabilirsiniz.

🤝 Partner Başvuru  
🆘 Yardım  
👥 Ekip Alım  
⚠️ Şikayet

Butonlarla ticketi devralabilir veya kapatabilirsiniz.
""",
        color=0x5865F2
    )

    await interaction.response.send_message(embed=embed, view=TicketView(interaction.user))

# -----------------------------
# READY
# -----------------------------

@bot.event
async def on_ready():

    await bot.tree.sync()

    print(f"Bot aktif: {bot.user}")


bot.run(TOKEN)
