"""
DatabaseManagerのテストスクリプト
"""
import asyncio
import os
import sys
import shutil
import random
import json
from discord.ext import commands

# カレントディレクトリをモジュール検索パスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# テスト用のクリーンディレクトリ
TEST_DATA_DIR = "test_data"

class DummyBot(commands.Bot):
    """テスト用のダミーBot"""
    def __init__(self):
        import discord
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", help_command=None, intents=intents)
        
    async def close(self):
        """Botを閉じる"""
        pass

async def cleanup_test_data():
    """テストデータをクリーンアップ"""
    if os.path.exists(TEST_DATA_DIR):
        shutil.rmtree(TEST_DATA_DIR)
    print("テスト用ディレクトリをクリーンアップしました")

async def setup_test_environment():
    """テスト環境のセットアップ"""
    await cleanup_test_data()
    
    # テスト用ディレクトリを作成
    os.makedirs(f"{TEST_DATA_DIR}/config", exist_ok=True)
    os.makedirs(f"{TEST_DATA_DIR}/stats", exist_ok=True)
    os.makedirs(f"{TEST_DATA_DIR}/logs", exist_ok=True)
    
    print("テスト環境をセットアップしました")
    return True

async def test_database_manager():
    """DatabaseManagerのテスト"""
    try:
        # テスト環境のセットアップ
        await setup_test_environment()
        
        # ダミーBotを作成
        bot = DummyBot()
        
        # DatabaseManagerのインポート
        from utils.database_manager import DatabaseManager
        
        # DatabaseManagerをインスタンス化
        db_manager = DatabaseManager(bot)
        
        # 元のパスを保存
        original_config_dir = db_manager.config_dir
        original_stats_dir = db_manager.stats_dir
        original_logs_dir = db_manager.logs_dir
        
        # テスト用パスへの変更
        db_manager.config_dir = f"{TEST_DATA_DIR}/config"
        db_manager.stats_dir = f"{TEST_DATA_DIR}/stats"
        db_manager.logs_dir = f"{TEST_DATA_DIR}/logs"
        
        # テスト1: サーバー設定の取得と更新
        print("\n===テスト1: サーバー設定の取得と更新===")
        guild_id = "123456789"
        
        # デフォルト設定の取得
        settings = await db_manager.get_server_settings(guild_id)
        print(f"デフォルト設定を取得: {settings.keys()}")
        
        # 特定の設定の更新
        success = await db_manager.update_server_setting(guild_id, "test_setting", "テスト値")
        print(f"設定の更新: {'成功' if success else '失敗'}")
        
        # 更新された設定の取得
        settings = await db_manager.get_server_settings(guild_id)
        print(f"更新された設定: test_setting = {settings.get('test_setting')}")
        
        # テスト2: 役職構成の設定
        print("\n===テスト2: 役職構成の設定===")
        roles_config = {
            "5": {"村人": 2, "人狼": 1, "占い師": 1, "狩人": 1},
            "6": {"村人": 2, "人狼": 1, "占い師": 1, "狩人": 1, "狂人": 1},
        }
        
        success = await db_manager.update_server_setting(guild_id, "roles_config", roles_config)
        print(f"役職構成の設定: {'成功' if success else '失敗'}")
        
        # 更新された役職構成の取得
        settings = await db_manager.get_server_settings(guild_id)
        roles = settings.get("roles_config", {})
        print(f"5人用の役職構成: {roles.get('5')}")
        
        # テスト3: プレイヤー統計の更新
        print("\n===テスト3: プレイヤー統計の更新===")
        player_id = "987654321"
        
        # 初期統計の取得
        stats = await db_manager.get_player_stats(player_id)
        print(f"初期統計: games_played = {stats.get('games_played')}")
        
        # 統計の更新
        stats_update = {
            "games_played": 1,
            "games_won": 1,
            "roles_played": {"村人": 1}
        }
        
        success = await db_manager.update_player_stats(player_id, stats_update)
        print(f"統計の更新: {'成功' if success else '失敗'}")
        
        # 更新された統計の取得
        stats = await db_manager.get_player_stats(player_id)
        print(f"更新された統計: games_played = {stats.get('games_played')}, games_won = {stats.get('games_won')}")
        
        # テスト4: ゲーム結果の記録
        print("\n===テスト4: ゲーム結果の記録===")
        game_data = {
            "timestamp": "2025-03-22 12:30:00",
            "players": ["Player1", "Player2", "Player3", "Player4", "Player5"],
            "roles": {"Player1": "村人", "Player2": "村人", "Player3": "人狼", "Player4": "占い師", "Player5": "狩人"},
            "winner": "村人陣営",
            "day_count": 3,
            "votes": [
                {"day": 1, "executed": "Player2"},
                {"day": 2, "executed": "Player3"}
            ],
            "night_actions": [
                {"night": 1, "wolf_target": "Player1", "seer_target": "Player3", "hunter_target": "Player1"},
                {"night": 2, "wolf_target": None, "seer_target": None, "hunter_target": None}
            ]
        }
        
        success = await db_manager.log_game_result(guild_id, game_data)
        print(f"ゲーム結果の記録: {'成功' if success else '失敗'}")
        
        # ゲームログの取得
        logs = await db_manager.get_game_logs(guild_id)
        print(f"ゲームログの数: {len(logs)}")
        if logs:
            print(f"最新のゲームログ: 勝者陣営 = {logs[0].get('winner')}")
        
        # テスト5: バックアップと復元
        print("\n===テスト5: バックアップと復元===")
        
        # バックアップの作成
        backup_success, backup_path = await db_manager.backup_all_data(f"{TEST_DATA_DIR}/backup")
        print(f"バックアップの作成: {'成功' if backup_success else '失敗'}")
        
        if backup_success and backup_path:
            # バックアップからの復元
            restore_success, message = await db_manager.restore_from_backup(backup_path)
            print(f"バックアップからの復元: {'成功' if restore_success else '失敗'} - {message}")
        
        # 元のパスに戻す
        db_manager.config_dir = original_config_dir
        db_manager.stats_dir = original_stats_dir
        db_manager.logs_dir = original_logs_dir
        
        print("\nテストが完了しました")
        await cleanup_test_data()
        return True
    
    except Exception as e:
        print(f"テスト中にエラーが発生しました: {e}")
        await cleanup_test_data()
        return False

if __name__ == "__main__":
    asyncio.run(test_database_manager())
