"""
猫又の役職クラス
死亡時に任意のプレイヤーを道連れにする特殊村人
"""
from .base_role import BaseRole
import discord
import random

class Cat(BaseRole):
    """猫又クラス"""
    
    @property
    def name(self):
        return "猫又"
    
    def can_use_night_action(self):
        """猫又は夜のアクションを使用できない"""
        return False
    
    async def execute_night_action(self, target_id):
        """猫又は夜のアクションがないため何もしない"""
        return False, "猫又には夜のアクションがありません。"
    
    def on_game_start(self):
        """ゲーム開始時、役割情報をDMで送信"""
        embed = discord.Embed(
            title="猫又情報",
            description="あなたは猫又です。死亡したとき、任意のプレイヤーを道連れにできます。",
            color=0x4CAF50  # 緑色（村人陣営）
        )
        
        embed.add_field(
            name="特殊能力", 
            value="処刑または襲撃で死亡した場合、生存者の中から一人を選んで道連れにできます。", 
            inline=False
        )
        
        # DM送信処理は外部で行うため、Embedを返す
        return embed
    
    def on_executed(self):
        """処刑されたときの処理（道連れ能力の発動）"""
        return self._activate_curse_ability()
    
    def on_killed(self):
        """襲撃されたときの処理（道連れ能力の発動）"""
        return self._activate_curse_ability()
    
    def _activate_curse_ability(self):
        """道連れ能力の発動処理"""
        # 生存者リストを作成
        living_players = []
        for player in self.game.players.values():
            if player.is_alive and player.user_id != self.player.user_id:
                living_players.append(player)
        
        if not living_players:
            return None
        
        # 道連れ対象選択用のEmbedを作成
        embed = discord.Embed(
            title="猫又の能力発動",
            description="あなたは死亡しました。道連れにするプレイヤーを選択してください。",
            color=0xFF5722  # オレンジ色（特殊能力）
        )
        
        for i, player in enumerate(living_players):
            embed.add_field(
                name=f"{i+1}. {player.name}",
                value=f"ID: {player.user_id}",
                inline=True
            )
        
        # 選択情報をゲームオブジェクトに保存
        self.game.cat_revenge_options = {
            "cat_user_id": self.player.user_id,
            "living_players": living_players
        }
        
        return embed
