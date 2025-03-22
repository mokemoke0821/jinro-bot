"""
DatabaseManagerの簡易テストスクリプト
"""
import asyncio
import discord
from discord.ext import commands

# Botのモック作成
class MockBot:
    def get_cog(self, name):
        if name == "DatabaseManager":
            from utils.database_manager import DatabaseManager
            return DatabaseManager(self)
        return None

async def main():
    bot = MockBot()
    db_manager = bot.get_cog("DatabaseManager")
    if not db_manager:
        print("DatabaseManagerが見つかりません")
        return
    
    guild_id = "123456789"
    
    # 設定の取得
    print("サーバー設定を取得中...")
    settings = await db_manager.get_server_settings(guild_id)
    print(f"取得成功: {type(settings)}")
    print(f"設定の内容: {list(settings.keys())}")
    
    # 設定の更新
    print("\n設定を更新中...")
    success = await db_manager.update_server_setting(guild_id, "test_key", "test_value")
    print(f"更新成功: {success}")
    
    # 更新された設定の確認
    settings = await db_manager.get_server_settings(guild_id)
    print(f"更新後設定: test_key = {settings.get('test_key')}")
    
    print("\nテスト完了")

if __name__ == "__main__":
    asyncio.run(main())
