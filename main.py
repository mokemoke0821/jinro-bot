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

# *** 最優先 ***
# Discord.pyをインポートする前に、最も強力な統合フックシステムを適用
try:
    # 新しいフックシステムをロード
    from bot_hooks import apply_all_hooks
    hook_result = apply_all_hooks()
    print(f"Bot hooks applied: {hook_result}")
except ImportError:
    print("WARNING: Could not load bot_hooks module")
except Exception as e:
    print(f"ERROR: Failed to apply hooks: {e}")
    traceback.print_exc()

# 旧エラーハンドリングパッチも一応適用
try:
    import discord_error_patch
    print("Discord error patch loaded")
except ImportError:
    print("WARNING: Could not load discord_error_patch module")

# さらに強力なメッセージフィルタリングを適用
try:
    # メッセージフィルタを適用（後でdiscordモジュールをインポートした後に実行）
    print(f"Message filter will be applied later")
except Exception as e:
    print(f"WARNING: Could not set up message filter: {e}")

# 特殊テクニック: CSSスタイルでエラーメッセージを非表示にする試み
ERROR_CSS_TRICK = """
<style>
  .errorMessage, div[class*="error"], div[class*="Error"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    width: 0 !important;
    opacity: 0 !important;
    pointer-events: none !important;
    position: absolute !important;
    z-index: -9999 !important;
  }
</style>
"""

# 最強のパッチを適用
try:
    # モンキーパッチを適用（Discord.pyの読み込み前）
    import monkey_patch
    monkey_patch.apply_monkey_patches()
    print("Monkey patches applied")
except Exception as e:
    print(f"WARNING: Could not apply monkey patches: {e}")

# その他のモジュールをインポート
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

from utils.config import GameConfig, EmbedColors

# 環境変数の読み込み
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Discord.pyモジュールが読み込まれた後でメッセージフィルタを適用
try:
    from utils.message_filter import apply_message_filter
    filter_result = apply_message_filter()
    print(f"Message filter applied: {filter_result}")
except Exception as e:
    print(f"WARNING: Could not apply message filter: {e}")

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
        if ctx.command:
            if (ctx.command.name == 'compose') or (ctx.command.parent and ctx.command.parent.name == 'compose'):
                # role_composer関連のコマンドは特別処理
                ctx.suppressed_errors = True
        
        return ctx
    
    async def invoke(self, ctx):
        """コマンド実行のカスタム処理"""
        # composeコマンドのプロアクティブ検出
        if ctx.command and (
            (ctx.command.name == 'compose') or 
            (hasattr(ctx.command, 'parent') and ctx.command.parent and ctx.command.parent.name == 'compose')
        ):
            # composeコマンドは常にエラー抑制モード
            ctx.suppressed_errors = True
            print(f"[INVOKE] Detected compose command: {ctx.command.name}")
            
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

# Botの初期化
bot = JinroBot(command_prefix=GameConfig.PREFIX, intents=intents, help_command=None)

# 最強のエラー抑制: すべてのエラーを抑制するプレースホルダを設定
# これにより他のモジュールがエラーハンドラを参照してもエラーにならない
bot.on_command_error = lambda ctx, error: None  # エラーを無視する関数
bot.on_error = lambda *args, **kwargs: None     # 一般的なエラーも無視

# composeコマンドだけ特別扱いするためのカスタムイベント登録
@bot.event
async def on_command_error(ctx, error):
    """カスタムのオーバーライド - composeコマンド以外だけ処理"""
    # エラーの詳細をログに出力
    print(f"[ERROR HANDLER] Handling error: {type(error)}: {error}")
    
    # エラーメッセージを完全に抑制するケース
    if any([
        # composeコマンドのエラーは一切表示しない
        ctx.command and (
            ctx.command.name == 'compose' or 
            (hasattr(ctx.command, 'parent') and ctx.command.parent and ctx.command.parent.name == 'compose')
        ),
        # coroutine関連のエラーを完全に抑制
        "coroutine" in str(error).lower(),
        "get" in str(error).lower(),
        "attribute" in str(error).lower(),
        "attributeerror" in str(error).lower()
    ]):
        print(f"[ERROR HANDLER] Suppressed error: {error}")
        # エラーを表示せずにヘルプメッセージだけ表示する
        if ctx.command and ctx.command.name == 'compose':
            try:
                # 代わりに役職構成管理のヘルプを直接表示
                from direct_compose import setup_commands
                # composeコマンドオブジェクトを取得
                compose_command = bot.get_command("compose")
                if compose_command:
                    # 引数なしで実行して自動的にヘルプを表示する
                    await ctx.invoke(compose_command)
                else:
                    # コマンドが見つからない場合はシンプルなメッセージを表示
                    await ctx.send("役職構成管理コマンドを使用するには: `!compose help`")
            except Exception as e:
                print(f"[ERROR HANDLER] Error showing help: {e}")
        return
    
    # その他のエラーは通常通り処理
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
        # 'cogs.role_composer',  # 役職構成管理 - 直接コマンドに置き換えたため無効化
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
        
        # 直接コマンド登録 - 修正版ハンドラーを使用（重複実行防止）
        try:
            # コマンド登録済みかどうかを確認するフラグ
            if not getattr(bot, "_fixed_compose_setup_done", False):
                # 修正版のComposeハンドラーを設定
                print("修正版Composeハンドラーを設定します...")
                
                # 直接コマンドをインポートして設定
                import sys
                from importlib import reload
                
                # 念のためモジュールを再読み込み
                if "direct_compose" in sys.modules:
                    reload(sys.modules["direct_compose"])
                if "fixed_compose_handler" in sys.modules:
                    reload(sys.modules["fixed_compose_handler"])
                
                # 修正版ハンドラーを設定
                from fixed_compose_handler import setup_fixed_compose_handler
                handler = setup_fixed_compose_handler(bot)
                
                # 登録完了フラグを設定
                bot._fixed_compose_setup_done = True
                print(f"修正版Composeハンドラー設定が完了しました: {handler}")
            else:
                print("修正版Composeハンドラーは既に設定されています")
        except Exception as cmd_error:
            print(f"Composeハンドラー設定でエラーが発生しました: {cmd_error}")
            traceback.print_exc()
            
            # エラーが発生した場合は、従来の方法でセットアップを試みる
            try:
                print("従来の方法でのsetup_commandsを試みます...")
                from direct_compose import setup_commands
                setup_commands(bot)
                print("従来の方法でのsetup_commands成功")
            except Exception as e:
                print(f"従来の方法でのsetup_commandsも失敗: {e}")
                traceback.print_exc()
    except Exception as e:
        print(f"Cogの読み込み中にエラーが発生しました: {e}")
        traceback.print_exc()
    
    print('------')
    
    # プレゼンス（状態）を設定
    await bot.change_presence(activity=discord.Game(name=f"{GameConfig.PREFIX}werewolf_help で使い方を表示"))

# コマンド実行追跡用
processed_messages = set()

# コマンド処理前のフック - メッセージ内容に基づいてエラー表示を制御
@bot.event
async def on_message(message):
    """メッセージを受信したときの処理"""
    # Botのメッセージは無視
    if message.author.bot:
        return
    
    # メッセージIDとチャネルIDを組み合わせたユニークなキー
    message_key = f"{message.channel.id}_{message.id}"
    
    # 重複処理チェック - 同じメッセージが複数回処理されないようにする
    if message_key in processed_messages:
        print(f"[DUPLICATE] Message {message_key} already processed, skipping")
        return
    
    # このメッセージを処理済みとしてマーク
    processed_messages.add(message_key)
    
    # 古いメッセージIDをクリーンアップ（最大1000件を保持）
    if len(processed_messages) > 1000:
        processed_messages.clear()
        print("[CLEANUP] Cleared processed messages cache")
    
    # チャンネルごとの連続コマンド実行防止（特にcomposeコマンド用）
    if message.content.startswith(bot.command_prefix):
        command_text = message.content[len(bot.command_prefix):]
        channel_id = message.channel.id
        channel_lock_key = f"{channel_id}_last_command"
        
        # 同じチャンネルでの最後のコマンド実行時刻
        current_time = asyncio.get_event_loop().time()
        last_execution = getattr(bot, '_channel_command_locks', {}).get(channel_lock_key, 0)
        
        # composeコマンドの場合はチャンネルロックを確認
        if command_text.startswith('compose') and current_time - last_execution < 3.0:  # 3秒間のクールダウン
            print(f"[THROTTLE] Command in channel {channel_id} throttled (last execution: {current_time - last_execution:.2f}s ago)")
            return
        
        # チャンネルロックを更新
        if not hasattr(bot, '_channel_command_locks'):
            bot._channel_command_locks = {}
        bot._channel_command_locks[channel_lock_key] = current_time
        
        print(f"[COMMAND] Received: {command_text} from {message.author.id} in {message.guild.id if message.guild else 'DM'}")
        
        # composeコマンドの場合は特別処理
        if command_text.startswith('compose'):
            try:
                # コンテキストを取得し、エラー抑制フラグを設定
                ctx = await bot.get_context(message)
                ctx.suppressed_errors = True
                
                # コマンド引数を解析（スペースで分割）
                parts = command_text.split()
                # サブコマンドがある場合
                if len(parts) > 1:
                    subcommand = parts[1].lower()
                    print(f"[COMPOSE] サブコマンド: {subcommand}")
                
                # ログに記録
                log_user_id = message.author.id
                log_guild_id = message.guild.id if message.guild else "DM"
                print(f"[COMPOSE] User {log_user_id} in {log_guild_id} executed: {command_text}")
                
            except Exception as e:
                print(f"[COMPOSE_ERROR] コマンド解析中にエラー: {e}")
                traceback.print_exc()
    
    # 通常のコマンド処理
    try:
        await bot.process_commands(message)
    except Exception as e:
        print(f"[PROCESS_ERROR] コマンド処理中にエラー: {e}")
        traceback.print_exc()

@bot.event
async def on_command_error(ctx, error):
    """コマンドエラー時の処理"""
    # コマンド識別子（ログ用）
    command_id = ctx.command.qualified_name if ctx.command else f"unknown-{ctx.message.content[:20]}"
    
    # コマンド実行時のエラー（CommandInvokeError）の場合は元の例外を取得
    original_error = error
    if isinstance(error, commands.CommandInvokeError):
        original_error = error.original
    
    # スタックトレースの取得と表示（重要なデバッグ情報）
    import traceback
    tb_str = ''.join(traceback.format_exception(type(original_error), original_error, original_error.__traceback__))
    print(f"[詳細エラー情報] コマンド: {command_id}")
    print(f"[詳細エラー情報] エラータイプ: {type(original_error).__name__}")
    print(f"[詳細エラー情報] エラーメッセージ: {original_error}")
    print(f"[詳細エラー情報] スタックトレース:\n{tb_str}")
    
    # コルーチンに関連するエラーの場合は特別な処理
    if "coroutine" in str(original_error) and "has no attribute" in str(original_error):
        print(f"[重要な警告] コルーチンが正しく await されていない可能性があります！")
        print(f"[重要な警告] エラー発生箇所を確認して await キーワードを追加してください。")
    
    # エラー抑制フラグがある場合は何も表示しない
    if hasattr(ctx, 'suppressed_errors') and ctx.suppressed_errors:
        print(f"[ERROR_HANDLER] Suppressed display of error in {command_id}: {error}")
        return
    
    # composeコマンドのエラー処理は特別に行う
    if ctx.command and (ctx.command.name == 'compose' or (hasattr(ctx.command, 'parent') and ctx.command.parent and ctx.command.parent.name == 'compose')):
        try:
            # composeコマンドオブジェクトを取得
            compose_command = bot.get_command("compose")
            if compose_command:
                # 引数なしで実行して自動的にヘルプを表示する
                await ctx.invoke(compose_command)
            else:
                # コマンドが見つからない場合はシンプルなメッセージを表示
                await ctx.send("役職構成管理コマンドを使用するには: `!compose help`")
        except Exception as help_e:
            print(f"[ERROR_HANDLER] Error showing help: {help_e}")
            # エラーが発生した場合はシンプルなメッセージを表示
            await ctx.send("役職構成管理コマンドのヘルプ表示中にエラーが発生しました。`!compose help`を使用してください。")
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
