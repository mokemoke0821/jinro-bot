"""
DatabaseManagerのデバッグ用スクリプト
"""
import asyncio
import inspect
import os
import sys

# カレントディレクトリをモジュール検索パスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# DatabaseManagerをインポート
try:
    print("DatabaseManagerをインポート中...")
    from utils.database_manager import DatabaseManager
    print("インポート成功")
except Exception as e:
    print(f"インポートエラー: {e}")
    sys.exit(1)

class MockBot:
    """テスト用のダミーBot"""
    def __init__(self):
        pass
    
    def get_cog(self, name):
        if name == "DatabaseManager":
            return DatabaseManager(self)
        return None

async def debug_coroutines():
    """メソッドの非同期性の確認"""
    print("\n非同期メソッドの確認:")
    for name, method in inspect.getmembers(DatabaseManager, inspect.isfunction):
        if name.startswith('_') and name != '__init__':
            continue
        is_coroutine = inspect.iscoroutinefunction(method)
        print(f"- {name}: {'非同期' if is_coroutine else '同期'}")

async def test_get_server_settings():
    """get_server_settings関数のテスト"""
    print("\nget_server_settings関数のテスト:")
    try:
        bot = MockBot()
        db_manager = DatabaseManager(bot)
        print("DatabaseManagerのインスタンス化成功")
        
        guild_id = "123456789"
        print(f"サーバー設定を取得中... guild_id={guild_id}")
        settings = await db_manager.get_server_settings(guild_id)
        
        print(f"設定の取得成功: {type(settings)}")
        print(f"設定内容のキー: {list(settings.keys())}")
        return True
    except Exception as e:
        print(f"エラー発生: {e}")
        import traceback
        traceback.print_exc()
        return False

async def debug_directory_structure():
    """ディレクトリ構造の確認"""
    print("\nディレクトリ構造の確認:")
    db_manager = DatabaseManager(MockBot())
    
    print(f"- config_dir: {db_manager.config_dir}")
    print(f"  存在する: {os.path.exists(db_manager.config_dir)}")
    
    print(f"- stats_dir: {db_manager.stats_dir}")
    print(f"  存在する: {os.path.exists(db_manager.stats_dir)}")
    
    print(f"- logs_dir: {db_manager.logs_dir}")
    print(f"  存在する: {os.path.exists(db_manager.logs_dir)}")

async def main():
    """メイン処理"""
    print("DatabaseManagerのデバッグを開始します")
    
    # 非同期メソッドの確認
    await debug_coroutines()
    
    # ディレクトリ構造の確認
    await debug_directory_structure()
    
    # get_server_settings関数のテスト
    success = await test_get_server_settings()
    
    print(f"\nデバッグ結果: {'成功' if success else '失敗'}")

if __name__ == "__main__":
    asyncio.run(main())
