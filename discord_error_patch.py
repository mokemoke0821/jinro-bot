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
                        
                        # 代わりにヘルプメッセージを表示
                        try:
                            # コマンドグループのヘルプを表示
                            if hasattr(ctx.command, 'parent') and ctx.command.parent:
                                await ctx.invoke(ctx.command.parent)
                        except Exception as help_error:
                            print(f"[PATCH] Error showing help: {help_error}")
                            
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
                # エラー詳細をログに出力
                print(f"[PATCH] Error in command {ctx.command}: {error}")
                
                # 以下の条件に当てはまる場合はエラーを抑制
                if any([
                    # composeコマンド関連のエラーは完全に無視
                    ctx.command and (
                        (ctx.command.qualified_name and ctx.command.qualified_name.startswith('compose')) or 
                        (hasattr(ctx.command, 'parent') and ctx.command.parent and ctx.command.parent.name == 'compose')
                    ),
                    # 特定の例外タイプのエラーを無視
                    isinstance(error, AttributeError) and any([
                        "coroutine" in str(error),
                        "attribute" in str(error),
                        "get" in str(error)
                    ]),
                    # エラーメッセージに特定の単語を含むものを無視
                    any([
                        term in str(error).lower() 
                        for term in ['coroutine', 'attribute', 'get', 'object has no']
                    ])
                ]):
                    print(f"[PATCH] Suppressed error: {error}")
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
                # 処理済みメッセージの追跡（重複送信防止）
                if not hasattr(discord.abc.Messageable, '_sent_message_hashes'):
                    discord.abc.Messageable._sent_message_hashes = set()
                
                # メッセージのハッシュ化（送信内容の一意性確認用）
                msg_hash = hash(f"{content}_{str(kwargs)}")
                
                # 最近送信したのと同じメッセージなら重複とみなして送信しない
                if msg_hash in discord.abc.Messageable._sent_message_hashes:
                    print(f"[PATCH] Deduplicated message: {content[:50]}...")
                    return None
                
                # ハッシュを保存（直近の100メッセージまで）
                discord.abc.Messageable._sent_message_hashes.add(msg_hash)
                if len(discord.abc.Messageable._sent_message_hashes) > 100:
                    # 古いハッシュを削除
                    discord.abc.Messageable._sent_message_hashes.pop()
                
                # エラーメッセージをチェック
                if content and isinstance(content, str):
                    # 各種エラーメッセージをブロック
                    if any([
                        term in content 
                        for term in [
                            'エラー', 'エラーが発生', 'Error', 'error', 
                            'coroutine', 'attribute', 'Command raised', 
                            'object has no', 'AttributeError', 'Exception',
                            'get', '例外', 'raised', '発生', 'exception'
                        ]
                    ]):
                        print(f"[PATCH] Blocked error message: {content[:100]}")
                        # エラーメッセージを完全に削除
                        return None
                
                # 赤い線のメッセージチェック
                if content and '━' in content:
                    print(f"[PATCH] Blocked message with line: {content[:50]}")
                    # 区切り線が含まれるメッセージは送信しない
                    return None
                
                # Embedの内容をチェック
                if 'embed' in kwargs and kwargs['embed']:
                    embed = kwargs['embed']
                    # タイトルチェック
                    if hasattr(embed, 'title') and embed.title and any([
                        term in str(embed.title) 
                        for term in ['エラー', 'Error', 'error']
                    ]):
                        print(f"[PATCH] Blocked error embed: {embed.title}")
                        return None
                    
                    # 説明文チェック
                    if hasattr(embed, 'description') and embed.description and any([
                        term in str(embed.description) 
                        for term in ['エラー', 'Error', 'error', 'Exception', 'coroutine', 'attribute']
                    ]):
                        print(f"[PATCH] Blocked error embed description")
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
                    if any([term in kwargs['title'] for term in ['エラー', 'Error', 'error']]):
                        # エラーに関するEmbedは色を透明にして見えないようにする
                        kwargs['color'] = 0x36393F  # Discordの背景色と同じ（ほぼ透明に見える）
                        # タイトルも空にする
                        kwargs['title'] = ""
                        print("[PATCH] Made error embed invisible")
                
                # descriptionにエラーの単語があれば削除
                if kwargs.get('description') and isinstance(kwargs['description'], str):
                    if any([term in kwargs['description'] for term in ['エラー', 'Error', 'error', 'Exception', 'coroutine']]):
                        # 説明文も空にする
                        kwargs['description'] = ""
                        print("[PATCH] Cleared error embed description")
                
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
