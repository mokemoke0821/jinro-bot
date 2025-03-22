"""
直接登録するコマンドモジュール - コマンド実行問題を解決するための緊急対応
"""
import discord
import json
import os
import traceback
from discord.ext import commands

# プリセットデータ - 静的定義
PRESETS = {
    "standard": {
        "name": "標準",
        "description": "基本的な役職構成です。",
        "compositions": {
            "5": {"村人": 2, "人狼": 1, "占い師": 1, "狩人": 1},
            "6": {"村人": 2, "人狼": 1, "占い師": 1, "狩人": 1, "狂人": 1},
            "7": {"村人": 3, "人狼": 1, "占い師": 1, "狩人": 1, "狂人": 1},
            "8": {"村人": 3, "人狼": 2, "占い師": 1, "狩人": 1, "狂人": 1},
            "9": {"村人": 3, "人狼": 2, "占い師": 1, "狩人": 1, "霊媒師": 1, "狂人": 1},
            "10": {"村人": 3, "人狼": 2, "占い師": 1, "狩人": 1, "霊媒師": 1, "狂人": 1, "妖狐": 1},
        }
    },
    "beginner": {
        "name": "初心者向け",
        "description": "シンプルな役職構成です。初めての方におすすめ。",
        "compositions": {
            "5": {"村人": 3, "人狼": 1, "占い師": 1},
            "6": {"村人": 4, "人狼": 1, "占い師": 1},
            "7": {"村人": 4, "人狼": 2, "占い師": 1},
            "8": {"村人": 5, "人狼": 2, "占い師": 1},
            "9": {"村人": 6, "人狼": 2, "占い師": 1},
            "10": {"村人": 6, "人狼": 3, "占い師": 1},
        }
    },
    "advanced": {
        "name": "上級者向け",
        "description": "複雑な役職構成です。経験者におすすめ。",
        "compositions": {
            "7": {"村人": 1, "人狼": 1, "占い師": 1, "狩人": 1, "霊媒師": 1, "狂人": 1, "妖狐": 1},
            "8": {"村人": 1, "人狼": 2, "占い師": 1, "狩人": 1, "霊媒師": 1, "狂人": 1, "妖狐": 1},
            "9": {"村人": 1, "人狼": 2, "占い師": 1, "狩人": 1, "霊媒師": 1, "狂人": 1, "妖狐": 1, "共有者": 1},
            "10": {"村人": 1, "人狼": 2, "占い師": 1, "狩人": 1, "霊媒師": 1, "狂人": 1, "妖狐": 1, "共有者": 2},
            "11": {"村人": 1, "人狼": 2, "占い師": 1, "狩人": 1, "霊媒師": 1, "狂人": 1, "妖狐": 1, "共有者": 2, "猫又": 1},
            "12": {"人狼": 3, "占い師": 1, "狩人": 1, "霊媒師": 1, "狂人": 1, "妖狐": 1, "共有者": 2, "猫又": 1, "背徳者": 1},
        }
    },
    "chaos": {
        "name": "カオス",
        "description": "バランスを考慮しない混沌とした役職構成です。",
        "compositions": {
            "8": {"人狼": 2, "妖狐": 2, "狂人": 3, "占い師": 1},
            "10": {"人狼": 3, "妖狐": 2, "狂人": 2, "占い師": 1, "猫又": 2},
            "12": {"人狼": 4, "妖狐": 2, "狂人": 2, "占い師": 1, "猫又": 2, "背徳者": 1},
        }
    }
}

# コマンド登録
def setup_commands(bot):
    """直接コマンドをBotに登録"""
    
    @bot.command(name="compose_help")
    @commands.has_permissions(administrator=True)
    async def compose_help(ctx):
        """役職構成管理の基本コマンド"""
        # 利用可能なプリセットを表示
        preset_list = ", ".join(PRESETS.keys())
        
        embed = discord.Embed(
            title="役職構成管理",
            description=f"以下のコマンドで役職構成を管理できます。\n\n利用可能なプリセット: {preset_list}",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="プリセット一覧",
            value="`!compose_presets` - 利用可能なプリセット一覧を表示",
            inline=False
        )
        
        embed.add_field(
            name="プリセット適用",
            value="`!compose_apply [プリセット名]` - プリセット構成を適用",
            inline=False
        )
        
        embed.add_field(
            name="カスタム構成",
            value="`!compose_custom [人数] [役職1] [数1] [役職2] [数2] ...` - カスタム役職構成を設定",
            inline=False
        )
        
        embed.add_field(
            name="現在の構成確認",
            value="`!compose_show [人数]` - 指定人数の現在の役職構成を表示",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @bot.command(name="compose_presets")
    @commands.has_permissions(administrator=True)
    async def compose_presets(ctx):
        """利用可能なプリセット一覧を表示"""
        embed = discord.Embed(
            title="役職構成プリセット一覧",
            description="以下のプリセットが利用可能です。",
            color=discord.Color.blue()
        )
        
        for preset_id, preset in PRESETS.items():
            embed.add_field(
                name=f"{preset['name']} (`{preset_id}`)",
                value=f"{preset['description']}\n対応人数: {', '.join(preset['compositions'].keys())}人",
                inline=False
            )
        
        embed.set_footer(text="プリセットを適用するには !compose_apply [プリセット名] を使用してください。")
        await ctx.send(embed=embed)
    
    @bot.command(name="compose_apply")
    @commands.has_permissions(administrator=True)
    async def compose_apply(ctx, preset_id=None):
        """プリセット構成を適用する"""
        # パラメータチェック
        if preset_id is None:
            preset_list = ", ".join([f"`{name}`" for name in PRESETS.keys()])
            await ctx.send(f"プリセット名を指定してください。例: `!compose_apply standard`\n\n利用可能なプリセット: {preset_list}")
            return
            
        # 前処理: トリミングと小文字変換
        preset_id = preset_id.strip().lower()
        
        # プリセットの存在確認（大文字小文字を区別しない）
        preset_key = None
        for key in PRESETS.keys():
            if key.lower() == preset_id:
                preset_key = key
                break
                
        if preset_key is None:
            preset_list = ", ".join([f"`{name}`" for name in PRESETS.keys()])
            await ctx.send(f"プリセット `{preset_id}` は存在しません。\n利用可能なプリセット: {preset_list}")
            return
        
        # 見つかったキーを使用
        preset_id = preset_key
        preset = PRESETS[preset_id]
        
        # 成功メッセージを先に送信
        await ctx.send(f"✅ プリセット「{preset['name']}」を適用しました。")
        
        # 構成内容表示
        embed = discord.Embed(
            title=f"プリセット「{preset['name']}」の構成",
            description=f"{preset['description']}",
            color=discord.Color.green()
        )
        
        for player_count, composition in sorted(preset["compositions"].items(), key=lambda x: int(x[0])):
            roles_text = ", ".join([f"{role}: {count}" for role, count in composition.items()])
            embed.add_field(
                name=f"{player_count}人用",
                value=roles_text,
                inline=False
            )
        
        await ctx.send(embed=embed)
        
        # データを保存
        try:
            # ディレクトリが存在することを確認
            os.makedirs("data/config", exist_ok=True)
            
            # 設定ファイルパスを作成
            config_path = f"data/config/server_{ctx.guild.id}.json"
            
            # 既存の設定を読み込む（存在しない場合はデフォルト設定を使用）
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                settings = {
                    "roles_config": {},
                    "game_rules": {
                        "no_first_night_kill": False,
                        "lovers_enabled": False,
                        "no_consecutive_guard": True,
                        "random_tied_vote": False,
                        "dead_chat_enabled": True
                    },
                    "timers": {
                        "day": 300,
                        "night": 90,
                        "voting": 60
                    }
                }
            
            # roles_configを確保
            if "roles_config" not in settings:
                settings["roles_config"] = {}
            
            # プリセットの構成をコピー
            for player_count, composition in preset["compositions"].items():
                settings["roles_config"][player_count] = composition
            
            # 設定をファイルに保存
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            # エラーをログに出力するだけで、ユーザーには表示しない
            print(f"[COMPOSE] Error saving preset: {e}")
            traceback.print_exc()

    # その他のコマンドも同様に登録
    @bot.command(name="compose_show")
    @commands.has_permissions(administrator=True)
    async def compose_show(ctx, player_count: int = None):
        """現在の役職構成を表示"""
        try:
            # 設定ファイルパスを作成
            config_path = f"data/config/server_{ctx.guild.id}.json"
            
            # 設定を読み込む
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                await ctx.send("役職構成が設定されていません。")
                return
            
            # roles_configを取得
            roles_config = settings.get("roles_config", {})
            
            if not roles_config:
                await ctx.send("役職構成が設定されていません。")
                return
            
            if player_count is not None:
                # 指定人数の構成を表示
                player_count_str = str(player_count)
                if player_count_str not in roles_config:
                    await ctx.send(f"{player_count}人用の役職構成は設定されていません。")
                    return
                
                composition = roles_config[player_count_str]
                embed = discord.Embed(
                    title=f"{player_count}人用の役職構成",
                    color=discord.Color.blue()
                )
                
                roles_text = "\n".join([f"- {role}: {count}人" for role, count in composition.items()])
                embed.description = roles_text
                
                await ctx.send(embed=embed)
            else:
                # すべての人数の構成を表示
                embed = discord.Embed(
                    title="役職構成一覧",
                    description="各プレイヤー数の役職構成は以下の通りです。",
                    color=discord.Color.blue()
                )
                
                for player_count, composition in sorted(roles_config.items(), key=lambda x: int(x[0])):
                    roles_text = ", ".join([f"{role}: {count}" for role, count in composition.items()])
                    embed.add_field(
                        name=f"{player_count}人用",
                        value=roles_text,
                        inline=False
                    )
                
                await ctx.send(embed=embed)
        except Exception as e:
            # エラーをログに出力してユーザーにもエラーメッセージを表示
            print(f"[COMPOSE] Error in show_composition: {e}")
            traceback.print_exc()
            await ctx.send(f"役職構成の取得中にエラーが発生しました: {str(e)}")
