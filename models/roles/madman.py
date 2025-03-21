"""
狂人の役職クラス
人狼陣営だが村人と判定される
"""
from .base_role import BaseRole

class Madman(BaseRole):
    """狂人クラス"""
    
    @property
    def name(self):
        return "狂人"
    
    @property
    def team(self):
        """人狼陣営に所属"""
        return "人狼陣営"
    
    def can_use_night_action(self):
        """狂人は夜のアクションを使用できない"""
        return False
    
    async def execute_night_action(self, target_id):
        """狂人は夜のアクションがないため何もしない"""
        return False, "狂人には夜のアクションがありません。"
