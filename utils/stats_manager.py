import os
import json
import datetime
from typing import Dict, Any, List, Optional, Tuple
import discord
from collections import defaultdict, Counter

class StatsManager:
    """
    ゲーム統計の記録と管理を行うクラス
    """
    def __init__(self):
        self.stats_directory = "data/stats"
        self.player_stats_file = f"{self.stats_directory}/player_stats.json"
        self.server_stats_file = f"{self.stats_directory}/server_stats.json"
        self.ensure_stats_directory()
        self.ensure_stats_files()
        
        # matplotlibが利用可能かチェック
        self.matplotlib_available = False
        try:
            import matplotlib.pyplot as plt
            import io
            self.plt = plt
            self.io = io
            self.matplotlib_available = True
        except ImportError:
            print("matplotlib is not available. Charts will not be generated.")
    
    def ensure_stats_directory(self):
        """統計ディレクトリが存在することを確認"""
        if not os.path.exists(self.stats_directory):
            os.makedirs(self.stats_directory)
    
    def ensure_stats_files(self):
        """統計ファイルが存在することを確認"""
        # プレイヤー統計ファイル
        if not os.path.exists(self.player_stats_file):
            with open(self.player_stats_file, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
        
        # サーバー統計ファイル
        if not os.path.exists(self.server_stats_file):
            with open(self.server_stats_file, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
    
    def _load_player_stats(self) -> Dict[str, Any]:
        """プレイヤー統計ファイルを読み込む"""
        try:
            with open(self.player_stats_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _save_player_stats(self, stats: Dict[str, Any]):
        """プレイヤー統計ファイルを保存する"""
        with open(self.player_stats_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    
    def _load_server_stats(self) -> Dict[str, Any]:
        """サーバー統計ファイルを読み込む"""
        try:
            with open(self.server_stats_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _save_server_stats(self, stats: Dict[str, Any]):
        """サーバー統計ファイルを保存する"""
        with open(self.server_stats_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    
    def record_game_result(self, game_data: Dict[str, Any]):
        """
        ゲーム結果を統計に記録する
        
        Parameters:
        -----------
        game_data: Dict[str, Any]
            ゲームデータを含む辞書
            {
                "id": str - ゲームID,
                "guild_id": int - サーバーID,
                "guild_name": str - サーバー名,
                "start_time": str - ゲーム開始時間,
                "end_time": str - ゲーム終了時間,
                "duration": int - ゲーム時間（秒）,
                "winner": str - 勝者チーム（"werewolf" or "village"）,
                "players": list - プレイヤー情報のリスト
                    [
                        {
                            "id": int - プレイヤーID,
                            "name": str - プレイヤー名,
                            "role": str - 役職名,
                            "team": str - チーム（"werewolf" or "village"）,
                            "is_alive": bool - 生存状態,
                            "death_reason": str or None - 死亡理由,
                            "death_day": int or None - 死亡日
                        }
                    ]
            }
        """
        # サーバー統計の更新
        self._update_server_stats(game_data)
        
        # プレイヤー統計の更新
        self._update_player_stats(game_data)
    
    def _update_server_stats(self, game_data: Dict[str, Any]):
        """サーバー統計を更新する"""
        server_stats = self._load_server_stats()
        
        guild_id = str(game_data["guild_id"])  # JSONのキーは文字列である必要がある
        game_id = game_data["id"]
        winner = game_data["winner"]
        
        # サーバーの統計がなければ初期化
        if guild_id not in server_stats:
            server_stats[guild_id] = {
                "name": game_data["guild_name"],
                "total_games": 0,
                "village_wins": 0,
                "werewolf_wins": 0,
                "game_history": [],
                "role_stats": {},
                "average_duration": 0,
                "last_updated": datetime.datetime.now().isoformat()
            }
        
        # 統計を更新
        server_stats[guild_id]["total_games"] += 1
        
        if winner == "village":
            server_stats[guild_id]["village_wins"] += 1
        elif winner == "werewolf":
            server_stats[guild_id]["werewolf_wins"] += 1
        
        # 役職統計
        role_counts = {}
        for player in game_data["players"]:
            role = player["role"]
            if role not in role_counts:
                role_counts[role] = 0
            role_counts[role] += 1
        
        # 役職ごとの勝率を更新
        for role, count in role_counts.items():
            if role not in server_stats[guild_id]["role_stats"]:
                server_stats[guild_id]["role_stats"][role] = {
                    "appearances": 0,
                    "wins": 0
                }
            
            server_stats[guild_id]["role_stats"][role]["appearances"] += count
            
            # 勝利した役職の勝利数を更新
            for player in game_data["players"]:
                if player["role"] == role and player["team"] == winner:
                    server_stats[guild_id]["role_stats"][role]["wins"] += 1
        
        # ゲーム履歴を追加
        game_summary = {
            "id": game_id,
            "date": game_data["end_time"],
            "duration": game_data["duration"],
            "player_count": len(game_data["players"]),
            "winner": winner
        }
        
        server_stats[guild_id]["game_history"].append(game_summary)
        
        # 最近の10ゲームのみ履歴を保持
        if len(server_stats[guild_id]["game_history"]) > 10:
            server_stats[guild_id]["game_history"] = server_stats[guild_id]["game_history"][-10:]
        
        # 平均ゲーム時間を更新
        total_duration = sum(game["duration"] for game in server_stats[guild_id]["game_history"])
        server_stats[guild_id]["average_duration"] = total_duration / len(server_stats[guild_id]["game_history"])
        
        # 最終更新日時
        server_stats[guild_id]["last_updated"] = datetime.datetime.now().isoformat()
        
        # 保存
        self._save_server_stats(server_stats)
    
    def _update_player_stats(self, game_data: Dict[str, Any]):
        """プレイヤー統計を更新する"""
        player_stats = self._load_player_stats()
        winner = game_data["winner"]
        
        for player_data in game_data["players"]:
            player_id = str(player_data["id"])  # JSONのキーは文字列である必要がある
            player_name = player_data["name"]
            player_role = player_data["role"]
            player_team = player_data["team"]
            
            # プレイヤーの統計がなければ初期化
            if player_id not in player_stats:
                player_stats[player_id] = {
                    "name": player_name,
                    "total_games": 0,
                    "wins": 0,
                    "losses": 0,
                    "role_count": {},
                    "survival_rate": 0,
                    "voting_accuracy": 0,
                    "votes_received": 0,
                    "last_updated": datetime.datetime.now().isoformat()
                }
            else:
                # 名前が変わっている可能性があるため更新
                player_stats[player_id]["name"] = player_name
            
            # 統計を更新
            player_stats[player_id]["total_games"] += 1
            
            # 勝敗を記録
            if player_team == winner:
                player_stats[player_id]["wins"] += 1
            else:
                player_stats[player_id]["losses"] += 1
            
            # 役職カウントを更新
            if player_role not in player_stats[player_id]["role_count"]:
                player_stats[player_id]["role_count"][player_role] = 0
            player_stats[player_id]["role_count"][player_role] += 1
            
            # 生存率を更新
            survival_count = 0
            total_games = player_stats[player_id]["total_games"]
            
            if player_data["is_alive"]:
                survival_count = player_stats[player_id].get("survival_count", 0) + 1
            else:
                survival_count = player_stats[player_id].get("survival_count", 0)
            
            player_stats[player_id]["survival_count"] = survival_count
            player_stats[player_id]["survival_rate"] = (survival_count / total_games) * 100
            
            # 最終更新日時
            player_stats[player_id]["last_updated"] = datetime.datetime.now().isoformat()
        
        # 保存
        self._save_player_stats(player_stats)
    
    async def get_server_stats(self, guild_id: int) -> Dict[str, Any]:
        """サーバーの統計情報を取得する"""
        server_stats = self._load_server_stats()
        guild_id_str = str(guild_id)
        
        if guild_id_str not in server_stats:
            return {
                "name": "不明",
                "total_games": 0,
                "village_wins": 0,
                "werewolf_wins": 0,
                "game_history": [],
                "role_stats": {},
                "average_duration": 0,
                "last_updated": None
            }
        
        return server_stats[guild_id_str]
    
    async def get_player_stats(self, player_id: int) -> Dict[str, Any]:
        """プレイヤーの統計情報を取得する"""
        player_stats = self._load_player_stats()
        player_id_str = str(player_id)
        
        if player_id_str not in player_stats:
            return {
                "name": "不明",
                "total_games": 0,
                "wins": 0,
                "losses": 0,
                "role_count": {},
                "survival_rate": 0,
                "voting_accuracy": 0,
                "votes_received": 0,
                "last_updated": None
            }
        
        return player_stats[player_id_str]
    
    async def generate_server_stats_embed(self, guild_id: int) -> discord.Embed:
        """サーバーの統計情報を含むembedを生成する"""
        from utils.embed_creator import EmbedCreator
        
        stats = await self.get_server_stats(guild_id)
        embed_creator = EmbedCreator()
        
        embed = embed_creator.create_info_embed(
            title=f"サーバー統計: {stats['name']}",
            description=f"総ゲーム数: {stats['total_games']}"
        )
        
        # ゲーム結果の統計
        total_games = stats["total_games"]
        if total_games > 0:
            village_win_rate = (stats["village_wins"] / total_games) * 100
            werewolf_win_rate = (stats["werewolf_wins"] / total_games) * 100
            
            game_stats = [
                f"村人陣営の勝利: {stats['village_wins']} ({village_win_rate:.1f}%)",
                f"人狼陣営の勝利: {stats['werewolf_wins']} ({werewolf_win_rate:.1f}%)"
            ]
            
            embed.add_field(name="ゲーム結果", value="\n".join(game_stats), inline=False)
        
        # 役職統計
        if stats["role_stats"]:
            role_stats_text = []
            for role, role_data in sorted(stats["role_stats"].items()):
                appearances = role_data["appearances"]
                wins = role_data["wins"]
                win_rate = (wins / appearances) * 100 if appearances > 0 else 0
                role_stats_text.append(f"{role}: {appearances}回出現, 勝率 {win_rate:.1f}%")
            
            embed.add_field(name="役職統計", value="\n".join(role_stats_text[:10]) + 
                          ("\n..." if len(role_stats_text) > 10 else ""),
                          inline=False)
        
        # 平均ゲーム時間
        if stats["average_duration"] > 0:
            minutes, seconds = divmod(int(stats["average_duration"]), 60)
            hours, minutes = divmod(minutes, 60)
            
            duration_str = ""
            if hours > 0:
                duration_str += f"{hours}時間"
            if minutes > 0:
                duration_str += f"{minutes}分"
            duration_str += f"{seconds}秒"
            
            embed.add_field(name="平均ゲーム時間", value=duration_str, inline=True)
        
        # 最近のゲーム
        if stats["game_history"]:
            recent_games = []
            for i, game in enumerate(reversed(stats["game_history"][:5])):
                date = datetime.datetime.fromisoformat(game["date"]).strftime("%Y/%m/%d %H:%M")
                winner = "村人陣営" if game["winner"] == "village" else "人狼陣営"
                recent_games.append(f"{i+1}. {date} - {game['player_count']}人参加 - 勝者: {winner}")
            
            embed.add_field(name="最近のゲーム", value="\n".join(recent_games), inline=False)
        
        # 最終更新日時
        if stats["last_updated"]:
            last_updated = datetime.datetime.fromisoformat(stats["last_updated"]).strftime("%Y/%m/%d %H:%M:%S")
            embed.set_footer(text=f"最終更新: {last_updated}")
        
        return embed
    
    async def generate_player_stats_embed(self, member: discord.Member) -> discord.Embed:
        """プレイヤーの統計情報を含むembedを生成する"""
        from utils.embed_creator import EmbedCreator
        
        stats = await self.get_player_stats(member.id)
        embed_creator = EmbedCreator()
        
        embed = embed_creator.create_info_embed(
            title=f"プレイヤー統計: {member.display_name}",
            description=f"総ゲーム数: {stats['total_games']}"
        )
        
        # アイコンを設定
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # 勝敗統計
        total_games = stats["total_games"]
        if total_games > 0:
            win_rate = (stats["wins"] / total_games) * 100
            
            game_stats = [
                f"勝利: {stats['wins']} ({win_rate:.1f}%)",
                f"敗北: {stats['losses']} ({100 - win_rate:.1f}%)",
                f"生存率: {stats['survival_rate']:.1f}%"
            ]
            
            embed.add_field(name="戦績", value="\n".join(game_stats), inline=False)
        
        # 役職統計
        if stats["role_count"]:
            role_stats_text = []
            for role, count in sorted(stats["role_count"].items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_games) * 100 if total_games > 0 else 0
                role_stats_text.append(f"{role}: {count}回 ({percentage:.1f}%)")
            
            embed.add_field(name="役職別プレイ回数", value="\n".join(role_stats_text), inline=False)
        
        # 最終更新日時
        if stats["last_updated"]:
            last_updated = datetime.datetime.fromisoformat(stats["last_updated"]).strftime("%Y/%m/%d %H:%M:%S")
            embed.set_footer(text=f"最終更新: {last_updated}")
        
        return embed
    
    async def generate_role_stats_chart(self, guild_id: int) -> Optional[discord.File]:
        """役職ごとの勝率を示す棒グラフを生成する"""
        if not self.matplotlib_available:
            return None
            
        stats = await self.get_server_stats(guild_id)
        
        if not stats["role_stats"]:
            return None
        
        # matplotlib の設定
        self.plt.figure(figsize=(10, 6))
        self.plt.style.use('dark_background')
        
        roles = []
        win_rates = []
        appearances = []
        
        # データを準備
        for role, data in stats["role_stats"].items():
            if data["appearances"] >= 5:  # 5回以上出現した役職のみを表示
                roles.append(role)
                win_rate = (data["wins"] / data["appearances"]) * 100
                win_rates.append(win_rate)
                appearances.append(data["appearances"])
        
        if not roles:
            return None
        
        # グラフを描画
        bar_colors = ['green' if rate >= 50 else 'red' for rate in win_rates]
        bars = self.plt.bar(roles, win_rates, color=bar_colors)
        
        # グラフの装飾
        self.plt.title('役職別勝率', fontsize=16)
        self.plt.xlabel('役職', fontsize=12)
        self.plt.ylabel('勝率 (%)', fontsize=12)
        self.plt.ylim(0, 100)
        self.plt.grid(axis='y', alpha=0.3)
        
        # 出現回数を各バーの上に表示
        for bar, appearance in zip(bars, appearances):
            height = bar.get_height()
            self.plt.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{appearance}回',
                    ha='center', va='bottom', rotation=0, fontsize=8)
        
        # 勝率の値を各バーの中に表示
        for bar, rate in zip(bars, win_rates):
            height = bar.get_height()
            self.plt.text(bar.get_x() + bar.get_width()/2., height / 2,
                    f'{rate:.1f}%',
                    ha='center', va='center', color='white', fontweight='bold')
        
        # x軸のラベルが重ならないように調整
        self.plt.xticks(rotation=45, ha='right')
        self.plt.tight_layout()
        
        # ファイルとして保存
        buf = self.io.BytesIO()
        self.plt.savefig(buf, format='png')
        buf.seek(0)
        self.plt.close()
        
        return discord.File(buf, filename='role_stats.png')
    
    async def generate_win_rate_chart(self, guild_id: int) -> Optional[discord.File]:
        """村人陣営vs人狼陣営の勝率を示す円グラフを生成する"""
        if not self.matplotlib_available:
            return None
            
        stats = await self.get_server_stats(guild_id)
        
        if stats["total_games"] < 5:  # 5ゲーム以上ある場合のみグラフを生成
            return None
        
        # matplotlib の設定
        self.plt.figure(figsize=(8, 8))
        self.plt.style.use('dark_background')
        
        # データを準備
        labels = ['村人陣営', '人狼陣営']
        sizes = [stats["village_wins"], stats["werewolf_wins"]]
        colors = ['lightblue', 'red']
        explode = (0.1, 0)  # 村人陣営を少し強調
        
        # グラフを描画
        self.plt.pie(sizes, explode=explode, labels=labels, colors=colors,
               autopct='%1.1f%%', shadow=True, startangle=90)
        
        # グラフの装飾
        self.plt.title('陣営別勝率', fontsize=16)
        self.plt.axis('equal')  # 円が歪まないようにする
        
        # ファイルとして保存
        buf = self.io.BytesIO()
        self.plt.savefig(buf, format='png')
        buf.seek(0)
        self.plt.close()
        
        return discord.File(buf, filename='win_rate.png')
    
    def reset_player_stats(self, player_id: int) -> bool:
        """プレイヤーの統計をリセットする"""
        player_stats = self._load_player_stats()
        player_id_str = str(player_id)
        
        if player_id_str in player_stats:
            del player_stats[player_id_str]
            self._save_player_stats(player_stats)
            return True
        
        return False
    
    def reset_server_stats(self, guild_id: int) -> bool:
        """サーバーの統計をリセットする"""
        server_stats = self._load_server_stats()
        guild_id_str = str(guild_id)
        
        if guild_id_str in server_stats:
            del server_stats[guild_id_str]
            self._save_server_stats(server_stats)
            return True
        
        return False
