"""
投票処理コグ
投票フェーズでの処理とゲーム終了処理
"""
import discord
from discord.ext import commands
from utils.embed_creator import create_base_embed, create_game_status_embed
from utils.validators import is_guild_channel, MentionConverter
from utils.config import GameConfig, EmbedColors
from views.vote_view import VoteView

class VotingCog(commands.Cog):
    """投票処理Cog"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="vote")
    async def vote(self, ctx, target: MentionConverter):
        """投票コマンド"""
        # サーバーチャンネルでのみ実行可能
        if not is_guild_channel(ctx):
            await ctx.send("このコマンドはサーバーのチャンネルでのみ使用できます。")
            return
        
        # ゲームマネージャーの取得
        game_manager = self.bot.get_cog("GameManagementCog")
        if not game_manager:
            await ctx.send("ゲーム管理システムが見つかりません。")
            return
        
        # ゲームが進行中かチェック
        if not game_manager.is_game_active(ctx.guild.id):
            await ctx.send("現在進行中のゲームがありません。")
            return
        
        game = game_manager.get_game(ctx.guild.id)
        
        # 投票フェーズかチェック
        if game.phase != "voting":
            await ctx.send("現在は投票フェーズではありません。")
            return
        
        # プレイヤーチェック
        if str(ctx.author.id) not in game.players:
            await ctx.send("あなたはこのゲームに参加していません。")
            return
        
        player = game.players[str(ctx.author.id)]
        
        # 生存プレイヤーかチェック
        if not player.is_alive:
            await ctx.send("あなたはすでに死亡しているため、投票できません。")
            return
        
        # 投票対象が有効かチェック
        if str(target) not in game.players:
            await ctx.send("指定したプレイヤーはゲームに参加していません。")
            return
        
        target_player = game.players[str(target)]
        
        # 投票対象が生存しているかチェック
        if not target_player.is_alive:
            await ctx.send("指定したプレイヤーはすでに死亡しています。")
            return
        
        # 投票を追加
        game.add_vote(ctx.author.id, target)
        
        # 投票成功メッセージ
        embed = create_base_embed(
            title="投票",
            description=f"{ctx.author.mention} が {target_player.name} に投票しました。",
            color=EmbedColors.PRIMARY
        )
        
        # 投票状況
        vote_count = len(game.votes)
        alive_count = len(game.get_alive_players())
        embed.add_field(name="投票状況", value=f"{vote_count}/{alive_count}", inline=False)
        
        await ctx.send(embed=embed)
        
        # 全員が投票したらタイマーを終了して結果処理
        if vote_count >= alive_count:
            # タイマーをキャンセル
            game.cancel_timer()
            
            # 投票結果を処理
            await self.process_voting_results(ctx.channel, game)
    
    @commands.command(name="voteui")
    async def vote_ui(self, ctx):
        """ボタンUIを使った投票を開始"""
        # サーバーチャンネルでのみ実行可能
        if not is_guild_channel(ctx):
            await ctx.send("このコマンドはサーバーのチャンネルでのみ使用できます。")
            return
        
        # ゲームマネージャーの取得
        game_manager = self.bot.get_cog("GameManagementCog")
        if not game_manager:
            await ctx.send("ゲーム管理システムが見つかりません。")
            return
        
        # ゲームが進行中かチェック
        if not game_manager.is_game_active(ctx.guild.id):
            await ctx.send("現在進行中のゲームがありません。")
            return
        
        game = game_manager.get_game(ctx.guild.id)
        
        # 投票フェーズかチェック
        if game.phase != "voting":
            await ctx.send("現在は投票フェーズではありません。")
            return
        
        # タイムアウト値を設定
        timeout = GameConfig.VOTE_TIME
        
        # VoteViewを作成
        view = VoteView(game, ctx, timeout=timeout)
        
        # 埋め込みメッセージを作成
        embed = create_base_embed(
            title="🗳️ 投票",
            description=f"処刑する人を決めるための投票です。\n"
                        f"投票時間: {timeout}秒\n\n"
                        f"**ボタンをクリックして投票してください**",
            color=EmbedColors.PRIMARY
        )
        
        # 生存プレイヤーリストを追加
        alive_players = game.get_alive_players()
        player_list = "\n".join([f"- {p.name}" for p in alive_players])
        embed.add_field(name="生存者", value=player_list, inline=False)
        
        # 投票状況フィールド（初期状態は空）
        embed.add_field(name="投票状況", value="まだ投票はありません。", inline=False)
        
        # 進行状況
        embed.add_field(
            name="進行状況", 
            value=f"0/{len(alive_players)} 投票完了", 
            inline=False
        )
        
        # メッセージを送信
        message = await ctx.send(embed=embed, view=view)
        
        # メッセージIDを保存して後で更新できるようにする
        view.message = message
        game.vote_message = message
    
    async def start_voting_phase(self, channel, game):
        """投票フェーズを開始"""
        if not channel:
            return
        
        # 投票フェーズメッセージを送信
        embed = create_game_status_embed(game, "voting")
        
        # 生存プレイヤー一覧
        alive_players = game.get_alive_players()
        if alive_players:
            players_mention = " ".join([f"<@{p.user_id}>" for p in alive_players])
            embed.add_field(name="生存者へのメンション", value=players_mention, inline=False)
        
        await channel.send(embed=embed)
        
        # 投票開始メッセージ
        vote_msg = "🗳️ 処刑する人を決める投票を開始します。\n"
        vote_msg += "`!vote @ユーザー名` コマンドで投票するか、下のボタンUIを使用してください。\n"
        vote_msg += f"投票時間は{GameConfig.VOTE_TIME}秒です。"
        
        await channel.send(vote_msg)
        
        # ボタンUIを自動表示
        ctx = await self.bot.get_context(channel.last_message)
        await self.vote_ui(ctx)
        
        # 制限時間を設定
        async def update_timer(remaining):
            if remaining == 30:
                await channel.send("⏰ 投票終了まであと30秒です！")
        
        async def timer_complete():
            if game.phase == "voting":
                # 投票結果を処理
                await self.process_voting_results(channel, game)
        
        # タイマー開始
        await game.start_timer(GameConfig.VOTE_TIME, update_timer, timer_complete)
    
    async def process_voting_results(self, channel, game):
        """投票結果を処理"""
        if not channel:
            return
        
        # 投票集計
        game.process_voting()
        
        # 最多票の対象を特定
        max_votes = 0
        targets = []
        
        for target_id, count in game.vote_count.items():
            if count > max_votes:
                max_votes = count
                targets = [target_id]
            elif count == max_votes:
                targets.append(target_id)
        
        # 投票結果メッセージ
        if not game.vote_count:
            result_msg = "投票がありませんでした。"
        else:
            result_msg = "**投票結果**\n"
            for player_id, player in game.players.items():
                if player.is_alive:
                    votes = game.vote_count.get(player_id, 0)
                    result_msg += f"{player.name}: {votes}票\n"
        
        embed = create_base_embed(
            title="投票結果",
            description=result_msg,
            color=EmbedColors.PRIMARY
        )
        
        # 処刑結果
        if game.last_killed:
            executed_player = game.players[game.last_killed]
            embed.add_field(
                name="処刑結果",
                value=f"**{executed_player.name}** が処刑されました。",
                inline=False
            )
            
            # 霊能者がいる場合は処刑者の役職を通知
            for player in game.players.values():
                if player.is_alive and player.role == "霊能者":
                    try:
                        member = self.bot.get_guild(int(game.guild_id)).get_member(int(player.user_id))
                        if member:
                            is_werewolf = executed_player.role == "人狼"
                            medium_embed = create_base_embed(
                                title="霊能結果",
                                description=f"処刑された **{executed_player.name}** は " + 
                                            (f"**人狼**でした！" if is_werewolf else f"**人狼ではありません**。"),
                                color=EmbedColors.ERROR if is_werewolf else EmbedColors.SUCCESS
                            )
                            await member.send(embed=medium_embed)
                    except Exception as e:
                        print(f"霊能者への通知に失敗: {e}")
        else:
            embed.add_field(
                name="処刑結果",
                value="同数票のため、誰も処刑されませんでした。",
                inline=False
            )
        
        await channel.send(embed=embed)
        
        # ゲーム終了判定
        is_game_end, winning_team = game.check_game_end()
        
        if is_game_end:
            # ゲーム終了処理
            await self.end_game(channel, game, winning_team)
        else:
            # 次の夜フェーズへ
            game.next_phase()
            
            # 夜のフェーズを開始
            from cogs.game_management import GameManagementCog
            game_cog = self.bot.get_cog("GameManagementCog")
            if game_cog:
                await game_cog.start_night_phase(channel, game)
    
    async def end_game(self, channel, game, winning_team):
        """ゲーム終了処理"""
        if not channel:
            return
        
        # ゲーム終了メッセージ
        if winning_team == "villager":
            title = "🎉 村人陣営の勝利！"
            description = "すべての人狼が排除されました。村に平和が戻りました。"
            color = EmbedColors.SUCCESS
        elif winning_team == "werewolf":
            title = "🐺 人狼陣営の勝利！"
            description = "村人たちはすべて食べられてしまいました..."
            color = EmbedColors.ERROR
        elif winning_team == "fox":
            title = "🦊 妖狐の勝利！"
            description = "妖狐は最後まで生き残り、勝利しました！"
            color = EmbedColors.WARNING
        else:
            title = "ゲーム終了"
            description = "ゲームが終了しました。"
            color = EmbedColors.PRIMARY
        
        embed = create_base_embed(title, description, color)
        
        # 役職一覧の表示
        role_list = "**最終役職一覧**\n"
        for player in game.players.values():
            status = "💀" if not player.is_alive else "✅"
            role_list += f"{status} {player.name}: {player.role}\n"
        
        embed.add_field(name="役職", value=role_list, inline=False)
        embed.add_field(
            name="新しいゲーム",
            value="`!start` コマンドで新しいゲームを開始できます。",
            inline=False
        )
        
        await channel.send(embed=embed)
        
        # ゲーム情報をクリア
        game_manager = self.bot.get_cog("GameManagementCog")
        if game_manager:
            game.phase = "finished"
            del game_manager.games[str(game.guild_id)]

async def setup(bot):
    """Cogをbotに追加"""
    await bot.add_cog(VotingCog(bot))
