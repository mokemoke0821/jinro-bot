"""
ゲームバランスを管理するCog
"""
import discord
from discord.ext import commands
import io
import json
import datetime
from typing import Optional, Dict, List, Any, Union
from utils.balance_analyzer import BalanceAnalyzer

class BalanceCog(commands.Cog):
    """ゲームバランスを管理するコグ"""
    
    def __init__(self, bot):
        self.bot = bot
        self.analyzer = None
        
    @commands.Cog.listener()
    async def on_ready(self):
        """Cogの準備完了時に呼ばれる"""
        print(f"{self.__class__.__name__} Cog is ready.")
        stats_manager = self.bot.get_cog("StatsCog")
        if stats_manager:
            self.analyzer = BalanceAnalyzer(stats_manager)
        else:
            print("警告: StatsCogが見つかりません。BalanceCogは正常に機能しません。")
    
    @commands.group(name="balance", invoke_without_command=True)
    async def balance(self, ctx):
        """バランス関連コマンドグループ"""
        if not self.analyzer:
            await ctx.send("バランス分析システムが初期化されていません。StatsCogが有効になっているか確認してください。")
            return
            
        embed = discord.Embed(
            title="バランス調整システム",
            description="以下のコマンドでゲームバランスを分析・調整できます。",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="勝率分析",
            value=(
                f"`{ctx.prefix}balance roles` - 役職ごとの勝率を表示\n"
                f"`{ctx.prefix}balance teams` - 陣営ごとの勝率を表示"
            ),
            inline=False
        )
        
        embed.add_field(
            name="バランス調整",
            value=(
                f"`{ctx.prefix}balance suggest` - バランス調整の提案を表示\n"
                f"`{ctx.prefix}balance adjust <role> <buff/nerf> <値>` - 役職のパラメータを調整"
            ),
            inline=False
        )
        
        embed.add_field(
            name="レポート",
            value=f"`{ctx.prefix}balance report` - 総合的なバランスレポートを生成",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @balance.command(name="roles")
    async def show_role_win_rates(self, ctx):
        """役職ごとの勝率を表示"""
        if not self.analyzer:
            await ctx.send("バランス分析システムが初期化されていません。")
            return
            
        # 役職勝率のグラフを生成
        chart = self.analyzer.generate_win_rate_chart()
        if not chart:
            await ctx.send("十分なデータがありません。少なくとも10回以上プレイされた役職が必要です。")
            return
            
        # グラフをファイルとして送信
        file = discord.File(chart, filename="role_win_rates.png")
        
        # 役職勝率の分析結果を取得
        analysis = self.analyzer.analyze_role_win_rates()
        
        embed = discord.Embed(
            title="役職別勝率分析",
            description="各役職の勝率と提案される調整",
            color=discord.Color.blue()
        )
        
        # 勝率テーブル
        win_rates_text = ""
        for role, rate in sorted(analysis["win_rates"].items(), key=lambda x: x[1], reverse=True):
            play_count = analysis["play_counts"][role]
            win_rates_text += f"**{role}**: {rate:.1%} ({play_count}回プレイ)\n"
            
        embed.add_field(name="役職勝率", value=win_rates_text or "データがありません", inline=False)
        
        # 調整提案
        if analysis["suggestions"]:
            embed.add_field(
                name="調整提案",
                value="\n".join(analysis["suggestions"]),
                inline=False
            )
        
        embed.set_image(url="attachment://role_win_rates.png")
        await ctx.send(embed=embed, file=file)
    
    @balance.command(name="teams")
    async def show_team_win_rates(self, ctx):
        """陣営ごとの勝率を表示"""
        if not self.analyzer:
            await ctx.send("バランス分析システムが初期化されていません。")
            return
            
        # 陣営勝率のグラフを生成
        chart = self.analyzer.generate_team_win_chart()
        if not chart:
            await ctx.send("十分なデータがありません。")
            return
            
        # グラフをファイルとして送信
        file = discord.File(chart, filename="team_win_rates.png")
        
        # 陣営バランスの分析結果を取得
        analysis = self.analyzer.analyze_team_balance()
        
        embed = discord.Embed(
            title="陣営別勝率分析",
            description=f"全{analysis['total_games']}ゲームの陣営別勝率",
            color=discord.Color.blue()
        )
        
        # 勝率テーブル
        win_rates_text = ""
        for team, rate in sorted(analysis["win_rates"].items(), key=lambda x: x[1], reverse=True):
            wins = analysis["team_wins"][team]
            win_rates_text += f"**{team}**: {rate:.1%} ({wins}勝)\n"
            
        embed.add_field(name="陣営勝率", value=win_rates_text or "データがありません", inline=False)
        
        # 平均ゲーム時間
        duration_text = ""
        for team, duration in analysis["avg_game_duration"].items():
            minutes = int(duration / 60)
            seconds = int(duration % 60)
            duration_text += f"**{team}**: {minutes}分{seconds}秒\n"
            
        if duration_text:
            embed.add_field(name="平均ゲーム時間", value=duration_text, inline=False)
        
        # 調整提案
        if analysis["suggestions"]:
            embed.add_field(
                name="調整提案",
                value="\n".join(analysis["suggestions"]),
                inline=False
            )
        
        embed.set_image(url="attachment://team_win_rates.png")
        await ctx.send(embed=embed, file=file)
    
    @balance.command(name="suggest")
    async def suggest_balance_adjustments(self, ctx):
        """バランス調整の提案を表示"""
        if not self.analyzer:
            await ctx.send("バランス分析システムが初期化されていません。")
            return
            
        # バランス調整の提案を取得
        suggestions = self.analyzer.suggest_role_adjustments()
        
        if not suggestions["adjustments"]:
            await ctx.send("十分なデータがないか、現在のバランスに問題ありません。")
            return
            
        embed = discord.Embed(
            title="バランス調整提案",
            description="統計データに基づく役職バランスの調整提案",
            color=discord.Color.gold()
        )
        
        # 役職ごとの調整提案
        adjustments_text = ""
        for role, adjustment in suggestions["adjustments"].items():
            direction = "強化" if adjustment["direction"] == "buff" else "弱体化"
            severity = "!" * adjustment["severity"]
            adjustments_text += f"**{role}**: {direction}{severity} - {adjustment['suggestion']}\n"
            
        embed.add_field(name="役職調整", value=adjustments_text or "調整が必要な役職はありません。", inline=False)
        
        # 全体的な提案
        if suggestions["suggestions"]:
            embed.add_field(
                name="全体的な提案",
                value="\n".join(suggestions["suggestions"]),
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @balance.command(name="adjust")
    @commands.has_permissions(administrator=True)
    async def adjust_role_balance(self, ctx, role: str, direction: str, value: float = 0.1):
        """役職のバランスパラメータを調整"""
        if not self.analyzer:
            await ctx.send("バランス分析システムが初期化されていません。")
            return
            
        # 役職の存在チェック
        role_manager = self.bot.get_cog("RoleComposerCog")
        if not role_manager or not hasattr(role_manager, "is_valid_role"):
            await ctx.send("RoleComposerCogが見つかりません。")
            return
        
        if not role_manager.is_valid_role(role):
            await ctx.send(f"役職 `{role}` は存在しません。")
            return
            
        # 方向のチェック
        if direction not in ["buff", "nerf"]:
            await ctx.send("調整方向は `buff` または `nerf` を指定してください。")
            return
            
        # 値のチェック
        if value <= 0 or value > 1:
            await ctx.send("調整値は0より大きく1以下である必要があります。")
            return
            
        # 設定ファイルのパス
        import os
        role_params_path = "data/role_parameters.json"
        
        # パラメータファイルの読み込み
        try:
            if os.path.exists(role_params_path):
                with open(role_params_path, "r", encoding="utf-8") as f:
                    role_params = json.load(f)
            else:
                # ファイルがない場合は新規作成
                role_params = {}
                os.makedirs(os.path.dirname(role_params_path), exist_ok=True)
        except (json.JSONDecodeError, FileNotFoundError):
            role_params = {}
        
        # 役職のパラメータがなければ初期化
        if role not in role_params:
            role_params[role] = self._get_default_params(role)
        
        # 現在のパラメータをバックアップ
        original_params = role_params[role].copy()
        
        # 役職タイプに応じて調整するパラメータを選択
        updated = self._adjust_role_params(role, role_params[role], direction, value)
        
        if not updated:
            await ctx.send(f"役職 `{role}` には調整可能なパラメータがありません。")
            return
        
        # パラメータを保存
        with open(role_params_path, "w", encoding="utf-8") as f:
            json.dump(role_params, f, ensure_ascii=False, indent=2)
        
        # 調整内容を表示
        embed = discord.Embed(
            title="役職バランス調整",
            description=f"役職 `{role}` のバランスを調整しました。",
            color=discord.Color.green()
        )
        
        for key, old_value in original_params.items():
            if key in role_params[role] and old_value != role_params[role][key]:
                embed.add_field(
                    name=key,
                    value=f"{old_value:.2f} → {role_params[role][key]:.2f}",
                    inline=True
                )
        
        await ctx.send(embed=embed)
    
    def _get_default_params(self, role: str) -> Dict[str, float]:
        """役職のデフォルトパラメータを取得"""
        if role in ["villager", "mason"]:
            return {"vote_power": 1.0}
        elif role == "werewolf":
            return {"kill_success_rate": 1.0}
        elif role in ["seer", "prophet"]:
            return {"divination_accuracy": 1.0}
        elif role == "bodyguard":
            return {"guard_success_rate": 1.0}
        elif role == "fox":
            return {"death_on_divination_rate": 0.5}
        elif role == "madman":
            return {"vote_power": 1.0, "detection_immunity": 0.0}
        elif role == "medium":
            return {"divination_accuracy": 1.0}
        elif role == "fanatic":
            return {"vote_power": 1.0}
        elif role == "heretic":
            return {"detection_rate": 0.5}
        elif role == "cat":
            return {"revenge_success_rate": 1.0}
        else:
            return {}
    
    def _adjust_role_params(self, role: str, params: Dict[str, float], direction: str, value: float) -> bool:
        """役職パラメータを調整"""
        updated = False
        
        if role in ["villager", "mason", "madman", "fanatic"]:
            # 投票力を調整
            if "vote_power" in params:
                if direction == "buff":
                    params["vote_power"] = min(params["vote_power"] + value, 2.0)
                else:
                    params["vote_power"] = max(params["vote_power"] - value, 0.5)
                updated = True
                
        elif role in ["werewolf"]:
            # 襲撃成功率を調整
            if "kill_success_rate" in params:
                if direction == "buff":
                    params["kill_success_rate"] = min(params["kill_success_rate"] + value, 1.0)
                else:
                    params["kill_success_rate"] = max(params["kill_success_rate"] - value, 0.5)
                updated = True
                
        elif role in ["seer", "prophet", "medium"]:
            # 占い/霊媒成功率を調整
            if "divination_accuracy" in params:
                if direction == "buff":
                    params["divination_accuracy"] = min(params["divination_accuracy"] + value, 1.0)
                else:
                    params["divination_accuracy"] = max(params["divination_accuracy"] - value, 0.7)
                updated = True
                
        elif role in ["bodyguard"]:
            # 護衛成功率を調整
            if "guard_success_rate" in params:
                if direction == "buff":
                    params["guard_success_rate"] = min(params["guard_success_rate"] + value, 1.0)
                else:
                    params["guard_success_rate"] = max(params["guard_success_rate"] - value, 0.7)
                updated = True
                
        elif role in ["fox"]:
            # 占われた時の死亡率を調整
            if "death_on_divination_rate" in params:
                if direction == "buff":
                    params["death_on_divination_rate"] = max(params["death_on_divination_rate"] - value, 0.0)
                else:
                    params["death_on_divination_rate"] = min(params["death_on_divination_rate"] + value, 1.0)
                updated = True
                
        elif role in ["cat"]:
            # 道連れ成功率を調整
            if "revenge_success_rate" in params:
                if direction == "buff":
                    params["revenge_success_rate"] = min(params["revenge_success_rate"] + value, 1.0)
                else:
                    params["revenge_success_rate"] = max(params["revenge_success_rate"] - value, 0.5)
                updated = True
                
        elif role in ["heretic"]:
            # 背徳者の検出確率を調整
            if "detection_rate" in params:
                if direction == "buff":
                    params["detection_rate"] = max(params["detection_rate"] - value, 0.0)
                else:
                    params["detection_rate"] = min(params["detection_rate"] + value, 1.0)
                updated = True
            
        return updated
    
    @balance.command(name="report")
    async def generate_balance_report(self, ctx):
        """総合的なバランスレポートを生成"""
        if not self.analyzer:
            await ctx.send("バランス分析システムが初期化されていません。")
            return
            
        await ctx.send("バランスレポートを生成中...")
        
        # 役職勝率のグラフ
        role_chart = self.analyzer.generate_win_rate_chart()
        
        # 陣営勝率のグラフ
        team_chart = self.analyzer.generate_team_win_chart()
        
        # 役職バランスの分析
        role_analysis = self.analyzer.analyze_role_win_rates()
        
        # 陣営バランスの分析
        team_analysis = self.analyzer.analyze_team_balance()
        
        # バランス調整の提案
        suggestions = self.analyzer.suggest_role_adjustments()
        
        # レポートの生成
        embed = discord.Embed(
            title="ゲームバランス総合レポート",
            description="現在のゲームバランスの総合的な分析です。",
            color=discord.Color.blue()
        )
        
        # 基本情報
        embed.add_field(
            name="基本情報",
            value=f"分析対象: {team_analysis['total_games']}ゲーム",
            inline=False
        )
        
        # 陣営勝率
        team_win_rates = ""
        for team, rate in sorted(team_analysis["win_rates"].items(), key=lambda x: x[1], reverse=True):
            wins = team_analysis["team_wins"][team]
            team_win_rates += f"**{team}**: {rate:.1%} ({wins}勝)\n"
            
        embed.add_field(name="陣営勝率", value=team_win_rates or "データがありません", inline=False)
        
        # 最も勝率の高い/低い役職
        if role_analysis["win_rates"]:
            highest_role = max(role_analysis["win_rates"].items(), key=lambda x: x[1])
            lowest_role = min(role_analysis["win_rates"].items(), key=lambda x: x[1])
            
            embed.add_field(
                name="役職勝率の極値",
                value=(
                    f"最も勝率が高い: **{highest_role[0]}** ({highest_role[1]:.1%})\n"
                    f"最も勝率が低い: **{lowest_role[0]}** ({lowest_role[1]:.1%})"
                ),
                inline=False
            )
        
        # 調整提案のサマリー
        if suggestions["adjustments"]:
            buffs = [role for role, adj in suggestions["adjustments"].items() if adj["direction"] == "buff"]
            nerfs = [role for role, adj in suggestions["adjustments"].items() if adj["direction"] == "nerf"]
            
            adjustment_summary = ""
            if buffs:
                adjustment_summary += f"強化推奨: {', '.join(buffs)}\n"
            if nerfs:
                adjustment_summary += f"弱体化推奨: {', '.join(nerfs)}"
                
            embed.add_field(name="調整提案サマリー", value=adjustment_summary, inline=False)
        
        # バランス評価
        balance_score = 0
        if team_analysis["win_rates"]:
            balance_score = sum(abs(rate - 0.5) for rate in team_analysis["win_rates"].values()) / len(team_analysis["win_rates"])
        
        if balance_score < 0.1:
            balance_rating = "非常に良好"
        elif balance_score < 0.15:
            balance_rating = "良好"
        elif balance_score < 0.2:
            balance_rating = "やや不均衡"
        else:
            balance_rating = "不均衡"
            
        embed.add_field(name="バランス総合評価", value=f"{balance_rating} (スコア: {balance_score:.2f})", inline=False)
        
        # グラフの添付
        files = []
        if role_chart:
            role_file = discord.File(role_chart, filename="role_win_rates.png")
            files.append(role_file)
            embed.set_image(url="attachment://role_win_rates.png")
            
        await ctx.send(embed=embed, files=files)
        
        # 2つ目のグラフ（陣営勝率）を別メッセージで送信
        if team_chart:
            team_embed = discord.Embed(title="陣営別勝率", color=discord.Color.blue())
            team_file = discord.File(team_chart, filename="team_win_rates.png")
            team_embed.set_image(url="attachment://team_win_rates.png")
            await ctx.send(embed=team_embed, file=team_file)
        
        # 詳細な分析レポートをテキストファイルとして生成
        if role_analysis["win_rates"] and team_analysis["win_rates"]:
            report_text = self.analyzer.generate_detailed_report(role_analysis, team_analysis, suggestions)
            report_buffer = io.BytesIO(report_text.encode('utf-8'))
            report_file = discord.File(report_buffer, filename="balance_report.txt")
            
            await ctx.send("詳細なバランス分析レポート:", file=report_file)
        else:
            await ctx.send("十分なデータがないため、詳細なレポートを生成できません。")

async def setup(bot):
    await bot.add_cog(BalanceCog(bot))
