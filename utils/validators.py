"""
バリデーション関連ユーティリティ
"""
import discord
from discord.ext import commands

def is_guild_channel(ctx):
    """サーバーのチャンネルかどうか確認"""
    return ctx.guild is not None

def is_game_owner(ctx, game_manager):
    """ゲームの開始者かどうか確認"""
    # サーバーチャンネルでのみ実行可能
    if not is_guild_channel(ctx):
        return False, "このコマンドはサーバーのチャンネルでのみ使用できます。"
    
    # ゲームが存在するかチェック
    if not game_manager.is_game_active(ctx.guild.id):
        return False, "現在進行中のゲームがありません。"
    
    game = game_manager.get_game(ctx.guild.id)
    
    # 開始者のみが実行可能
    if ctx.author.id != int(game.owner_id):
        return False, "このコマンドはゲーム開始者のみが使用できます。"
    
    return True, game

def is_admin(ctx):
    """管理者権限を持っているかどうか確認"""
    if not is_guild_channel(ctx):
        return False, "このコマンドはサーバーのチャンネルでのみ使用できます。"
    
    if ctx.author.guild_permissions.administrator:
        return True, "管理者権限を確認しました。"
    
    return False, "このコマンドは管理者のみが使用できます。"

def can_perform_night_action(ctx, game_manager):
    """夜のアクションを実行できるかどうか確認"""
    # DMチャンネルでのみ実行可能
    if ctx.guild is not None:
        return False, "このコマンドはDMでのみ使用できます。"
    
    # プレイヤーを特定
    player = None
    
    for guild in game_manager.bot.guilds:
        if not game_manager.is_game_active(guild.id):
            continue
        
        game = game_manager.get_game(guild.id)
        
        if str(ctx.author.id) in game.players:
            player = game.players[str(ctx.author.id)]
            break
    
    if not player:
        return False, "あなたは現在進行中のゲームに参加していません。"
    
    # 生存しているかチェック
    if not player.is_alive:
        return False, "あなたはすでに死亡しています。"
    
    # 夜のフェーズかチェック
    if player.game.phase != "night":
        return False, "現在は夜のフェーズではありません。"
    
    # 夜のアクションがあるかチェック
    if not player.has_night_action():
        return False, "あなたの役職には夜のアクションがありません。"
    
    # すでにアクションを使用済みかチェック
    if player.night_action_used:
        return False, "あなたはすでに今夜のアクションを使用しています。"
    
    return True, player

def is_valid_target(ctx, game_manager, target_id):
    """対象が有効かどうか確認"""
    # プレイヤーを特定
    player = None
    
    for guild in game_manager.bot.guilds:
        if not game_manager.is_game_active(guild.id):
            continue
        
        game = game_manager.get_game(guild.id)
        
        if str(ctx.author.id) in game.players:
            player = game.players[str(ctx.author.id)]
            break
    
    if not player:
        return False, "あなたは現在進行中のゲームに参加していません。"
    
    # 対象のプレイヤーが存在するかチェック
    if str(target_id) not in player.game.players:
        return False, "指定したプレイヤーはゲームに参加していません。"
    
    target_player = player.game.players[str(target_id)]
    
    # 自分自身が対象でないかチェック (占い師と狩人)
    if str(target_id) == str(player.user_id) and player.role in ["占い師", "狩人"]:
        return False, "自分自身を対象にすることはできません。"
    
    # 対象が生存しているかチェック
    if not target_player.is_alive:
        return False, "指定したプレイヤーはすでに死亡しています。"
    
    # 狩人の場合、同じ人を連続で護衛できないチェック
    if player.role == "狩人" and player.last_protected == str(target_id):
        return False, "同じプレイヤーを連続で護衛することはできません。"
    
    # 人狼の場合、他の人狼は襲撃対象にできないチェック
    if player.role == "人狼" and target_player.role == "人狼":
        return False, "他の人狼を襲撃対象にすることはできません。"
    
    return True, target_player

class MentionConverter(commands.Converter):
    """メンションをユーザーIDに変換するコンバーター"""
    async def convert(self, ctx, argument):
        # 既にIDならそのまま返す
        if argument.isdigit():
            return argument
        
        # メンションからIDを抽出
        if argument.startswith('<@') and argument.endswith('>'):
            user_id = argument.strip('<@!>')
            if user_id.isdigit():
                return user_id
        
        # メンバー名から検索
        for guild in ctx.bot.guilds:
            for member in guild.members:
                if member.name.lower() == argument.lower() or (member.nick and member.nick.lower() == argument.lower()):
                    return str(member.id)
        
        raise commands.BadArgument(f'"{argument}" は有効なユーザーではありません。')
