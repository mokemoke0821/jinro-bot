"""
役職のバランスをチェックするユーティリティ
役職構成が適切かどうかを判定する機能を提供
"""
from discord.ext import commands

class RoleBalancer(commands.Cog):
    """役職のバランスをチェックするクラス"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # 役職の強さの重み
        self.role_weights = {
            "村人": 1.0,
            "人狼": -3.0,
            "占い師": 3.0,
            "狩人": 2.0,
            "霊媒師": 1.5,
            "狂人": -1.0,
            "妖狐": 0.0,  # 第三陣営はニュートラル
            "共有者": 1.2,
            "背徳者": -0.5,
            "猫又": 1.5,
            "預言者": 3.5,
            "狂信者": -1.5
        }
        
        # 役職の陣営
        self.role_teams = {
            "村人": "村人陣営",
            "人狼": "人狼陣営",
            "占い師": "村人陣営",
            "狩人": "村人陣営",
            "霊媒師": "村人陣営",
            "狂人": "人狼陣営",
            "妖狐": "妖狐陣営",
            "共有者": "村人陣営",
            "背徳者": "妖狐陣営",
            "猫又": "村人陣営",
            "預言者": "村人陣営",
            "狂信者": "人狼陣営"
        }
    
    def check_balance(self, composition):
        """役職構成のバランスをチェックし、問題があれば警告を返す"""
        result = {
            "balanced": True,
            "warnings": [],
            "score": 0.0
        }
        
        # プレイヤー総数
        total_players = sum(composition.values())
        
        # 各陣営の人数をカウント
        team_counts = {"村人陣営": 0, "人狼陣営": 0, "妖狐陣営": 0}
        for role, count in composition.items():
            if role in self.role_teams:
                team = self.role_teams[role]
                team_counts[team] += count
        
        # バランススコアを計算
        balance_score = 0.0
        for role, count in composition.items():
            if role in self.role_weights:
                balance_score += self.role_weights[role] * count
        
        result["score"] = balance_score
        
        # 基本チェック
        if total_players < 5:
            result["balanced"] = False
            result["warnings"].append("プレイヤー数が5人未満です。最低5人必要です。")
        
        # 陣営バランスのチェック
        if team_counts["人狼陣営"] == 0:
            result["balanced"] = False
            result["warnings"].append("人狼陣営のプレイヤーがいません。少なくとも1人の人狼が必要です。")
        
        if team_counts["村人陣営"] == 0:
            result["balanced"] = False
            result["warnings"].append("村人陣営のプレイヤーがいません。少なくとも1人の村人陣営が必要です。")
        
        # 役職の妥当性チェック
        if "人狼" not in composition or composition.get("人狼", 0) == 0:
            result["balanced"] = False
            result["warnings"].append("人狼役職がいません。少なくとも1人の人狼が必要です。")
        
        # 占い師と預言者の同時採用は非推奨
        if composition.get("占い師", 0) > 0 and composition.get("預言者", 0) > 0:
            result["warnings"].append("占い師と預言者が同時に含まれています。どちらか一方のみを採用することを推奨します。")
        
        # 陣営比率チェック
        if team_counts["人狼陣営"] >= team_counts["村人陣営"]:
            result["balanced"] = False
            result["warnings"].append("人狼陣営の人数が村人陣営の人数以上です。村人陣営の人数を増やしてください。")
        
        # 妖狐と背徳者のチェック
        if composition.get("背徳者", 0) > 0 and composition.get("妖狐", 0) == 0:
            result["warnings"].append("背徳者がいますが、妖狐がいません。背徳者は妖狐がいない場合は村人陣営として扱われます。")
        
        # バランススコアの評価
        if balance_score < -5.0:
            result["warnings"].append("人狼陣営が有利すぎる構成です。村人陣営の役職を増やすことを検討してください。")
        elif balance_score > 10.0:
            result["warnings"].append("村人陣営が有利すぎる構成です。人狼陣営の役職を増やすことを検討してください。")
        
        return result
    
    def get_recommended_composition(self, player_count):
        """プレイヤー人数に応じた推奨役職構成を返す"""
        if player_count < 5:
            return None
        
        # デフォルトの推奨構成
        recommended = {
            5: {"村人": 2, "人狼": 1, "占い師": 1, "狩人": 1},
            6: {"村人": 2, "人狼": 1, "占い師": 1, "狩人": 1, "狂人": 1},
            7: {"村人": 3, "人狼": 1, "占い師": 1, "狩人": 1, "狂人": 1},
            8: {"村人": 3, "人狼": 2, "占い師": 1, "狩人": 1, "狂人": 1},
            9: {"村人": 3, "人狼": 2, "占い師": 1, "狩人": 1, "霊媒師": 1, "狂人": 1},
            10: {"村人": 3, "人狼": 2, "占い師": 1, "狩人": 1, "霊媒師": 1, "狂人": 1, "妖狐": 1},
            11: {"村人": 3, "人狼": 3, "占い師": 1, "狩人": 1, "霊媒師": 1, "狂人": 1, "共有者": 1},
            12: {"村人": 2, "人狼": 3, "占い師": 1, "狩人": 1, "霊媒師": 1, "狂人": 1, "妖狐": 1, "共有者": 2},
            13: {"村人": 2, "人狼": 3, "占い師": 1, "狩人": 1, "霊媒師": 1, "狂人": 1, "妖狐": 1, "共有者": 2, "背徳者": 1},
            14: {"村人": 2, "人狼": 3, "占い師": 1, "狩人": 1, "霊媒師": 1, "狂人": 1, "妖狐": 1, "共有者": 2, "背徳者": 1, "猫又": 1},
            15: {"村人": 2, "人狼": 3, "占い師": 1, "狩人": 1, "霊媒師": 1, "狂人": 1, "狂信者": 1, "妖狐": 1, "共有者": 2, "背徳者": 1, "猫又": 1}
        }
        
        # 範囲外の場合は最も近い人数の構成をベースに調整
        if player_count > 15:
            base = dict(recommended[15])
            extra = player_count - 15
            for _ in range(extra):
                base["村人"] = base.get("村人", 0) + 1
            return base
        
        return recommended.get(player_count)

async def setup(bot):
    await bot.add_cog(RoleBalancer(bot))
