"""
背徳者の役職クラス
村人として扱われるが妖狐陣営の役職
"""
from .base_role import BaseRole
import discord

class Heretic(BaseRole):
    """背徳者クラス"""
    
    @property
    def name(self):
        return "背徳者"
    
    @property
    def team(self):
        """妖狐陣営に所属するが、村人として扱われる"""
        return "妖狐陣営"
    
    def can_use_night_action(self):
        """背徳者は夜のアクションを使用できない"""
        return False
    
    async def execute_night_action(self, target_id):
        """背徳者は夜のアクションがないため何もしない"""
        return False, "背徳者には夜のアクションがありません。"
    
    def on_game_start(self):
        """ゲーム開始時、妖狐に関する情報をDMで送信"""
        # 妖狐を探す
        foxes = []
        for player in self.game.players.values():
            if player.role == "妖狐" and player.is_alive:
                foxes.append(player)
        
        # 妖狐情報を表示するメッセージを作成
        embed = discord.Embed(
            title="背徳者情報",
            description="あなたは背徳者です。妖狐陣営として妖狐の勝利を目指します。",
            color=0x9C27B0  # 紫色（妖狐陣営）
        )
        
        if foxes:
            fox_text = "\n".join([f"・{player.name}" for player in foxes])
            embed.add_field(name="妖狐", value=fox_text, inline=False)
            embed.add_field(
                name="勝利条件", 
                value="妖狐が生き残ることで勝利します。妖狐陣営の一員として行動してください。", 
                inline=False
            )
        else:
            embed.add_field(
                name="妖狐なし", 
                value="妖狐がいません。あなたは村人陣営として扱われます。", 
                inline=False
            )
            embed.add_field(
                name="勝利条件", 
                value="村人陣営の勝利条件「人狼の全滅」が適用されます。", 
                inline=False
            )
        
        # DM送信処理は外部で行うため、Embedを返す
        return embed
