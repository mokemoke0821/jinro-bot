"""
預言者の役職クラス
夜に一人を預言して、人狼と妖狐を区別できる上位互換の占い師
"""
from .base_role import BaseRole

class Prophet(BaseRole):
    """預言者クラス"""
    
    @property
    def name(self):
        return "預言者"
    
    def can_use_night_action(self):
        """預言者は夜のアクションを使用できる"""
        return True
    
    async def execute_night_action(self, target_id):
        """指定したプレイヤーを高度な占いで調査"""
        # 預言対象を設定
        self.player.night_action_target = target_id
        self.player.night_action_used = True
        
        target_player = self.game.players.get(target_id)
        if not target_player:
            return False, "指定されたプレイヤーが見つかりません。"
        
        # 預言結果を記録 (人狼、妖狐、村人陣営の3種類で判定)
        if target_player.role == "人狼":
            result = "werewolf"  # 人狼
        elif target_player.role == "妖狐":
            result = "fox"  # 妖狐
        else:
            result = "human"  # その他（村人陣営または狂人など）
        
        # 預言結果をプレイヤーに保存
        if not hasattr(self.player, "prophecy_results"):
            self.player.prophecy_results = {}
        
        self.player.prophecy_results[target_id] = result
        
        # 妖狐の占い死判定 - 預言者も妖狐を死亡させる
        if target_player.role == "妖狐" and target_player.is_alive:
            target_player.kill()
            self.game.killed_by_divination = target_id
        
        return True, "預言を実行しました。"
    
    def get_night_action_result(self):
        """預言結果を取得"""
        if not self.player.night_action_target:
            return None, None
        
        target_player = self.game.players.get(self.player.night_action_target)
        if not target_player:
            return None, None
        
        # 預言結果がなければ取得できない
        if not hasattr(self.player, "prophecy_results") or self.player.night_action_target not in self.player.prophecy_results:
            return None, None
        
        result = self.player.prophecy_results[self.player.night_action_target]
        # 結果に応じて表示用テキストを設定
        result_text = {
            "werewolf": "人狼",
            "fox": "妖狐",
            "human": "村人陣営"
        }.get(result, "不明")
        
        return target_player, result_text
