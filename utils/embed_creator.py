"""
DiscordのEmbed作成ユーティリティ
"""
import discord
from utils.config import EmbedColors

def create_base_embed(title, description, color):
    """基本的なEmbedを作成"""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    return embed

def create_game_status_embed(game, phase):
    """ゲームステータスのEmbedを作成"""
    if phase == "waiting":
        title = "🎮 ゲーム募集中"
        description = "人狼ゲームの参加者を募集しています。"
        color = EmbedColors.PRIMARY
    elif phase == "night":
        title = "🌙 夜のフェーズ"
        description = f"第{game.day_count}夜 - 各自の役職に応じたアクションを実行してください。"
        color = EmbedColors.NIGHT
    elif phase == "day":
        title = "☀️ 昼のフェーズ"
        description = f"第{game.day_count}日 - 議論の時間です。"
        color = EmbedColors.DAY
    elif phase == "voting":
        title = "🗳️ 投票フェーズ"
        description = f"第{game.day_count}日 - 処刑する人を決めるための投票です。"
        color = EmbedColors.WARNING
    else:
        title = "🎮 人狼ゲーム"
        description = "ゲームの状態"
        color = EmbedColors.PRIMARY
    
    embed = create_base_embed(title, description, color)
    
    # 参加者情報
    alive_players = game.get_alive_players()
    dead_players = game.get_dead_players()
    
    embed.add_field(name="参加者数", value=f"{len(game.players)}", inline=True)
    embed.add_field(name="生存者数", value=f"{len(alive_players)}", inline=True)
    
    # 参加者一覧（フェーズに応じて表示内容を変更）
    if phase == "waiting":
        player_list = "\n".join([f"- {p.name}" for p in game.players.values()])
        embed.add_field(name="参加者一覧", value=player_list or "まだ参加者がいません", inline=False)
    elif phase != "waiting":
        alive_list = "\n".join([f"- {p.name}" for p in alive_players])
        embed.add_field(name="生存者", value=alive_list or "生存者がいません", inline=False)
        
        if dead_players:
            dead_list = "\n".join([f"- {p.name} ({p.role})" for p in dead_players])
            embed.add_field(name="死亡者", value=dead_list, inline=False)
    
    # フッター
    embed.set_footer(text="!werewolf_help でコマンド一覧を表示")
    return embed

def create_role_embed(player):
    """役職通知のEmbedを作成"""
    role = player.role
    
    if role == "人狼":
        title = "🐺 あなたは「人狼」です"
        description = "村人に怪しまれないように振る舞いながら、夜に村人を襲撃してください。"
        color = EmbedColors.ERROR
    elif role == "占い師":
        title = "🔮 あなたは「占い師」です"
        description = "夜に一人を選んで占い、人狼かどうかを確認できます。"
        color = EmbedColors.PRIMARY
    elif role == "狩人":
        title = "🛡️ あなたは「狩人」です"
        description = "夜に一人を選んで護衛し、人狼の襲撃から守ることができます。"
        color = EmbedColors.SUCCESS
    elif role == "霊能者":
        title = "👻 あなたは「霊能者」です"
        description = "処刑された人が人狼かどうかを知ることができます。"
        color = EmbedColors.INFO
    elif role == "狂人":
        title = "🤪 あなたは「狂人」です"
        description = "人狼陣営です。正体を隠して人狼に協力しましょう。"
        color = EmbedColors.WARNING
    elif role == "妖狐":
        title = "🦊 あなたは「妖狐」です"
        description = "人狼にも村人にも属さず、占われると死亡します。最後まで生き残りましょう。"
        color = EmbedColors.WARNING
    else:  # 村人
        title = "👨‍🌾 あなたは「村人」です"
        description = "議論に参加して人狼を見つけ出しましょう。"
        color = EmbedColors.PRIMARY
    
    embed = create_base_embed(title, description, color)
    
    # 役職の説明詳細
    if role == "人狼":
        embed.add_field(name="能力", value="夜のフェーズで一人を選んで襲撃できます。", inline=False)
        
        # 他の人狼がいる場合は表示
        game = player.game
        if game:
            other_wolves = [p for p in game.get_werewolves() if str(p.user_id) != str(player.user_id)]
            if other_wolves:
                wolf_list = "\n".join([f"- {p.name}" for p in other_wolves])
                embed.add_field(name="仲間の人狼", value=wolf_list, inline=False)
    elif role == "占い師":
        embed.add_field(name="能力", value="夜のフェーズで一人を選んで、その人が人狼かどうかを占えます。", inline=False)
    elif role == "狩人":
        embed.add_field(name="能力", value="夜のフェーズで一人を選んで、人狼の襲撃から守ることができます。ただし、同じ人を連続で護衛することはできません。", inline=False)
    elif role == "霊能者":
        embed.add_field(name="能力", value="処刑されたプレイヤーが人狼かどうかがわかります。", inline=False)
    elif role == "狂人":
        embed.add_field(name="注意", value="あなたは村人に見えますが、人狼陣営です。人狼の勝利があなたの勝利となります。", inline=False)
    elif role == "妖狐":
        embed.add_field(name="特殊能力", value="人狼に襲撃されても死亡しません。ただし、占い師に占われると死亡します。", inline=False)
        embed.add_field(name="勝利条件", value="生き残って、人狼か村人のどちらかが全滅すれば勝利です。", inline=False)
    
    embed.add_field(name="コマンド", value="DMで `!action @ユーザー名` と入力することで、夜のアクションを実行できます。", inline=False)
    return embed

def create_night_action_embed(player):
    """夜のアクション指示のEmbedを作成"""
    role = player.role
    
    if role == "人狼":
        title = "🐺 人狼のアクション"
        description = "襲撃する対象を選んでください。"
        color = EmbedColors.ERROR
        action_description = "襲撃したいプレイヤーを選んで、`!action @ユーザー名` と入力してください。"
    elif role == "占い師":
        title = "🔮 占い師のアクション"
        description = "占う対象を選んでください。"
        color = EmbedColors.PRIMARY
        action_description = "占いたいプレイヤーを選んで、`!action @ユーザー名` と入力してください。"
    elif role == "狩人":
        title = "🛡️ 狩人のアクション"
        description = "護衛する対象を選んでください。"
        color = EmbedColors.SUCCESS
        action_description = "護衛したいプレイヤーを選んで、`!action @ユーザー名` と入力してください。"
    else:
        title = "🌙 夜のフェーズ"
        description = "あなたは特別なアクションがありません。"
        color = EmbedColors.NIGHT
        action_description = "朝になるまでお待ちください。"
    
    embed = create_base_embed(title, description, color)
    
    # 生存プレイヤー一覧
    if player.game and (role == "人狼" or role == "占い師" or role == "狩人"):
        alive_players = player.game.get_alive_players()
        player_list = "\n".join([f"- {p.name}" for p in alive_players if str(p.user_id) != str(player.user_id)])
        embed.add_field(name="選択可能なプレイヤー", value=player_list or "選択可能なプレイヤーがいません", inline=False)
    
    embed.add_field(name="アクション方法", value=action_description, inline=False)
    return embed

def create_divination_result_embed(target_player, is_werewolf):
    """占い結果のEmbedを作成"""
    title = "🔮 占い結果"
    
    if is_werewolf:
        description = f"**{target_player.name}** は **人狼** です！"
        color = EmbedColors.ERROR
    else:
        description = f"**{target_player.name}** は **人狼ではありません**。"
        color = EmbedColors.SUCCESS
    
    embed = create_base_embed(title, description, color)
    return embed

def create_night_result_embed(killed_player, protected):
    """夜の結果のEmbedを作成"""
    if killed_player:
        title = "🌙 夜の結果"
        description = f"**{killed_player.name}** が無残な姿で発見されました。"
        color = EmbedColors.ERROR
    elif protected:
        title = "🌙 夜の結果"
        description = "今夜は犠牲者がありませんでした。誰かが守られたようです。"
        color = EmbedColors.SUCCESS
    else:
        title = "🌙 夜の結果"
        description = "今夜は犠牲者がありませんでした。"
        color = EmbedColors.SUCCESS
    
    embed = create_base_embed(title, description, color)
    return embed

def create_help_embed():
    """ヘルプEmbedを作成"""
    embed = create_base_embed(
        title="🐺 人狼Bot ヘルプ",
        description="Discord上で遊べる人狼ゲームのコマンド一覧と遊び方です。",
        color=EmbedColors.PRIMARY
    )
    
    # コマンド一覧
    embed.add_field(name="!werewolf_help", value="このヘルプを表示します。", inline=False)
    embed.add_field(name="!start", value="新しい人狼ゲームの募集を開始します。", inline=False)
    embed.add_field(name="!join", value="募集中のゲームに参加します。", inline=False)
    embed.add_field(name="!begin", value="参加者が揃ったらゲームを開始します（ゲーム開始者のみ）。", inline=False)
    embed.add_field(name="!cancel", value="進行中のゲームをキャンセルします（ゲーム開始者・管理者のみ）。", inline=False)
    embed.add_field(name="!status", value="現在のゲーム状態を表示します。", inline=False)
    embed.add_field(name="!vote @ユーザー名", value="指定したユーザーに投票します（投票フェーズのみ）。", inline=False)
    embed.add_field(name="!action @ユーザー名", value="夜のアクションを実行します（DMでのみ使用可能）。", inline=False)
    
    # ゲームの流れ
    embed.add_field(
        name="ゲームの流れ",
        value="1. `!start` でゲームを開始\n"
              "2. `!join` で参加者を募集\n"
              "3. `!begin` でゲーム開始\n"
              "4. 役職が配られ、夜のフェーズが始まる\n"
              "5. 昼のフェーズで議論\n"
              "6. 投票で処刑する人を決定\n"
              "7. これを繰り返し、村人か人狼が勝利するまで続く",
        inline=False
    )
    
    # 役職説明
    embed.add_field(
        name="役職一覧",
        value="**村人陣営**：\n"
              "- 村人：特殊能力なし\n"
              "- 占い師：夜に一人を占い、人狼かどうかを確認できる\n"
              "- 狩人：夜に一人を人狼の襲撃から守ることができる\n"
              "- 霊能者：処刑された人が人狼かどうかを知ることができる\n\n"
              "**人狼陣営**：\n"
              "- 人狼：夜に一人を襲撃できる\n"
              "- 狂人：人狼ではないが、人狼陣営\n\n"
              "**第三陣営**：\n"
              "- 妖狐：人狼の襲撃では死なないが、占われると死亡する",
        inline=False
    )
    
    return embed
