"""
妖狐の役職クラス
占われると死亡する、生き残れば単独勝利となる特殊役職
"""
from .base_role import BaseRole

class Fox(BaseRole):
    """妖狐クラス"""
    
    @property
    def name(self):
        return "妖狐"
    
    @property
    def team(self):
        """妖狐陣営に所属"""
        return "妖狐陣営"
    
    def can_use_night_action(self):
        """妖狐は夜のアクションを使用できない"""
        return False
    
    async def execute_night_action(self, target_id):
        """妖狐は夜のアクションがないため何もしない"""
        return False, "妖狐には夜のアクションがありません。"
    
    def on_killed(self):
        """人狼に襲撃されても死なない特殊処理"""
        # ただし占いによる死亡は別処理で行われる
        if self.game.wolf_target == self.player.user_id:
            # 人狼による襲撃から復活
            self.player.is_alive = True
            return True
        return False
