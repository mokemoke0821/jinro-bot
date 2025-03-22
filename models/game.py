"""
ゲームモデル
"""
import random
import asyncio
from models.player import Player
from utils.config import GameConfig

class Game:
    """ゲームクラス"""
    
    def __init__(self, guild_id, channel_id, owner_id):
        self.guild_id = guild_id  # サーバーID
        self.channel_id = channel_id  # チャンネルID
        self.owner_id = owner_id  # 開始者ID
        self.players = {}  # {user_id: Player}
        self.phase = "waiting"  # waiting, night, day, voting, finished
        self.day_count = 0  # 経過日数
        
        # Discord Bot参照（後で設定）
        self.bot = None
        
        # 夜のアクション結果
        self.wolf_target = None  # 人狼の標的
        self.protected_target = None  # 狩人の護衛対象
        self.last_killed = None  # 最後に殺された人
        self.killed_by_divination = None  # 占いによって殺された妖狐
        
        # 投票関連
        self.votes = {}  # {voter_id: target_id}
        self.vote_count = {}  # {target_id: count}
        self.vote_message = None  # 投票用UIメッセージ
        
        # タイマー関連
        self.timer = None
        self.remaining_time = 0
        
        # 特殊ルール
        from models.special_rules import SpecialRules
        self.special_rules = SpecialRules()
    
    def add_player(self, user_id, name):
        """プレイヤーを追加"""
        if str(user_id) in self.players:
            return None
        
        player = Player(user_id, name, self)
        self.players[str(user_id)] = player
        return player
    
    def start_game(self):
        """ゲームを開始、役職を割り当て"""
        if len(self.players) < 5:
            return False, "ゲームを開始するには最低5人の参加者が必要です。"
        
        # 役職割り当て
        try:
            self.assign_roles()
            self.phase = "night"
            self.day_count = 1
            return True, None
        except Exception as e:
            return False, str(e)
    
    def assign_roles(self):
        """役職を割り当て"""
        player_count = len(self.players)
        role_dist = GameConfig.get_role_distribution(player_count)
        
        # 役職リストを作成
        role_list = []
        for role, count in role_dist.items():
            role_list.extend([role] * count)
        
        # シャッフル
        random.shuffle(role_list)
        
        # 各プレイヤーに役職を割り当て
        player_ids = list(self.players.keys())
        for i, player_id in enumerate(player_ids):
            if i < len(role_list):
                self.players[player_id].assign_role(role_list[i])
    
    def next_phase(self):
        """次のフェーズへ移行"""
        self.cancel_timer()  # 現在のタイマーをキャンセル
        
        if self.phase == "waiting":
            self.phase = "night"
            self.day_count = 1
        elif self.phase == "night":
            self.phase = "day"
            self.process_night_actions()
        elif self.phase == "day":
            self.phase = "voting"
        elif self.phase == "voting":
            self.phase = "night"
            self.process_voting()
            self.day_count += 1
            self.reset_night_actions()
    
    def process_night_actions(self):
        """夜のアクションを処理"""
        # 人狼の襲撃処理
        if self.wolf_target:
            target_id = self.wolf_target
            target_player = self.players.get(str(target_id))
            
            # 護衛対象かチェック
            if self.protected_target == target_id:
                # 護衛成功
                pass
            # 妖狐の襲撃耐性チェック
            elif target_player and target_player.is_fox():
                # 妖狐は人狼の襲撃では死なない
                pass
            else:
                # 襲撃成功
                if target_player:
                    target_player.kill()
                    self.last_killed = str(target_id)
                    
                    # プレイヤーが死亡した場合、霊界チャットの権限を更新
                    if hasattr(self, 'dead_chat_channel_id') and self.special_rules.dead_chat_enabled:
                        guild = self.bot.get_guild(int(self.guild_id))
                        if guild:
                            game_manager = self.bot.get_cog("GameManagementCog")
                            if game_manager:
                                # 非同期でパーミッション更新
                                import asyncio
                                asyncio.create_task(game_manager.update_dead_chat_permissions(guild, self, target_player))
                
        # 状態リセット
        self.wolf_target = None
        self.protected_target = None
    
    def process_voting(self):
        """投票を集計"""
        self.vote_count = {}
        
        # 票を集計
        for target_id in self.votes.values():
            if str(target_id) not in self.vote_count:
                self.vote_count[str(target_id)] = 0
            self.vote_count[str(target_id)] += 1
        
        # 最多票を確認
        max_votes = 0
        targets = []
        
        for target_id, count in self.vote_count.items():
            if count > max_votes:
                max_votes = count
                targets = [target_id]
            elif count == max_votes:
                targets.append(target_id)
        
        # 同票数の場合はランダム、それ以外は最多票のプレイヤーを処刑
        if targets:
            executed_id = random.choice(targets)
            if str(executed_id) in self.players:
                self.players[str(executed_id)].kill()
                self.last_killed = str(executed_id)
        
        # 投票リセット
        self.votes = {}
        self.vote_count = {}
    
    def check_game_end(self):
        """ゲーム終了判定"""
        wolves_alive = 0
        villagers_alive = 0
        foxes_alive = 0
        
        for player in self.players.values():
            if player.is_alive:
                if player.is_werewolf():
                    wolves_alive += 1
                elif player.is_villager_team():
                    villagers_alive += 1
                elif player.is_fox():
                    foxes_alive += 1
        
        # 人狼勝利: 村人陣営が0人
        if villagers_alive == 0:
            return True, "werewolf"
        
        # 村人勝利: 人狼が0人
        if wolves_alive == 0:
            # 妖狐が生存している場合は妖狐の勝利
            if foxes_alive > 0:
                return True, "fox"
            return True, "villager"
        
        # ゲーム続行
        return False, None
    
    def reset_night_actions(self):
        """夜のアクション状態をリセット"""
        for player in self.players.values():
            player.reset_night_action()
        
        self.wolf_target = None
        self.protected_target = None
        self.killed_by_divination = None
    
    def add_vote(self, voter_id, target_id):
        """投票を追加"""
        self.votes[str(voter_id)] = str(target_id)
        return len(self.votes)
    
    def get_alive_players(self):
        """生存しているプレイヤーを取得"""
        return [p for p in self.players.values() if p.is_alive]
    
    def get_dead_players(self):
        """死亡しているプレイヤーを取得"""
        return [p for p in self.players.values() if not p.is_alive]
    
    def get_werewolves(self):
        """人狼プレイヤーを取得"""
        return [p for p in self.players.values() if p.is_werewolf()]
    
    async def start_timer(self, seconds, update_callback, complete_callback):
        """タイマーを開始"""
        # 既存のタイマーをキャンセル
        self.cancel_timer()
        
        self.remaining_time = seconds
        
        # タイマー処理
        while self.remaining_time > 0:
            if update_callback:
                await update_callback(self.remaining_time)
            
            await asyncio.sleep(1)
            self.remaining_time -= 1
        
        # タイマー完了
        if complete_callback:
            await complete_callback()
    
    def cancel_timer(self):
        """タイマーをキャンセル"""
        if self.timer:
            self.timer.cancel()
            self.timer = None
        
        self.remaining_time = 0
