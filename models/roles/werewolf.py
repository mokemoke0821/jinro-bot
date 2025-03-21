"""
人狼の役職クラス
夜に一人を襲撃できる能力を持つ
"""
from .base_role import BaseRole

class Werewolf(BaseRole):
    """人狼クラス"""
    
    @property
    def name(self):
        return "人狼"
    
    @property
    def team(self):
        """人狼陣営に所属"""
        return "人狼陣営"
    
    def can_use_night_action(self):
        """人狼は夜のアクションを使用できる"""
        return True
    
    async def execute_night_action(self, target_id):
        """指定したプレイヤーを襲撃対象として設定"""
        # 襲撃対象を設定
        self.player.night_action_target = target_id
        self.player.night_action_used = True
        
        # 他の人狼プレイヤーにも共有（複数人狼がいる場合）
        other_wolves = []
        for player in self.game.players.values():
            if (player.role == "人狼" and 
                player.is_alive and 
                player.user_id != self.player.user_id):
                other_wolves.append(player)
                player.night_action_target = target_id
                player.night_action_used = True
        
        return True, "襲撃対象を設定しました。"
    
    def get_teammates(self):
        """仲間の人狼を取得"""
        return [p for p in self.game.players.values() 
                if p.role == "人狼" and p.user_id != self.player.user_id]
