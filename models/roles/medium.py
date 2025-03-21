"""
霊媒師の役職クラス
処刑されたプレイヤーが人狼かどうかを知る能力を持つ
"""
from .base_role import BaseRole

class Medium(BaseRole):
    """霊媒師クラス"""
    
    @property
    def name(self):
        return "霊媒師"
    
    def can_use_night_action(self):
        """霊媒師は自動的に結果を得るため、夜のアクション選択は不要"""
        return False
    
    async def execute_night_action(self, target_id):
        """霊媒師は対象を選択する夜のアクションがない"""
        return False, "霊媒師は対象を選択するアクションがありません。処刑結果は自動的に通知されます。"
    
    def on_night_start(self):
        """夜のフェーズ開始時に自動的に処刑者の結果を得る"""
        if not self.game.last_executed:
            return
        
        executed_player = self.game.players.get(self.game.last_executed)
        if executed_player:
            is_werewolf = executed_player.role == "人狼"
            self.player.medium_results[self.game.last_executed] = is_werewolf
            # アクション済みフラグを立てる
            self.player.night_action_used = True
    
    def get_night_action_result(self):
        """霊媒結果を取得"""
        if not self.game.last_executed:
            return None, None
        
        executed_player = self.game.players.get(self.game.last_executed)
        if not executed_player:
            return None, None
        
        is_werewolf = executed_player.role == "人狼"
        return executed_player, is_werewolf
