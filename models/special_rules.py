"""
特殊ルールを管理するクラス
ゲームの特殊ルールを設定・管理する
"""

class SpecialRules:
    """特殊ルールを管理するクラス"""
    
    def __init__(self):
        # デフォルト設定
        self.no_first_night_kill = False  # 初日の襲撃なし
        self.lovers_enabled = False       # 恋人ルール
        self.no_consecutive_guard = False # 連続ガード禁止
        self.random_tied_vote = False     # 投票同数時ランダム処刑
        self.dead_chat_enabled = False    # 霊界チャット
        
        # 恋人関連のデータ
        self.lovers = []  # 恋人のプレイヤーIDのペアを格納
        
        # 連続ガード禁止用のデータ
        self.last_guarded = {}  # Key: 狩人のID, Value: 最後に護衛したプレイヤーID
    
    def to_dict(self):
        """設定を辞書形式でエクスポート"""
        return {
            "no_first_night_kill": self.no_first_night_kill,
            "lovers_enabled": self.lovers_enabled,
            "no_consecutive_guard": self.no_consecutive_guard,
            "random_tied_vote": self.random_tied_vote,
            "dead_chat_enabled": self.dead_chat_enabled,
            "lovers": self.lovers,
            "last_guarded": self.last_guarded
        }
    
    def from_dict(self, data):
        """辞書からデータをインポート"""
        if data:
            self.no_first_night_kill = data.get("no_first_night_kill", False)
            self.lovers_enabled = data.get("lovers_enabled", False)
            self.no_consecutive_guard = data.get("no_consecutive_guard", False)
            self.random_tied_vote = data.get("random_tied_vote", False) 
            self.dead_chat_enabled = data.get("dead_chat_enabled", False)
            self.lovers = data.get("lovers", [])
            self.last_guarded = data.get("last_guarded", {})
    
    def set_lovers(self, player1_id, player2_id):
        """恋人を設定"""
        # すでに恋人がいないか確認
        for pair in self.lovers:
            if player1_id in pair or player2_id in pair:
                return False
        
        # 恋人ペアを追加
        self.lovers.append((player1_id, player2_id))
        return True
    
    def is_lover(self, player_id):
        """プレイヤーが恋人かどうか確認"""
        for pair in self.lovers:
            if player_id in pair:
                return True
        return False
    
    def get_partner(self, player_id):
        """恋人の相手を取得"""
        for pair in self.lovers:
            if pair[0] == player_id:
                return pair[1]
            elif pair[1] == player_id:
                return pair[0]
        return None
    
    def can_guard(self, guard_id, target_id):
        """護衛可能かどうかを判定（連続ガード禁止ルールがある場合）"""
        if not self.no_consecutive_guard:
            return True
        
        # 前回護衛した対象と同じかチェック
        return self.last_guarded.get(guard_id) != target_id
    
    def set_guarded(self, guard_id, target_id):
        """護衛情報を記録"""
        self.last_guarded[guard_id] = target_id
    
    def reset_game_state(self):
        """ゲーム固有の状態をリセット"""
        self.lovers = []
        self.last_guarded = {}
