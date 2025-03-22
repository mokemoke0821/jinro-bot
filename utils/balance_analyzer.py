"""
ゲームバランスを分析するユーティリティ
"""
import io
from collections import defaultdict
import datetime
from typing import Dict, List, Any, Optional, Tuple, Union

class BalanceAnalyzer:
    """役職バランスを分析するクラス"""
    
    def __init__(self, stats_manager):
        self.stats_manager = stats_manager
        
        # matplotlibとnumpyが利用可能かチェック
        self.matplotlib_available = False
        try:
            import numpy as np
            import matplotlib.pyplot as plt
            self.np = np
            self.plt = plt
            self.matplotlib_available = True
        except ImportError:
            print("matplotlib or numpy is not available. Charts will not be generated.")
        
    def analyze_role_win_rates(self, min_games: int = 10) -> Dict[str, Any]:
        """役職ごとの勝率を分析"""
        # 統計マネージャーから役職統計を取得
        role_stats = self.stats_manager.get_role_stats()
        
        results = {
            "win_rates": {},
            "play_counts": {},
            "balance_scores": {},
            "suggestions": []
        }
        
        # 役職ごとの勝率を計算
        for role, stats in role_stats.items():
            if stats["times_played"] >= min_games:
                win_rate = stats["times_won"] / stats["times_played"] if stats["times_played"] > 0 else 0
                results["win_rates"][role] = win_rate
                results["play_counts"][role] = stats["times_played"]
                
                # バランススコアを計算（50%からの乖離）
                balance_score = abs(win_rate - 0.5)
                results["balance_scores"][role] = balance_score
                
                # バランス調整の提案
                if win_rate > 0.65:
                    results["suggestions"].append(f"{role}の勝率が高すぎます（{win_rate:.1%}）。弱体化を検討してください。")
                elif win_rate < 0.35:
                    results["suggestions"].append(f"{role}の勝率が低すぎます（{win_rate:.1%}）。強化を検討してください。")
        
        return results
        
    def analyze_team_balance(self) -> Dict[str, Any]:
        """陣営バランスを分析"""
        # 統計マネージャーからゲームログを取得
        game_logs = self.stats_manager.get_game_logs()
        
        results = {
            "team_wins": defaultdict(int),
            "total_games": len(game_logs),
            "win_rates": {},
            "avg_game_duration": {},
            "suggestions": []
        }
        
        # 陣営ごとの勝利回数を集計
        for game in game_logs:
            winner = game.get("winner")
            if winner in ["village", "werewolf", "fox"]:
                results["team_wins"][winner] += 1
                
            # ゲーム時間の集計
            if game.get("duration"):
                if winner not in results["avg_game_duration"]:
                    results["avg_game_duration"][winner] = []
                    
                results["avg_game_duration"][winner].append(game["duration"])
        
        # 勝率を計算
        total_games = results["total_games"]
        for team, wins in results["team_wins"].items():
            results["win_rates"][team] = wins / total_games if total_games > 0 else 0
            
        # 平均ゲーム時間を計算
        for team, durations in list(results["avg_game_duration"].items()):
            results["avg_game_duration"][team] = sum(durations) / len(durations) if durations else 0
            
        # バランス調整の提案
        village_win_rate = results["win_rates"].get("village", 0)
        werewolf_win_rate = results["win_rates"].get("werewolf", 0)
        fox_win_rate = results["win_rates"].get("fox", 0)
        
        if village_win_rate > 0.55:
            results["suggestions"].append(f"村人陣営の勝率が高い（{village_win_rate:.1%}）。人狼陣営を強化するか、村人陣営を弱体化することを検討してください。")
        elif werewolf_win_rate > 0.45:
            results["suggestions"].append(f"人狼陣営の勝率が高い（{werewolf_win_rate:.1%}）。村人陣営を強化するか、人狼陣営を弱体化することを検討してください。")
        
        if fox_win_rate > 0.15:  # 妖狐は単独なので勝率は低めが適正
            results["suggestions"].append(f"妖狐の勝率が高い（{fox_win_rate:.1%}）。妖狐を弱体化することを検討してください。")
            
        return results
        
    def generate_win_rate_chart(self) -> Optional[io.BytesIO]:
        """役職勝率のグラフを生成"""
        if not self.matplotlib_available:
            return None
            
        # 役職勝率データを取得
        analysis = self.analyze_role_win_rates()
        win_rates = analysis["win_rates"]
        
        if not win_rates:
            return None
            
        # グラフ作成
        self.plt.figure(figsize=(10, 6))
        
        roles = list(win_rates.keys())
        rates = list(win_rates.values())
        
        # 陣営ごとの色分け
        colors = []
        for role in roles:
            if role in ["villager", "seer", "bodyguard", "medium", "mason", "cat", "prophet"]:
                colors.append("green")  # 村人陣営
            elif role in ["werewolf", "madman", "fanatic"]:
                colors.append("red")    # 人狼陣営
            elif role in ["fox", "heretic"]:
                colors.append("gold")   # 妖狐陣営
            else:
                colors.append("blue")   # その他
                
        # 横棒グラフ
        bars = self.plt.barh(roles, [r * 100 for r in rates], color=colors)
        
        # 50%ラインを追加
        self.plt.axvline(x=50, color='gray', linestyle='--', alpha=0.7)
        
        # 各バーに値を表示
        for bar in bars:
            width = bar.get_width()
            self.plt.text(width + 1, bar.get_y() + bar.get_height()/2, f'{width:.1f}%',
                    va='center')
        
        self.plt.title('役職別勝率')
        self.plt.xlabel('勝率 (%)')
        self.plt.tight_layout()
        
        # 画像をバイトストリームに保存
        buffer = io.BytesIO()
        self.plt.savefig(buffer, format='png')
        buffer.seek(0)
        self.plt.close()
        
        return buffer
        
    def generate_team_win_chart(self) -> Optional[io.BytesIO]:
        """陣営勝率のグラフを生成"""
        if not self.matplotlib_available:
            return None
            
        # 陣営勝率データを取得
        analysis = self.analyze_team_balance()
        win_rates = analysis["win_rates"]
        
        if not win_rates:
            return None
            
        # グラフ作成
        self.plt.figure(figsize=(8, 6))
        
        teams = list(win_rates.keys())
        rates = [win_rates[team] * 100 for team in teams]
        
        # 陣営ごとの色設定
        colors = []
        for team in teams:
            if team == "village":
                colors.append("green")  # 村人陣営
            elif team == "werewolf":
                colors.append("red")    # 人狼陣営
            elif team == "fox":
                colors.append("gold")   # 妖狐陣営
            else:
                colors.append("blue")   # その他
        
        # 円グラフ
        self.plt.pie(rates, labels=teams, colors=colors, autopct='%1.1f%%',
                startangle=90, shadow=True)
        self.plt.axis('equal')
        self.plt.title('陣営別勝率')
        
        # 画像をバイトストリームに保存
        buffer = io.BytesIO()
        self.plt.savefig(buffer, format='png')
        buffer.seek(0)
        self.plt.close()
        
        return buffer
        
    def suggest_role_adjustments(self) -> Dict[str, Any]:
        """役職バランス調整の提案"""
        # 役職勝率を分析
        role_analysis = self.analyze_role_win_rates()
        team_analysis = self.analyze_team_balance()
        
        # 各役職のバランススコアをもとに調整提案
        adjustments = {}
        
        for role, score in role_analysis["balance_scores"].items():
            # スコアが0.15以上なら調整が必要
            if score >= 0.15:
                win_rate = role_analysis["win_rates"][role]
                
                if win_rate > 0.65:
                    # 勝率が高すぎる場合
                    if role in ["villager", "seer", "bodyguard", "medium", "mason", "cat", "prophet"]:
                        adjustments[role] = {
                            "direction": "nerf",
                            "severity": min(int(score * 10), 3),  # 1-3の強さ
                            "suggestion": "能力の弱体化または出現確率の低下"
                        }
                    elif role in ["werewolf", "madman", "fanatic"]:
                        adjustments[role] = {
                            "direction": "nerf",
                            "severity": min(int(score * 10), 3),
                            "suggestion": "能力の弱体化または人数の削減"
                        }
                    elif role in ["fox", "heretic"]:
                        adjustments[role] = {
                            "direction": "nerf",
                            "severity": min(int(score * 10), 3),
                            "suggestion": "能力の弱体化"
                        }
                elif win_rate < 0.35:
                    # 勝率が低すぎる場合
                    if role in ["villager", "seer", "bodyguard", "medium", "mason", "cat", "prophet"]:
                        adjustments[role] = {
                            "direction": "buff",
                            "severity": min(int(score * 10), 3),
                            "suggestion": "能力の強化または出現確率の上昇"
                        }
                    elif role in ["werewolf", "madman", "fanatic"]:
                        adjustments[role] = {
                            "direction": "buff",
                            "severity": min(int(score * 10), 3),
                            "suggestion": "能力の強化または人数の増加"
                        }
                    elif role in ["fox", "heretic"]:
                        adjustments[role] = {
                            "direction": "buff",
                            "severity": min(int(score * 10), 3),
                            "suggestion": "能力の強化"
                        }
        
        # 陣営バランスの調整提案も考慮
        suggestions = role_analysis["suggestions"] + team_analysis["suggestions"]
        
        return {
            "adjustments": adjustments,
            "suggestions": suggestions
        }
    
    def generate_detailed_report(self, role_analysis: Dict[str, Any], team_analysis: Dict[str, Any], 
                               suggestions: Dict[str, Any]) -> str:
        """詳細なレポートテキストを生成"""
        report = []
        
        # ヘッダー
        report.append("===== 人狼ゲーム バランス分析詳細レポート =====")
        report.append(f"分析日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"分析対象: {team_analysis['total_games']}ゲーム\n")
        
        # 陣営勝率
        report.append("===== 陣営勝率 =====")
        for team, rate in sorted(team_analysis["win_rates"].items(), key=lambda x: x[1], reverse=True):
            wins = team_analysis["team_wins"][team]
            report.append(f"{team}: {rate:.1%} ({wins}勝)")
        report.append("")
        
        # 役職勝率
        report.append("===== 役職勝率 =====")
        for role, rate in sorted(role_analysis["win_rates"].items(), key=lambda x: x[1], reverse=True):
            plays = role_analysis["play_counts"][role]
            report.append(f"{role}: {rate:.1%} ({plays}回プレイ)")
        report.append("")
        
        # 調整提案
        report.append("===== 調整提案 =====")
        for role, adjustment in suggestions["adjustments"].items():
            direction = "強化" if adjustment["direction"] == "buff" else "弱体化"
            severity = "!" * adjustment["severity"]
            report.append(f"{role}: {direction}{severity} - {adjustment['suggestion']}")
        report.append("")
        
        if suggestions["suggestions"]:
            report.append("===== 全体的な提案 =====")
            for suggestion in suggestions["suggestions"]:
                report.append(suggestion)
            report.append("")
        
        # 詳細分析
        report.append("===== 詳細分析 =====")
        
        # バランススコア
        if role_analysis["balance_scores"]:
            report.append("役職バランススコア (0に近いほど理想的):")
            for role, score in sorted(role_analysis["balance_scores"].items(), key=lambda x: x[1], reverse=True):
                report.append(f"{role}: {score:.2f}")
        
        return "\n".join(report)
