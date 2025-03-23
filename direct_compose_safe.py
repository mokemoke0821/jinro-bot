"""
直接登録するコマンドモジュール - 完全に安全な最小バージョン
"""
import discord
import json
import os
import traceback
import sys
import asyncio
import time
from discord.ext import commands

# 設定ファイルのパス
CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR, exist_ok=True)

# シンプルなロガー
class SimpleLogger:
    def info(self, msg): print(f"[INFO] {msg}")
    def error(self, msg): print(f"[ERROR] {msg}")
    def warning(self, msg): print(f"[WARNING] {msg}")
    def debug(self, msg): print(f"[DEBUG] {msg}")

logger = SimpleLogger()

# プリセットデータ
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
    }
}

# 定数
CMD_PREFIX = "!"

def setup_commands(bot):
    """直接コマンドをBotに登録 - シンプルなバージョン"""
    print("シンプルな役職構成管理コマンドを登録します")
    
    # 既存のコマンドをログ出力
    existing_commands = [cmd.name for cmd in bot.commands]
    print(f"既存コマンド: {existing_commands}")
    
    # 既存のcomposeコマンドを削除
    to_remove = []
    for cmd in bot.commands:
        if cmd.name == "compose" or cmd.name.startswith("compose_"):
            to_remove.append(cmd)
    
    for cmd in to_remove:
        bot.remove_command(cmd.name)
        print(f"既存コマンドを削除: {cmd.name}")

    # メインコマンドの登録
    @bot.command(name="compose")
    async def compose_command(ctx, *args):
        """役職構成管理のメインコマンド - シンプルなバージョン"""
        try:
            print(f"compose コマンド実行: 引数={args}")
            
            # 引数がない場合はヘルプを表示
            if not args:
                embed = discord.Embed(
                    title="役職構成管理",
                    description="以下のコマンドで役職構成を管理できます。",
                    color=discord.Color.blue()
                )
                
                embed.add_field(
                    name="プリセット一覧",
                    value="`!compose presets` - 利用可能なプリセット一覧を表示",
                    inline=False
                )
                await ctx.send(embed=embed)
                return
            
            # 最初の引数をサブコマンドとして解釈
            subcommand = args[0].lower()
            
            if subcommand == "presets":
                # プリセット一覧表示
                embed = discord.Embed(
                    title="役職構成プリセット一覧",
                    description="以下のプリセットから選択できます。",
                    color=discord.Color.green()
                )
                
                for preset_id, preset_data in PRESETS.items():
                    # 各プリセットの情報を追加
                    player_counts = list(preset_data["compositions"].keys())
                    player_range = f"{min(player_counts)}人〜{max(player_counts)}人"
                    
                    embed.add_field(
                        name=f"{preset_data['name']} ({preset_id})",
                        value=f"説明: {preset_data['description']}\n対応人数: {player_range}",
                        inline=False
                    )
                
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"未知のサブコマンド: `{subcommand}`")
                
        except Exception as e:
            print(f"エラーが発生しました: {e}")
            traceback.print_exc()
            try:
                await ctx.send(f"コマンド実行中にエラーが発生しました。")
            except:
                pass
    
    print("シンプルな役職構成管理コマンドの登録が完了しました")
    return True
