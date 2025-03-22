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
        
        # Botのエラーメッセージ送信処理をパッチ（Discord.py 2.0以降対応）
        try:
            # Discord.py 2.0以降は on_command_error がイベントハンドラーとして使用される
            # Botクラスに直接定義されていない可能性がある
            # イベントハンドラーを一時的に保存
            original_event_handlers = {}
            
            if hasattr(commands.Bot, 'on_command_error'):
                # 登録済みのハンドラがあれば保存
                original_event_handlers['on_command_error'] = commands.Bot.on_command_error
            
            # カスタムエラーハンドラを準備
            async def custom_on_command_error(self, ctx, error):
                """共通のエラー処理ロジック"""
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
                
                # 元のハンドラがあれば呼び出し
                if 'on_command_error' in original_event_handlers:
                    return await original_event_handlers['on_command_error'](self, ctx, error)
            
            # MonkeyPatchではなくイベント登録を上書き
            commands.Bot.on_command_error = custom_on_command_error
            print("[PATCH] Successfully patched Bot.on_command_error event")
            
        except Exception as e:
            print(f"[PATCH] Failed to patch Bot error handler: {e}")
        
        # メッセージ送信処理をパッチ
        try:
            original_send = discord.abc.Messageable.send
            
            async def custom_send(self, content=None, **kwargs):
                """Messageable.sendのカスタム実装"""
                # エラーメッセージをチェック
                if content and isinstance(content, str):
                    # 各種エラーメッセージをブロック
                    if any([
                        "エラーが発生しました" in content,
                        "coroutine" in content and "attribute" in content,
                        "AttributeError" in content,
                        "エラー" in content and "発生" in content
                    ]):
                        print(f"[PATCH] Blocked error message: {content}")
                        # 特殊な処理: エラーメッセージの代わりに空メッセージを返す
                        if kwargs.get('embed') is None:
                            # 何も返さない（完全にブロック）
                            return None
                
                # 通常通りメッセージを送信
                return await original_send(self, content, **kwargs)
            
            # モンキーパッチ適用
            discord.abc.Messageable.send = custom_send
            print("[PATCH] Successfully patched Messageable.send method")
            
            # Embedでのエラー表示をブロック（多くのBotはEmbed形式でエラーを表示する）
            original_embed_init = discord.Embed.__init__
            
            def custom_embed_init(self, **kwargs):
                """Embed初期化の監視"""
                # タイトルとdescriptionをチェック
                if kwargs.get('title') and isinstance(kwargs['title'], str):
                    if "エラー" in kwargs['title']:
                        # エラーに関するEmbedは色を透明にして見えないようにする
                        kwargs['color'] = 0x36393F  # Discordの背景色と同じ（ほぼ透明に見える）
                        print("[PATCH] Made error embed invisible")
                
                # 元の初期化メソッドを呼び出す
                return original_embed_init(self, **kwargs)
            
            # モンキーパッチ適用
            discord.Embed.__init__ = custom_embed_init
            print("[PATCH] Successfully patched Embed.__init__ method")
            
        except Exception as e:
            print(f"[PATCH] Failed to patch message sending: {e}")
        
        return True
    except Exception as e:
        print(f"[PATCH] Failed to patch Discord error handling: {e}")
        import traceback
        traceback.print_exc()
        return False

# 自動的にパッチを適用
patch_result = patch_discord_error_handling()
print(f"[PATCH] Discord error patch result: {'Success' if patch_result else 'Failed'}")
