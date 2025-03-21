import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List
import asyncio
import datetime

from models.game import Game
from models.player import Player
from utils.config import ConfigManager
from utils.embed_creator import EmbedCreator
from utils.validators import is_admin
from utils.log_manager import LogManager


class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = ConfigManager()
        self.embed_creator = EmbedCreator()
        self.log_manager = LogManager()
        
    @commands.hybrid_group(name="admin", description="管理者専用コマンド")
    @app_commands.default_permissions(administrator=True)
    @commands.check(is_admin)
    async def admin(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = self.embed_creator.create_info_embed(
                title="管理者コマンド",
                description="以下の管理者コマンドが利用可能です："
            )
            embed.add_field(name="!admin game", value="ゲーム管理コマンド", inline=False)
            embed.add_field(name="!admin player", value="プレイヤー管理コマンド", inline=False)
            embed.add_field(name="!admin config", value="設定管理コマンド", inline=False)
            embed.add_field(name="!admin log", value="ログ管理コマンド", inline=False)
            
            await ctx.send(embed=embed, ephemeral=True)
    
    @admin.group(name="game", description="ゲーム管理コマンド")
    async def admin_game(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = self.embed_creator.create_info_embed(
                title="ゲーム管理コマンド",
                description="以下のゲーム管理コマンドが利用可能です："
            )
            embed.add_field(name="!admin game status", value="ゲームの現在の状態を表示", inline=False)
            embed.add_field(name="!admin game force_end", value="ゲームを強制終了", inline=False)
            embed.add_field(name="!admin game force_day", value="強制的に昼のフェーズに移行", inline=False)
            embed.add_field(name="!admin game force_night", value="強制的に夜のフェーズに移行", inline=False)
            embed.add_field(name="!admin game skip_timer", value="現在のタイマーをスキップ", inline=False)
            
            await ctx.send(embed=embed, ephemeral=True)
    
    @admin_game.command(name="status", description="ゲームの現在の状態を表示")
    async def game_status(self, ctx):
        game = Game.get_game(ctx.guild.id)
        if not game:
            await ctx.send("現在アクティブなゲームはありません。", ephemeral=True)
            return
        
        # ゲーム情報のエンベッドを作成
        embed = self.embed_creator.create_info_embed(
            title="ゲーム状態情報 (管理者向け)",
            description=f"ゲームID: {game.id}\n"
                      f"ステータス: {game.status}\n"
                      f"フェーズ: {game.phase}\n"
                      f"開始時刻: {game.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                      f"プレイヤー数: {len(game.players)}"
        )
        
        # 役職情報を追加
        role_counts = {}
        for player in game.players:
            role_name = player.role.__class__.__name__
            role_counts[role_name] = role_counts.get(role_name, 0) + 1
        
        role_info = "\n".join([f"{role}: {count}" for role, count in role_counts.items()])
        embed.add_field(name="役職分布", value=role_info or "情報なし", inline=False)
        
        # 生存プレイヤー情報
        alive_players = [p for p in game.players if p.is_alive]
        alive_info = "\n".join([f"{p.member.display_name}: {p.role.__class__.__name__}" for p in alive_players])
        embed.add_field(name="生存プレイヤー", value=alive_info or "情報なし", inline=False)
        
        # 死亡プレイヤー情報
        dead_players = [p for p in game.players if not p.is_alive]
        dead_info = "\n".join([f"{p.member.display_name}: {p.role.__class__.__name__}" for p in dead_players])
        embed.add_field(name="死亡プレイヤー", value=dead_info or "なし", inline=False)
        
        await ctx.send(embed=embed, ephemeral=True)
    
    @admin_game.command(name="force_end", description="ゲームを強制終了")
    async def force_end_game(self, ctx):
        game = Game.get_game(ctx.guild.id)
        if not game:
            await ctx.send("現在アクティブなゲームはありません。", ephemeral=True)
            return
        
        confirm_msg = await ctx.send("ゲームを強制終了しますか？これにより現在のゲームは中断され、すべてのプレイヤーに通知されます。続行する場合は ✅ を、キャンセルする場合は ❌ をクリックしてください。", ephemeral=True)
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirm_msg.id
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            if str(reaction.emoji) == "✅":
                # ログにゲーム強制終了を記録
                self.log_manager.log_admin_action(game.id, ctx.author.id, "force_end_game", 
                                                "ゲームを管理者によって強制終了しました")
                
                # ゲーム終了処理
                await game.end_game(reason="管理者による強制終了")
                await ctx.send("ゲームを強制終了しました。", ephemeral=True)
                
                # 全体に通知
                announcement_channel = game.announcement_channel
                if announcement_channel:
                    embed = self.embed_creator.create_error_embed(
                        title="ゲーム強制終了",
                        description="管理者によってゲームが強制終了されました。"
                    )
                    await announcement_channel.send(embed=embed)
            else:
                await ctx.send("操作をキャンセルしました。", ephemeral=True)
        except asyncio.TimeoutError:
            await ctx.send("タイムアウトしました。操作はキャンセルされました。", ephemeral=True)
    
    @admin_game.command(name="force_day", description="強制的に昼のフェーズに移行")
    async def force_day(self, ctx):
        game = Game.get_game(ctx.guild.id)
        if not game:
            await ctx.send("現在アクティブなゲームはありません。", ephemeral=True)
            return
        
        if game.phase == "day":
            await ctx.send("既に昼のフェーズです。", ephemeral=True)
            return
        
        # ログに記録
        self.log_manager.log_admin_action(game.id, ctx.author.id, "force_day", 
                                        "管理者によって強制的に昼フェーズに移行しました")
        
        # 昼フェーズに強制移行
        await game.start_day_phase()
        await ctx.send("ゲームを強制的に昼フェーズに移行しました。", ephemeral=True)
    
    @admin_game.command(name="force_night", description="強制的に夜のフェーズに移行")
    async def force_night(self, ctx):
        game = Game.get_game(ctx.guild.id)
        if not game:
            await ctx.send("現在アクティブなゲームはありません。", ephemeral=True)
            return
        
        if game.phase == "night":
            await ctx.send("既に夜のフェーズです。", ephemeral=True)
            return
        
        # ログに記録
        self.log_manager.log_admin_action(game.id, ctx.author.id, "force_night", 
                                        "管理者によって強制的に夜フェーズに移行しました")
        
        # 夜フェーズに強制移行
        await game.start_night_phase()
        await ctx.send("ゲームを強制的に夜フェーズに移行しました。", ephemeral=True)
    
    @admin_game.command(name="skip_timer", description="現在のタイマーをスキップ")
    async def skip_timer(self, ctx):
        game = Game.get_game(ctx.guild.id)
        if not game:
            await ctx.send("現在アクティブなゲームはありません。", ephemeral=True)
            return
        
        if not game.current_timer_task:
            await ctx.send("現在アクティブなタイマーはありません。", ephemeral=True)
            return
        
        # タイマーをキャンセル
        game.current_timer_task.cancel()
        game.current_timer_task = None
        
        # ログに記録
        self.log_manager.log_admin_action(game.id, ctx.author.id, "skip_timer", 
                                        "管理者によってタイマーがスキップされました")
        
        # フェーズに応じたスキップ処理
        if game.phase == "day":
            await game.end_day_phase()
        elif game.phase == "night":
            await game.end_night_phase()
        
        await ctx.send("タイマーをスキップしました。", ephemeral=True)
    
    @admin.group(name="player", description="プレイヤー管理コマンド")
    async def admin_player(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = self.embed_creator.create_info_embed(
                title="プレイヤー管理コマンド",
                description="以下のプレイヤー管理コマンドが利用可能です："
            )
            embed.add_field(name="!admin player list", value="プレイヤーのリストを表示", inline=False)
            embed.add_field(name="!admin player kill", value="プレイヤーを強制的に死亡させる", inline=False)
            embed.add_field(name="!admin player revive", value="死亡したプレイヤーを蘇生させる", inline=False)
            embed.add_field(name="!admin player role", value="プレイヤーの役職を確認または変更", inline=False)
            
            await ctx.send(embed=embed, ephemeral=True)
    
    @admin_player.command(name="list", description="プレイヤーのリストを表示")
    async def player_list(self, ctx):
        game = Game.get_game(ctx.guild.id)
        if not game:
            await ctx.send("現在アクティブなゲームはありません。", ephemeral=True)
            return
        
        embed = self.embed_creator.create_info_embed(
            title="プレイヤーリスト (管理者向け)",
            description=f"ゲームID: {game.id} | 総プレイヤー数: {len(game.players)}"
        )
        
        # すべてのプレイヤー情報を詳細に表示
        player_info = []
        for idx, player in enumerate(game.players):
            status = "生存" if player.is_alive else "死亡"
            role = player.role.__class__.__name__
            player_info.append(f"{idx+1}. {player.member.display_name} - {role} ({status})")
        
        embed.add_field(name="プレイヤー情報", value="\n".join(player_info) or "プレイヤーなし", inline=False)
        await ctx.send(embed=embed, ephemeral=True)
    
    @admin_player.command(name="kill", description="プレイヤーを強制的に死亡させる")
    async def kill_player(self, ctx, player: discord.Member):
        game = Game.get_game(ctx.guild.id)
        if not game:
            await ctx.send("現在アクティブなゲームはありません。", ephemeral=True)
            return
        
        game_player = game.get_player(player.id)
        if not game_player:
            await ctx.send(f"{player.display_name} はゲームに参加していません。", ephemeral=True)
            return
        
        if not game_player.is_alive:
            await ctx.send(f"{player.display_name} は既に死亡しています。", ephemeral=True)
            return
        
        # プレイヤーを死亡させる
        game_player.is_alive = False
        game_player.death_reason = "管理者による強制死亡"
        game_player.death_day = game.day
        
        # ログに記録
        self.log_manager.log_admin_action(game.id, ctx.author.id, "kill_player", 
                                        f"{player.display_name} (ID: {player.id}) を強制的に死亡させました")
        
        await ctx.send(f"{player.display_name} を強制的に死亡させました。", ephemeral=True)
        
        # 死亡通知
        announcement_channel = game.announcement_channel
        if announcement_channel:
            embed = self.embed_creator.create_error_embed(
                title="プレイヤー死亡",
                description=f"**{player.display_name}** が管理者によって死亡しました。"
            )
            await announcement_channel.send(embed=embed)
        
        # 勝利条件チェック
        await game.check_win_condition()
    
    @admin_player.command(name="revive", description="死亡したプレイヤーを蘇生させる")
    async def revive_player(self, ctx, player: discord.Member):
        game = Game.get_game(ctx.guild.id)
        if not game:
            await ctx.send("現在アクティブなゲームはありません。", ephemeral=True)
            return
        
        game_player = game.get_player(player.id)
        if not game_player:
            await ctx.send(f"{player.display_name} はゲームに参加していません。", ephemeral=True)
            return
        
        if game_player.is_alive:
            await ctx.send(f"{player.display_name} は既に生存しています。", ephemeral=True)
            return
        
        # プレイヤーを蘇生させる
        game_player.is_alive = True
        game_player.death_reason = None
        game_player.death_day = None
        
        # ログに記録
        self.log_manager.log_admin_action(game.id, ctx.author.id, "revive_player", 
                                        f"{player.display_name} (ID: {player.id}) を蘇生させました")
        
        await ctx.send(f"{player.display_name} を蘇生させました。", ephemeral=True)
        
        # 蘇生通知
        announcement_channel = game.announcement_channel
        if announcement_channel:
            embed = self.embed_creator.create_success_embed(
                title="プレイヤー蘇生",
                description=f"**{player.display_name}** が管理者によって蘇生しました。"
            )
            await announcement_channel.send(embed=embed)
        
        # 勝利条件チェック
        await game.check_win_condition()
    
    @admin_player.command(name="role", description="プレイヤーの役職を確認または変更")
    async def player_role(self, ctx, player: discord.Member, new_role: Optional[str] = None):
        game = Game.get_game(ctx.guild.id)
        if not game:
            await ctx.send("現在アクティブなゲームはありません。", ephemeral=True)
            return
        
        game_player = game.get_player(player.id)
        if not game_player:
            await ctx.send(f"{player.display_name} はゲームに参加していません。", ephemeral=True)
            return
        
        current_role = game_player.role.__class__.__name__
        
        if not new_role:
            # 役職の確認のみ
            await ctx.send(f"{player.display_name} の現在の役職は **{current_role}** です。", ephemeral=True)
            return
        
        # 役職の変更
        available_roles = ["Villager", "Werewolf", "Seer", "Hunter", "Medium", "Madman", "Fox"]
        if new_role not in available_roles:
            role_list = ", ".join(available_roles)
            await ctx.send(f"無効な役職です。利用可能な役職: {role_list}", ephemeral=True)
            return
        
        # 役職をインポート
        from models.roles.villager import Villager
        from models.roles.werewolf import Werewolf
        from models.roles.seer import Seer
        from models.roles.hunter import Hunter
        from models.roles.medium import Medium
        from models.roles.madman import Madman
        from models.roles.fox import Fox
        
        # 役職クラスのマッピング
        role_classes = {
            "Villager": Villager,
            "Werewolf": Werewolf,
            "Seer": Seer,
            "Hunter": Hunter,
            "Medium": Medium,
            "Madman": Madman,
            "Fox": Fox
        }
        
        # 新しい役職インスタンスを作成
        new_role_instance = role_classes[new_role](game_player)
        
        # 役職を変更
        game_player.role = new_role_instance
        
        # ログに記録
        self.log_manager.log_admin_action(game.id, ctx.author.id, "change_role", 
                                        f"{player.display_name} (ID: {player.id}) の役職を {current_role} から {new_role} に変更しました")
        
        await ctx.send(f"{player.display_name} の役職を **{current_role}** から **{new_role}** に変更しました。", ephemeral=True)
        
        # プレイヤーにDMで通知
        try:
            embed = self.embed_creator.create_warning_embed(
                title="役職変更通知",
                description=f"管理者によってあなたの役職が **{current_role}** から **{new_role}** に変更されました。"
            )
            embed.add_field(name="新しい役職の説明", value=new_role_instance.description, inline=False)
            
            await player.send(embed=embed)
        except discord.Forbidden:
            # DMが送れない場合は管理者に通知
            await ctx.send(f"警告: {player.display_name} にDMを送信できませんでした。", ephemeral=True)
    
    @admin.group(name="config", description="設定管理コマンド")
    async def admin_config(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = self.embed_creator.create_info_embed(
                title="設定管理コマンド",
                description="以下の設定管理コマンドが利用可能です："
            )
            embed.add_field(name="!admin config view", value="現在の設定を表示", inline=False)
            embed.add_field(name="!admin config set", value="設定を変更", inline=False)
            embed.add_field(name="!admin config reset", value="設定をデフォルトに戻す", inline=False)
            
            await ctx.send(embed=embed, ephemeral=True)
    
    @admin_config.command(name="view", description="現在の設定を表示")
    async def view_config(self, ctx):
        server_config = self.config.get_server_config(ctx.guild.id)
        
        embed = self.embed_creator.create_info_embed(
            title="サーバー設定 (管理者向け)",
            description=f"サーバーID: {ctx.guild.id} の現在の設定"
        )
        
        # ゲーム設定
        game_settings = [
            f"🕰️ 昼フェーズ時間: {server_config.get('day_time', 300)} 秒",
            f"🌙 夜フェーズ時間: {server_config.get('night_time', 90)} 秒",
            f"👥 最小プレイヤー数: {server_config.get('min_players', 4)} 人",
            f"👥 最大プレイヤー数: {server_config.get('max_players', 15)} 人",
            f"🎲 ゲーム開始時の役職ランダム割り当て: {'有効' if server_config.get('random_roles', True) else '無効'}",
            f"💬 死亡プレイヤーの観戦チャット: {'有効' if server_config.get('spectator_chat', True) else '無効'}"
        ]
        
        embed.add_field(name="ゲーム設定", value="\n".join(game_settings), inline=False)
        
        # 役職設定
        role_settings = []
        for role, config in server_config.get('roles', {}).items():
            if config.get('enabled', True):
                min_count = config.get('min_count', 0)
                max_count = config.get('max_count', 999)
                role_settings.append(f"✅ {role}: 最小 {min_count}、最大 {max_count}")
            else:
                role_settings.append(f"❌ {role}: 無効")
        
        embed.add_field(name="役職設定", value="\n".join(role_settings) or "デフォルト設定", inline=False)
        
        # 管理者設定
        admin_roles = server_config.get('admin_roles', [])
        admin_role_names = []
        for role_id in admin_roles:
            role = ctx.guild.get_role(role_id)
            if role:
                admin_role_names.append(role.name)
        
        embed.add_field(name="管理者ロール", value=", ".join(admin_role_names) or "設定なし", inline=False)
        
        await ctx.send(embed=embed, ephemeral=True)
    
    @admin_config.command(name="set", description="設定を変更")
    async def set_config(self, ctx, setting: str, value: str):
        server_config = self.config.get_server_config(ctx.guild.id)
        
        # 設定項目の検証
        valid_settings = ["day_time", "night_time", "min_players", "max_players", 
                          "random_roles", "spectator_chat"]
        
        if setting not in valid_settings and not setting.startswith("roles."):
            settings_list = ", ".join(valid_settings + ["roles.{役職名}.{enabled|min_count|max_count}"])
            await ctx.send(f"無効な設定項目です。有効な設定項目: {settings_list}", ephemeral=True)
            return
        
        # 数値設定の変換
        numeric_settings = ["day_time", "night_time", "min_players", "max_players"]
        boolean_settings = ["random_roles", "spectator_chat"]
        
        # 設定を更新
        if setting in numeric_settings:
            try:
                numeric_value = int(value)
                if numeric_value <= 0:
                    await ctx.send("値は正の整数でなければなりません。", ephemeral=True)
                    return
                
                # 特定の設定の制限
                if setting == "day_time" and numeric_value < 60:
                    await ctx.send("昼フェーズ時間は最低60秒以上に設定してください。", ephemeral=True)
                    return
                elif setting == "night_time" and numeric_value < 30:
                    await ctx.send("夜フェーズ時間は最低30秒以上に設定してください。", ephemeral=True)
                    return
                
                server_config[setting] = numeric_value
            except ValueError:
                await ctx.send("数値設定には整数を入力してください。", ephemeral=True)
                return
        elif setting in boolean_settings:
            if value.lower() in ["true", "yes", "on", "1"]:
                server_config[setting] = True
            elif value.lower() in ["false", "no", "off", "0"]:
                server_config[setting] = False
            else:
                await ctx.send("ブール値設定には true/false, yes/no, on/off, 1/0 のいずれかを入力してください。", ephemeral=True)
                return
        elif setting.startswith("roles."):
            # 役職設定の変更
            parts = setting.split(".")
            if len(parts) != 3:
                await ctx.send("役職設定は `roles.{役職名}.{enabled|min_count|max_count}` の形式で指定してください。", ephemeral=True)
                return
            
            role_name = parts[1]
            role_setting = parts[2]
            
            # 有効な役職名かチェック
            valid_roles = ["Villager", "Werewolf", "Seer", "Hunter", "Medium", "Madman", "Fox"]
            if role_name not in valid_roles:
                role_list = ", ".join(valid_roles)
                await ctx.send(f"無効な役職名です。有効な役職名: {role_list}", ephemeral=True)
                return
            
            # 有効な役職設定かチェック
            valid_role_settings = ["enabled", "min_count", "max_count"]
            if role_setting not in valid_role_settings:
                setting_list = ", ".join(valid_role_settings)
                await ctx.send(f"無効な役職設定です。有効な役職設定: {setting_list}", ephemeral=True)
                return
            
            # roles
