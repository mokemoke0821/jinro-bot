"""
データベースマネージャー
サーバー設定やプレイヤー統計データを管理するためのユーティリティクラス
"""
import os
import json
import asyncio
from discord.ext import commands
from typing import Dict, Any, Optional, List

class DatabaseManager(commands.Cog):
    """サーバー設定やゲームデータを管理するためのCog"""
    
    def __init__(self, bot):
        self.bot = bot
        self.settings_lock = asyncio.Lock()  # 同時書き込み防止用ロック
        self.stats_lock = asyncio.Lock()     # 統計データ用ロック
        self.game_log_lock = asyncio.Lock()  # ゲームログ用ロック
        
        # 設定ディレクトリパス
        self.config_dir = "data/config"
        self.stats_dir = "data/stats"
        self.logs_dir = "data/logs"
        
        # 必要なディレクトリが存在することを確認
        for directory in [self.config_dir, self.stats_dir, self.logs_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
    
    async def get_server_settings(self, guild_id):
        """サーバーの設定を取得"""
        guild_id = str(guild_id)  # IDを文字列に変換
        settings_path = f"{self.config_dir}/server_{guild_id}.json"
        
        # デバッグ用ログを追加
        print(f"[DATABASE] Loading settings for guild {guild_id} from {settings_path}")
        
        # デフォルト設定を事前に取得
        default_settings = self._get_default_settings()
        print(f"[DATABASE] Default settings type: {type(default_settings)}")
        
        if os.path.exists(settings_path):
            try:
                async with self.settings_lock:
                    with open(settings_path, "r", encoding="utf-8") as f:
                        result = json.load(f)
                        
                        # デバッグログを追加
                        print(f"[DATABASE] Loaded settings: {type(result)}")
                        
                        # 辞書型でない場合は例外を発生させる
                        if not isinstance(result, dict):
                            print(f"[DATABASE] ERROR: Loaded settings is not a dict: {type(result)}")
                            return default_settings
                        
                        return result
            except json.JSONDecodeError as e:
                # ファイルが破損している場合、デフォルト設定を返す
                print(f"[DATABASE] JSON decode error: {e}. Returning default settings")
                return default_settings
            except Exception as e:
                # その他のエラーが発生した場合も、デフォルト設定を返す
                print(f"[DATABASE] Error loading settings: {e}")
                import traceback
                traceback.print_exc()
                return default_settings
        else:
            # 設定ファイルが存在しない場合、デフォルト設定を返す
            print(f"[DATABASE] Settings file not found, returning default settings")
            
            # 新しいサーバーの場合は設定ファイルを作成しておく
            try:
                async with self.settings_lock:
                    with open(settings_path, "w", encoding="utf-8") as f:
                        json.dump(default_settings, f, ensure_ascii=False, indent=2)
                print(f"[DATABASE] Created new settings file for guild {guild_id}")
            except Exception as e:
                print(f"[DATABASE] Error creating settings file: {e}")
            
            return default_settings
    
    async def update_server_setting(self, guild_id, key, value):
        """サーバーの特定の設定を更新"""
        guild_id = str(guild_id)  # IDを文字列に変換
        settings_path = f"{self.config_dir}/server_{guild_id}.json"
        
        try:
            print(f"[DATABASE] Updating setting for guild {guild_id}, key: {key}")
            # 現在の設定を取得
            settings = await self.get_server_settings(guild_id)
            print(f"[DATABASE] Current settings type: {type(settings)}")
            
            # 例外ケースをチェック
            if asyncio.iscoroutine(settings):
                print("[DATABASE] Warning: settings is still a coroutine in update_server_setting, awaiting again")
                settings = await settings
                print(f"[DATABASE] After second await, settings type: {type(settings)}")
            
            # 設定が辞書型でない場合は新しい辞書を作成
            if not isinstance(settings, dict):
                print(f"[DATABASE] Settings is not a dict, creating new settings")
                settings = self._get_default_settings()
            
            # 設定を更新
            settings[key] = value
            
            # 設定を保存
            print(f"[DATABASE] Saving updated settings to {settings_path}")
            async with self.settings_lock:
                with open(settings_path, "w", encoding="utf-8") as f:
                    json.dump(settings, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"[DATABASE] 設定更新エラー: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def get_player_stats(self, player_id):
        """プレイヤーの統計情報を取得"""
        player_id = str(player_id)  # IDを文字列に変換
        stats_path = f"{self.stats_dir}/player_{player_id}.json"
        
        if os.path.exists(stats_path):
            try:
                async with self.stats_lock:
                    with open(stats_path, "r", encoding="utf-8") as f:
                        return json.load(f)
            except json.JSONDecodeError:
                # ファイルが破損している場合、初期統計を返す
                return self._get_initial_player_stats()
            except Exception as e:
                print(f"統計読み込みエラー: {e}")
                return self._get_initial_player_stats()
        else:
            # 統計ファイルが存在しない場合、初期統計を返す
            return self._get_initial_player_stats()
    
    async def update_player_stats(self, player_id, stats_data):
        """プレイヤーの統計情報を更新"""
        player_id = str(player_id)  # IDを文字列に変換
        stats_path = f"{self.stats_dir}/player_{player_id}.json"
        
        try:
            # 現在の統計を取得（存在しない場合は新規作成）
            current_stats = {}
            if os.path.exists(stats_path):
                try:
                    async with self.stats_lock:
                        with open(stats_path, "r", encoding="utf-8") as f:
                            current_stats = json.load(f)
                except:
                    current_stats = self._get_initial_player_stats()
            else:
                current_stats = self._get_initial_player_stats()
            
            # 統計を更新
            for key, value in stats_data.items():
                if key in current_stats and isinstance(current_stats[key], (int, float)) and isinstance(value, (int, float)):
                    # 数値の場合は加算
                    current_stats[key] += value
                else:
                    # その他の場合は上書き
                    current_stats[key] = value
            
            # 統計を保存
            async with self.stats_lock:
                with open(stats_path, "w", encoding="utf-8") as f:
                    json.dump(current_stats, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"統計更新エラー: {e}")
            return False
    
    async def log_game_result(self, guild_id, game_data):
        """ゲーム結果を記録"""
        guild_id = str(guild_id)  # IDを文字列に変換
        log_dir = f"{self.logs_dir}/{guild_id}"
        
        # サーバーごとのログディレクトリを作成
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # タイムスタンプをファイル名に使用
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = f"{log_dir}/game_{timestamp}.json"
        
        try:
            # ゲームデータを保存
            async with self.game_log_lock:
                with open(log_path, "w", encoding="utf-8") as f:
                    json.dump(game_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"ゲームログ保存エラー: {e}")
            return False
    
    async def get_game_logs(self, guild_id, limit=10):
        """サーバーのゲームログを取得"""
        guild_id = str(guild_id)  # IDを文字列に変換
        log_dir = f"{self.logs_dir}/{guild_id}"
        
        if not os.path.exists(log_dir):
            return []
        
        try:
            # ゲームログファイルのリストを取得
            log_files = [f for f in os.listdir(log_dir) if f.startswith("game_") and f.endswith(".json")]
            
            # 新しい順にソート
            log_files.sort(reverse=True)
            
            # 指定された数だけログを読み込む
            logs = []
            for i, log_file in enumerate(log_files):
                if i >= limit:
                    break
                
                log_path = f"{log_dir}/{log_file}"
                try:
                    with open(log_path, "r", encoding="utf-8") as f:
                        log_data = json.load(f)
                        logs.append(log_data)
                except:
                    continue
            
            return logs
        except Exception as e:
            print(f"ゲームログ取得エラー: {e}")
            return []
    
    def _get_default_settings(self):
        """デフォルトのサーバー設定を返す"""
        return {
            "roles_config": {
                "5": {"村人": 2, "人狼": 1, "占い師": 1, "狩人": 1},
                "6": {"村人": 2, "人狼": 1, "占い師": 1, "狩人": 1, "狂人": 1},
                "7": {"村人": 3, "人狼": 1, "占い師": 1, "狩人": 1, "狂人": 1},
                "8": {"村人": 3, "人狼": 2, "占い師": 1, "狩人": 1, "狂人": 1},
                "9": {"村人": 3, "人狼": 2, "占い師": 1, "狩人": 1, "霊媒師": 1, "狂人": 1},
                "10": {"村人": 3, "人狼": 2, "占い師": 1, "狩人": 1, "霊媒師": 1, "狂人": 1, "妖狐": 1},
            },
            "game_rules": {
                "no_first_night_kill": False,
                "lovers_enabled": False,
                "no_consecutive_guard": True,
                "random_tied_vote": False,
                "dead_chat_enabled": True
            },
            "timers": {
                "day": 300,    # 昼のフェーズの時間（秒）
                "night": 90,   # 夜のフェーズの時間（秒）
                "voting": 60   # 投票フェーズの時間（秒）
            }
        }
    
    def _get_initial_player_stats(self):
        """初期プレイヤー統計を返す"""
        return {
            "games_played": 0,
            "games_won": 0,
            "games_lost": 0,
            "roles_played": {},
            "times_killed": 0,
            "times_survived": 0,
            "villager_wins": 0,
            "werewolf_wins": 0,
            "third_party_wins": 0,
            "last_updated": ""
        }

    async def backup_all_data(self, backup_dir="data/backup"):
        """全データのバックアップを作成"""
        import datetime
        import shutil
        
        # バックアップディレクトリが存在することを確認
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{backup_dir}/backup_{timestamp}"
        
        try:
            # バックアップディレクトリを作成
            os.makedirs(backup_path, exist_ok=True)
            
            # 設定ディレクトリのバックアップ
            config_backup = f"{backup_path}/config"
            if os.path.exists(self.config_dir):
                shutil.copytree(self.config_dir, config_backup)
            
            # 統計ディレクトリのバックアップ
            stats_backup = f"{backup_path}/stats"
            if os.path.exists(self.stats_dir):
                shutil.copytree(self.stats_dir, stats_backup)
            
            # ログディレクトリのバックアップ
            logs_backup = f"{backup_path}/logs"
            if os.path.exists(self.logs_dir):
                shutil.copytree(self.logs_dir, logs_backup)
            
            return True, backup_path
        except Exception as e:
            print(f"バックアップエラー: {e}")
            return False, None

    async def restore_from_backup(self, backup_path):
        """バックアップからデータを復元"""
        import shutil
        
        if not os.path.exists(backup_path):
            return False, "バックアップパスが存在しません"
        
        try:
            # 設定ディレクトリの復元
            config_backup = f"{backup_path}/config"
            if os.path.exists(config_backup):
                if os.path.exists(self.config_dir):
                    shutil.rmtree(self.config_dir)
                shutil.copytree(config_backup, self.config_dir)
            
            # 統計ディレクトリの復元
            stats_backup = f"{backup_path}/stats"
            if os.path.exists(stats_backup):
                if os.path.exists(self.stats_dir):
                    shutil.rmtree(self.stats_dir)
                shutil.copytree(stats_backup, self.stats_dir)
            
            # ログディレクトリの復元
            logs_backup = f"{backup_path}/logs"
            if os.path.exists(logs_backup):
                if os.path.exists(self.logs_dir):
                    shutil.rmtree(self.logs_dir)
                shutil.copytree(logs_backup, self.logs_dir)
            
            return True, "バックアップからの復元が完了しました"
        except Exception as e:
            print(f"復元エラー: {e}")
            return False, f"復元中にエラーが発生しました: {str(e)}"

async def setup(bot):
    """Cogのセットアップ"""
    await bot.add_cog(DatabaseManager(bot))
