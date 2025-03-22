"""
Discord人狼Bot メインエントリーポイント
"""
import os
import asyncio
import sys
import discord
from discord.ext import commands
from dotenv import load_dotenv

# カレントディレクトリをモジュール検索パスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from utils.config import GameConfig, EmbedColors

# 環境変数の読み込み
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# データディレクトリが存在することを確認
for directory in [GameConfig.DATA_DIR, GameConfig.CONFIG_DIR, GameConfig.STATS_DIR, GameConfig.LOG_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

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
    # views モジュールが存在するか確認し、存在しない場合はインポートエラーを防ぐために空のパッケージを作成
    views_dir = os.path.join(current_dir, 'views')
    if not os.path.exists(views_dir):
        try:
            os.makedirs(views_dir, exist_ok=True)
            init_file = os.path.join(views_dir, '__init__.py')
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f:
                    f.write('"""投票UI用のViewsパッケージ"""')
            print("Created views package directory and __init__.py file")
        except Exception as e:
            print(f"Warning: Failed to create views package: {e}")

    # 基本的なユーティリティCogを先に読み込む
    utility_cogs = [
        'utils.role_balancer',   # 役職バランサー
    ]
    
    # コア機能のCog
    core_cogs = [
        'cogs.game_management',  # ゲーム管理
        'cogs.night_actions',    # 夜のアクション
        'cogs.day_actions',      # 昼のアクション
        'cogs.voting',           # 投票システム
    ]
    
    # 管理系のCog
    admin_cogs = [
        'cogs.admin',            # 管理者コマンド
    ]
    
    # 統計情報とフィードバック系のCog
    stats_cogs = [
        'cogs.stats',            # 統計情報
        'cogs.feedback',         # フィードバック
    ]
    
    # 追加機能のCog
    additional_cogs = [
        'cogs.rules_manager',    # ルール管理
        'cogs.role_composer',    # 役職構成管理
        'cogs.community',        # コミュニティ提案システム
        'cogs.balance',          # ゲームバランス調整システム
        'cogs.documentation'     # ドキュメント管理
    ]
    
    # 全てのCogを読み込む
    all_cogs = utility_cogs + core_cogs + admin_cogs + stats_cogs + additional_cogs
    
    for cog in all_cogs:
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
        embed = discord.Embed(
            title="引数不足",
            description=f"引数が不足しています。`{GameConfig.PREFIX}werewolf_help` でコマンドの使い方を確認してください。",
            color=EmbedColors.ERROR
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.BadArgument):
        embed = discord.Embed(
            title="引数エラー",
            description=f"引数の形式が正しくありません。{str(error)}",
            color=EmbedColors.ERROR
        )
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="エラー発生",
            description=f"エラーが発生しました: {str(error)}",
            color=EmbedColors.ERROR
        )
        await ctx.send(embed=embed)
        print(f"Command error: {error}")

# Botの起動
if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN環境変数が設定されていません。")
        print(".envファイルを確認してください。")
        exit(1)
    
    # 依存パッケージのチェック
    try:
        import aiohttp
        print("aiohttp パッケージが正常に読み込まれました")
    except ImportError:
        print("ERROR: aiohttp パッケージがインストールされていません。")
        print("pip install -r requirements.txt を実行してください。")
        exit(1)
    
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("ERROR: Discordへのログインに失敗しました。トークンが正しいか確認してください。")
    except Exception as e:
        print(f"ERROR: Botの起動中にエラーが発生しました: {e}")
