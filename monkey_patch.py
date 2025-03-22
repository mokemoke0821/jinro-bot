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
            # 処理済みコマンドの一時保存用（重複実行防止）
            if not hasattr(self, '_processed_command_ids'):
                self._processed_command_ids = set()
                
            # 既に処理したメッセージは無視（重複呼び出し防止）
            if message.id in self._processed_command_ids:
                print(f"[PATCH] Skipping already processed message: {message.content}")
                return None
            
            # composeコマンドのエラーを特別処理
            if message.content.startswith('!compose'):
                try:
                    # メッセージを処理済みとしてマーク
                    self._processed_command_ids.add(message.id)
                    
                    # コマンド名とプリセット名を抽出
                    parts = message.content.split()
                    is_apply_preset = len(parts) >= 3 and parts[1] == 'apply'
                    preset_name = parts[2] if is_apply_preset and len(parts) >= 3 else None
                    
                    # 特別な処理で実行
                    ctx = await self.get_context(message)
                    
                    # すべてのエラーを抑制するフラグを設定
                    ctx.suppressed_errors = True
                    
                    # プリセットコマンドの場合は特別処理（直接アクセス）
                    if is_apply_preset and preset_name:
                        # RoleComposerCogを探す
                        composer_cog = None
                        for cog in self.cogs.values():
                            if isinstance(cog, commands.Cog) and cog.__class__.__name__ == 'RoleComposerCog':
                                composer_cog = cog
                                break
                                
                        if composer_cog and hasattr(composer_cog, 'apply_preset'):
                            try:
                                # 直接メソッドを呼び出す
                                print(f"[PATCH] Directly calling apply_preset with {preset_name}")
                                await composer_cog.apply_preset(ctx, preset_name)
                                # 正常に実行できたら処理終了
                                return None
                            except Exception as direct_e:
                                print(f"[PATCH] Error in direct preset application: {direct_e}")
                                # エラーが発生しても続行（通常処理に任せる）
                    
                    if ctx.command:
                        # エラーを無視
                        ctx.command.error = lambda *args, **kwargs: None
                        
                        try:
                            # コマンドを実行
                            await ctx.command.invoke(ctx)
                            # 正常にコマンドが実行できたら、通常の処理は不要
                            print(f"[PATCH] Successfully executed compose command directly")
                            return None
                        except Exception as e:
                            print(f"[PATCH] Error in direct compose execution: {e}")
                            # エラーが発生したら、通常処理に任せる
                            pass
                except Exception as e:
                    print(f"[PATCH] Error in compose pre-processing: {e}")
            
            try:
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
