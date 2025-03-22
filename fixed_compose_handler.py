"""
コマンド重複実行問題を解決するためのパッチモジュール
"""
import asyncio
import discord
from discord.ext import commands
import functools
import time
import traceback

# グローバルロックシステム
_GLOBAL_LOCKS = {}
_PROCESSED_MESSAGES = set()
_LAST_CLEANUP = time.time()

def process_once(func):
    """
    各メッセージを確実に1回だけ処理するデコレータ
    """
    @functools.wraps(func)
    async def wrapper(ctx, *args, **kwargs):
        # メッセージIDと時間に基づくユニークなキー
        message_id = ctx.message.id
        key = f"msg_{message_id}"
        
        # 既に処理済みの場合は早期リターン
        if key in _PROCESSED_MESSAGES:
            print(f"[DUPE] メッセージ {message_id} は既に処理済みです")
            return None
        
        # 処理済みとしてマーク
        _PROCESSED_MESSAGES.add(key)
        
        # 古いエントリーをクリーンアップ（30分ごと）
        global _LAST_CLEANUP
        now = time.time()
        if now - _LAST_CLEANUP > 1800:  # 30分
            _PROCESSED_MESSAGES.clear()
            _LAST_CLEANUP = now
            print("[CLEANUP] 処理済みメッセージキャッシュをクリア")
        
        # 実際の処理を実行
        try:
            return await func(ctx, *args, **kwargs)
        except Exception as e:
            print(f"[ERROR] {func.__name__}でエラー発生: {e}")
            traceback.print_exc()
            return None
    
    return wrapper

def channel_lock(timeout=5.0):
    """
    チャンネルごとにコマンドをロックするデコレータ
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(ctx, *args, **kwargs):
            # チャンネルIDに基づくロックキー
            channel_id = ctx.channel.id
            command_name = func.__name__
            lock_key = f"lock_{channel_id}_{command_name}"
            
            # 既にロックされている場合は早期リターン
            if lock_key in _GLOBAL_LOCKS:
                print(f"[LOCK] チャンネル {channel_id} の {command_name} はロック中")
                return None
            
            # ロックを設定
            _GLOBAL_LOCKS[lock_key] = True
            
            try:
                # 実行
                return await func(ctx, *args, **kwargs)
            finally:
                # タイムアウト後にロックを解除
                async def release_lock():
                    await asyncio.sleep(timeout)
                    if lock_key in _GLOBAL_LOCKS:
                        del _GLOBAL_LOCKS[lock_key]
                        print(f"[UNLOCK] チャンネル {channel_id} の {command_name} のロックを解除")
                
                asyncio.create_task(release_lock())
        
        return wrapper
    return decorator

class ComposeHandler:
    """
    リデザインされたComposeコマンドハンドラ
    """
    def __init__(self, bot, direct_compose):
        self.bot = bot
        self.direct_compose = direct_compose
        
        # モジュールから必要な関数とデータを取得
        self.logger = direct_compose.logger
        self.PRESETS = direct_compose.PRESETS
        self.load_config = direct_compose.load_config
        self.save_config = direct_compose.save_config
        self.check_balance = direct_compose.check_balance
        
        # 実行済みメッセージIDを追跡
        self.processed_messages = set()
        
        # ハンドラーの登録
        self.register_handlers()
    
    def register_handlers(self):
        """コマンドハンドラーをBotに登録"""
        # 既存のcomposeコマンドを削除
        if self.bot.get_command("compose"):
            self.bot.remove_command("compose")
            self.logger.info("既存のcomposeコマンドを削除")
        
        # 新しいcomposeコマンドグループを追加
        compose_group = commands.Group(
            name="compose",
            callback=self.compose_main,
            help="役職構成管理コマンド",
            invoke_without_command=True
        )
        
        # サブコマンドを追加
        compose_group.add_command(commands.Command(
            name="help",
            callback=self.compose_help,
            help="役職構成管理のヘルプを表示"
        ))
        
        compose_group.add_command(commands.Command(
            name="presets",
            callback=self.compose_presets,
            help="利用可能なプリセット一覧を表示"
        ))
        
        compose_group.add_command(commands.Command(
            name="apply",
            callback=self.compose_apply,
            help="プリセット構成を適用"
        ))
        
        compose_group.add_command(commands.Command(
            name="custom",
            callback=functools.partial(self.compose_custom, force_mode=False),
            help="カスタム役職構成を設定"
        ))
        
        compose_group.add_command(commands.Command(
            name="force",
            callback=functools.partial(self.compose_custom, force_mode=True),
            help="バランスチェックを無視してカスタム構成を設定"
        ))
        
        compose_group.add_command(commands.Command(
            name="recommend",
            callback=self.compose_recommend,
            help="指定した人数に適した役職構成を提案"
        ))
        
        compose_group.add_command(commands.Command(
            name="show",
            callback=self.compose_show,
            help="現在の役職構成を表示"
        ))
        
        # コマンドをBotに追加
        self.bot.add_command(compose_group)
        self.logger.info("新しいcomposeコマンドグループを追加")
    
    @process_once
    @channel_lock(timeout=3.0)
    async def compose_main(self, ctx):
        """役職構成管理のメインコマンド"""
        self.logger.info(f"compose メインコマンド実行: {ctx.message.id}")
        return await self.compose_help(ctx)
    
    @process_once
    @channel_lock(timeout=3.0)
    async def compose_help(self, ctx):
        """役職構成管理のヘルプを表示"""
        self.logger.info(f"compose help 実行: {ctx.message.id}")
        
        embed = discord.Embed(
            title="役職構成管理",
            description="以下のコマンドで役職構成を管理できます。",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="プリセット一覧",
            value="`!compose presets` - 利用可能なプリセット一覧を表示",
            inline=False
        )
        
        embed.add_field(
            name="プリセット適用",
            value="`!compose apply [プリセット名]` - プリセット構成を適用",
            inline=False
        )
        
        embed.add_field(
            name="カスタム構成",
            value="`!compose custom [人数] [役職1] [数1] [役職2] [数2] ...` - カスタム役職構成を設定",
            inline=False
        )
        
        embed.add_field(
            name="強制カスタム構成",
            value="`!compose force [人数] [役職1] [数1] [役職2] [数2] ...` - バランスチェックを無視してカスタム構成を設定",
            inline=False
        )
        
        embed.add_field(
            name="構成提案",
            value="`!compose recommend [人数]` - 指定した人数に適した役職構成を提案",
            inline=False
        )
        
        embed.add_field(
            name="現在の構成確認",
            value="`!compose show [人数]` - 指定人数の現在の役職構成を表示",
            inline=False
        )
        
        await ctx.send(embed=embed)
        self.logger.info(f"compose help メッセージ送信成功: {ctx.channel.id}")
    
    @process_once
    @channel_lock(timeout=3.0)
    async def compose_presets(self, ctx):
        """利用可能なプリセット一覧を表示"""
        self.logger.info(f"compose presets 実行: {ctx.message.id}")
        
        embed = discord.Embed(
            title="役職構成プリセット一覧",
            description="以下のプリセットから選択できます。`!compose apply [プリセット名]`で適用できます。",
            color=discord.Color.green()
        )
        
        for preset_id, preset_data in self.PRESETS.items():
            # 各プリセットの情報を追加
            player_counts = list(preset_data["compositions"].keys())
            player_counts_str = ", ".join(player_counts)
            
            embed.add_field(
                name=f"{preset_data['name']} (`{preset_id}`)",
                value=f"説明: {preset_data['description']}\n対応人数: {player_counts_str}人",
                inline=False
            )
        
        await ctx.send(embed=embed)
        self.logger.info(f"compose presets メッセージ送信成功: {ctx.channel.id}")
    
    @process_once
    @channel_lock(timeout=3.0)
    async def compose_apply(self, ctx, preset_name=None):
        """プリセット構成を適用する"""
        self.logger.info(f"compose apply 実行: {ctx.message.id}, プリセット: {preset_name}")
        
        if preset_name is None:
            await ctx.send("使用方法: `!compose apply [プリセット名]`")
            return
        
        # プリセット名の検証
        preset_name = preset_name.lower()
        if preset_name not in self.PRESETS:
            preset_list = ", ".join(self.PRESETS.keys())
            embed = discord.Embed(
                title="プリセットエラー",
                description=f"'{preset_name}' は有効なプリセット名ではありません。\n有効なプリセット: {preset_list}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # サーバーIDを取得（DMの場合は個人ID）
        guild_id = ctx.guild.id if ctx.guild else ctx.author.id
        
        # 現在の設定を読み込む
        config = await self.load_config(guild_id)
        
        # プリセットから構成をコピー
        preset_data = self.PRESETS[preset_name]
        
        # 設定に適用
        for player_count, composition in preset_data["compositions"].items():
            config[player_count] = composition.copy()
        
        # 設定を保存
        success = await self.save_config(guild_id, config)
        
        if success:
            embed = discord.Embed(
                title="プリセット適用成功",
                description=f"'{preset_data['name']}' プリセットを適用しました。",
                color=discord.Color.green()
            )
            
            # 適用したプリセットの内容を追加
            for player_count, composition in sorted(preset_data["compositions"].items(), key=lambda x: int(x[0])):
                roles_text = ", ".join([f"{role}: {num}" for role, num in composition.items()])
                embed.add_field(
                    name=f"{player_count}人用構成",
                    value=roles_text,
                    inline=True
                )
            
            await ctx.send(embed=embed)
            self.logger.info(f"プリセット適用: guild_id={guild_id}, preset={preset_name}")
        else:
            embed = discord.Embed(
                title="エラー",
                description="プリセット適用中にエラーが発生しました。再度お試しください。",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @process_once
    @channel_lock(timeout=3.0)
    async def compose_custom(self, ctx, force_mode, *args):
        """カスタム役職構成を設定する"""
        self.logger.info(f"compose {'force' if force_mode else 'custom'} 実行: {ctx.message.id}, 引数: {args}")
        
        if not args:
            embed = discord.Embed(
                title="引数エラー",
                description=f"使用方法: `!compose {'force' if force_mode else 'custom'} [人数] [役職1] [数1] [役職2] [数2] ...`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # この関数の残りの実装は直接original_compose.pyの実装を呼び出す
        try:
            # 元の実装を呼び出す
            await self.direct_compose.custom_composition(ctx, force_mode, *args)
        except Exception as e:
            self.logger.error(f"custom_composition エラー: {e}")
            await ctx.send(f"エラーが発生しました: {e}")
    
    @process_once
    @channel_lock(timeout=3.0)
    async def compose_recommend(self, ctx, player_count=None):
        """指定した人数に適した役職構成を提案する"""
        self.logger.info(f"compose recommend 実行: {ctx.message.id}, 人数: {player_count}")
        
        if player_count is None:
            await ctx.send("使用方法: `!compose recommend [人数]`")
            return
        
        # 元の実装を呼び出す
        try:
            await self.direct_compose.recommend_composition(ctx, player_count)
        except Exception as e:
            self.logger.error(f"recommend_composition エラー: {e}")
            await ctx.send(f"エラーが発生しました: {e}")
    
    @process_once
    @channel_lock(timeout=3.0)
    async def compose_show(self, ctx, player_count=None):
        """現在の役職構成を表示する"""
        self.logger.info(f"compose show 実行: {ctx.message.id}, 人数: {player_count}")
        
        # 元の実装を呼び出す
        try:
            await self.direct_compose.show_composition(ctx, player_count)
        except Exception as e:
            self.logger.error(f"show_composition エラー: {e}")
            await ctx.send(f"エラーが発生しました: {e}")

def setup_fixed_compose_handler(bot):
    """
    改善されたComposeハンドラーをセットアップ
    """
    import sys
    if "direct_compose" in sys.modules:
        direct_compose = sys.modules["direct_compose"]
    else:
        import direct_compose
    
    # 新しいハンドラーインスタンスを作成
    handler = ComposeHandler(bot, direct_compose)
    
    # グローバル参照を保持（GC防止）
    bot._fixed_compose_handler = handler
    
    return handler
