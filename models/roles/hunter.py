"""
狩人の役職クラス
夜に一人を護衛して人狼の襲撃から守る能力を持つ
"""
from .base_role import BaseRole

class Hunter(BaseRole):
    """狩人クラス"""
    
    @property
    def name(self):
        return "狩人"
    
    def can_use_night_action(self):
        """狩人は夜のアクションを使用できる"""
        return True
    
    async def execute_night_action(self, target_id):
        """指定したプレイヤーを護衛する"""
        # 前回と同じ対象を選択できないチェック
        if self.player.last_protected == target_id:
            return False, "同じ対象を連続で護衛することはできません。"
        
        # 護衛対象を設定
        self.player.night_action_target = target_id
        self.player.night_action_used = True
        
        return True, "護衛対象を設定しました。"
