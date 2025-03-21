"""
プレイヤーモデル
"""

class Player:
    """プレイヤークラス"""
    
    def __init__(self, user_id, name, game=None):
        self.user_id = user_id  # Discord ユーザーID
        self.name = name  # プレイヤー名
        self.role = None  # 役職
        self.is_alive = True  # 生存状態
        self.game = game  # ゲーム参照
        
        # 夜のアクション用
        self.night_action_used = False  # 夜のアクションを使用したか
        self.night_action_target = None  # 夜のアクションの対象
        self.last_protected = None  # 前回の護衛対象（狩人用）
        
        # 占い結果保存用（占い師用）
        self.divination_results = {}  # {user_id: is_werewolf}
    
    def assign_role(self, role):
        """役職を割り当て"""
        self.role = role
        return self
    
    def kill(self):
        """プレイヤーを死亡させる"""
        self.is_alive = False
        return self
    
    def reset_night_action(self):
        """夜のアクション状態をリセット"""
        self.night_action_used = False
        self.night_action_target = None
    
    def is_werewolf(self):
        """人狼かどうか"""
        return self.role == "人狼"
    
    def is_villager_team(self):
        """村人陣営かどうか"""
        return self.role in ["村人", "占い師", "狩人", "霊能者"]
    
    def is_wolf_team(self):
        """人狼陣営かどうか"""
        return self.role in ["人狼", "狂人"]
    
    def is_fox(self):
        """妖狐かどうか"""
        return self.role == "妖狐"
    
    def has_night_action(self):
        """夜のアクションがあるかどうか"""
        return self.role in ["人狼", "占い師", "狩人"]
