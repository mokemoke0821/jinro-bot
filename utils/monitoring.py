"""
モニタリングモジュール
ボットのリソース使用状況を監視する
"""
import os
import psutil
import datetime
import discord

class BotMonitor:
    """ボットモニタリングクラス"""
    
    def __init__(self, bot):
        """初期化"""
        self.bot = bot
        self.start_time = datetime.datetime.now()
    
    def get_uptime(self):
        """起動時間を取得"""
        delta = datetime.datetime.now() - self.start_time
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{days}日 {hours}時間 {minutes}分 {seconds}秒"
    
    def get_memory_usage(self):
        """メモリ使用量を取得"""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        return f"{memory_info.rss / 1024 / 1024:.2f} MB"
    
    def get_cpu_usage(self):
        """CPU使用率を取得"""
        return f"{psutil.cpu_percent()}%"
    
    def get_server_count(self):
        """参加サーバー数を取得"""
        return len(self.bot.guilds)
    
    def get_active_games(self):
        """アクティブなゲーム数を取得"""
        game_cog = self.bot.get_cog("GameManagementCog")
        if game_cog:
            return len(game_cog.games)
        return 0
    
    async def create_status_embed(self):
        """ステータス埋め込みを作成"""
        embed = discord.Embed(
            title="🤖 ボットステータス",
            description="現在のボットの状態",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(name="起動時間", value=self.get_uptime(), inline=True)
        embed.add_field(name="メモリ使用量", value=self.get_memory_usage(), inline=True)
        embed.add_field(name="CPU使用率", value=self.get_cpu_usage(), inline=True)
        embed.add_field(name="参加サーバー数", value=self.get_server_count(), inline=True)
        embed.add_field(name="アクティブなゲーム", value=self.get_active_games(), inline=True)
        
        return embed
