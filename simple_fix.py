"""
コマンドの重複実行問題を最小限の変更で解決するモジュール
"""

def fix_discord_bot(bot):
    """
    重複実行問題を解決するためにBotに最小限の修正を適用
    """
    print("===== 最小限の修正を適用 =====")
    
    # 前処理: 既存のすべてのパッチを無効化
    if hasattr(bot, "_fixed_compose_setup_done"):
        delattr(bot, "_fixed_compose_setup_done")
    if hasattr(bot, "_simple_compose_setup_done"):
        delattr(bot, "_simple_compose_setup_done")
    if hasattr(bot, "_direct_compose_setup_done"):
        delattr(bot, "_direct_compose_setup_done")
    
    # 既存のcomposeコマンドを削除
    for cmd in list(bot.commands):
        if cmd.name == "compose":
            bot.remove_command("compose")
            print("既存のcomposeコマンドを削除しました")
    
    # 通常のcomposeコマンドをセットアップ
    from direct_compose import setup_commands
    setup_commands(bot)
    print("通常のコマンド設定が完了しました")
    
    # 追加のフラグ設定
    bot._normal_setup_complete = True
    
    return True
