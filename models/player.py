"""
プレイヤーモデル
"""
from models.roles import create_role_instance

class Player:
    """プレイヤークラス"""
    
    def __init__(self, user_id, name, game=None):
        self.user_id = user_id  # Discord ユーザーID
        self.name = name  # プレイヤー名
        self.role_name = None  # 役職名（文字列）
        self.role_instance = None  # 役職クラスのインスタンス
        self.is_alive = True  # 生存状態
        self.game = game  # ゲーム参照
        
        # 夜のアクション用
        self.night_action_used = False  # 夜のアクションを使用したか
        self.night_action_target = None  # 夜のアクションの対象
        self.last_protected = None  # 前回の護衛対象（狩人用）
        
        # 占い結果保存用（占い師用）
        self.divination_results = {}  # {user_id: is_werewolf}
    
    def assign_role(self, role_name):
        """役職を割り当て"""
        self.role_name = role_name
        self.role_instance = create_role_instance(role_name, self)
        return self
    
    @property
    def role(self):
        """役職名を返す（後方互換性のため）"""
        return self.role_name
    
    @role.setter
    def role(self, value):
        """役職名を設定（後方互換性のため）"""
        self.assign_role(value)
    
    def kill(self):
        """プレイヤーを死亡させる"""
        # 妖狐の特殊処理（人狼からの襲撃耐性）
        if self.is_fox() and (self.game.wolf_target == self.user_id):
            # kill操作を無視
            return self
            
        self.is_alive = False
        
        # 恋人の相方も死亡させる
        if self.game and hasattr(self.game, 'special_rules'):
            special_rules = self.game.special_rules
            if special_rules.lovers_enabled:
                # 恋人の相方を取得
                partner_id = special_rules.get_partner(self.user_id)
                if partner_id and str(partner_id) in self.game.players:
                    partner = self.game.players[str(partner_id)]
                    if partner.is_alive:
                        # 恋人の相方を死亡させる
                        partner.is_alive = False
                        # Note: ここでは連鎖的に kill() を呼び出さない（無限ループ回避）
        
        return self
    
    def reset_night_action(self):
        """夜のアクション状態をリセット"""
        self.night_action_used = False
        self.night_action_target = None
    
    def is_werewolf(self):
        """人狼かどうか"""
        return self.role_name == "人狼"
    
    def is_villager_team(self):
        """村人陣営かどうか"""
        if self.role_instance:
            return self.role_instance.team == "村人陣営"
        return self.role_name in ["村人", "占い師", "狩人", "霊能者"]
    
    def is_wolf_team(self):
        """人狼陣営かどうか"""
        if self.role_instance:
            return self.role_instance.team == "人狼陣営"
        return self.role_name in ["人狼", "狂人"]
    
    def is_fox(self):
        """妖狐かどうか"""
        return self.role_name == "妖狐"
    
    def has_night_action(self):
        """夜のアクションがあるかどうか"""
        if self.role_instance:
            return self.role_instance.can_use_night_action()
        return self.role_name in ["人狼", "占い師", "狩人"]
        
    async def execute_night_action(self, target_id):
        """夜のアクションを実行"""
        if self.role_instance:
            return await self.role_instance.execute_night_action(target_id)
        return False, "役職クラスが初期化されていません。"
