import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# 環境変数を読み込む
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Botの設定
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    print(f'Bot ID: {bot.user.id}')
    print('------')

@bot.command()
async def hello(ctx):
    await ctx.send('こんにちは！私は人狼Botです。')

@bot.command(name="werewolf_help")
async def werewolf_help(ctx):
    embed = discord.Embed(title="人狼Bot コマンド一覧", color=discord.Color.blue())
    embed.add_field(name="!hello", value="挨拶します", inline=False)
    embed.add_field(name="!start", value="ゲームの募集を開始します", inline=False)
    embed.add_field(name="!join", value="ゲームに参加します", inline=False)
    embed.add_field(name="!werewolf_help", value="このヘルプを表示します", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def start(ctx):
    await ctx.send('新しいゲームの募集を開始しました！参加する方は `!join` と入力してください。')

@bot.command()
async def join(ctx):
    await ctx.send(f'{ctx.author.mention} さんがゲームに参加しました！')

# Botを実行
bot.run(TOKEN)
