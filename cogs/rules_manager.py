"""
特殊ルールを管理するためのコグ
ゲームの特殊ルールの設定・管理を行う
"""
import discord
from discord.ext import commands
import random

class RulesManagerCog(commands.Cog):
    """特殊ルールを管理するコグ"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.group(name="rules", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def rules(self, ctx):
        """特殊ルールを管理するコマンドグループ"""
        # 現在の設定を取得
        db_manager = self.bot.get_cog("DatabaseManager")
        if not db_manager:
            await ctx.send("DatabaseManagerが見つかりません。")
            return
        
        settings = await db_manager.get_server_settings(str(ctx.guild.id))
        rules = settings.get("game_rules", {})
        
        # 現在の設定を表示
        embed = discord.Embed(
            title="特殊ルール設定",
            description="現在の特殊ルール設定は以下の通りです。",
            color=discord.Color.blue()
        )
        
        # 各ルールの表示用名前と説明
        rules_info = {
            "no_first_night_kill": {
                "name": "初日の襲撃なし",
                "description": "初日の夜は人狼による襲撃ができません。"
            },
            "lovers_enabled": {
                "name": "恋人ルール",
                "description": "ゲーム開始時に2人のプレイヤーが恋人になります。片方が死ぬともう片方も死亡します。"
            },
            "no_consecutive_guard": {
                "name": "連続ガード禁止",
                "description": "狩人が同じ人を連続して護衛できません。"
            },
            "random_tied_vote": {
                "name": "投票同数時ランダム処刑",
                "description": "投票が同数の場合、その中からランダムに1人が処刑されます。"
            },
            "dead_chat_enabled": {
                "name": "霊界チャット",
                "description": "死亡したプレイヤーが専用チャンネルで会話できます。"
            }
        }
        
        # 各ルールの状態を表示
        for rule_id, info in rules_info.items():
            status = "有効" if rules.get(rule_id, False) else "無効"
            embed.add_field(
                name=f"{info['name']}",
                value=f"{info['description']}\n**現在の状態**: {status}\n設定変更: `!rules {rule_id} on/off`",
                inline=False
            )
        
        embed.set_footer(text="特殊ルールはゲーム開始前に設定してください。")
        await ctx.send(embed=embed)
    
    @rules.command(name="no_first_night_kill")
    @commands.has_permissions(administrator=True)
    async def set_no_first_night_kill(self, ctx, option: str):
        """初日の襲撃なしルールを設定"""
        await self._set_rule(ctx, "no_first_night_kill", option, "初日の襲撃なし")
    
    @rules.command(name="lovers")
    @commands.has_permissions(administrator=True)
    async def set_lovers(self, ctx, option: str):
        """恋人ルールを設定"""
        await self._set_rule(ctx, "lovers_enabled", option, "恋人ルール")
    
    @rules.command(name="no_consecutive_guard")
    @commands.has_permissions(administrator=True)
    async def set_no_consecutive_guard(self, ctx, option: str):
        """連続ガード禁止ルールを設定"""
        await self._set_rule(ctx, "no_consecutive_guard", option, "連続ガード禁止")
    
    @rules.command(name="random_tied_vote")
    @commands.has_permissions(administrator=True)
    async def set_random_tied_vote(self, ctx, option: str):
        """投票同数時ランダム処刑ルールを設定"""
        await self._set_rule(ctx, "random_tied_vote", option, "投票同数時ランダム処刑")
    
    @rules.command(name="dead_chat")
    @commands.has_permissions(administrator=True)
    async def set_dead_chat(self, ctx, option: str):
        """霊界チャットルールを設定"""
        await self._set_rule(ctx, "dead_chat_enabled", option, "霊界チャット")
    
    async def _set_rule(self, ctx, rule_id, option, display_name):
        """ルール設定を変更する共通処理"""
        # オプションの検証
        option = option.lower()
        if option not in ["on", "off"]:
            await ctx.send("オプションは `on` または `off` を指定してください。")
            return
        
        enabled = (option == "on")
        
        # データベース更新
        db_manager = self.bot.get_cog("DatabaseManager")
        if not db_manager:
            await ctx.send("DatabaseManagerが見つかりません。")
            return
        
        settings = await db_manager.get_server_settings(str(ctx.guild.id))
        rules = settings.get("game_rules", {})
        rules[rule_id] = enabled
        
        # 設定を保存
        await db_manager.update_server_setting(str(ctx.guild.id), "game_rules", rules)
        
        # 確認メッセージを送信
        status = "有効" if enabled else "無効"
        await ctx.send(f"「{display_name}」ルールを **{status}** に設定しました。")
    
    # ゲーム準備時に実行するメソッド（Game Managerから呼び出される）
    async def setup_special_rules(self, guild_id, game):
        """特殊ルールをゲームに適用する"""
        db_manager = self.bot.get_cog("DatabaseManager")
        if not db_manager:
            return
        
        settings = await db_manager.get_server_settings(str(guild_id))
        rule_settings = settings.get("game_rules", {})
        
        # 特殊ルールオブジェクトを設定
        from models.special_rules import SpecialRules
        game.special_rules = SpecialRules()
        
        # 各ルールを適用
        game.special_rules.no_first_night_kill = rule_settings.get("no_first_night_kill", False)
        game.special_rules.lovers_enabled = rule_settings.get("lovers_enabled", False)
        game.special_rules.no_consecutive_guard = rule_settings.get("no_consecutive_guard", False)
        game.special_rules.random_tied_vote = rule_settings.get("random_tied_vote", False)
        game.special_rules.dead_chat_enabled = rule_settings.get("dead_chat_enabled", False)
        
        # 恋人ルールが有効の場合、恋人を設定
        if game.special_rules.lovers_enabled and len(game.players) >= 4:
            await self._setup_lovers(game)
    
    async def _setup_lovers(self, game):
        """恋人を設定する処理"""
        if len(game.players) < 2:
            return
        
        # プレイヤーから2人をランダムに選択
        player_ids = list(game.players.keys())
        random.shuffle(player_ids)
        lover1_id = player_ids[0]
        lover2_id = player_ids[1]
        
        # 恋人設定
        game.special_rules.set_lovers(lover1_id, lover2_id)
        
        # DMで通知
        lover1 = game.players[lover1_id]
        lover2 = game.players[lover2_id]
        
        embed1 = discord.Embed(
            title="恋人設定",
            description=f"あなたは **{lover2.name}** と恋人に設定されました。",
            color=discord.Color.pink()
        )
        embed1.add_field(
            name="恋人ルール", 
            value="片方が死亡するともう片方も死亡します。二人とも生き残れば勝利となります。", 
            inline=False
        )
        
        embed2 = discord.Embed(
            title="恋人設定",
            description=f"あなたは **{lover1.name}** と恋人に設定されました。",
            color=discord.Color.pink()
        )
        embed2.add_field(
            name="恋人ルール", 
            value="片方が死亡するともう片方も死亡します。二人とも生き残れば勝利となります。", 
            inline=False
        )
        
        # DMを送信
        try:
            await lover1.user.send(embed=embed1)
            await lover2.user.send(embed=embed2)
        except discord.Forbidden:
            # DMが送信できない場合のエラーハンドリング
            pass

async def setup(bot):
    await bot.add_cog(RulesManagerCog(bot))
