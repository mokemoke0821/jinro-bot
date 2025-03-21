"""
設定関連モジュール
"""
from enum import Enum
import random

class GameConfig:
    """ゲーム設定"""
    PREFIX = "!"  # コマンドプレフィックス
    NIGHT_PHASE_TIME = 120  # 夜のフェーズの制限時間（秒）
    DAY_PHASE_TIME = 300  # 昼のフェーズの制限時間（秒）
    VOTE_TIME = 60  # 投票時間（秒）
    
    # 役職の構成
    # プレイヤー数ごとの役職分布（人狼, 占い師, 狩人, 霊能者, 狂人, 妖狐）
    ROLE_DISTRIBUTION = {
        5: {"人狼": 1, "占い師": 1, "村人": 3},
        6: {"人狼": 1, "占い師": 1, "村人": 4},
        7: {"人狼": 2, "占い師": 1, "村人": 4},
        8: {"人狼": 2, "占い師": 1, "狩人": 1, "村人": 4},
        9: {"人狼": 2, "占い師": 1, "狩人": 1, "霊能者": 1, "村人": 4},
        10: {"人狼": 2, "占い師": 1, "狩人": 1, "霊能者": 1, "狂人": 1, "村人": 4},
        11: {"人狼": 3, "占い師": 1, "狩人": 1, "霊能者": 1, "狂人": 1, "村人": 4},
        12: {"人狼": 3, "占い師": 1, "狩人": 1, "霊能者": 1, "狂人": 1, "妖狐": 1, "村人": 4},
    }
    
    @staticmethod
    def get_role_distribution(player_count):
        """プレイヤー数に応じた役職分布を取得"""
        if player_count in GameConfig.ROLE_DISTRIBUTION:
            return GameConfig.ROLE_DISTRIBUTION[player_count]
        
        # 対応するプレイヤー数がない場合は最大値に村人を追加
        max_count = max(GameConfig.ROLE_DISTRIBUTION.keys())
        base_dist = GameConfig.ROLE_DISTRIBUTION[max_count].copy()
        
        extra_villagers = player_count - max_count
        if extra_villagers > 0:
            base_dist["村人"] += extra_villagers
        
        return base_dist

class EmbedColors:
    """Embedの色定義"""
    PRIMARY = 0x3498db  # 青
    SUCCESS = 0x2ecc71  # 緑
    WARNING = 0xf1c40f  # 黄
    ERROR = 0xe74c3c  # 赤
    INFO = 0x95a5a6  # グレー
    NIGHT = 0x34495e  # 濃い青（夜）
    DAY = 0xf39c12  # オレンジ（昼）
