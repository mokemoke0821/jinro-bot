"""
占い師の役職クラス
夜に一人を占い、陣営を知ることができる
"""
from .base_role import BaseRole

class Seer(BaseRole):
    """占い師クラス"""
    
    @property
    def name(self):
        return "占い師"
    
    def can_use_night_action(self):
        """占い師は夜のアクションを使用できる"""
        return True
    
    async def execute_night_action(self, target_id):
        """指定したプレイヤーを占う"""
        # 占い対象を設定
        self.player.night_action_target = target_id
        self.player.night_action_used = True
        
        target_player = self.game.players.get(target_id)
        if not target_player:
            return False, "指定されたプレイヤーが見つかりません。"
        
        # 占い結果を記録
        is_werewolf = target_player.role == "人狼"
        self.player.divination_results[target_id] = is_werewolf
        
        # 妖狐の占い死判定
        if target_player.role == "妖狐" and target_player.is_alive:
            target_player.kill()
            self.game.killed_by_divination = target_id
        
        return True, "占いを実行しました。"
    
    def get_night_action_result(self):
        """占い結果を取得"""
        if not self.player.night_action_target:
            return None, None
        
        target_player = self.game.players.get(self.player.night_action_target)
        if not target_player:
            return None, None
        
        is_werewolf = target_player.role == "人狼"
        return target_player, is_werewolf
