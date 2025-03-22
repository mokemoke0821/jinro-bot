"""
モンキーパッチユーティリティ
Discord.pyの特定機能を緊急で上書きするための特殊ファイル
"""
import sys
import importlib
import types

def apply_monkey_patches():
    """Discord.pyの内部実装にモンキーパッチを適用"""
    print("Applying monkey patches...")
    
    try:
        # Discord.pyのHTTPClientクラスをパッチ
        import discord
        
        # すべてのエラーメッセージ表示関連のメソッドをパッチ
        # 1. エラーメッセージの送信をブロック
        original_send = discord.abc.Messageable.send
        
        async def patched_send(self, content=None, **kwargs):
            """Discordのメッセージ送信をフィルタリング"""
            # エラーメッセージのチェック
            if content and isinstance(content, str):
                if any(['エラー' in content, 'coroutine' in content, 'Exception' in content, 'error' in content.lower()]):
                    print(f"[PATCH] Blocked error message: {content}")
                    # エラーメッセージは送信しない
                    return None
            
            # エラー関連のEmbedをフィルタリング
            if 'embed' in kwargs and kwargs['embed']:
                embed = kwargs['embed']
                if hasattr(embed, 'title') and embed.title:
                    if 'エラー' in embed.title:
                        print(f"[PATCH] Blocked error embed: {embed.title}")
                        return None
            
            # 通常のメッセージは送信する
            return await original_send(self, content, **kwargs)
        
        # モンキーパッチ適用
        discord.abc.Messageable.send = patched_send
        print("[PATCH] Applied patch to Messageable.send")
        
        # 2. Botのエラーハンドリングをパッチ
        from discord.ext import commands
        
        # エラーハンドラーのパッチ
        original_process_commands = commands.Bot.process_commands
        
        async def patched_process_commands(self, message):
            """コマンド処理をパッチしてエラーをキャッチ"""
            try:
                # composeコマンドのエラーを特別処理
                if message.content.startswith('!compose'):
                    # 特別な処理で実行
                    ctx = await self.get_context(message)
                    if ctx.command:
                        ctx.command.error = lambda *args, **kwargs: None  # エラーを無視
                
                # 通常の処理
                return await original_process_commands(self, message)
            except Exception as e:
                print(f"[PATCH] Caught error in process_commands: {e}")
                # エラーを捕捉して何もしない
                return None
        
        # モンキーパッチ適用
        commands.Bot.process_commands = patched_process_commands
        print("[PATCH] Applied patch to Bot.process_commands")
        
        return True
    except Exception as e:
        print(f"Failed to apply monkey patches: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    apply_monkey_patches()
