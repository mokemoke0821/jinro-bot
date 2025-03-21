"""
村人の役職クラス
特殊能力を持たない基本役職
"""
from .base_role import BaseRole

class Villager(BaseRole):
    """村人クラス"""
    
    @property
    def name(self):
        return "村人"
    
    def can_use_night_action(self):
        """村人は夜のアクションを使用できない"""
        return False
    
    async def execute_night_action(self, target_id):
        """村人は夜のアクションがないため何もしない"""
        return False, "村人には夜のアクションがありません。"
