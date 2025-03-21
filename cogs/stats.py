import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import asyncio
import datetime

from utils.stats_manager import StatsManager
from utils.embed_creator import EmbedCreator


class Stats(commands.Cog):
    """ゲーム統計関連のコマンドを提供するCog"""
    
    def __init__(self, bot):
        self.bot = bot
        self.stats_manager = StatsManager()
        self.embed_creator = EmbedCreator()
    
    @commands.hybrid_group(name="stats", description="ゲーム統計情報を表示します")
    async def stats(self, ctx):
        if ctx.invoked_subcommand is None:
            # サーバー統計のデフォルト表示
            await self.server(ctx)
    
    @stats.command(name="server", description="サーバーのゲーム統計を表示します")
    async def server(self, ctx):
        """サーバーのゲーム統計を表示するコマンド"""
        async with ctx.typing():
            # サーバー統計のembedを生成
            embed = await self.stats_manager.generate_server_stats_embed(ctx.guild.id)
            
            # サーバー統計が存在するか確認
            server_stats = await self.stats_manager.get_server_stats(ctx.guild.id)
            
            if server_stats["total_games"] == 0:
                await ctx.send("このサーバーではまだゲームが行われていません。", ephemeral=True)
                return
            
            # 統計グラフも準備
            win_chart = await self.stats_manager.generate_win_rate_chart(ctx.guild.id)
            role_chart = await self.stats_manager.generate_role_stats_chart(ctx.guild.id)
            
            # Embedだけを先に送信
            message = await ctx.send(embed=embed)
            
            # グラフがある場合は添付ファイルとして送信
            files = []
            if win_chart:
                files.append(win_chart)
            if role_chart:
                files.append(role_chart)
            
            if files:
                # グラフファイルがある場合は、別のメッセージとして送信
                await ctx.send(files=files)
    
    @stats.command(name="player", description="プレイヤーのゲーム統計を表示します")
    async def player(self, ctx, member: Optional[discord.Member] = None):
        """プレイヤーのゲーム統計を表示するコマンド"""
        # メンバーが指定されていない場合はコマンド実行者を対象とする
        if member is None:
            member = ctx.author
        
        async with ctx.typing():
            # プレイヤー統計を取得
            player_stats = await self.stats_manager.get_player_stats(member.id)
            
            if player_stats["total_games"] == 0:
                await ctx.send(f"{member.display_name} はまだゲームに参加していません。", ephemeral=True)
                return
            
            # プレイヤー統計のembedを生成
            embed = await self.stats_manager.generate_player_stats_embed(member)
            await ctx.send(embed=embed)
    
    @stats.command(name="roles", description="役職別の統計を表示します")
    async def roles(self, ctx):
        """役職別の統計を表示するコマンド"""
        async with ctx.typing():
            # サーバー統計を取得
            server_stats = await self.stats_manager.get_server_stats(ctx.guild.id)
            
            if server_stats["total_games"] == 0:
                await ctx.send("このサーバーではまだゲームが行われていません。", ephemeral=True)
                return
            
            if not server_stats["role_stats"]:
                await ctx.send("役職の統計情報がありません。", ephemeral=True)
                return
            
            # 役職統計のembedを生成
            embed = self.embed_creator.create_info_embed(
                title="役職別統計",
                description=f"サーバー: {ctx.guild.name} の役職統計"
            )
            
            # 役職ごとの勝率を計算して表示
            role_stats_text = []
            for role, data in sorted(server_stats["role_stats"].items(), 
                                   key=lambda x: x[1]["appearances"], reverse=True):
                appearances = data["appearances"]
                wins = data["wins"]
                win_rate = (wins / appearances) * 100 if appearances > 0 else 0
                role_stats_text.append(f"{role}: {appearances}回出現, 勝利 {wins}回, 勝率 {win_rate:.1f}%")
            
            # 10個ずつに分けて表示（Embedのフィールドサイズ制限）
            for i in range(0, len(role_stats_text), 10):
                chunk = role_stats_text[i:i+10]
                embed.add_field(
                    name=f"役職データ {i//10 + 1}" if i > 0 else "役職データ",
                    value="\n".join(chunk),
                    inline=False
                )
            
            # グラフも準備
            role_chart = await self.stats_manager.generate_role_stats_chart(ctx.guild.id)
            
            # Embedと共にグラフを送信
            if role_chart:
                await ctx.send(embed=embed, file=role_chart)
            else:
                await ctx.send(embed=embed)
    
    @stats.command(name="reset", description="統計データをリセットします (管理者のみ)")
    @commands.has_permissions(administrator=True)
    async def reset_stats(self, ctx, target: str = "server"):
        """統計データをリセットするコマンド (管理者のみ)"""
        if target not in ["server", "player"]:
            await ctx.send("リセット対象は `server` または `player` を指定してください。", ephemeral=True)
            return
        
        # 確認メッセージ
        confirm_msg = await ctx.send(
            f"{'サーバー' if target == 'server' else 'プレイヤー'}の統計データをリセットしますか？この操作は元に戻せません。"
            f"続行するには ✅ を、キャンセルするには ❌ をクリックしてください。",
            ephemeral=True
        )
        
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirm_msg.id
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            
            if str(reaction.emoji) == "✅":
                if target == "server":
                    # サーバー統計のリセット
                    result = self.stats_manager.reset_server_stats(ctx.guild.id)
                    if result:
                        await ctx.send("サーバーの統計データをリセットしました。", ephemeral=True)
                    else:
                        await ctx.send("リセットする統計データがありませんでした。", ephemeral=True)
                else:
                    # プレイヤーの指定
                    await ctx.send("統計をリセットするプレイヤーのIDを入力してください（自分自身の場合は「me」と入力）：", ephemeral=True)
                    
                    def message_check(m):
                        return m.author == ctx.author and m.channel == ctx.channel
                    
                    try:
                        message = await self.bot.wait_for('message', timeout=60.0, check=message_check)
                        player_id = None
                        
                        if message.content.lower() == "me":
                            player_id = ctx.author.id
                        else:
                            try:
                                player_id = int(message.content.strip())
                            except ValueError:
                                await ctx.send("無効なプレイヤーIDです。リセットを中止します。", ephemeral=True)
                                return
                        
                        # プレイヤー統計のリセット
                        result = self.stats_manager.reset_player_stats(player_id)
                        if result:
                            await ctx.send(f"プレイヤー（ID: {player_id}）の統計データをリセットしました。", ephemeral=True)
                        else:
                            await ctx.send("リセットする統計データがありませんでした。", ephemeral=True)
                    
                    except asyncio.TimeoutError:
                        await ctx.send("プレイヤーIDの入力がタイムアウトしました。リセットを中止します。", ephemeral=True)
            else:
                await ctx.send("統計データのリセットをキャンセルしました。", ephemeral=True)
        
        except asyncio.TimeoutError:
            await ctx.send("タイムアウトしました。統計データのリセットをキャンセルします。", ephemeral=True)
    
    @stats.command(name="leaderboard", description="プレイヤーのランキングを表示します")
    async def leaderboard(self, ctx, category: str = "wins"):
        """プレイヤーのランキングを表示するコマンド"""
        valid_categories = ["wins", "games", "survival", "winrate"]
        
        if category not in valid_categories:
            categories_str = ", ".join(f"`{c}`" for c in valid_categories)
            await ctx.send(f"無効なカテゴリです。有効なカテゴリ: {categories_str}", ephemeral=True)
            return
        
        async with ctx.typing():
            # すべてのプレイヤー統計を取得
            player_stats = self.stats_manager._load_player_stats()
            
            if not player_stats:
                await ctx.send("統計データがありません。", ephemeral=True)
                return
            
            # ギルドメンバーのIDを取得
            guild_member_ids = [str(member.id) for member in ctx.guild.members]
            
            # ギルドに所属するプレイヤーのみをフィルタリング
            guild_players = {player_id: data for player_id, data in player_stats.items() 
                           if player_id in guild_member_ids and data["total_games"] > 0}
            
            if not guild_players:
                await ctx.send("このサーバーにはプレイヤー統計がありません。", ephemeral=True)
                return
            
            # カテゴリに応じてソート
            if category == "wins":
                sorted_players = sorted(guild_players.items(), key=lambda x: x[1]["wins"], reverse=True)
                category_name = "勝利数"
                value_key = "wins"
            elif category == "games":
                sorted_players = sorted(guild_players.items(), key=lambda x: x[1]["total_games"], reverse=True)
                category_name = "総ゲーム数"
                value_key = "total_games"
            elif category == "survival":
                sorted_players = sorted(guild_players.items(), key=lambda x: x[1].get("survival_rate", 0), reverse=True)
                category_name = "生存率"
                value_key = "survival_rate"
            elif category == "winrate":
                # 勝率の計算
                for player_id, data in guild_players.items():
                    total_games = data["total_games"]
                    if total_games > 0:
                        data["winrate"] = (data["wins"] / total_games) * 100
                    else:
                        data["winrate"] = 0
                
                sorted_players = sorted(guild_players.items(), key=lambda x: x[1].get("winrate", 0), reverse=True)
                category_name = "勝率"
                value_key = "winrate"
            
            # ランキングのembedを生成
            embed = self.embed_creator.create_info_embed(
                title=f"プレイヤーランキング: {category_name}",
                description=f"サーバー: {ctx.guild.name} のランキング"
            )
            
            # ランキングを表示
            rank_text = []
            for i, (player_id, data) in enumerate(sorted_players[:10]):  # 上位10人まで表示
                player_name = data["name"]
                
                if category in ["survival", "winrate"]:
                    value = f"{data.get(value_key, 0):.1f}%"
                else:
                    value = str(data.get(value_key, 0))
                
                rank_text.append(f"{i+1}. {player_name}: {value}")
            
            embed.add_field(name="ランキング", value="\n".join(rank_text) or "データなし", inline=False)
            
            # 実行者の順位も表示
            author_id = str(ctx.author.id)
            if author_id in guild_players:
                author_rank = next((i+1 for i, (player_id, _) in enumerate(sorted_players) if player_id == author_id), None)
                if author_rank:
                    author_data = guild_players[author_id]
                    
                    if category in ["survival", "winrate"]:
                        author_value = f"{author_data.get(value_key, 0):.1f}%"
                    else:
                        author_value = str(author_data.get(value_key, 0))
                    
                    embed.add_field(
                        name="あなたの順位",
                        value=f"{author_rank}位: {author_value}",
                        inline=False
                    )
            
            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Stats(bot))
