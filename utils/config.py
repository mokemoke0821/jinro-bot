"""
設定管理のためのユーティリティクラス
"""
import os
import json
from typing import Dict, Any, Optional, List

class EmbedColors:
    """埋め込みメッセージの色定義"""
    PRIMARY = 0x007BFF    # 青色 (プライマリカラー)
    SUCCESS = 0x28A745    # 緑色 (成功)
    WARNING = 0xFFC107    # 黄色 (警告)
    ERROR = 0xDC3545      # 赤色 (エラー)
    INFO = 0x17A2B8       # 水色 (情報)
    DAY = 0xF8D568        # 昼の色
    NIGHT = 0x2C3E50      # 夜の色

class GameConfig:
    """ゲームの基本設定を格納する定数クラス"""
    # コマンドプレフィックス
    PREFIX = "!"
    
    # ゲーム設定のデフォルト値
    DEFAULT_DAY_TIME = 300  # 昼フェーズの時間（秒）
    DEFAULT_NIGHT_TIME = 90  # 夜フェーズの時間（秒）
    MIN_PLAYERS = 4  # 最小プレイヤー数
    MAX_PLAYERS = 15  # 最大プレイヤー数
    
    # ディレクトリパス
    DATA_DIR = "data"
    CONFIG_DIR = os.path.join(DATA_DIR, "config")
    STATS_DIR = os.path.join(DATA_DIR, "stats")
    LOG_DIR = os.path.join(DATA_DIR, "logs")

class ConfigManager:
    """サーバーごとの設定を管理するクラス"""
    
    def __init__(self):
        self.config_directory = "data/config"
        self._ensure_config_directory()
        self.default_config = self._get_default_config()
    
    def _ensure_config_directory(self):
        """設定ディレクトリが存在することを確認"""
        if not os.path.exists(self.config_directory):
            os.makedirs(self.config_directory)
    
    def _get_server_config_path(self, guild_id: int) -> str:
        """サーバー設定ファイルのパスを取得"""
        return f"{self.config_directory}/{guild_id}_config.json"
    
    def _get_default_config(self) -> Dict[str, Any]:
        """デフォルト設定を取得"""
        return {
            # ゲーム設定
            "day_time": 300,       # 昼フェーズの時間（秒）
            "night_time": 90,      # 夜フェーズの時間（秒）
            "min_players": 4,      # 最小プレイヤー数
            "max_players": 15,     # 最大プレイヤー数
            "random_roles": True,  # 役職ランダム割り当て
            "spectator_chat": True,  # 死亡プレイヤーのチャット
            
            # 役職設定
            "roles": {
                "Villager": {"enabled": True, "min_count": 1, "max_count": 999},
                "Werewolf": {"enabled": True, "min_count": 1, "max_count": 999},
                "Seer": {"enabled": True, "min_count": 0, "max_count": 1},
                "Hunter": {"enabled": True, "min_count": 0, "max_count": 1},
                "Medium": {"enabled": True, "min_count": 0, "max_count": 1},
                "Madman": {"enabled": True, "min_count": 0, "max_count": 1},
                "Fox": {"enabled": True, "min_count": 0, "max_count": 1}
            },
            
            # 管理者権限
            "admin_roles": []
        }
    
    def get_server_config(self, guild_id: int) -> Dict[str, Any]:
        """サーバーの設定を取得"""
        config_path = self._get_server_config_path(guild_id)
        
        # 設定ファイルが存在する場合は読み込む
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                return config
            except json.JSONDecodeError:
                # ファイルが破損している場合はデフォルト設定を返す
                return self.default_config.copy()
        else:
            # 設定ファイルが存在しない場合はデフォルト設定を返す
            return self.default_config.copy()
    
    def save_server_config(self, guild_id: int, config: Dict[str, Any]):
        """サーバーの設定を保存"""
        config_path = self._get_server_config_path(guild_id)
        
        # 設定ディレクトリが存在することを確認
        self._ensure_config_directory()
        
        # 設定を保存
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def reset_server_config(self, guild_id: int):
        """サーバーの設定をリセット"""
        config_path = self._get_server_config_path(guild_id)
        
        # 設定ファイルが存在する場合は削除
        if os.path.exists(config_path):
            os.remove(config_path)
    
    def get_setting(self, guild_id: int, setting: str, default=None) -> Any:
        """特定の設定値を取得"""
        config = self.get_server_config(guild_id)
        return config.get(setting, default)
    
    def update_setting(self, guild_id: int, setting: str, value: Any):
        """特定の設定値を更新"""
        config = self.get_server_config(guild_id)
        config[setting] = value
        self.save_server_config(guild_id, config)
    
    def get_role_config(self, guild_id: int, role: str) -> Dict[str, Any]:
        """特定の役職の設定を取得"""
        config = self.get_server_config(guild_id)
        roles = config.get("roles", {})
        
        if role in roles:
            return roles[role]
        else:
            # デフォルト設定を返す
            return self.default_config["roles"].get(role, {"enabled": True, "min_count": 0, "max_count": 999})
    
    def update_role_config(self, guild_id: int, role: str, role_config: Dict[str, Any]):
        """特定の役職の設定を更新"""
        config = self.get_server_config(guild_id)
        
        if "roles" not in config:
            config["roles"] = {}
        
        config["roles"][role] = role_config
        self.save_server_config(guild_id, config)
    
    def is_role_enabled(self, guild_id: int, role: str) -> bool:
        """役職が有効かどうか確認"""
        role_config = self.get_role_config(guild_id, role)
        return role_config.get("enabled", True)
    
    def get_admin_roles(self, guild_id: int) -> List[int]:
        """管理者ロールのIDリストを取得"""
        config = self.get_server_config(guild_id)
        return config.get("admin_roles", [])
    
    def add_admin_role(self, guild_id: int, role_id: int):
        """管理者ロールを追加"""
        config = self.get_server_config(guild_id)
        
        if "admin_roles" not in config:
            config["admin_roles"] = []
        
        if role_id not in config["admin_roles"]:
            config["admin_roles"].append(role_id)
            self.save_server_config(guild_id, config)
    
    def remove_admin_role(self, guild_id: int, role_id: int):
        """管理者ロールを削除"""
        config = self.get_server_config(guild_id)
        
        if "admin_roles" in config and role_id in config["admin_roles"]:
            config["admin_roles"].remove(role_id)
            self.save_server_config(guild_id, config)
