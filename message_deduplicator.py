"""
メッセージの重複処理を完全に防止するための最終解決策
"""
import asyncio
import functools
import time
import logging

# ロガーの設定
logger = logging.getLogger('message_deduplicator')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('[%(levelname)s] %(name)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class MessageDeduplicator:
    """メッセージの重複処理を防止するクラス"""
    
    def __init__(self):
        # 処理済みメッセージを追跡
        self.processed_messages = set()
        # チャンネルごとのコマンドロック
        self.channel_locks = {}
        # コマンド実行時刻追跡
        self.command_timestamps = {}
        # 最後のクリーンアップ時刻
        self.last_cleanup = time.time()
    
    def is_duplicate(self, message_id):
        """メッセージが重複しているかチェック"""
        return message_id in self.processed_messages
    
    def mark_processed(self, message_id):
        """メッセージを処理済みとしてマーク"""
        self.processed_messages.add(message_id)
        
        # 定期的なクリーンアップ（10分ごと）
        current_time = time.time()
        if current_time - self.last_cleanup > 600:  # 10分
            self.cleanup()
            self.last_cleanup = current_time
    
    def is_channel_locked(self, channel_id, command_name):
        """チャンネルがロックされているかチェック"""
        lock_key = f"{channel_id}_{command_name}"
        return lock_key in self.channel_locks
    
    def lock_channel(self, channel_id, command_name, duration=2.0):
        """チャンネルをロック"""
        lock_key = f"{channel_id}_{command_name}"
        self.channel_locks[lock_key] = time.time() + duration
    
    def unlock_channel(self, channel_id, command_name):
        """チャンネルのロックを解除"""
        lock_key = f"{channel_id}_{command_name}"
        if lock_key in self.channel_locks:
            del self.channel_locks[lock_key]
    
    def cleanup(self):
        """古いロックと処理済みメッセージをクリーンアップ"""
        # 期限切れのロックを削除
        current_time = time.time()
        expired_locks = [key for key, expiry in self.channel_locks.items() if expiry < current_time]
        for key in expired_locks:
            del self.channel_locks[key]
        
        # 処理済みメッセージのサイズを制限
        if len(self.processed_messages) > 1000:
            self.processed_messages.clear()
            logger.info("処理済みメッセージをクリア")

# グローバルなDeduplicatorインスタンス
_deduplicator = MessageDeduplicator()

def get_deduplicator():
    """グローバルなDeduplicatorインスタンスを取得"""
    global _deduplicator
    return _deduplicator

def patch_bot(bot):
    """Botのイベント処理を修正してメッセージの重複を防止"""
    logger.info("Botのイベント処理を修正してメッセージの重複を防止します")
    
    # オリジナルのprocess_commands関数を保存
    original_process_commands = bot.process_commands
    
    # メッセージ処理関数を上書き
    async def deduplicated_process_commands(message):
        # Deduplicatorインスタンスを取得
        deduplicator = get_deduplicator()
        
        # メッセージIDを取得
        message_id = message.id
        
        # 重複チェック
        if deduplicator.is_duplicate(message_id):
            logger.debug(f"重複メッセージをスキップ: {message_id}")
            return
        
        # 処理済みとしてマーク
        deduplicator.mark_processed(message_id)
        
        # コマンドプレフィックスかどうか確認
        if message.content.startswith(bot.command_prefix):
            command_parts = message.content[len(bot.command_prefix):].split()
            if not command_parts:
                return
            
            command_name = command_parts[0].lower()
            channel_id = message.channel.id
            
            # チャンネルロックをチェック
            if deduplicator.is_channel_locked(channel_id, command_name):
                logger.debug(f"チャンネルロックによりコマンドをスキップ: {command_name} in {channel_id}")
                return
            
            # チャンネルをロック (特定のコマンドだけより長いロック時間を設定)
            lock_duration = 5.0 if command_name == "compose" else 2.0
            deduplicator.lock_channel(channel_id, command_name, lock_duration)
            
            try:
                # オリジナルの処理を実行
                await original_process_commands(message)
            finally:
                # 一定時間後にロックを解除
                await asyncio.sleep(0.5)  # 最小限の実行時間を保証
                deduplicator.unlock_channel(channel_id, command_name)
        else:
            # コマンド以外のメッセージはそのまま処理
            await original_process_commands(message)
    
    # 処理関数を上書き
    bot.process_commands = deduplicated_process_commands
    
    # オリジナルのinvoke関数を保存
    original_invoke = bot.invoke
    
    # invoke関数を上書き
    async def deduplicated_invoke(ctx):
        # メッセージIDを取得
        message_id = ctx.message.id
        
        # Deduplicatorインスタンスを取得
        deduplicator = get_deduplicator()
        
        # ここで二重にチェック
        if hasattr(ctx, "_processed") or hasattr(ctx.message, "_processed"):
            logger.debug(f"重複invokeをスキップ: {message_id}")
            return
        
        # 処理済みとしてマーク
        setattr(ctx, "_processed", True)
        setattr(ctx.message, "_processed", True)
        
        # オリジナルの処理を実行
        return await original_invoke(ctx)
    
    # invoke関数を上書き
    bot.invoke = deduplicated_invoke
    
    logger.info("Botのパッチ適用完了")
    return bot

def patch_command(command_name):
    """特定のコマンドに重複防止機能を追加するデコレータ"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(ctx, *args, **kwargs):
            # Deduplicatorインスタンスを取得
            deduplicator = get_deduplicator()
            
            # メッセージIDと時間に基づくユニークなキー
            message_id = ctx.message.id
            
            # 重複チェック (確実に二重にチェック)
            if hasattr(ctx, f"_processed_{command_name}") or deduplicator.is_duplicate(f"{message_id}_{command_name}"):
                logger.debug(f"重複コマンド実行をスキップ: {command_name} for message {message_id}")
                return
            
            # 処理済みとしてマーク
            setattr(ctx, f"_processed_{command_name}", True)
            deduplicator.processed_messages.add(f"{message_id}_{command_name}")
            
            # チャンネルIDを取得
            channel_id = ctx.channel.id
            
            # 同一チャンネルでの連続実行をチェック
            if deduplicator.is_channel_locked(channel_id, command_name):
                logger.debug(f"チャンネルロックによりコマンドをスキップ: {command_name} in {channel_id}")
                return
            
            # チャンネルをロック
            deduplicator.lock_channel(channel_id, command_name)
            
            try:
                # 実際の処理を実行
                return await func(ctx, *args, **kwargs)
            finally:
                # 一定時間後にロックを解除
                await asyncio.sleep(0.5)  # 最小限の実行時間を保証
                deduplicator.unlock_channel(channel_id, command_name)
        
        return wrapper
    
    return decorator
