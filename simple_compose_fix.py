"""
重複実行問題を解決するためのシンプルな修正モジュール
"""
import asyncio
import discord
from discord.ext import commands
import functools
import traceback

# コマンド実行状態を追跡
_command_locks = {}
_command_history = {}

def setup_compose_commands(bot):
    """
    composeコマンドを登録する単純な関数
    - 既存のBotのコマンド登録メカニズムを使用
    - 追加のラッパーで重複実行を防止
    """
    print("シンプルなコマンド重複防止機能を設定...")
    
    # 直接コマンドを登録
    from direct_compose import setup_commands
    
    # 元のメソッドを呼び出し
    setup_commands(bot)
    
    # 登録されたcomposeコマンドをラップする
    if bot.get_command("compose"):
        original_callback = bot.get_command("compose").callback
        
        # 新しいコールバック関数
        @functools.wraps(original_callback)
        async def safe_compose_callback(ctx, *args, **kwargs):
            # メッセージとチャンネルID
            message_id = ctx.message.id
            channel_id = ctx.channel.id
            key = f"{channel_id}_{message_id}"
            
            # 重複実行チェック
            if key in _command_history:
                print(f"[DUPE] メッセージ {message_id} は既に処理済みです")
                return
            
            # チャンネルロックチェック
            channel_key = f"channel_{channel_id}"
            if channel_key in _command_locks:
                print(f"[LOCK] チャンネル {channel_id} はロック中です")
                return
            
            # ロックと履歴に追加
            _command_locks[channel_key] = True
            _command_history[key] = True
            
            # 古い履歴を削除（1000件以上の場合）
            if len(_command_history) > 1000:
                _command_history.clear()
                print("[CLEANUP] コマンド履歴をクリア")
            
            try:
                # 元のコールバックを実行
                return await original_callback(ctx, *args, **kwargs)
            except Exception as e:
                print(f"[ERROR] composeコマンド実行エラー: {e}")
                traceback.print_exc()
            finally:
                # ロックを解除する関数
                async def release_lock():
                    await asyncio.sleep(3)  # 3秒後にロック解除
                    if channel_key in _command_locks:
                        del _command_locks[channel_key]
                
                # 非同期タスクとして実行
                asyncio.create_task(release_lock())
        
        # コマンドのコールバックを上書き
        bot.get_command("compose").callback = safe_compose_callback
        print("composeコマンドを安全なバージョンでラップしました")
    
    return True
