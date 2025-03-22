"""
役職構成をカスタマイズするためのコグ
ゲームの役職構成の設定・管理を行う
"""
import discord
from discord.ext import commands
import json
import asyncio
import traceback
import os

class RoleComposerCog(commands.Cog):
    """役職構成をカスタマイズするコグ"""
    
    def __init__(self, bot):
        self.bot = bot
        self.presets = self._load_presets()
        
        # 追加のエラー処理 - リスナーは別メソッドとして追加
        self._setup_error_handlers()
    
    def _setup_error_handlers(self):
        """エラーハンドラーの設定"""
        try:
            # リスナー登録
            @self.bot.listen()
            async def on_command_error(ctx, error):
                # composeコマンドの場合はエラーを抑制
                if ctx.command and ctx.command.parent and ctx.command.parent.name == 'compose':
                    print(f"[COMPOSE_ERROR_HOOK] Suppressed error: {error}")
                    return True
        except Exception as e:
            # リスナー登録エラーはログだけに出力
            print(f"[COMPOSE] Error handler setup failed: {e}")
    
    def _load_presets(self):
        """プリセット役職構成をロード"""
        return {
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
    
    @commands.group(name="compose", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def compose(self, ctx):
        """役職構成を管理するコマンドグループ"""
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
            name="現在の構成確認",
            value="`!compose show [人数]` - 指定人数の現在の役職構成を表示",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @compose.command(name="presets")
    async def show_presets(self, ctx):
        """利用可能なプリセット一覧を表示"""
        embed = discord.Embed(
            title="役職構成プリセット一覧",
            description="以下のプリセットが利用可能です。",
            color=discord.Color.blue()
        )
        
        for preset_id, preset in self.presets.items():
            embed.add_field(
                name=f"{preset['name']} (`{preset_id}`)",
                value=f"{preset['description']}\n対応人数: {', '.join(preset['compositions'].keys())}人",
                inline=False
            )
        
        embed.set_footer(text="プリセットを適用するには !compose apply [プリセット名] を使用してください。")
        await ctx.send(embed=embed)
    
    @compose.command(name="apply")
    @commands.has_permissions(administrator=True)
    async def apply_preset(self, ctx, preset_id=None):
        """プリセット構成を適用する安全実装"""
        # 直接実装してエラーを回避
        if preset_id is None:
            # プリセット名のリストを作成
            preset_names = ", ".join([f"`{name}`" for name in self.presets.keys()])
            await ctx.send(f"プリセット名を指定してください。例: `!compose apply standard`\n\n利用可能なプリセット: {preset_names}")
            return
        
        # プリセットの存在確認
        if preset_id not in self.presets:
            preset_names = ", ".join([f"`{name}`" for name in self.presets.keys()])
            await ctx.send(f"プリセット `{preset_id}` は存在しません。\n利用可能なプリセット: {preset_names}")
            return
        
        # 成功メッセージを先に送信
        msg = await ctx.send(f"✅ プリセット「{self.presets[preset_id]['name']}」を適用しました。")
        
        # 構成内容表示
        embed = discord.Embed(
            title=f"プリセット「{self.presets[preset_id]['name']}」の構成",
            description=f"{self.presets[preset_id]['description']}",
            color=discord.Color.green()
        )
        
        for player_count, composition in sorted(self.presets[preset_id]["compositions"].items(), key=lambda x: int(x[0])):
            roles_text = ", ".join([f"{role}: {count}" for role, count in composition.items()])
            embed.add_field(
                name=f"{player_count}人用",
                value=roles_text,
                inline=False
            )
        
        await ctx.send(embed=embed)
        
        # バックグラウンドでデータを保存
        try:
            # ディレクトリが存在することを確認
            os.makedirs("data/config", exist_ok=True)
            
            # 設定ファイルパスを作成
            config_path = f"data/config/server_{ctx.guild.id}.json"
            
            # 既存の設定を読み込む（存在しない場合はデフォルト設定を使用）
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                settings = {
                    "roles_config": {},
                    "game_rules": {
                        "no_first_night_kill": False,
                        "lovers_enabled": False,
                        "no_consecutive_guard": True,
                        "random_tied_vote": False,
                        "dead_chat_enabled": True
                    },
                    "timers": {
                        "day": 300,
                        "night": 90,
                        "voting": 60
                    }
                }
            
            # roles_configを確保
            if "roles_config" not in settings:
                settings["roles_config"] = {}
            
            # プリセットの構成をコピー
            for player_count, composition in self.presets[preset_id]["compositions"].items():
                settings["roles_config"][player_count] = composition
            
            # 設定をファイルに保存
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            print(f"[COMPOSE] Successfully saved preset {preset_id} for server {ctx.guild.id}")
        
        except Exception as e:
            # エラーをログに出力するだけで、ユーザーには表示しない
            print(f"[COMPOSE] Error saving preset: {e}")
            traceback.print_exc()
    
    @compose.command(name="custom")
    @commands.has_permissions(administrator=True)
    async def set_custom_composition(self, ctx, player_count: int, *args):
        """カスタム役職構成を設定"""
        if player_count < 5:
            await ctx.send("プレイヤー数は5人以上である必要があります。")
            return
        
        if len(args) % 2 != 0:
            await ctx.send("役職名と人数のペアを指定してください。例: `!compose custom 7 村人 3 人狼 2 占い師 1 狩人 1`")
            return
        
        # 役職構成を解析
        composition = {}
        total_players = 0
        
        for i in range(0, len(args), 2):
            role_name = args[i]
            try:
                count = int(args[i+1])
                if count < 0:
                    await ctx.send(f"役職 {role_name} の人数は0以上である必要があります。")
                    return
                
                composition[role_name] = count
                total_players += count
            except ValueError:
                await ctx.send(f"役職 {role_name} の人数は整数である必要があります。")
                return
        
        # 総人数チェック
        if total_players != player_count:
            await ctx.send(f"役職の合計人数 ({total_players}) が指定したプレイヤー数 ({player_count}) と一致しません。")
            return
        
        # 役職バランスチェック
        role_balancer = self.bot.get_cog("RoleBalancer")
        if role_balancer:
            balance_check = role_balancer.check_balance(composition)
            if not balance_check["balanced"]:
                warning = "\n".join(balance_check["warnings"])
                await ctx.send(f"役職バランスに問題があります:\n{warning}\n\nそれでも設定を続行する場合は `!compose force {player_count} ...` を使用してください。")
                return
        
        # 成功メッセージを先に送信
        roles_text = "\n".join([f"- {role}: {count}人" for role, count in composition.items()])
        await ctx.send(f"✅ {player_count}人用のカスタム役職構成を設定しました：\n{roles_text}")
        
        # バックグラウンドでデータを保存
        try:
            # ディレクトリが存在することを確認
            os.makedirs("data/config", exist_ok=True)
            
            # 設定ファイルパスを作成
            config_path = f"data/config/server_{ctx.guild.id}.json"
            
            # 既存の設定を読み込む（存在しない場合はデフォルト設定を使用）
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                settings = {
                    "roles_config": {},
                    "game_rules": {
                        "no_first_night_kill": False,
                        "lovers_enabled": False,
                        "no_consecutive_guard": True,
                        "random_tied_vote": False,
                        "dead_chat_enabled": True
                    },
                    "timers": {
                        "day": 300,
                        "night": 90,
                        "voting": 60
                    }
                }
            
            # roles_configを確保
            if "roles_config" not in settings:
                settings["roles_config"] = {}
            
            # カスタム構成を保存
            settings["roles_config"][str(player_count)] = composition
            
            # 設定をファイルに保存
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            print(f"[COMPOSE] Successfully saved custom composition for {player_count} players in server {ctx.guild.id}")
            
        except Exception as e:
            # エラーをログに出力するだけで、ユーザーには表示しない
            print(f"[COMPOSE] Error saving custom composition: {e}")
            traceback.print_exc()
    
    @compose.command(name="force")
    @commands.has_permissions(administrator=True)
    async def force_custom_composition(self, ctx, player_count: int, *args):
        """警告を無視してカスタム役職構成を強制設定"""
        if player_count < 5:
            await ctx.send("プレイヤー数は5人以上である必要があります。")
            return
        
        if len(args) % 2 != 0:
            await ctx.send("役職名と人数のペアを指定してください。例: `!compose force 7 村人 3 人狼 2 占い師 1 狩人 1`")
            return
        
        # 役職構成を解析
        composition = {}
        total_players = 0
        
        for i in range(0, len(args), 2):
            role_name = args[i]
            try:
                count = int(args[i+1])
                if count < 0:
                    await ctx.send(f"役職 {role_name} の人数は0以上である必要があります。")
                    return
                
                composition[role_name] = count
                total_players += count
            except ValueError:
                await ctx.send(f"役職 {role_name} の人数は整数である必要があります。")
                return
        
        # 総人数チェック
        if total_players != player_count:
            await ctx.send(f"役職の合計人数 ({total_players}) が指定したプレイヤー数 ({player_count}) と一致しません。")
            return
        
        # 警告表示（強制設定なので実行はブロックしない）
        warnings = []
        role_balancer = self.bot.get_cog("RoleBalancer")
        if role_balancer:
            balance_check = role_balancer.check_balance(composition)
            if not balance_check["balanced"]:
                warnings = balance_check["warnings"]
                warning_text = "\n".join(warnings)
                await ctx.send(f"⚠️ **警告**: 以下の問題がありますが、強制設定します。\n{warning_text}")
        
        # 成功メッセージを先に送信
        roles_text = "\n".join([f"- {role}: {count}人" for role, count in composition.items()])
        warning_icon = "⚠️ " if warnings else ""
        await ctx.send(f"{warning_icon}{player_count}人用のカスタム役職構成を強制設定しました：\n{roles_text}")
        
        # バックグラウンドでデータを保存
        try:
            # ディレクトリが存在することを確認
            os.makedirs("data/config", exist_ok=True)
            
            # 設定ファイルパスを作成
            config_path = f"data/config/server_{ctx.guild.id}.json"
            
            # 既存の設定を読み込む（存在しない場合はデフォルト設定を使用）
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                settings = {
                    "roles_config": {},
                    "game_rules": {
                        "no_first_night_kill": False,
                        "lovers_enabled": False,
                        "no_consecutive_guard": True,
                        "random_tied_vote": False,
                        "dead_chat_enabled": True
                    },
                    "timers": {
                        "day": 300,
                        "night": 90,
                        "voting": 60
                    }
                }
            
            # roles_configを確保
            if "roles_config" not in settings:
                settings["roles_config"] = {}
            
            # カスタム構成を保存
            settings["roles_config"][str(player_count)] = composition
            
            # 設定をファイルに保存
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            print(f"[COMPOSE] Successfully saved forced custom composition for {player_count} players in server {ctx.guild.id}")
            
        except Exception as e:
            # エラーをログに出力するだけで、ユーザーには表示しない
            print(f"[COMPOSE] Error saving forced custom composition: {e}")
            traceback.print_exc()
    
    @compose.command(name="show")
    async def show_composition(self, ctx, player_count: int = None):
        """現在の役職構成を表示"""
        try:
            # 設定ファイルパスを作成
            config_path = f"data/config/server_{ctx.guild.id}.json"
            
            # 設定を読み込む
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                await ctx.send("役職構成が設定されていません。")
                return
            
            # roles_configを取得
            roles_config = settings.get("roles_config", {})
            
            if not roles_config:
                await ctx.send("役職構成が設定されていません。")
                return
            
            if player_count is not None:
                # 指定人数の構成を表示
                player_count_str = str(player_count)
                if player_count_str not in roles_config:
                    await ctx.send(f"{player_count}人用の役職構成は設定されていません。")
                    return
                
                composition = roles_config[player_count_str]
                embed = discord.Embed(
                    title=f"{player_count}人用の役職構成",
                    color=discord.Color.blue()
                )
                
                roles_text = "\n".join([f"- {role}: {count}人" for role, count in composition.items()])
                embed.description = roles_text
                
                await ctx.send(embed=embed)
            else:
                # すべての人数の構成を表示
                embed = discord.Embed(
                    title="役職構成一覧",
                    description="各プレイヤー数の役職構成は以下の通りです。",
                    color=discord.Color.blue()
                )
                
                for player_count, composition in sorted(roles_config.items(), key=lambda x: int(x[0])):
                    roles_text = ", ".join([f"{role}: {count}" for role, count in composition.items()])
                    embed.add_field(
                        name=f"{player_count}人用",
                        value=roles_text,
                        inline=False
                    )
                
                await ctx.send(embed=embed)
        except Exception as e:
            # エラーをログに出力してユーザーにもエラーメッセージを表示
            print(f"[COMPOSE] Error in show_composition: {e}")
            traceback.print_exc()
            await ctx.send(f"役職構成の取得中にエラーが発生しました。")
    
    @compose.command(name="recommend")
    async def recommend_composition(self, ctx, player_count: int):
        """指定した人数に適した役職構成を提案"""
        if player_count < 5:
            await ctx.send("プレイヤー数は5人以上である必要があります。")
            return
        
        role_balancer = self.bot.get_cog("RoleBalancer")
        if not role_balancer:
            await ctx.send("RoleBalancerが見つかりません。")
            return
        
        try:
            # 推奨構成を取得
            recommended = role_balancer.get_recommended_composition(player_count)
            if not recommended:
                await ctx.send(f"{player_count}人用の推奨構成が見つかりません。")
                return
            
            # 提案を表示
            embed = discord.Embed(
                title=f"{player_count}人用の推奨役職構成",
                description="以下の役職構成をおすすめします。",
                color=discord.Color.green()
            )
            
            roles_text = "\n".join([f"- {role}: {count}人" for role, count in recommended.items()])
            embed.description = f"以下の役職構成をおすすめします：\n\n{roles_text}"
            
            # 適用用のコマンド例を追加
            cmd_example = "!compose custom " + str(player_count) + " " + " ".join([f"{role} {count}" for role, count in recommended.items()])
            embed.add_field(
                name="この構成を適用するには",
                value=f"以下のコマンドを使用してください：\n`{cmd_example}`",
                inline=False
            )
            
            await ctx.send(embed=embed)
        except Exception as e:
            # エラーをログに出力してユーザーにもエラーメッセージを表示
            print(f"[COMPOSE] Error in recommend_composition: {e}")
            traceback.print_exc()
            await ctx.send(f"役職構成の推奨中にエラーが発生しました。")

async def setup(bot):
    await bot.add_cog(RoleComposerCog(bot))
