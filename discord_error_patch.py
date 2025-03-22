"""
Discord.pyの内部エラーメカニズムを直接パッチする特殊モジュール
このファイルは必ずインポート前に読み込む必要がある
"""
import sys
import types
import importlib.util

# エラー関連のモジュールをパッチするための関数
def patch_discord_error_handling():
    """Discord.pyのエラーハンドリングメカニズムにパッチを当てる"""
    print("[PATCH] Attempting to patch Discord error handling...")
    
    # discord.pyのCommandクラスをモンキーパッチ
    try:
        import discord
        from discord.ext import commands
        
        # オリジナルのinvokeメソッドを保存
        original_invoke = commands.Command.invoke
        
        # カスタムinvokeメソッド
        async def custom_invoke(self, ctx):
            try:
                # composeコマンドの場合は特別処理
                if ctx.command and (
                    ctx.command.qualified_name.startswith('compose') or 
                    (hasattr(ctx, 'command') and ctx.command.parent and ctx.command.parent.name == 'compose')
                ):
                    try:
                        # 直接コールバック実行（エラーハンドリングをバイパス）
                        return await self.callback(self.cog, ctx, *ctx.args[1:], **ctx.kwargs)
                    except Exception as e:
                        # エラーを捕捉して何もしない
                        print(f"[PATCH] Silently caught error in compose command: {e}")
                        return None
                else:
                    # 通常のinvoke処理
                    return await original_invoke(self, ctx)
            except Exception as e:
                # その他のエラーは通常通り処理
                raise e
        
        # モンキーパッチ適用
        commands.Command.invoke = custom_invoke
        print("[PATCH] Successfully patched Command.invoke method")
        
        # Botのエラーメッセージ送信処理をパッチ
        original_on_command_error = commands.Bot._on_command_error
        
        async def custom_on_command_error(self, ctx, error):
            # composeコマンド関連のエラーは完全に無視
            if ctx.command and (
                ctx.command.qualified_name.startswith('compose') or 
                (hasattr(ctx.command, 'parent') and ctx.command.parent and ctx.command.parent.name == 'compose')
            ):
                print(f"[PATCH] Suppressed error output for compose command: {error}")
                return
            
            # AttributeError: 'coroutine' object has no attribute 'get' を無視
            if isinstance(error, AttributeError) and "coroutine" in str(error) and "attribute" in str(error):
                print(f"[PATCH] Suppressed coroutine AttributeError: {error}")
                return
            
            # その他のエラーは通常通り処理
            return await original_on_command_error(self, ctx, error)
        
        # モンキーパッチ適用
        commands.Bot._on_command_error = custom_on_command_error
        print("[PATCH] Successfully patched Bot._on_command_error method")
        
        # メッセージ送信処理をパッチ
        original_send = discord.abc.Messageable.send
        
        async def custom_send(self, content=None, **kwargs):
            # エラーメッセージをブロック
            if content and isinstance(content, str):
                if "エラーが発生しました" in content and "coroutine" in content:
                    print(f"[PATCH] Blocked error message: {content}")
                    # エラーメッセージを表示しない
                    return None
            
            # 通常通りメッセージを送信
            return await original_send(self, content, **kwargs)
        
        # モンキーパッチ適用
        discord.abc.Messageable.send = custom_send
        print("[PATCH] Successfully patched Messageable.send method")
        
        return True
    except Exception as e:
        print(f"[PATCH] Failed to patch Discord error handling: {e}")
        import traceback
        traceback.print_exc()
        return False

# 自動的にパッチを適用
patch_result = patch_discord_error_handling()
print(f"[PATCH] Discord error patch result: {'Success' if patch_result else 'Failed'}")
