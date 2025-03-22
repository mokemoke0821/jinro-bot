"""
投票用のボタンインターフェース
"""
import discord
from discord.ui import Button
from typing import Dict, Optional
from .base_view import GameControlView
from utils.embed_creator import create_base_embed
from utils.config import EmbedColors

class VoteView(GameControlView):
    """投票用のViewクラス"""
    
    def __init__(self, game, ctx, timeout: float = 60.0):
        super().__init__(game.bot.get_cog("GameManagementCog"), timeout=timeout)
        self.game = game
        self.ctx = ctx
        self.channel = ctx.channel
        self.message = None
        self.voters: Dict[str, str] = {}  # {投票者ID: 投票先ID}
        
        # 生存プレイヤーのボタンを追加
        alive_players = game.get_alive_players()
        for player in alive_players:
            # 各プレイヤーに対応するボタンを作成
            button = Button(
                style=discord.ButtonStyle.primary,
                label=player.name,
                custom_id=f"vote_{player.user_id}"
            )
            # ボタンのコールバック関数を設定
            button.callback = self.vote_button_callback
            self.add_item(button)
    
    async def vote_button_callback(self, interaction: discord.Interaction):
        """投票ボタンが押されたときのコールバック"""
        # ボタンを押したユーザーのIDを取得
        voter_id = str(interaction.user.id)
        # 投票先のIDをカスタムIDから抽出
        target_id = interaction.data["custom_id"].split("_")[1]
        
        # 投票者がゲームに参加しているかチェック
        if voter_id not in self.game.players:
            await interaction.response.send_message("あなたはこのゲームに参加していません。", ephemeral=True)
            return
        
        # 投票者が生存しているかチェック
        voter = self.game.players[voter_id]
        if not voter.is_alive:
            await interaction.response.send_message("あなたはすでに死亡しているため、投票できません。", ephemeral=True)
            return
        
        # 投票先が存在するかチェック
        if target_id not in self.game.players:
            await interaction.response.send_message("指定したプレイヤーはゲームに参加していません。", ephemeral=True)
            return
        
        # 投票先が生存しているかチェック
        target = self.game.players[target_id]
        if not target.is_alive:
            await interaction.response.send_message("指定したプレイヤーはすでに死亡しています。", ephemeral=True)
            return
        
        # 自分自身への投票を禁止
        if voter_id == target_id:
            await interaction.response.send_message("自分自身には投票できません。", ephemeral=True)
            return
        
        # 前回の投票をチェック
        previous_vote_id = self.game.votes.get(voter_id)
        previous_vote = None
        if previous_vote_id:
            previous_vote = self.game.players.get(previous_vote_id)
        
        # 投票を記録
        self.game.add_vote(voter_id, target_id)
        self.voters[voter_id] = target_id
        
        # 応答メッセージを送信
        if previous_vote:
            await interaction.response.send_message(
                f"{previous_vote.name}への投票を取り消し、{target.name}に投票しました。",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"{target.name}に投票しました。",
                ephemeral=True
            )
        
        # 投票状況を更新して表示
        await self.update_vote_status()
        
        # 全員が投票したかチェック
        alive_count = len(self.game.get_alive_players())
        vote_count = len(self.game.votes)
        
        if vote_count >= alive_count:
            # 全員が投票した場合、タイマーを終了して結果処理
            self.game.cancel_timer()
            
            # 投票Cogを取得して結果処理を呼び出す
            voting_cog = self.game.bot.get_cog("VotingCog")
            if voting_cog:
                await voting_cog.process_voting_results(self.channel, self.game)
    
    async def update_vote_status(self):
        """投票状況の埋め込みメッセージを更新"""
        if not self.message:
            return
        
        # 生存プレイヤー数と投票数を取得
        alive_players = self.game.get_alive_players()
        vote_count = len(self.game.votes)
        
        # 埋め込みメッセージを作成
        embed = create_base_embed(
            title="🗳️ 投票",
            description=f"処刑する人を決めるための投票です。\n"
                       f"投票時間: {self.timeout}秒\n\n"
                       f"**ボタンをクリックして投票してください**",
            color=EmbedColors.PRIMARY
        )
        
        # 生存プレイヤーリストを追加
        player_list = "\n".join([f"- {p.name}" for p in alive_players])
        embed.add_field(name="生存者", value=player_list, inline=False)
        
        # 投票状況フィールド
        vote_status = ""
        
        if not self.game.votes:
            vote_status = "まだ投票はありません。"
        else:
            for voter_id, target_id in self.game.votes.items():
                voter = self.game.players[voter_id]
                target = self.game.players[target_id]
                vote_status += f"{voter.name} → {target.name}\n"
        
        embed.add_field(name="投票状況", value=vote_status, inline=False)
        
        # 投票状況を追加
        embed.add_field(
            name="進行状況", 
            value=f"{vote_count}/{len(alive_players)} 投票完了", 
            inline=False
        )
        
        # メッセージを更新
        try:
            await self.message.edit(embed=embed, view=self)
        except discord.NotFound:
            pass
    
    async def on_timeout(self):
        """タイムアウト時の処理"""
        # ボタンを無効化
        for item in self.children:
            item.disabled = True
        
        # メッセージを更新
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass
        
        # VotingCogを取得して結果処理
        voting_cog = self.game.bot.get_cog("VotingCog")
        if voting_cog and self.game.phase == "voting":
            await voting_cog.process_voting_results(self.channel, self.game)
