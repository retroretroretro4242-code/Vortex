import discord
from discord.ext import commands
from discord.ui import View, Select, Button
from dotenv import load_dotenv
import os
import datetime

load_dotenv()
TOKEN = os.getenv("TOKEN")

# =========================
# IDLER
# =========================
CATEGORY_ID = 1480796146510332120
LOG_CHANNEL = 1480796145608556691
JOIN_CHANNEL = 1480796146271129759
LEAVE_CHANNEL = 1480796146271129759
AUTO_ROLE = 1480796145591648432
VALORANT_ROLE = 1480796145579200582
MINECRAFT_ROLE = 1480796145570676779
INVITE_LOG_CHANNEL = 1480796146510332118  # invite log kanalı

YETKILI_ROLLER = [
    1480796145608556685,
    1480796145600172131,
    1480796145600172130
]

INVITE_ROLE_THRESHOLD = 5  # 5 invite = rol ödülü

# =========================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# Invite Tracker
# =========================
invites_cache = {}  # guild_id: {code: uses}
member_inviter = {}  # member.id: inviter.id
invite_counts = {}   # inviter.id: total_invites

# =========================
def yetkili_mi(member):
    return any(role.id in YETKILI_ROLLER for role in member.roles)

# =========================
@bot.event
async def on_ready():
    for guild in bot.guilds:
        invites_cache[guild.id] = await guild.invites()
        await bot.tree.sync(guild=guild)  # Guild bazlı sync
    print(f"Bot aktif: {bot.user}")

# =========================
# MEMBER JOIN
# =========================
@bot.event
async def on_member_join(member):
    guild = member.guild

    # Oto rol
    role = guild.get_role(AUTO_ROLE)
    if role:
        await member.add_roles(role)

    # DM mesajı
    try:
        dm_embed = discord.Embed(
            title="👋 Sunucuya Hoş Geldin!",
            description=f"""
Merhaba **{member.name}** 🎉

🏰 Towny Klan Sunucumuza hoş geldin!

⚔️ Klan kur
🏠 Şehir oluştur
💰 Ekonomi kas
🤝 Arkadaş edin

İyi eğlenceler!
""",
            color=0x2ecc71
        )
        dm_embed.set_thumbnail(url=guild.icon.url if guild.icon else member.display_avatar.url)
        await member.send(embed=dm_embed)
    except:
        pass

    # Invite sistemi
    invites_before = {inv.code: inv.uses for inv in invites_cache.get(guild.id, [])}
    invites_after = await guild.invites()

    for inv in invites_after:
        if inv.code in invites_before:
            if inv.uses > invites_before[inv.code]:
                inviter = inv.inviter
                if (datetime.datetime.utcnow() - member.created_at).days >= 7:  # fake kontrol
                    member_inviter[member.id] = inviter.id
                    invite_counts[inviter.id] = invite_counts.get(inviter.id, 0) + 1

                    # Rol ödülü
                    if invite_counts[inviter.id] == INVITE_ROLE_THRESHOLD:
                        await inviter.add_roles(guild.get_role(AUTO_ROLE))

                # Invite log
                log_channel = guild.get_channel(INVITE_LOG_CHANNEL)
                if log_channel:
                    embed = discord.Embed(
                        title="📨 Yeni Davet",
                        description=f"👤 {member.mention} **{inviter}** tarafından davet edildi!",
                        color=0xFFD700
                    )
                    await log_channel.send(embed=embed)
        invites_cache[guild.id] = invites_after

    # Join log
    join_channel = guild.get_channel(JOIN_CHANNEL)
    if join_channel:
        embed = discord.Embed(
            title="✅ Yeni Üye Katıldı",
            description=f"👤 {member.mention}\n🆔 `{member.id}`\n📅 Hesap: <t:{int(member.created_at.timestamp())}:R>",
            color=0x57F287
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Toplam Üye: {guild.member_count}")
        await join_channel.send(embed=embed)

# =========================
# MEMBER LEAVE
# =========================
@bot.event
async def on_member_remove(member):
    guild = member.guild
    leave_channel = guild.get_channel(LEAVE_CHANNEL)
    if leave_channel:
        embed = discord.Embed(
            title="📤 Üye Ayrıldı",
            description=f"👤 {member.name}\n🆔 `{member.id}`",
            color=0xED4245
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Toplam Üye: {guild.member_count}")
        await leave_channel.send(embed=embed)

# =========================
# SLASH KOMUTLAR
# =========================
@bot.tree.command(name="invites")
async def invites(interaction: discord.Interaction):
    total = invite_counts.get(interaction.user.id, 0)
    embed = discord.Embed(
        title=f"📊 {interaction.user.name} Davet Bilgisi",
        description=f"Toplam geçerli davet: **{total}**",
        color=0x5865F2
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="inviteleaderboard")
async def invite_leaderboard(interaction: discord.Interaction):
    leaderboard = sorted(invite_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    description = ""
    for i, (user_id, count) in enumerate(leaderboard, start=1):
        user = interaction.guild.get_member(user_id)
        if user:
            description += f"**{i}.** {user.mention} → {count} davet\n"
    embed = discord.Embed(title="🏆 Invite Leaderboard", description=description or "Davet yok", color=0xFFD700)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="inviter")
async def inviter(interaction: discord.Interaction, member: discord.Member):
    inviter_id = member_inviter.get(member.id)
    if inviter_id:
        inviter_user = interaction.guild.get_member(inviter_id)
        text = f"{member.mention} kişisini davet eden: {inviter_user.mention}"
    else:
        text = f"{member.mention} kişisini davet eden bulunamadı."
    await interaction.response.send_message(text, ephemeral=True)

@bot.tree.command(name="invitereset")
async def invite_reset(interaction: discord.Interaction, member: discord.Member):
    if not yetkili_mi(interaction.user):
        return await interaction.response.send_message("Yetkin yok.", ephemeral=True)
    inviter_id = member_inviter.pop(member.id, None)
    if inviter_id:
        invite_counts[inviter_id] -= 1
        await interaction.response.send_message(f"{member.mention} davet bilgisi sıfırlandı.", ephemeral=True)
    else:
        await interaction.response.send_message("Davet bilgisi bulunamadı.", ephemeral=True)

# =========================
# ROL BUTONLARI
# =========================
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

@bot.tree.command(name="roller")
async def roller(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎭 Rol Seçimi",
        description="Butonlara basarak rol alabilirsiniz.",
        color=0x5865F2
    )
    await interaction.response.send_message(embed=embed, view=RoleButtons())

# =========================
# MODERATION KOMUTLARI
# =========================
@bot.tree.command(name="ban")
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "Sebep belirtilmedi"):
    if not interaction.user.guild_permissions.ban_members:
        return await interaction.response.send_message("Yetkin yok.", ephemeral=True)
    await user.ban(reason=reason)
    await interaction.response.send_message(f"{user} banlandı.")

@bot.tree.command(name="kick")
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str = "Sebep belirtilmedi"):
    if not interaction.user.guild_permissions.kick_members:
        return await interaction.response.send_message("Yetkin yok.", ephemeral=True)
    await user.kick(reason=reason)
    await interaction.response.send_message(f"{user} atıldı.")

@bot.tree.command(name="clear")
async def clear(interaction: discord.Interaction, amount: int):
    if not interaction.user.guild_permissions.manage_messages:
        return await interaction.response.send_message("Yetkin yok.", ephemeral=True)
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(f"{amount} mesaj silindi.", ephemeral=True)

# =========================
# TICKET SYSTEM (Panel, Buttons, Select)
# =========================
class TicketButtons(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Talebi Devral", emoji="🛠️", style=discord.ButtonStyle.primary)
    async def claim(self, interaction: discord.Interaction, button: Button):
        if not yetkili_mi(interaction.user):
            return await interaction.response.send_message("Yetkili değilsin.", ephemeral=True)
        embed = discord.Embed(description=f"🛠️ Ticket {interaction.user.mention} tarafından devralındı.", color=0x3498db)
        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="Ticket Kapat", emoji="🔒", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: Button):
        if not yetkili_mi(interaction.user):
            return await interaction.response.send_message("Yetkili değilsin.", ephemeral=True)
        await interaction.response.send_message("Ticket 5 saniye içinde kapanıyor...")
        log_channel = interaction.guild.get_channel(LOG_CHANNEL)
        if log_channel:
            await log_channel.send(f"📁 {interaction.channel.name} kapatıldı • {interaction.user}")
        await discord.utils.sleep_until(discord.utils.utcnow() + datetime.timedelta(seconds=5))
        await interaction.channel.delete()

class TicketSelect(Select):
    def __init__(self):
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
        overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False),
                      interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
        yetkili_mentions = []
        for role_id in YETKILI_ROLLER:
            role = guild.get_role(role_id)
            overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            yetkili_mentions.append(role.mention)
        channel = await guild.create_text_channel(name=name, category=category, overwrites=overwrites)
        embed = discord.Embed(
            title="🎫 Destek Talebi Oluşturuldu",
            description=f"👤 {interaction.user.mention}\n📂 {self.values[0]}\n\n⏳ Yetkililer sizinle ilgilenecek.\n📌 Kurallar\n• Spam yok\n• Saygılı olun\n• Sorunu detaylı anlatın",
            color=0x2b2d31
        )
        embed.set_footer(text="Vortex Destek Sistemi")
        await channel.send(" ".join(yetkili_mentions), embed=embed, view=TicketButtons())
        await interaction.response.send_message(f"Ticket oluşturuldu: {channel.mention}", ephemeral=True)

class TicketPanel(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

@bot.tree.command(name="ticketpanel")
async def ticketpanel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎫 Vortex • Destek Merkezi",
        description="""Sunucu ekibiyle iletişime geçmek için aşağıdan bir kategori seçin.
━━━━━━━━━━━━━━━━━━
🤝 **Partner Başvuru**
🆘 **Yardım & Destek**
👥 **Ekip Alım**
⚠️ **Şikayet & Bildirim**
━━━━━━━━━━━━━━━━━━
📌 **Bilgilendirme**
• Gereksiz ticket açmayın  
• Yetkilileri spam pinglemeyin  
• Sorununuzu detaylı anlatın  
• Ticket bitince kapatılır
⏳ Yetkililer en kısa sürede sizinle ilgilenecektir.
""",
        color=0x5865F2
    )
    embed.set_footer(text="Vortex Destek Sistemi", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
    embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
    await interaction.response.send_message(embed=embed, view=TicketPanel())

bot.run(TOKEN)
