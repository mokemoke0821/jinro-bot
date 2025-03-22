"""
ボタンインターフェース用の基本Viewクラス
"""
import discord
from discord.ui import View, Button

class GameControlView(View):
    """ゲーム操作用の基本Viewクラス"""
    def __init__(self, game_manager, timeout=180):
        super().__init__(timeout=timeout)
        self.game_manager = game_manager
        
    async def on_timeout(self):
        """タイムアウト時の処理"""
        # ボタンを無効化
        for item in self.children:
            item.disabled = True
        
        # メッセージを更新（可能であれば）
        if hasattr(self, 'message') and self.message:
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass
