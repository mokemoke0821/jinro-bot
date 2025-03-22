"""
Discord人狼Bot メインエントリーポイント
"""
import os
import sys
import traceback

# カレントディレクトリをモジュール検索パスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# *** 重要 ***
# Discord.pyのモジュールをロードする前にエラーハンドリングパッチを適用
try:
    import discord_error_patch
    print("Discord error patch loaded")
except ImportError:
    print("WARNING: Could not load discord_error_patch module")

# その他のモジュールをインポート
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

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

# カスタムBotクラスの定義
class JinroBot(commands.Bot):
    async def get_context(self, message, *, cls=commands.Context):
        """カスタムコンテキスト処理"""
        # 元のコンテキスト取得
        ctx = await super().get_context(message, cls=cls)
        
        # コマンド処理カスタマイズ
        if ctx.command and ctx.command.parent and ctx.command.parent.name == 'compose':
            # role_composer関連のコマンドは特別処理
            ctx.suppressed_errors = True
        
        return ctx
    
    async def invoke(self, ctx):
        """コマンド実行のカスタム処理"""
        # composeコマンドのプロアクティブ検出
        if ctx.command and (
            (ctx.command.qualified_name.startswith('compose')) or 
            (hasattr(ctx.command, 'parent') and ctx.command.parent and ctx.command.parent.name == 'compose')
        ):
            # composeコマンドは常にエラー抑制モード
            ctx.suppressed_errors = True
            print(f"[INVOKE] Detected compose command: {ctx.command.qualified_name}")
            
        if hasattr(ctx, 'suppressed_errors') and ctx.suppressed_errors:
            # エラー抑制モード
            try:
                if ctx.command is not None:
                    # 直接実行する代わりに callback を呼び出す
                    # これによりエラーハンドリングパイプラインをバイパス
                    await ctx.command.callback(ctx.command.cog, ctx, *ctx.args[1:], **ctx.kwargs)
                return True
            except Exception as e:
                # エラーをログに記録するが表示はしない
                print(f"[SILENT_ERROR] Error in {ctx.command}: {e}")
                import traceback
                traceback.print_exc()
                return False
        else:
            # 通常の実行
            return await super().invoke(ctx)

# Botの初期化 - エラーハンドラーの登録方法を変更
bot = JinroBot(command_prefix=GameConfig.PREFIX, intents=intents, help_command=None)

# エラーハンドラーが必ず存在するようにプレースホルダを設定
# これにより他のモジュールがbot.on_command_errorを参照してもエラーにならない
bot.on_command_error = lambda ctx, error: None

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
        'utils.database_manager',  # データベース管理
        'utils.role_balancer',     # 役職バランサー
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
    
    try:
        # Cogを読み込む
        await load_extensions()
        print("すべてのCogの読み込みに成功しました")
    except Exception as e:
        print(f"Cogの読み込み中にエラーが発生しました: {e}")
        traceback.print_exc()
    
    print('------')
    
    # プレゼンス（状態）を設定
    await bot.change_presence(activity=discord.Game(name=f"{GameConfig.PREFIX}werewolf_help で使い方を表示"))

# コマンド処理前のフック - メッセージ内容に基づいてエラー表示を制御
@bot.event
async def on_message(message):
    """メッセージを受信したときの処理"""
    # Botのメッセージは無視
    if message.author.bot:
        return
    
    # メッセージからプレフィックスとコマンドを抽出
    if message.content.startswith(bot.command_prefix):
        command_text = message.content[len(bot.command_prefix):]
        
        # compose コマンドの場合は特別処理
        if command_text.startswith('compose'):
            try:
                # コンテキストを作成せずに直接コマンドを検索
                ctx = await bot.get_context(message)
                
                # これはエラーを抑制するためのもの
                ctx.suppressed_errors = True
                
                # コマンド処理を続行
                await bot.process_commands(message)
                return
            except Exception as e:
                print(f"[ON_MESSAGE] Error in compose command preprocessing: {e}")
                # エラーが発生しても通常の処理を続行
    
    # 通常のコマンド処理
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    """コマンドエラー時の処理"""
    # エラー抑制フラグがある場合は何も表示しない
    if hasattr(ctx, 'suppressed_errors') and ctx.suppressed_errors:
        print(f"[ERROR_HANDLER] Suppressed display of error in {ctx.command}: {error}")
        return
    
    # 常に詳細なエラー情報をログに出力（デバッグ用）
    command_name = ctx.command.qualified_name if ctx.command else 'unknown'
    print(f"[ERROR_HANDLER] Error in command '{command_name}': {error}")
    
    # コマンド実行時のエラー（CommandInvokeError）の場合は元の例外を取得
    original_error = error
    if isinstance(error, commands.CommandInvokeError):
        original_error = error.original
        print(f"[ERROR_HANDLER] Original error: {original_error}")
    
    # 特定のコマンドのエラーは無視する
    if ctx.command:
        if ctx.command.qualified_name.startswith('compose'):
            # role_composerコマンドグループのエラーは表示しない
            print(f"[ERROR_HANDLER] Suppressed error in compose command")
            return
    
    # 特定のエラータイプは無視する
    if isinstance(original_error, AttributeError) and "coroutine" in str(original_error).lower():
        print(f"[ERROR_HANDLER] Suppressed coroutine AttributeError")
        return
    
    if "coroutine" in str(error).lower() or "coroutine" in str(original_error).lower():
        print(f"[ERROR_HANDLER] Suppressed coroutine-related error")
        return
    
    # asyncioのエラーは無視
    if isinstance(original_error, asyncio.TimeoutError) or isinstance(original_error, asyncio.CancelledError):
        print(f"[ERROR_HANDLER] Suppressed asyncio error")
        return
    
    # 以下は通常のエラー処理
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
    elif isinstance(error, commands.CheckFailure):
        # 権限不足エラー
        embed = discord.Embed(
            title="権限エラー",
            description="このコマンドを実行する権限がありません。",
            color=EmbedColors.ERROR
        )
        await ctx.send(embed=embed)
    else:
        # 一般的なエラーメッセージ
        embed = discord.Embed(
            title="エラー発生",
            description=f"コマンドの実行中にエラーが発生しました。",
            color=EmbedColors.ERROR
        )
        await ctx.send(embed=embed)

# composeコマンドのエラーメッセージを完全にブロック
@bot.event
async def on_command(ctx):
    """コマンド実行前のフック - composeコマンドの場合はエラーを抑制"""
    # compose コマンドの場合
    if ctx.command and ctx.command.qualified_name.startswith('compose'):
        ctx.suppressed_errors = True
        print(f"[ON_COMMAND] Set suppressed_errors for {ctx.command}")

# パッチモジュールで実装済みのため、ここでの実装は不要になったので削除

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
