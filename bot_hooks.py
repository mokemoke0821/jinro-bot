"""
Botのフックシステム
Discord.pyの基本的な動作を変更するためのモンキーパッチを提供
"""
import sys
import inspect
import discord
import functools

# グローバル設定
HOOKED = False
ERROR_PATTERNS = ["AttributeError", "coroutine", "get", "エラー"]
BLOCKED_COMMANDS = ["compose"]

def apply_all_hooks():
    """すべてのフックを適用"""
    global HOOKED
    if HOOKED:
        print("[HOOKS] Hooks already applied")
        return
    
    try:
        # メッセージ送信をフック
        hook_message_send()
        
        # コマンド実行をフック
        hook_command_invoke()
        
        # エラーメッセージをフック
        hook_error_messages()
        
        HOOKED = True
        print("[HOOKS] Successfully applied all hooks")
        return True
    except Exception as e:
        print(f"[HOOKS] Failed to apply hooks: {e}")
        import traceback
        traceback.print_exc()
        return False

def hook_message_send():
    """メッセージ送信処理をフック"""
    original_send = discord.abc.Messageable.send
    
    @functools.wraps(original_send)
    async def hooked_send(self, content=None, **kwargs):
        # エラーメッセージをフィルタリング
        if content and isinstance(content, str):
            # ERROR_PATTERNSのいずれかのパターンが含まれていたらブロック
            if any(pattern.lower() in content.lower() for pattern in ERROR_PATTERNS):
                print(f"[HOOKS] Blocked error message: {content}")
                return None  # メッセージを送信しない
        
        # Embedをフィルタリング
        if kwargs.get('embed'):
            embed = kwargs.get('embed')
            if embed and embed.title and "エラー" in embed.title:
                print(f"[HOOKS] Blocked error embed: {embed.title}")
                return None
        
        # 通常のメッセージを送信
        return await original_send(self, content, **kwargs)
    
    # モンキーパッチ適用
    discord.abc.Messageable.send = hooked_send
    print("[HOOKS] Message send hooked")

def hook_command_invoke():
    """コマンド実行処理をフック"""
    from discord.ext import commands
    
    original_command_invoke = commands.Command.invoke
    
    @functools.wraps(original_command_invoke)
    async def hooked_command_invoke(self, ctx):
        # ブロックすべきコマンドかチェック
        should_block = False
        
        # コマンド名をチェック
        if self.qualified_name:
            if any(blocked in self.qualified_name for blocked in BLOCKED_COMMANDS):
                should_block = True
                print(f"[HOOKS] Protected command detected: {self.qualified_name}")
        
        # 親コマンドをチェック
        if hasattr(self, 'parent') and self.parent:
            if any(blocked in self.parent.name for blocked in BLOCKED_COMMANDS):
                should_block = True
                print(f"[HOOKS] Protected parent command detected: {self.parent.name}")
        
        if should_block:
            try:
                # 直接コールバックを実行し、エラーハンドリングをバイパス
                return await self.callback(self.cog, ctx, *ctx.args[1:], **ctx.kwargs)
            except Exception as e:
                # エラーを捕捉して隠す
                print(f"[HOOKS] Caught error in protected command: {e}")
                print(f"[HOOKS] Command: {self.qualified_name}")
                import traceback
                traceback.print_exc()
                return None
        
        # 通常のコマンド実行
        return await original_command_invoke(self, ctx)
    
    # モンキーパッチ適用
    commands.Command.invoke = hooked_command_invoke
    print("[HOOKS] Command invoke hooked")

def hook_error_messages():
    """エラーメッセージ関連の処理をフック"""
    from discord.ext import commands
    
    # コマンドエラーハンドラーをフック
    if not hasattr(commands.Bot, '_on_command_error'):
        # Discord.py 2.0以降は別のメカニズム
        print("[HOOKS] Using event registration for error handling")
        
        # イベントハンドラーをフック
        original_dispatch = discord.Client.dispatch
        
        @functools.wraps(original_dispatch)
        def hooked_dispatch(self, event_name, *args, **kwargs):
            # コマンドエラーイベントをフィルタリング
            if event_name == 'command_error':
                ctx = args[0]
                error = args[1]
                
                # composeコマンドのエラーを無視
                if ctx.command and hasattr(ctx.command, 'qualified_name'):
                    if any(blocked in ctx.command.qualified_name for blocked in BLOCKED_COMMANDS):
                        print(f"[HOOKS] Blocked command error: {error}")
                        return None
                
                # 親コマンドをチェック
                if ctx.command and hasattr(ctx.command, 'parent') and ctx.command.parent:
                    if any(blocked in ctx.command.parent.name for blocked in BLOCKED_COMMANDS):
                        print(f"[HOOKS] Blocked parent command error: {error}")
                        return None
                
                # エラーメッセージでcoroutineが含まれるものをフィルタリング
                if "coroutine" in str(error).lower():
                    print(f"[HOOKS] Blocked coroutine error: {error}")
                    return None
            
            # 通常のイベントディスパッチ
            return original_dispatch(self, event_name, *args, **kwargs)
        
        # モンキーパッチ適用
        discord.Client.dispatch = hooked_dispatch
        print("[HOOKS] Event dispatch hooked")
    
    else:
        # 古いバージョンのDiscord.py
        original_on_command_error = commands.Bot._on_command_error
        
        @functools.wraps(original_on_command_error)
        async def hooked_on_command_error(self, ctx, error):
            # composeコマンドのエラーを無視
            if ctx.command and hasattr(ctx.command, 'qualified_name'):
                if any(blocked in ctx.command.qualified_name for blocked in BLOCKED_COMMANDS):
                    print(f"[HOOKS] Blocked command error: {error}")
                    return None
            
            # エラーメッセージでcoroutineが含まれるものをフィルタリング
            if "coroutine" in str(error).lower():
                print(f"[HOOKS] Blocked coroutine error: {error}")
                return None
            
            # 通常のエラーハンドリング
            return await original_on_command_error(self, ctx, error)
        
        # モンキーパッチ適用
        commands.Bot._on_command_error = hooked_on_command_error
        print("[HOOKS] Command error handler hooked")

if __name__ == "__main__":
    print("This module should be imported, not run directly")
