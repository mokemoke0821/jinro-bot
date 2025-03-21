"""
共有者の役職クラス
お互いを認識できる村人陣営の役職
"""
from .base_role import BaseRole
import discord

class Mason(BaseRole):
    """共有者クラス"""
    
    @property
    def name(self):
        return "共有者"
    
    def can_use_night_action(self):
        """共有者は夜のアクションを使用できない"""
        return False
    
    async def execute_night_action(self, target_id):
        """共有者は夜のアクションがないため何もしない"""
        return False, "共有者には夜のアクションがありません。"
    
    def on_game_start(self):
        """ゲーム開始時、他の共有者に関する情報をDMで送信"""
        # 自分以外の共有者を探す
        other_masons = []
        for player in self.game.players.values():
            if (player.role == "共有者" and 
                player.is_alive and 
                player.user_id != self.player.user_id):
                other_masons.append(player)
        
        # 共有者情報を表示するメッセージを作成
        embed = discord.Embed(
            title="共有者情報",
            description="あなたは共有者です。他の共有者は以下の通りです。",
            color=0x4CAF50  # 緑色（村人陣営）
        )
        
        if other_masons:
            mason_text = "\n".join([f"・{player.name}" for player in other_masons])
            embed.add_field(name="他の共有者", value=mason_text, inline=False)
        else:
            embed.add_field(name="他の共有者", value="他の共有者はいません。あなた一人です。", inline=False)
        
        # DM送信処理は外部で行うため、Embedを返す
        return embed
