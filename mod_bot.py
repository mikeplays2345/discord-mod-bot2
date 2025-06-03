import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions
import json
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="?", intents=intents)

def load_warnings():
    if not os.path.exists("warnings.json"):
        with open("warnings.json", "w") as f:
            json.dump({}, f)
    with open("warnings.json", "r") as f:
        return json.load(f)

def save_warnings(warnings):
    with open("warnings.json", "w") as f:
        json.dump(warnings, f, indent=4)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
@has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason=None):
    warnings = load_warnings()
    user_id = str(member.id)

    if user_id not in warnings:
        warnings[user_id] = []
    warnings[user_id].append({"reason": reason, "mod": str(ctx.author)})

    save_warnings(warnings)

    warn_count = len(warnings[user_id])
    await ctx.send(f"{member.mention} has been warned. Total warnings: {warn_count}. Reason: {reason}")

    # Auto punishments
    if warn_count == 3:
        await member.timeout(discord.utils.utcnow() + discord.timedelta(minutes=30), reason="3 warnings")
        await ctx.send(f"{member.mention} has been muted for 30 minutes due to 3 warnings.")
    elif warn_count == 5:
        await member.kick(reason="5 warnings")
        await ctx.send(f"{member.mention} has been kicked due to 5 warnings.")
    elif warn_count == 7:
        await member.ban(reason="7 warnings")
        await ctx.send(f"{member.mention} has been banned due to 7 warnings.")

@bot.command()
@has_permissions(manage_messages=True)
async def warnings(ctx, member: discord.Member):
    warnings = load_warnings()
    user_id = str(member.id)

    if user_id in warnings and warnings[user_id]:
        embed = discord.Embed(title=f"Warnings for {member}", color=discord.Color.orange())
        for i, entry in enumerate(warnings[user_id], 1):
            embed.add_field(name=f"#{i}", value=f"Reason: {entry['reason']}\nMod: {entry['mod']}", inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"{member.mention} has no warnings.")

@bot.command()
@has_permissions(manage_messages=True)
async def mute(ctx, member: discord.Member, duration: int = 10, *, reason=None):
    await member.timeout(discord.utils.utcnow() + discord.timedelta(minutes=duration), reason=reason)
    await ctx.send(f"{member.mention} has been muted for {duration} minutes. Reason: {reason}")

@bot.command()
@has_permissions(manage_messages=True)
async def clearwarnings(ctx, member: discord.Member):
    warnings = load_warnings()
    user_id = str(member.id)
    if user_id in warnings:
        del warnings[user_id]
        save_warnings(warnings)
        await ctx.send(f"All warnings for {member.mention} have been cleared.")
    else:
        await ctx.send(f"{member.mention} has no warnings.")

@warn.error
@warnings.error
@mute.error
@clearwarnings.error
async def missing_perms_error(ctx, error):
    if isinstance(error, MissingPermissions):
        await ctx.send("You do not have permission to use this command.")

bot.run(os.getenv("DISCORD_TOKEN"))
