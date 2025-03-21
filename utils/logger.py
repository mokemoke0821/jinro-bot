"""
ロギングモジュール
ゲームのログを記録する
"""
import os
import logging
from datetime import datetime

class GameLogger:
    """ゲームロガークラス"""
    
    def __init__(self, log_dir="logs"):
        """初期化"""
        self.log_dir = log_dir
        
        # ログディレクトリが存在しない場合は作成
        os.makedirs(log_dir, exist_ok=True)
        
        # ロガーの設定
        self.logger = logging.getLogger("werewolf_game")
        self.logger.setLevel(logging.INFO)
        
        # 標準出力用ハンドラ
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
    
    def create_game_log(self, guild_id, channel_id):
        """新しいゲームのログファイルを作成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"{self.log_dir}/game_{guild_id}_{timestamp}.log"
        
        # ファイル用ハンドラ
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_format = logging.Formatter('%(asctime)s - %(message)s')
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)
        
        self.logger.info(f"ゲームログ開始 - サーバーID: {guild_id}, チャンネルID: {channel_id}")
        return log_filename
    
    def log_game_event(self, event_type, content):
        """ゲームイベントを記録"""
        self.logger.info(f"[{event_type}] {content}")
    
    def log_player_action(self, player_name, action, target=None):
        """プレイヤーアクションを記録"""
        if target:
            self.logger.info(f"[アクション] {player_name} が {action} を {target} に対して実行")
        else:
            self.logger.info(f"[アクション] {player_name} が {action} を実行")
    
    def log_phase_change(self, old_phase, new_phase, day=None):
        """フェーズ変更を記録"""
        day_info = f" (Day {day})" if day is not None else ""
        self.logger.info(f"[フェーズ変更] {old_phase} から {new_phase} へ{day_info}")
    
    def log_vote(self, voter, target, phase="投票"):
        """投票を記録"""
        self.logger.info(f"[{phase}] {voter} が {target} に投票")
    
    def log_death(self, player, cause):
        """死亡を記録"""
        self.logger.info(f"[死亡] {player} が {cause} で死亡")
    
    def log_game_end(self, winner, players_info):
        """ゲーム終了を記録"""
        self.logger.info(f"[ゲーム終了] 勝者: {winner}")
        self.logger.info(f"[プレイヤー情報] {players_info}")
    
    def close_log(self):
        """ロガーをクローズ"""
        handlers = self.logger.handlers[:]
        for handler in handlers:
            if isinstance(handler, logging.FileHandler):
                self.logger.removeHandler(handler)
                handler.close()
