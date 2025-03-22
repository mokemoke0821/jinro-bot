"""
役職構成をカスタマイズするためのコグ
ゲームの役職構成の設定・管理を行う
"""
import discord
from discord.ext import commands
import json
import asyncio

class RoleComposerCog(commands.Cog):
    """役職構成をカスタマイズするコグ"""
    
    def __init__(self, bot):
        self.bot = bot
        self.presets = self._load_presets()
    
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
    async def apply_preset(self, ctx, preset_id: str):
        """プリセット構成を適用"""
        if preset_id not in self.presets:
            preset_names = ", ".join(f"`{pid}`" for pid in self.presets.keys())
            await ctx.send(f"プリセット `{preset_id}` は存在しません。有効なプリセット: {preset_names}")
            return
        
        # データベース更新
        db_manager = self.bot.get_cog("DatabaseManager")
        if not db_manager:
            await ctx.send("DatabaseManagerが見つかりません。")
            return
        
        # デバッグ情報を追加
        print(f"Database manager type: {type(db_manager)}")
        print(f"Applying preset: {preset_id}")
        
        try:
            # 設定取得部分を例外処理で囲む
            settings = await db_manager.get_server_settings(str(ctx.guild.id))
            print(f"Retrieved settings type: {type(settings)}")
            
            # 例外ケースをチェック
            if asyncio.iscoroutine(settings):
                print("Warning: settings is still a coroutine, awaiting again")
                settings = await settings
                print(f"After second await, settings type: {type(settings)}")
            
            if not isinstance(settings, dict):
                print(f"Error: settings is not a dict: {type(settings)}")
                await ctx.send("設定の取得に失敗しました。管理者に連絡してください。")
                return
                
            roles_config = settings.get("roles_config", {})
            
            # プリセットの構成をコピー
            preset = self.presets[preset_id]
            for player_count, composition in preset["compositions"].items():
                roles_config[player_count] = composition
            
            # 設定を保存
            await db_manager.update_server_setting(str(ctx.guild.id), "roles_config", roles_config)
            
            # 確認メッセージを送信
            await ctx.send(f"プリセット「{preset['name']}」を適用しました。")
        except Exception as e:
            # 例外情報を詳細に出力
            import traceback
            print(f"Error in apply_preset: {e}")
            traceback.print_exc()
            await ctx.send(f"エラーが発生しました: {str(e)}")
    
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
        
        # データベース更新
        db_manager = self.bot.get_cog("DatabaseManager")
        if not db_manager:
            await ctx.send("DatabaseManagerが見つかりません。")
            return
        
        try:
            # 設定取得部分を例外処理で囲む
            settings = await db_manager.get_server_settings(str(ctx.guild.id))
            print(f"Custom composition - Retrieved settings type: {type(settings)}")
            
            # 例外ケースをチェック
            if asyncio.iscoroutine(settings):
                print("Warning: settings is still a coroutine in set_custom_composition, awaiting again")
                settings = await settings
                print(f"After second await, settings type: {type(settings)}")
            
            if not isinstance(settings, dict):
                print(f"Error: settings is not a dict: {type(settings)}")
                await ctx.send("設定の取得に失敗しました。管理者に連絡してください。")
                return
                
            roles_config = settings.get("roles_config", {})
            
            # 構成を保存
            roles_config[str(player_count)] = composition
            await db_manager.update_server_setting(str(ctx.guild.id), "roles_config", roles_config)
            
            # 確認メッセージを送信
            roles_text = "\n".join([f"- {role}: {count}人" for role, count in composition.items()])
            await ctx.send(f"{player_count}人用のカスタム役職構成を設定しました：\n{roles_text}")
        except Exception as e:
            # 例外情報を詳細に出力
            import traceback
            print(f"Error in set_custom_composition: {e}")
            traceback.print_exc()
            await ctx.send(f"エラーが発生しました: {str(e)}")
    
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
        role_balancer = self.bot.get_cog("RoleBalancer")
        if role_balancer:
            balance_check = role_balancer.check_balance(composition)
            if not balance_check["balanced"]:
                warning = "\n".join(balance_check["warnings"])
                await ctx.send(f"⚠️ **警告**: 以下の問題がありますが、強制設定します。\n{warning}")
        
        # データベース更新
        db_manager = self.bot.get_cog("DatabaseManager")
        if not db_manager:
            await ctx.send("DatabaseManagerが見つかりません。")
            return
        
        try:
            # 設定取得部分を例外処理で囲む
            settings = await db_manager.get_server_settings(str(ctx.guild.id))
            print(f"Force composition - Retrieved settings type: {type(settings)}")
            
            # 例外ケースをチェック
            if asyncio.iscoroutine(settings):
                print("Warning: settings is still a coroutine in force_custom_composition, awaiting again")
                settings = await settings
                print(f"After second await, settings type: {type(settings)}")
            
            if not isinstance(settings, dict):
                print(f"Error: settings is not a dict: {type(settings)}")
                await ctx.send("設定の取得に失敗しました。管理者に連絡してください。")
                return
                
            roles_config = settings.get("roles_config", {})
            
            # 構成を保存
            roles_config[str(player_count)] = composition
            await db_manager.update_server_setting(str(ctx.guild.id), "roles_config", roles_config)
            
            # 確認メッセージを送信
            roles_text = "\n".join([f"- {role}: {count}人" for role, count in composition.items()])
            await ctx.send(f"⚠️ {player_count}人用のカスタム役職構成を強制設定しました：\n{roles_text}")
        except Exception as e:
            # 例外情報を詳細に出力
            import traceback
            print(f"Error in force_custom_composition: {e}")
            traceback.print_exc()
            await ctx.send(f"エラーが発生しました: {str(e)}")
    
    @compose.command(name="show")
    async def show_composition(self, ctx, player_count: int = None):
        """現在の役職構成を表示"""
        db_manager = self.bot.get_cog("DatabaseManager")
        if not db_manager:
            await ctx.send("DatabaseManagerが見つかりません。")
            return
        
        try:
            # 設定取得部分を例外処理で囲む
            settings = await db_manager.get_server_settings(str(ctx.guild.id))
            print(f"Show composition - Retrieved settings type: {type(settings)}")
            
            # 例外ケースをチェック
            if asyncio.iscoroutine(settings):
                print("Warning: settings is still a coroutine in show_composition, awaiting again")
                settings = await settings
                print(f"After second await, settings type: {type(settings)}")
            
            if not isinstance(settings, dict):
                print(f"Error: settings is not a dict: {type(settings)}")
                await ctx.send("設定の取得に失敗しました。管理者に連絡してください。")
                return
                
            roles_config = settings.get("roles_config", {})
            
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
                
                if not roles_config:
                    embed.description = "役職構成が設定されていません。"
                    await ctx.send(embed=embed)
                    return
                
                for player_count, composition in sorted(roles_config.items(), key=lambda x: int(x[0])):
                    roles_text = ", ".join([f"{role}: {count}" for role, count in composition.items()])
                    embed.add_field(
                        name=f"{player_count}人用",
                        value=roles_text,
                        inline=False
                    )
                
                await ctx.send(embed=embed)
        except Exception as e:
            # 例外情報を詳細に出力
            import traceback
            print(f"Error in show_composition: {e}")
            traceback.print_exc()
            await ctx.send(f"エラーが発生しました: {str(e)}")
    
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

async def setup(bot):
    await bot.add_cog(RoleComposerCog(bot))
