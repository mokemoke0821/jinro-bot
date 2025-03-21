"""
昼のアクション処理コグ
昼のフェーズでの議論と日中処理を管理
"""
import discord
from discord.ext import commands
from utils.embed_creator import create_game_status_embed
from utils.config import GameConfig, EmbedColors

class DayActionsCog(commands.Cog):
    """昼のアクション処理Cog"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def start_day_phase(self, channel, game):
        """昼のフェーズを開始"""
        if not channel:
            return
        
        # 昼のフェーズメッセージを送信
        embed = create_game_status_embed(game, "day")
        
        # 生存プレイヤー一覧
        alive_players = game.get_alive_players()
        if alive_players:
            players_mention = " ".join([f"<@{p.user_id}>" for p in alive_players])
            embed.add_field(name="生存者へのメンション", value=players_mention, inline=False)
        
        await channel.send(embed=embed)
        
        # 朝の通知メッセージ
        day_msg = f"☀️ 第{game.day_count}日の朝になりました。生存者は議論を始めてください。\n"
        day_msg += "投票フェーズまで残り時間: "
        
        # 制限時間を設定
        async def update_timer(remaining):
            if remaining % 60 == 0 and remaining > 0:
                minutes = remaining // 60
                await channel.send(f"☀️ 議論時間: 残り {minutes}分")
        
        async def timer_complete():
            if game.phase == "day":
                # 次のフェーズへ
                game.next_phase()
                
                # 投票フェーズを開始
                from cogs.voting import VotingCog
                voting_cog = self.bot.get_cog("VotingCog")
                if voting_cog:
                    await voting_cog.start_voting_phase(channel, game)
        
        # 議論時間のお知らせ
        minutes = GameConfig.DAY_PHASE_TIME // 60
        day_msg += f"{minutes}分"
        await channel.send(day_msg)
        
        # タイマー開始
        await game.start_timer(GameConfig.DAY_PHASE_TIME, update_timer, timer_complete)

async def setup(bot):
    """Cogをbotに追加"""
    await bot.add_cog(DayActionsCog(bot))
