"""
embed_creator.pyの修正をテストするスクリプト
discordやaiohttpのようなライブラリはモックで置き換えます
"""
import sys
import os
import traceback
from unittest.mock import MagicMock

print("テストスクリプト開始")

try:
    # まず、discordをモックします
    sys.modules['discord'] = MagicMock()
    import discord

    # discord内のEmbedクラスをシミュレート
    discord.Embed = MagicMock()
    discord.Color = MagicMock()
    discord.Color.blue = MagicMock(return_value=0x0000FF)
    discord.Color.green = MagicMock(return_value=0x00FF00)
    discord.Color.gold = MagicMock(return_value=0xFFD700)
    discord.Color.red = MagicMock(return_value=0xFF0000)
    discord.Color.blurple = MagicMock(return_value=0x7289DA)
    discord.Color.dark_blue = MagicMock(return_value=0x000080)
    discord.Color.light_gray = MagicMock(return_value=0xD3D3D3)
    discord.Color.purple = MagicMock(return_value=0x800080)

    # 現在のディレクトリをsys.pathに追加
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    print("モック設定完了、テスト開始")

    # utils.embed_creatorを直接インポート
    print("utils.embed_creatorをインポート中...")
    
    # 関数をインポート
    from utils.embed_creator import (
        create_base_embed,
        create_game_status_embed, 
        create_role_embed,
        create_night_action_embed,
        create_divination_result_embed,
        create_night_result_embed,
        create_help_embed,
        EmbedCreator
    )
    
    # EmbedCreatorクラスのインスタンス化を試みる
    embed_creator = EmbedCreator()
    
    print("✅ 成功: 必要な関数とクラスのインポートが全て成功しました")
    
    # 各関数の検証
    print("\n関数の確認:")
    functions = [
        create_base_embed,
        create_game_status_embed,
        create_role_embed,
        create_night_action_embed,
        create_divination_result_embed,
        create_night_result_embed,
        create_help_embed
    ]
    
    for i, func in enumerate(functions):
        print(f"  ✓ {func.__name__} - 関数が存在")
    
    print("\n✅ テスト完了: すべての関数にアクセス可能です")
    print("embed_creator.pyの修正が正しく適用されています")
    print("コグがutils.embed_creatorから必要な関数をインポートできるようになりました")
    sys.exit(0)

except Exception as e:
    print(f"❌ エラー発生: {e}")
    print("\nスタックトレース:")
    traceback.print_exc()
    sys.exit(1)
