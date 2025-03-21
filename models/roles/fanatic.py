"""
狂信者の役職クラス
人狼を知っているが、人狼からは知られない特殊な狂人
"""
from .base_role import BaseRole
import discord

class Fanatic(BaseRole):
    """狂信者クラス"""
    
    @property
    def name(self):
        return "狂信者"
    
    @property
    def team(self):
        """狂信者は人狼陣営だが村人として扱われる"""
        return "人狼陣営"
    
    def can_use_night_action(self):
        """狂信者は夜のアクションを使用できない"""
        return False
    
    async def execute_night_action(self, target_id):
        """狂信者は夜のアクションがないため何もしない"""
        return False, "狂信者には夜のアクションがありません。"
    
    def on_game_start(self):
        """ゲーム開始時、人狼に関する情報をDMで送信"""
        # 人狼を探す
        werewolves = []
        for player in self.game.players.values():
            if player.role == "人狼" and player.is_alive:
                werewolves.append(player)
        
        # 人狼情報を表示するメッセージを作成
        embed = discord.Embed(
            title="狂信者情報",
            description="あなたは狂信者です。人狼を知っていますが、人狼からはあなたの正体は知られていません。",
            color=0x8B0000  # ダークレッド（人狼陣営）
        )
        
        if werewolves:
            wolf_text = "\n".join([f"・{player.name}" for player in werewolves])
            embed.add_field(name="人狼", value=wolf_text, inline=False)
            embed.add_field(
                name="勝利条件", 
                value="人狼陣営の勝利が、あなたの勝利となります。人狼をサポートしてください。", 
                inline=False
            )
        else:
            embed.add_field(
                name="人狼なし", 
                value="ゲーム内に人狼がいません。これはおそらくエラーです。", 
                inline=False
            )
        
        embed.add_field(
            name="注意事項", 
            value="あなたは人狼ではありませんので、襲撃能力はありません。村人から見れば普通の人です。", 
            inline=False
        )
        
        # DM送信処理は外部で行うため、Embedを返す
        return embed
