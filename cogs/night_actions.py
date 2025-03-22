"""
夜のアクション処理コグ
夜のフェーズでのプレイヤーのアクションを処理
"""
import discord
import asyncio
from discord.ext import commands
from utils.embed_creator import create_night_action_embed, create_divination_result_embed, create_night_result_embed, create_base_embed
from utils.validators import can_perform_night_action, is_valid_target, MentionConverter
from utils.config import EmbedColors, GameConfig

class NightActionsCog(commands.Cog):
    """夜のアクション処理Cog"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="action")
    async def night_action(self, ctx, target: MentionConverter):
        """夜のアクション実行コマンド（対象を指定）"""
        # ゲームマネージャーの取得
        game_manager = self.bot.get_cog("GameManagementCog")
        if not game_manager:
            await ctx.send("ゲーム管理システムが見つかりません。")
            return
        
        # アクション実行可能かチェック
        valid, result = can_perform_night_action(ctx, game_manager)
        
        if not valid:
            await ctx.send(result)
            return
        
        player = result
        game = player.game
        
        # 対象が有効かチェック
        valid, target_result = is_valid_target(ctx, game_manager, target)
        
        if not valid:
            await ctx.send(target_result)
            return
        
        target_player = target_result
        
        # 役職に応じたアクション処理
        success_msg = None
        
        if player.role_instance:
            # 役職インスタンスを使って処理
            success, message = await player.role_instance.execute_night_action(target)
            if success:
                success_msg = message
                
                # 人狼の場合、他の人狼にも通知
                if player.is_werewolf():
                    await self.notify_other_wolves(player, target_player)
                    game.wolf_target = target
                
                # 占い師の場合、結果を表示
                if player.role == "占い師":
                    is_werewolf = target_player.is_werewolf()
                    embed = create_divination_result_embed(target_player, is_werewolf)
                    await ctx.send(embed=embed)
                    success_msg = None  # 既に結果を表示したので成功メッセージは不要
                
                # 狩人の場合
                if player.role == "狩人":
                    game.protected_target = target
                    player.last_protected = target
            else:
                await ctx.send(message)
                return
        else:
            # 旧式の処理（役職インスタンスがない場合のフォールバック）
            if player.role == "人狼":
                # 人狼の襲撃
                success_msg = f"{target_player.name} を襲撃対象に設定しました。"
                game.wolf_target = target
                
                # 他の人狼にも通知
                await self.notify_other_wolves(player, target_player)
            elif player.role == "占い師":
                # 占い師の占い
                is_werewolf = target_player.is_werewolf()
                
                # 妖狐の占い死判定
                if target_player.is_fox() and target_player.is_alive:
                    target_player.kill()
                    game.killed_by_divination = target
                
                # 占い結果を記録
                player.divination_results[target] = is_werewolf
                
                # 占い結果を表示
                embed = create_divination_result_embed(target_player, is_werewolf)
                await ctx.send(embed=embed)
                success_msg = None  # 既に結果を表示したので成功メッセージは不要
            elif player.role == "狩人":
                # 前回と同じ対象を選択できないチェック
                if player.last_protected == target:
                    await ctx.send("同じ対象を連続で護衛することはできません。")
                    return
                
                # 狩人の護衛
                success_msg = f"{target_player.name} を護衛対象に設定しました。"
                game.protected_target = target
                player.last_protected = target
            else:
                # その他の役職（村人など）
                await ctx.send("あなたの役職には夜のアクションがありません。")
                return
        
        # アクション実行済みフラグを設定
        player.night_action_target = target
        player.night_action_used = True
        
        # 成功メッセージ（ある場合）
        if success_msg:
            embed = discord.Embed(
                title="アクション実行",
                description=success_msg,
                color=EmbedColors.SUCCESS
            )
            await ctx.send(embed=embed)
        
        # すべてのプレイヤーがアクションを実行したかチェック
        await self.check_all_actions_completed(game)
    
    async def notify_other_wolves(self, wolf_player, target_player):
        """他の人狼に襲撃対象を通知"""
        game = wolf_player.game
        wolves = game.get_werewolves()
        
        for w in wolves:
            if w.user_id != wolf_player.user_id and w.is_alive:
                # 他の人狼に通知
                try:
                    member = self.bot.get_guild(int(game.guild_id)).get_member(int(w.user_id))
                    if member:
                        embed = create_base_embed(
                            title="🐺 人狼の行動",
                            description=f"仲間の人狼 **{wolf_player.name}** が **{target_player.name}** を襲撃対象に選びました。",
                            color=EmbedColors.ERROR
                        )
                        await member.send(embed=embed)
                        
                        # 行動済みフラグを設定
                        w.night_action_target = target_player.user_id
                        w.night_action_used = True
                except Exception as e:
                    print(f"他の人狼への通知エラー: {e}")
    
    async def check_all_actions_completed(self, game):
        """全プレイヤーのアクションが完了したかチェック"""
        if game.phase != "night":
            return False
        
        all_completed = True
        wolves_acted = False
        
        # 最低1人の人狼がアクションを実行したかチェック
        for player in game.players.values():
            if player.is_alive and player.is_werewolf() and player.night_action_used:
                wolves_acted = True
                break
        
        for player in game.players.values():
            if player.is_alive:
                # アクションが必要な役職か確認
                needs_action = False
                
                if player.role == "人狼":
                    # 人狼の場合、1人がアクションを実行すれば全員が実行したことになる
                    needs_action = not wolves_acted
                elif player.role in ["占い師", "狩人"]:
                    needs_action = True
                
                # アクションが必要なのに実行していない場合
                if needs_action and not player.night_action_used:
                    all_completed = False
                    break
        
        if all_completed:
            # 非同期で次のフェーズへ進める
            # タイマーが実行中なら少し待ってからタイマーをキャンセル
            if game.remaining_time > 0:
                await asyncio.sleep(2)
                game.cancel_timer()
            
            # 次のフェーズへ
            await self.end_night_phase(game)
        
        return all_completed
    
    async def end_night_phase(self, game):
        """夜のフェーズを終了し、結果を処理"""
        # 夜のアクションを処理
        game.process_night_actions()
        game.next_phase()
        
        # メインチャンネルへの結果通知
        channel = self.bot.get_channel(int(game.channel_id))
        if not channel:
            return
        
        # 結果の生成
        killed_player = None
        protected = False
        
        if game.last_killed:
            killed_player = game.players[game.last_killed]
        elif game.wolf_target and game.wolf_target == game.protected_target:
            protected = True
        
        # 結果表示
        embed = create_night_result_embed(killed_player, protected)
        await channel.send(embed=embed)
        
        # 占いによる妖狐の死亡を処理
        if game.killed_by_divination:
            fox_player = game.players[game.killed_by_divination]
            fox_embed = discord.Embed(
                title="🦊 妖狐の死亡",
                description=f"{fox_player.name} が占いによって死亡しました。",
                color=EmbedColors.ERROR
            )
            await channel.send(embed=fox_embed)
            
            # 霊界チャットの権限を更新
            if hasattr(game, 'dead_chat_channel_id') and game.special_rules.dead_chat_enabled:
                guild = self.bot.get_guild(int(game.guild_id))
                if guild:
                    game_manager = self.bot.get_cog("GameManagementCog")
                    if game_manager:
                        await game_manager.update_dead_chat_permissions(guild, game, fox_player)
        
        # ゲーム終了判定
        is_game_end, winning_team = game.check_game_end()
        
        if is_game_end:
            # ゲーム終了処理
            from cogs.voting import VotingCog
            voting_cog = self.bot.get_cog("VotingCog")
            if voting_cog:
                await voting_cog.end_game(channel, game, winning_team)
            return
        
        # 次の昼フェーズを開始
        from cogs.day_actions import DayActionsCog
        day_cog = self.bot.get_cog("DayActionsCog")
        if day_cog:
            await day_cog.start_day_phase(channel, game)
    
    async def send_night_action_instructions(self, game):
        """各プレイヤーに夜のアクション指示をDM"""
        guild = self.bot.get_guild(int(game.guild_id))
        if not guild:
            return
        
        for player in game.players.values():
            if player.is_alive:
                member = guild.get_member(int(player.user_id))
                if member:
                    try:
                        embed = create_night_action_embed(player)
                        await member.send(embed=embed)
                    except discord.Forbidden:
                        # DMが送れない場合は代替手段を試みる
                        from utils.fallback_dm import send_fallback_dm
                        await send_fallback_dm(self.bot, guild, member, embed)
                        
                        # ログに記録
                        print(f"Failed to send DM to {member.name}")

async def setup(bot):
    """Cogをbotに追加"""
    await bot.add_cog(NightActionsCog(bot))
