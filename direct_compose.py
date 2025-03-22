"""
直接登録するコマンドモジュール - コマンド実行問題を解決するための緊急対応
"""
import discord
import json
import os
import traceback
import sys
import asyncio
from discord.ext import commands

# コマンド実行時のロックを管理する辞書
command_locks = {}
# 最近実行されたコマンドを追跡するキャッシュ
recent_commands = {}

# 最近のコマンドリストからエントリを削除する非同期関数
async def clear_recent_command(command_id, delay_seconds):
    """指定された時間後に最近使用したコマンドリストからコマンドIDを削除する"""
    await asyncio.sleep(delay_seconds)
    if command_id in recent_commands:
        del recent_commands[command_id]
        logger.debug(f"コマンド履歴から削除: {command_id}")

# ロガーの取得
try:
    from utils.logger import get_logger, log_command, log_role_composer, log_error
    logger = get_logger("direct_compose")
    logger.info("ロガーが正常に初期化されました")
except ImportError:
    # ロガーが利用できない場合は標準のprintで代用
    class FallbackLogger:
        def info(self, msg): print(f"[INFO] {msg}")
        def error(self, msg): print(f"[ERROR] {msg}")
        def warning(self, msg): print(f"[WARNING] {msg}")
        def debug(self, msg): print(f"[DEBUG] {msg}")
    
    logger = FallbackLogger()
    
    def log_command(user_id, guild_id, command, args):
        print(f"[COMMAND] User {user_id} in Guild {guild_id} executed '{command}' with args: {args}")
    
    def log_role_composer(guild_id, action, details):
        print(f"[ROLE_COMPOSER] Guild {guild_id} - {action}: {details}")
    
    def log_error(error, context=None):
        if context:
            print(f"[ERROR] {context}: {error}")
        else:
            print(f"[ERROR] {error}")
        traceback.print_exc()

# プリセットデータ - 静的定義
PRESETS = {
    "standard": {
        "name": "標準",
        "description": "基本的な役職構成です。",
        "compositions": {
            "5": {"村人": 2, "人狼": 1, "占い師": 1, "狩人": 1},
            "6": {"村人": 2, "人狼": 1, "占い師": 1, "狩人": 1, "狂人": 1},
            "7": {"村人": 3, "人狼": 1, "占い師": 1, "狩人": 1, "狂人": 1},
            "8": {"村人": 3, "人狼": 2, "占い師": 1, "狩人": 1, "狂人": 1},
            "9": {"村人": 3, "人狼": 2, "占い師": 1, "狩人": 1, "霊媒師": 1, "狂人": 1},
            "10": {"村人": 3, "人狼": 2, "占い師": 1, "狩人": 1, "霊媒師": 1, "狂人": 1, "妖狐": 1},
        }
    },
    "beginner": {
        "name": "初心者向け",
        "description": "シンプルな役職構成です。初めての方におすすめ。",
        "compositions": {
            "5": {"村人": 3, "人狼": 1, "占い師": 1},
            "6": {"村人": 4, "人狼": 1, "占い師": 1},
            "7": {"村人": 4, "人狼": 2, "占い師": 1},
            "8": {"村人": 5, "人狼": 2, "占い師": 1},
            "9": {"村人": 6, "人狼": 2, "占い師": 1},
            "10": {"村人": 6, "人狼": 3, "占い師": 1},
        }
    },
    "advanced": {
        "name": "上級者向け",
        "description": "複雑な役職構成です。経験者におすすめ。",
        "compositions": {
            "7": {"村人": 1, "人狼": 1, "占い師": 1, "狩人": 1, "霊媒師": 1, "狂人": 1, "妖狐": 1},
            "8": {"村人": 1, "人狼": 2, "占い師": 1, "狩人": 1, "霊媒師": 1, "狂人": 1, "妖狐": 1},
            "9": {"村人": 1, "人狼": 2, "占い師": 1, "狩人": 1, "霊媒師": 1, "狂人": 1, "妖狐": 1, "共有者": 1},
            "10": {"村人": 1, "人狼": 2, "占い師": 1, "狩人": 1, "霊媒師": 1, "狂人": 1, "妖狐": 1, "共有者": 2},
            "11": {"村人": 1, "人狼": 2, "占い師": 1, "狩人": 1, "霊媒師": 1, "狂人": 1, "妖狐": 1, "共有者": 2, "猫又": 1},
            "12": {"人狼": 3, "占い師": 1, "狩人": 1, "霊媒師": 1, "狂人": 1, "妖狐": 1, "共有者": 2, "猫又": 1, "背徳者": 1},
        }
    },
    "chaos": {
        "name": "カオス",
        "description": "バランスを考慮しない混沌とした役職構成です。",
        "compositions": {
            "8": {"人狼": 2, "妖狐": 2, "狂人": 3, "占い師": 1},
            "10": {"人狼": 3, "妖狐": 2, "狂人": 2, "占い師": 1, "猫又": 2},
            "12": {"人狼": 4, "妖狐": 2, "狂人": 2, "占い師": 1, "猫又": 2, "背徳者": 1},
        }
    }
}

# 定数
# プレフィックスを明示的に指定（設定との整合性を確保）
CMD_PREFIX = "!"

# 設定ファイルのパス
CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR, exist_ok=True)

# 役職リスト（検証用）
VALID_ROLES = [
    "村人", "人狼", "占い師", "狩人", "霊媒師", "狂人", "妖狐", "共有者", "猫又", "背徳者",
    "てるてる坊主", "賢者", "仮病人", "呪狼", "大狼", "子狼", "狼憑き"
]

# 役職グループ - バランス調整用
ROLE_GROUPS = {
    "村陣営": ["村人", "占い師", "狩人", "霊媒師", "共有者", "猫又", "てるてる坊主", "賢者", "仮病人"],
    "狼陣営": ["人狼", "呪狼", "大狼", "子狼"],
    "第三陣営": ["妖狐", "背徳者", "狼憑き"],
    "狂信者陣営": ["狂人"]
}

# 登録済みコマンド追跡用のグローバル変数
_registered_commands = set()

# コマンド呼び出し履歴（重複チェック用）
_command_history = {}

# 設定の読み込み/保存関数
async def load_config(guild_id):
    """サーバー固有の役職構成設定を読み込む"""
    config_path = os.path.join(CONFIG_DIR, f"role_config_{guild_id}.json")
    try:
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            logger.info(f"設定読み込み成功: guild_id={guild_id}")
            return config
        else:
            logger.info(f"設定ファイルなし: guild_id={guild_id}")
            return {}
    except Exception as e:
        logger.error(f"設定読み込みエラー: guild_id={guild_id}, error={e}")
        return {}

async def save_config(guild_id, config):
    """サーバー固有の役職構成設定を保存する"""
    config_path = os.path.join(CONFIG_DIR, f"role_config_{guild_id}.json")
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        logger.info(f"設定保存成功: guild_id={guild_id}")
        return True
    except Exception as e:
        logger.error(f"設定保存エラー: guild_id={guild_id}, error={e}")
        return False

# バランスチェック関数
def check_balance(roles):
    """役職構成のバランスをチェックする"""
    # 役職の合計数を計算
    total_players = sum(roles.values())
    
    # 陣営ごとの人数を計算
    village_count = sum(roles.get(role, 0) for role in ROLE_GROUPS["村陣営"])
    wolf_count = sum(roles.get(role, 0) for role in ROLE_GROUPS["狼陣営"])
    third_count = sum(roles.get(role, 0) for role in ROLE_GROUPS["第三陣営"])
    madman_count = sum(roles.get(role, 0) for role in ROLE_GROUPS["狂信者陣営"])
    
    # 最低限の役職確認
    if "占い師" not in roles or roles["占い師"] < 1:
        return False, "占い師が必要です"
    
    if not any(roles.get(role, 0) > 0 for role in ROLE_GROUPS["狼陣営"]):
        return False, "人狼が必要です"
    
    # 比率チェック
    if wolf_count >= village_count:
        return False, "人狼の数が多すぎます"
    
    if third_count > total_players // 4:
        return False, "第三陣営の数が多すぎます"
    
    if madman_count > wolf_count:
        return False, "狂人の数が人狼より多くなっています"
    
    # その他の特殊ルール
    if "妖狐" in roles and roles["妖狐"] > 0 and "占い師" not in roles:
        return False, "妖狐がいる場合は占い師が必要です"
    
    if "背徳者" in roles and roles["背徳者"] > 0 and ("妖狐" not in roles or roles["妖狐"] == 0):
        return False, "背徳者がいる場合は妖狐が必要です"
    
    return True, "バランスOK"

# コマンド実行を追跡するデコレータ
def track_command_execution(command_name):
    """コマンドの実行を追跡して重複実行を防止するデコレータ"""
    def decorator(func):
        async def wrapper(ctx, *args, **kwargs):
            global _command_history
            
            # メッセージIDと時間の組み合わせでユニークなキーを生成
            message_id = ctx.message.id
            key = f"{message_id}_{command_name}"
            
            # すでに実行済みかチェック
            if key in _command_history:
                logger.debug(f"重複実行を無視: {command_name} (メッセージID: {message_id})")
                return
            
            # 履歴に追加
            _command_history[key] = True
            
            # 5分後に履歴から削除
            async def clear_history():
                await asyncio.sleep(300)  # 5分待機
                if key in _command_history:
                    del _command_history[key]
            
            asyncio.create_task(clear_history())
            
            # 実際のコマンド実行
            return await func(ctx, *args, **kwargs)
        return wrapper
    return decorator

def setup_commands(bot):
    """直接コマンドをBotに登録"""
    global _registered_commands
    
    # 重複登録チェック
    if "compose_setup_done" in _registered_commands:
        logger.warning("役職構成管理コマンドはすでに登録されています。重複登録を回避します。")
        return
    
    logger.info("==========================================")
    logger.info("役職構成管理コマンドを登録します")
    logger.info(f"コマンドプレフィックス: {CMD_PREFIX}")
    logger.info(f"プリセット数: {len(PRESETS)}")
    logger.info("登録するコマンド: compose (help/presets/apply/custom/force/recommend/show)")
    
    # 既存のコマンドをログ出力
    existing_commands = [cmd.name for cmd in bot.commands]
    logger.info(f"既存コマンド: {existing_commands}")
    
    # 既存のcomposeコマンドを削除
    to_remove = []
    for cmd in bot.commands:
        if cmd.name == "compose" or cmd.name.startswith("compose_"):
            to_remove.append(cmd)
    
    for cmd in to_remove:
        bot.remove_command(cmd.name)
        logger.info(f"既存コマンドを削除: {cmd.name}")

    # =========== メインコマンド関連の再設計 ===========
    # サブコマンドの文字列処理を含むメインコマンド
    @bot.command(name="compose")
    @track_command_execution("compose")
    async def compose_command(ctx, *args):
        """役職構成管理のメインコマンド - サブコマンドを処理"""
        logger.info(f"compose メインコマンド実行: {ctx.message.id}, 引数: {args}")
        
        # 引数がない場合はヘルプを表示
        if not args:
            return await show_help(ctx)
        
        # 最初の引数をサブコマンドとして解釈
        subcommand = args[0].lower()
        subcommand_args = args[1:]
        
        if subcommand == "help":
            await show_help(ctx)
        elif subcommand == "presets":
            await show_presets(ctx)
        elif subcommand == "apply":
            if len(subcommand_args) < 1:
                await ctx.send("使用方法: `!compose apply [プリセット名]`")
                return
            await apply_preset(ctx, subcommand_args[0])
        elif subcommand == "custom":
            await custom_composition(ctx, False, *subcommand_args)
        elif subcommand == "force":
            await custom_composition(ctx, True, *subcommand_args)
        elif subcommand == "recommend":
            if len(subcommand_args) < 1:
                await ctx.send("使用方法: `!compose recommend [人数]`")
                return
            await recommend_composition(ctx, subcommand_args[0])
        elif subcommand == "show":
            player_count = subcommand_args[0] if subcommand_args else None
            await show_composition(ctx, player_count)
        else:
            # 未知のサブコマンドの場合はヘルプを表示
            await ctx.send(f"未知のサブコマンド: `{subcommand}`")
            await show_help(ctx)

    # =========== サブコマンド実装（独立関数として）===========
    # ヘルプ表示関数
    async def show_help(ctx):
        """役職構成管理のヘルプを表示"""
        logger.info(f"compose help 実行: {ctx.message.id}")
        
        # 利用可能なプリセットを表示
        preset_list = ", ".join(PRESETS.keys())
        
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
        logger.info(f"compose help メッセージ送信成功: {ctx.channel.id}")

    # プリセット一覧表示関数
    async def show_presets(ctx):
        """利用可能なプリセット一覧を表示"""
        logger.info(f"compose presets 実行: {ctx.message.id}")
        
        embed = discord.Embed(
            title="役職構成プリセット一覧",
            description="以下のプリセットから選択できます。`!compose apply [プリセット名]`で適用できます。",
            color=discord.Color.green()
        )
        
        for preset_id, preset_data in PRESETS.items():
            # 各プリセットの情報を追加
            player_counts = list(preset_data["compositions"].keys())
            player_range = f"{min(player_counts)}人〜{max(player_counts)}人"
            
            embed.add_field(
                name=f"{preset_data['name']} ({preset_id})",
                value=f"説明: {preset_data['description']}\n対応人数: {player_range}",
                inline=False
            )
        
        await ctx.send(embed=embed)
        logger.info(f"compose presets メッセージ送信成功: {ctx.channel.id}")
    
    # プリセット適用関数
    async def apply_preset(ctx, preset_name):
        """プリセット構成を適用する"""
        logger.info(f"compose apply 実行: {ctx.message.id}, プリセット: {preset_name}")
        
        # プリセット名の検証
        preset_name = preset_name.lower()
        if preset_name not in PRESETS:
            preset_list = ", ".join(PRESETS.keys())
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
        config = await load_config(guild_id)
        
        # プリセットから構成をコピー
        preset_data = PRESETS[preset_name]
        
        # 設定に適用
        for player_count, composition in preset_data["compositions"].items():
            config[player_count] = composition.copy()
        
        # 設定を保存
        success = await save_config(guild_id, config)
        
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
            log_role_composer(guild_id, "プリセット適用", f"プリセット: {preset_name}")
        else:
            embed = discord.Embed(
                title="エラー",
                description="プリセット適用中にエラーが発生しました。再度お試しください。",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    # =========== 現在の構成表示関数 ===========
    async def show_composition(ctx, player_count_str=None):
        """現在の役職構成を表示"""
        logger.info(f"compose show 実行: {ctx.message.id}, 人数: {player_count_str}")
        
        # サーバーIDを取得（DMの場合は個人ID）
        guild_id = ctx.guild.id if ctx.guild else ctx.author.id
        
        # 設定を読み込む
        config = await load_config(guild_id)
        
        if not config:
            embed = discord.Embed(
                title="設定なし",
                description=f"このサーバーには役職構成の設定がありません。`{CMD_PREFIX}compose apply standard` で標準設定を適用してください。",
                color=discord.Color.yellow()
            )
            await ctx.send(embed=embed)
            return
        
        # 特定の人数が指定されている場合
        if player_count_str:
            try:
                player_count = int(player_count_str)
                str_player_count = str(player_count)
                
                if str_player_count in config:
                    # 指定した人数の構成を表示
                    roles = config[str_player_count]
                    roles_text = ", ".join([f"{role}: {num}" for role, num in roles.items()])
                    
                    embed = discord.Embed(
                        title=f"{player_count}人用の役職構成",
                        description=f"このサーバーに設定されている{player_count}人用の役職構成です。",
                        color=discord.Color.blue()
                    )
                    
                    embed.add_field(
                        name="役職構成",
                        value=roles_text,
                        inline=False
                    )
                    
                    await ctx.send(embed=embed)
                else:
                    # 指定した人数の構成がない場合
                    embed = discord.Embed(
                        title="構成なし",
                        description=f"{player_count}人用の役職構成は設定されていません。",
                        color=discord.Color.yellow()
                    )
                    await ctx.send(embed=embed)
            except ValueError:
                embed = discord.Embed(
                    title="引数エラー",
                    description="プレイヤー数は数値で指定してください。",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
        else:
            # 全ての構成を表示
            embed = discord.Embed(
                title="役職構成一覧",
                description="このサーバーに設定されている役職構成です。",
                color=discord.Color.blue()
            )
            
            for count, roles in config.items():
                roles_text = ", ".join([f"{role}: {num}" for role, num in roles.items()])
                embed.add_field(
                    name=f"{count}人用構成",
                    value=roles_text,
                    inline=True
                )
            
            await ctx.send(embed=embed)
        
        logger.info(f"compose show 実行完了: 構成を表示")
    
    # カスタム構成設定関数
    async def custom_composition(ctx, force_mode, *args):
        """カスタム役職構成を設定する"""
        logger.info(f"compose {'force' if force_mode else 'custom'} 実行: {ctx.message.id}, 引数: {args}")
        
        # 引数の検証
        if len(args) < 3 or len(args) % 2 == 0:
            embed = discord.Embed(
                title="引数エラー",
                description=f"使用方法: `!compose {'force' if force_mode else 'custom'} [人数] [役職1] [数1] [役職2] [数2] ...`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # 人数の抽出と検証
        try:
            player_count = int(args[0])
            if player_count < 4 or player_count > 20:
                embed = discord.Embed(
                    title="人数エラー",
                    description="プレイヤー数は4人から20人の間である必要があります。",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
        except ValueError:
            embed = discord.Embed(
                title="引数エラー",
                description="プレイヤー数は数値で指定してください。",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # 役職と数の抽出
        roles = {}
        for i in range(1, len(args), 2):
            role_name = args[i]
            
            # 役職名の検証
            if role_name not in VALID_ROLES:
                embed = discord.Embed(
                    title="役職エラー",
                    description=f"'{role_name}'は有効な役職名ではありません。",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # 役職の数の抽出と検証
            try:
                if i + 1 < len(args):
                    count = int(args[i + 1])
                    if count < 0:
                        embed = discord.Embed(
                            title="数値エラー",
                            description=f"役職の数は0以上である必要があります。",
                            color=discord.Color.red()
                        )
                        await ctx.send(embed=embed)
                        return
                    roles[role_name] = count
            except ValueError:
                embed = discord.Embed(
                    title="引数エラー",
                    description=f"役職の数は数値で指定してください。'{args[i + 1]}'は数値ではありません。",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
        
        # 役職の合計数を検証
        total_roles = sum(roles.values())
        if total_roles != player_count:
            embed = discord.Embed(
                title="役職数エラー",
                description=f"役職の合計数({total_roles})がプレイヤー数({player_count})と一致しません。",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # バランスチェック（force_modeがFalseの場合のみ）
        if not force_mode:
            is_balanced, balance_message = check_balance(roles)
            if not is_balanced:
                embed = discord.Embed(
                    title="バランスエラー",
                    description=f"役職構成がバランスに問題があります: {balance_message}\n\nバランスチェックを無視するには `!compose force` コマンドを使用してください。",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
        
        # サーバーIDを取得（DMの場合は個人ID）
        guild_id = ctx.guild.id if ctx.guild else ctx.author.id
        
        # 現在の設定を読み込む
        config = await load_config(guild_id)
        
        # 設定に適用
        config[str(player_count)] = roles
        
        # 設定を保存
        success = await save_config(guild_id, config)
        
        if success:
            embed = discord.Embed(
                title="役職構成設定成功",
                description=f"{player_count}人用の役職構成を設定しました。",
                color=discord.Color.green()
            )
            
            # 設定した役職構成を表示
            roles_text = ", ".join([f"{role}: {num}" for role, num in roles.items()])
            embed.add_field(
                name="役職構成",
                value=roles_text,
                inline=False
            )
            
            # バランス情報を追加
            is_balanced, balance_message = check_balance(roles)
            balance_color = "🟢" if is_balanced else "🔴"
            embed.add_field(
                name="バランス情報",
                value=f"{balance_color} {balance_message}",
                inline=False
            )
            
            await ctx.send(embed=embed)
            log_role_composer(guild_id, "カスタム構成設定", f"人数: {player_count}, 構成: {roles}")
        else:
            embed = discord.Embed(
                title="エラー",
                description="役職構成の設定中にエラーが発生しました。再度お試しください。",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    # 役職構成提案関数
    async def recommend_composition(ctx, player_count_str):
        """指定した人数に適した役職構成を提案する"""
        logger.info(f"compose recommend 実行: {ctx.message.id}, 人数: {player_count_str}")
        
        # 人数の検証
        try:
            player_count = int(player_count_str)
            if player_count < 4 or player_count > 20:
                embed = discord.Embed(
                    title="人数エラー",
                    description="プレイヤー数は4人から20人の間である必要があります。",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
        except ValueError:
            embed = discord.Embed(
                title="引数エラー",
                description="プレイヤー数は数値で指定してください。",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # 適切なプリセットを見つける
        recommended_preset = None
        recommended_composition = None
        
        # 人数に完全に一致するプリセットを探す
        for preset_id, preset_data in PRESETS.items():
            if str(player_count) in preset_data["compositions"]:
                recommended_preset = preset_id
                recommended_composition = preset_data["compositions"][str(player_count)]
                break
        
        # 完全一致がない場合、最も近い人数のプリセットを探す
        if recommended_preset is None:
            # 標準プリセットから最も近い人数の構成をベースにする
            if "standard" in PRESETS:
                standard_counts = [int(c) for c in PRESETS["standard"]["compositions"].keys()]
                if standard_counts:
                    closest_count = min(standard_counts, key=lambda x: abs(x - player_count))
                    base_composition = PRESETS["standard"]["compositions"][str(closest_count)].copy()
                    
                    # 人数の差に基づいて調整
                    diff = player_count - closest_count
                    if diff > 0:
                        # 人数が多い場合は村人を増やす
                        base_composition["村人"] = base_composition.get("村人", 0) + diff
                    elif diff < 0:
                        # 人数が少ない場合は村人を減らす
                        base_composition["村人"] = max(1, base_composition.get("村人", 0) + diff)
                    
                    recommended_preset = "カスタム提案"
                    recommended_composition = base_composition
        
        if recommended_composition:
            embed = discord.Embed(
                title=f"{player_count}人用の役職構成提案",
                description=f"以下の役職構成を提案します。",
                color=discord.Color.blue()
            )
            
            # 役職構成を表示
            roles_text = ", ".join([f"{role}: {num}" for role, num in recommended_composition.items()])
            embed.add_field(
                name="役職構成",
                value=roles_text,
                inline=False
            )
            
            # バランス情報を追加
            is_balanced, balance_message = check_balance(recommended_composition)
            balance_color = "🟢" if is_balanced else "🔴"
            embed.add_field(
                name="バランス情報",
                value=f"{balance_color} {balance_message}",
                inline=False
            )
            
            # 使用方法の提案
            embed.add_field(
                name="この構成を適用するには",
                value=f"`!compose custom {player_count} "
                      + " ".join([f"{role} {num}" for role, num in recommended_composition.items()])
                      + "`",
                inline=False
            )
            
            await ctx.send(embed=embed)
            logger.info(f"compose recommend 実行完了: 構成を提案")
        else:
            embed = discord.Embed(
                title="提案エラー",
                description="指定した人数に適した役職構成を見つけることができませんでした。",
                color=discord.Color.yellow()
            )
            await ctx.send(embed=embed)
    
    # 重複登録を防ぐためのフラグを設定
    _registered_commands.add("compose_setup_done")
    logger.info("役職構成管理コマンドの登録が完了しました")
