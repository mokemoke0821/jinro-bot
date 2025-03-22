"""
RoleComposerCogとエラー処理をデバッグするためのスクリプト
"""
import asyncio
import discord
from discord.ext import commands
import os
import sys
import traceback

# カレントディレクトリをモジュール検索パスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Botと関連コンポーネントのモック
class MockContext:
    def __init__(self, guild_id, author_id):
        self.guild = MockGuild(guild_id)
        self.author = MockUser(author_id)
        self.command = MockCommand("apply")
        self.sent_messages = []
    
    async def send(self, content=None, embed=None):
        message = {"content": content, "embed": embed}
        self.sent_messages.append(message)
        print(f"メッセージ送信: {content if content else '(embed)'}")
        return MockMessage(content, embed)

class MockGuild:
    def __init__(self, guild_id):
        self.id = guild_id

class MockUser:
    def __init__(self, user_id):
        self.id = user_id

class MockCommand:
    def __init__(self, name):
        self.name = name
        self.parent = MockCommandParent("compose")

class MockCommandParent:
    def __init__(self, name):
        self.name = name

class MockMessage:
    def __init__(self, content=None, embed=None):
        self.content = content
        self.embed = embed
    
    async def edit(self, content=None, embed=None):
        self.content = content if content is not None else self.content
        self.embed = embed if embed is not None else self.embed
        print(f"メッセージ編集: {content if content else '(embed)'}")
        return self

class MockBot:
    def __init__(self):
        self.cogs = {}
    
    def get_cog(self, name):
        if name == "DatabaseManager":
            from utils.database_manager import DatabaseManager
            db_manager = DatabaseManager(self)
            self.cogs["DatabaseManager"] = db_manager
            return db_manager
        return self.cogs.get(name)
    
    def add_cog(self, cog):
        self.cogs[cog.__class__.__name__] = cog

async def test_apply_preset():
    """compose apply コマンドのテスト"""
    print("\ncompose apply コマンドのテスト開始...")
    
    # モックオブジェクト作成
    bot = MockBot()
    
    # DatabaseManagerのインスタンス化
    print("DatabaseManagerを初期化中...")
    db_manager = bot.get_cog("DatabaseManager")
    
    # RoleComposerCogをインポートしてインスタンス化
    try:
        print("RoleComposerCogをインポート中...")
        from cogs.role_composer import RoleComposerCog
        role_composer = RoleComposerCog(bot)
        print("RoleComposerCogのインスタンス化成功")
    except Exception as e:
        print(f"RoleComposerCogのインポートエラー: {e}")
        traceback.print_exc()
        return False
    
    # モックコンテキスト作成
    ctx = MockContext("123456789", "987654321")
    
    # apply_presetコマンドの実行
    try:
        print("\napply_presetコマンドを実行中...")
        await role_composer.apply_preset(ctx, "standard")
        print("コマンド実行完了")
        
        # 送信されたメッセージを確認
        for i, msg in enumerate(ctx.sent_messages):
            print(f"\n送信メッセージ {i+1}:")
            if msg['content']:
                print(f"内容: {msg['content']}")
            if msg['embed']:
                print(f"Embed: {msg['embed'].title if hasattr(msg['embed'], 'title') else 'No title'}")
        
        return True
    except Exception as e:
        print(f"\nコマンド実行エラー: {e}")
        print("詳細なエラー情報:")
        traceback.print_exc()
        return False

async def main():
    """メイン処理"""
    print("RoleComposerのデバッグを開始します")
    
    # compose applyコマンドのテスト
    success = await test_apply_preset()
    
    print(f"\nデバッグ結果: {'成功' if success else '失敗'}")

if __name__ == "__main__":
    asyncio.run(main())
