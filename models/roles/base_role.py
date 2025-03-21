"""
役職の基底クラス
全ての役職クラスはこのクラスを継承する
"""
from abc import ABC, abstractmethod

class BaseRole(ABC):
    """役職の基底クラス"""
    
    def __init__(self, player):
        self.player = player  # プレイヤーの参照
        self.game = player.game  # ゲームの参照
    
    @property
    def name(self):
        """役職名を返す"""
        return self.__class__.__name__
    
    @property
    def team(self):
        """所属する陣営を返す（村人陣営/人狼陣営/妖狐陣営）"""
        return "村人陣営"  # デフォルトは村人陣営
    
    @abstractmethod
    def can_use_night_action(self):
        """夜のアクションを使用できるかどうかを返す"""
        pass
    
    @abstractmethod
    async def execute_night_action(self, target_id):
        """夜のアクションを実行する"""
        pass
    
    def on_voted(self):
        """投票されたときの処理"""
        pass
    
    def on_executed(self):
        """処刑されたときの処理"""
        pass
    
    def on_killed(self):
        """襲撃されたときの処理"""
        pass
    
    def on_game_start(self):
        """ゲーム開始時の処理"""
        pass
    
    def on_night_start(self):
        """夜のフェーズ開始時の処理"""
        pass
    
    def on_day_start(self):
        """昼のフェーズ開始時の処理"""
        pass
    
    def get_night_action_result(self):
        """夜のアクション結果を取得"""
        return None
