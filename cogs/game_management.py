"""
ゲーム管理コグ
ゲームの開始、参加、開始、キャンセルなどのコマンドを提供
"""
import discord
from discord.ext import commands
from discord import app_commands
from models.game import Game
from utils.embed_creator import create_base_embed, create_game_status_embed, create_role_embed, create_help_embed
from utils.validators import is_guild_channel, is_game_owner, is_admin
from utils.config import EmbedColors

class GameManagementCog(commands.Cog):
    """ゲーム管理コマンドのCog"""
    
    def __init__(self, bot):
        self.bot = bot
        self.games = {}  # サーバーごとのゲーム情報 {guild_id: Game}
    
    def is_game_active(self, guild_id):
        """サーバーでゲームが進行中かどうか確認"""
        return str(guild_id) in self.games and self.games[str(guild_id)].phase != "finished"
    
    def get_game(self, guild_id):
        """サーバーのゲームを取得"""
        return self.games.get(str(guild_id), None)
    
    @commands.command(name="werewolf_help")
    async def werewolf_help_command(self, ctx):
        """ヘルプコマンド - 使用可能なコマンドとルールを表示"""
        embed = create_help_embed()
        await ctx.send(embed=embed)
    
    @commands.command(name="start")
    async def start_game(self, ctx):
        """ゲームの募集を開始"""
        # サーバーチャンネルでのみ実行可能
        if not is_guild_channel(ctx):
            await ctx.send("このコマンドはサーバーのチャンネルでのみ使用できます。")
            return
        
        # 既にゲームが進行中かチェック
        if self.is_game_active(ctx.guild.id):
            await ctx.send("既にゲームが進行中です。`!cancel` でキャンセルするか、ゲームの終了を待ってください。")
            return
        
        # 新しいゲームを作成
        game = Game(ctx.guild.id, ctx.channel.id, ctx.author.id)
        game.bot = self.bot  # Botインスタンスを設定
        self.games[str(ctx.guild.id)] = game
        
        # 開始者を自動的に参加者として追加
        game.add_player(ctx.author.id, ctx.author.display_name)
        
        # 開始メッセージを送信
        embed = create_game_status_embed(game, "waiting")
        embed.add_field(name="開始者", value=ctx.author.mention, inline=False)
        embed.add_field(name="参加方法", value="`!join` コマンドでゲームに参加できます。\n`!begin` で参加者が揃ったらゲームを開始します。", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="join")
    async def join_game(self, ctx):
        """募集中のゲームに参加"""
        # サーバーチャンネルでのみ実行可能
        if not is_guild_channel(ctx):
            await ctx.send("このコマンドはサーバーのチャンネルでのみ使用できます。")
            return
        
        # ゲームが募集中かチェック
        if not self.is_game_active(ctx.guild.id):
            await ctx.send("現在募集中のゲームがありません。`!start` で新しいゲームを開始してください。")
            return
        
        game = self.get_game(ctx.guild.id)
        
        if game.phase != "waiting":
            await ctx.send("ゲームはすでに開始されています。次のゲームをお待ちください。")
            return
        
        # 既に参加しているかチェック
        if str(ctx.author.id) in game.players:
            await ctx.send("あなたはすでにこのゲームに参加しています。")
            return
        
        # 参加者上限チェック
        if len(game.players) >= 12:
            await ctx.send("参加者が上限（12人）に達しています。")
            return
        
        # プレイヤーを追加
        player = game.add_player(ctx.author.id, ctx.author.display_name)
        
        if player:
            # 参加メッセージを送信
            embed = create_base_embed(
                title="ゲーム参加",
                description=f"{ctx.author.mention} がゲームに参加しました！",
                color=EmbedColors.SUCCESS
            )
            embed.add_field(name="現在の参加者数", value=f"{len(game.players)}/12", inline=False)
            
            # 参加者一覧を表示
            player_list = "\n".join([f"- {p.name}" for p in game.players.values()])
            embed.add_field(name="参加者一覧", value=player_list, inline=False)
            
            await ctx.send(embed=embed)
        else:
            await ctx.send("参加できませんでした。")
    
    @commands.command(name="begin")
    async def begin_game(self, ctx):
        """参加者を確定してゲームを開始"""
        # 権限チェック
        valid, result = is_game_owner(ctx, self)
        
        if not valid:
            await ctx.send(result)
            return
        
        game = result
        
        # 参加人数チェック
        if len(game.players) < 5:
            await ctx.send("ゲームを開始するには最低5人の参加者が必要です。")
            return
            
        # Botインスタンスを設定
        game.bot = self.bot
        
        # 役職を割り当ててゲーム開始
        success, error_msg = game.start_game()
        
        if not success:
            await ctx.send(f"ゲームを開始できませんでした: {error_msg}")
            return
        
        # ゲーム開始メッセージを送信
        embed = create_base_embed(
            title="🐺 人狼ゲーム開始",
            description="役職が割り当てられました。DMを確認してください。",
            color=EmbedColors.SUCCESS
        )
        embed.add_field(name="参加者数", value=str(len(game.players)), inline=False)
        
        start_msg = await ctx.send(embed=embed)
        
        # 各プレイヤーに役職をDMで通知
        for player in game.players.values():
            member = ctx.guild.get_member(int(player.user_id))
            if member:
                try:
                    embed = create_role_embed(player)
                    await member.send(embed=embed)
                except discord.Forbidden:
                    # DMが送れない場合
                    await ctx.send(f"{member.mention} にDMを送信できませんでした。プライバシー設定を確認してください。")
        
        # 夜のフェーズを開始
        await self.start_night_phase(ctx, game)
    
    @commands.command(name="cancel")
    async def cancel_game(self, ctx):
        """進行中のゲームをキャンセル"""
        # 権限チェック（ゲーム開始者または管理者）
        is_owner, result = is_game_owner(ctx, self)
        is_administrator, _ = is_admin(ctx)
        
        if not (is_owner or is_administrator):
            await ctx.send("このコマンドはゲーム開始者または管理者のみが使用できます。")
            return
        
        if not self.is_game_active(ctx.guild.id):
            await ctx.send("現在進行中のゲームがありません。")
            return
        
        # ゲームをキャンセル
        game = self.get_game(ctx.guild.id)
        
        # タイマーをキャンセル
        game.cancel_timer()
        
        # ゲームを終了
        game.phase = "finished"
        del self.games[str(ctx.guild.id)]
        
        embed = create_base_embed(
            title="ゲームキャンセル",
            description="ゲームがキャンセルされました。",
            color=EmbedColors.ERROR
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="status")
    async def game_status(self, ctx):
        """現在のゲーム状態を表示"""
        # サーバーチャンネルでのみ実行可能
        if not is_guild_channel(ctx):
            await ctx.send("このコマンドはサーバーのチャンネルでのみ使用できます。")
            return
        
        # ゲームが進行中かチェック
        if not self.is_game_active(ctx.guild.id):
            await ctx.send("現在進行中のゲームがありません。")
            return
        
        game = self.get_game(ctx.guild.id)
        embed = create_game_status_embed(game, game.phase)
        
        if game.phase != "waiting":
            # 残り時間を表示（タイマーがある場合）
            if game.remaining_time > 0:
                minutes = game.remaining_time // 60
                seconds = game.remaining_time % 60
                embed.add_field(name="残り時間", value=f"{minutes}分{seconds}秒", inline=False)
        
        await ctx.send(embed=embed)
    
    async def start_night_phase(self, ctx, game):
        """夜のフェーズを開始"""
        from cogs.night_actions import NightActionsCog
        
        # 夜のフェーズメッセージを送信
        embed = create_game_status_embed(game, "night")
        await ctx.send(embed=embed)
        
        # 各プレイヤーに夜のアクション指示をDM
        night_cog = self.bot.get_cog("NightActionsCog")
        if night_cog:
            await night_cog.send_night_action_instructions(game)
        
        # 制限時間を設定
        from utils.config import GameConfig
        
        async def update_timer(remaining):
            # 30秒ごとにアナウンス
            if remaining % 30 == 0 and remaining > 0:
                minutes = remaining // 60
                seconds = remaining % 60
                time_str = f"{minutes}分{seconds}秒" if minutes > 0 else f"{seconds}秒"
                
                channel = self.bot.get_channel(int(game.channel_id))
                if channel:
                    await channel.send(f"🌙 夜のフェーズ: 残り {time_str}")
        
        async def timer_complete():
            channel = self.bot.get_channel(int(game.channel_id))
            if channel and game.phase == "night":
                # 次の昼フェーズへ
                game.next_phase()
                
                # 昼のフェーズを開始
                from cogs.day_actions import DayActionsCog
                day_cog = self.bot.get_cog("DayActionsCog")
                if day_cog:
                    await day_cog.start_day_phase(channel, game)
        
        # タイマー開始
        await game.start_timer(GameConfig.NIGHT_PHASE_TIME, update_timer, timer_complete)

async def setup(bot):
    """Cogをbotに追加"""
    await bot.add_cog(GameManagementCog(bot))
