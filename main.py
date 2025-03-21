"""
Discord人狼Bot メインエントリーポイント
"""
import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from utils.config import GameConfig

# 環境変数の読み込み
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Intentの設定
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

# Botの初期化
bot = commands.Bot(command_prefix=GameConfig.PREFIX, intents=intents, help_command=None)

# Cogの読み込み
async def load_extensions():
    """すべてのCogを読み込む"""
    cogs = [
        'cogs.game_management',
        'cogs.night_actions',
        'cogs.day_actions',
        'cogs.voting'
    ]
    
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f'Loaded extension: {cog}')
        except Exception as e:
            print(f'Failed to load extension {cog}: {e}')

@bot.event
async def on_ready():
    """Botの準備完了時に呼ばれる"""
    print(f'{bot.user.name} has connected to Discord!')
    print(f'Bot ID: {bot.user.id}')
    print('------')
    
    # Cogを読み込む
    await load_extensions()
    
    # プレゼンス（状態）を設定
    await bot.change_presence(activity=discord.Game(name=f"{GameConfig.PREFIX}werewolf_help で使い方を表示"))

@bot.event
async def on_command_error(ctx, error):
    """コマンドエラー時の処理"""
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"引数が不足しています。`{GameConfig.PREFIX}werewolf_help` でコマンドの使い方を確認してください。")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"引数の形式が正しくありません。{str(error)}")
    else:
        await ctx.send(f"エラーが発生しました: {str(error)}")
        print(f"Command error: {error}")

# Botの起動
if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN環境変数が設定されていません。")
        print(".envファイルを確認してください。")
        exit(1)
    
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("ERROR: Discordへのログインに失敗しました。トークンが正しいか確認してください。")
    except Exception as e:
        print(f"ERROR: Botの起動中にエラーが発生しました: {e}")
