import os
import json
import datetime
import discord
from typing import Optional, List, Dict, Any
import uuid

class LogManager:
    """
    ゲームログの記録と管理を行うクラス
    """
    def __init__(self):
        self.log_directory = "logs"
        self.ensure_log_directory()
        
    def ensure_log_directory(self):
        """ログディレクトリが存在することを確認"""
        if not os.path.exists(self.log_directory):
            os.makedirs(self.log_directory)
    
    def generate_log_filename(self, game_id: str) -> str:
        """ゲームIDに基づいてログファイル名を生成"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{self.log_directory}/game_{game_id}_{timestamp}.log"
    
    def log_game_event(self, game_id: str, event_type: str, details: Dict[str, Any]):
        """ゲーム内イベントをログに記録"""
        timestamp = datetime.datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "game_id": game_id,
            "type": event_type,
            "details": details
        }
        
        filename = f"{self.log_directory}/game_{game_id}.log"
        self._write_log_entry(filename, log_entry)
        return log_entry
    
    def log_player_action(self, game_id: str, player_id: int, action_type: str, details: str):
        """プレイヤーのアクションをログに記録"""
        return self.log_game_event(game_id, "player_action", {
            "player_id": player_id,
            "action_type": action_type,
            "details": details
        })
    
    def log_role_action(self, game_id: str, player_id: int, role: str, action_type: str, target_id: Optional[int], details: str):
        """役職のアクションをログに記録"""
        return self.log_game_event(game_id, "role_action", {
            "player_id": player_id,
            "role": role,
            "action_type": action_type,
            "target_id": target_id,
            "details": details
        })
    
    def log_phase_change(self, game_id: str, from_phase: str, to_phase: str, day: int):
        """フェーズ変更をログに記録"""
        return self.log_game_event(game_id, "phase_change", {
            "from": from_phase,
            "to": to_phase,
            "day": day
        })
    
    def log_vote(self, game_id: str, voter_id: int, target_id: int, vote_type: str):
        """投票をログに記録"""
        return self.log_game_event(game_id, "vote", {
            "voter_id": voter_id,
            "target_id": target_id,
            "vote_type": vote_type
        })
    
    def log_death(self, game_id: str, player_id: int, reason: str, day: int):
        """プレイヤーの死亡をログに記録"""
        return self.log_game_event(game_id, "death", {
            "player_id": player_id,
            "reason": reason,
            "day": day
        })
    
    def log_game_start(self, game_id: str, guild_id: int, players: List[Dict[str, Any]]):
        """ゲーム開始をログに記録"""
        player_info = [{
            "id": p["id"],
            "name": p["name"],
            "role": p["role"]
        } for p in players]
        
        return self.log_game_event(game_id, "game_start", {
            "guild_id": guild_id,
            "player_count": len(players),
            "players": player_info
        })
    
    def log_game_end(self, game_id: str, winner: str, reason: str, game_duration: int):
        """ゲーム終了をログに記録"""
        return self.log_game_event(game_id, "game_end", {
            "winner": winner,
            "reason": reason,
            "duration_seconds": game_duration
        })
    
    def log_admin_action(self, game_id: str, admin_id: int, action_type: str, details: str):
        """管理者のアクションをログに記録"""
        return self.log_game_event(game_id, "admin_action", {
            "admin_id": admin_id,
            "action_type": action_type,
            "details": details
        })
    
    def _write_log_entry(self, filename: str, log_entry: Dict[str, Any]):
        """ログエントリをファイルに書き込む"""
        with open(filename, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    async def export_game_log(self, game_id: str, game_data: Dict[str, Any]) -> Optional[str]:
        """
        ゲームログをテキストファイルにエクスポートして、そのファイルパスを返す
        """
        # ログファイルが存在するか確認
        log_file = f"{self.log_directory}/game_{game_id}.log"
        if not os.path.exists(log_file):
            return None
        
        # エクスポート用のファイル名を生成
        export_filename = self.generate_log_filename(game_id)
        
        # ゲーム情報をヘッダーとして追加
        with open(export_filename, "w", encoding="utf-8") as export_file:
            # ゲームの基本情報を書き込む
            export_file.write("======== 人狼ゲームログ ========\n")
            export_file.write(f"ゲームID: {game_id}\n")
            export_file.write(f"サーバー: {game_data.get('guild_name', '不明')}\n")
            export_file.write(f"開始時刻: {game_data.get('start_time', '不明')}\n")
            export_file.write(f"終了時刻: {game_data.get('end_time', '不明')}\n")
            export_file.write(f"勝者: {game_data.get('winner', '不明')}\n")
            export_file.write(f"プレイヤー数: {len(game_data.get('players', []))}\n\n")
            
            # プレイヤー一覧を書き込む
            export_file.write("-------- プレイヤー情報 --------\n")
            for player in game_data.get('players', []):
                status = "生存" if player.get("is_alive", False) else f"死亡 (理由: {player.get('death_reason', '不明')})"
                export_file.write(f"{player.get('name', '不明')} - 役職: {player.get('role', '不明')} - {status}\n")
            export_file.write("\n")
            
            # ゲームの進行ログを時系列順に整形
            export_file.write("-------- ゲーム進行ログ --------\n")
            log_entries = []
            
            # ログファイルからすべてのエントリを読み込む
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        log_entries.append(entry)
                    except json.JSONDecodeError:
                        continue
            
            # タイムスタンプでソート
            log_entries.sort(key=lambda x: x.get("timestamp", ""))
            
            # 整形して書き込む
            day_tracker = 0
            for entry in log_entries:
                timestamp = datetime.datetime.fromisoformat(entry.get("timestamp", "")).strftime("%Y-%m-%d %H:%M:%S")
                event_type = entry.get("type", "unknown")
                details = entry.get("details", {})
                
                # フェーズ変更の処理
                if event_type == "phase_change":
                    to_phase = details.get("to", "unknown")
                    day = details.get("day", 0)
                    
                    # 日付が変わったら日付区切りを挿入
                    if day > day_tracker:
                        day_tracker = day
                        export_file.write(f"\n=== {day}日目 ===\n")
                    
                    if to_phase == "day":
                        export_file.write(f"\n[{timestamp}] ☀️ {day}日目の昼になりました。\n")
                    elif to_phase == "night":
                        export_file.write(f"\n[{timestamp}] 🌙 {day}日目の夜になりました。\n")
                
                # 投票の処理
                elif event_type == "vote":
                    voter_name = self._get_player_name(game_data, details.get("voter_id"))
                    target_name = self._get_player_name(game_data, details.get("target_id"))
                    vote_type = details.get("vote_type", "unknown")
                    
                    if vote_type == "day_vote":
                        export_file.write(f"[{timestamp}] 🗳️ {voter_name} が {target_name} に投票しました。\n")
                    elif vote_type == "werewolf_vote":
                        export_file.write(f"[{timestamp}] 🐺 {voter_name} が {target_name} を襲撃対象に選びました。\n")
                
                # 役職アクションの処理
                elif event_type == "role_action":
                    player_name = self._get_player_name(game_data, details.get("player_id"))
                    role = details.get("role", "unknown")
                    action_type = details.get("action_type", "unknown")
                    target_id = details.get("target_id")
                    target_name = self._get_player_name(game_data, target_id) if target_id else "なし"
                    
                    if role == "Seer":
                        if action_type == "divine":
                            target_role = self._get_player_role(game_data, target_id)
                            export_file.write(f"[{timestamp}] 🔮 占い師 {player_name} が {target_name} を占いました。結果: {target_role}\n")
                    elif role == "Medium":
                        if action_type == "divine":
                            target_role = self._get_player_role(game_data, target_id)
                            export_file.write(f"[{timestamp}] 👻 霊媒師 {player_name} が {target_name} の霊を視ました。結果: {target_role}\n")
                    elif role == "Hunter":
                        if action_type == "shoot":
                            export_file.write(f"[{timestamp}] 🔫 ハンター {player_name} が死亡時に {target_name} を道連れにしました。\n")
                
                # 死亡の処理
                elif event_type == "death":
                    player_name = self._get_player_name(game_data, details.get("player_id"))
                    reason = details.get("reason", "不明")
                    day = details.get("day", 0)
                    
                    export_file.write(f"[{timestamp}] ☠️ {player_name} が {day}日目に {reason} で死亡しました。\n")
                
                # 管理者アクションの処理
                elif event_type == "admin_action":
                    admin_id = details.get("admin_id")
                    admin_name = self._get_player_name(game_data, admin_id) or f"管理者(ID:{admin_id})"
                    action_details = details.get("details", "不明")
                    
                    export_file.write(f"[{timestamp}] ⚙️ 管理者アクション: {admin_name} が {action_details}\n")
                
                # ゲーム開始と終了の処理
                elif event_type == "game_start":
                    export_file.write(f"[{timestamp}] 🎮 ゲームが開始されました。プレイヤー数: {details.get('player_count', 0)}\n")
                elif event_type == "game_end":
                    winner = details.get("winner", "不明")
                    reason = details.get("reason", "不明")
                    duration = details.get("duration_seconds", 0)
                    minutes, seconds = divmod(duration, 60)
                    hours, minutes = divmod(minutes, 60)
                    
                    duration_str = ""
                    if hours > 0:
                        duration_str += f"{hours}時間"
                    if minutes > 0:
                        duration_str += f"{minutes}分"
                    duration_str += f"{seconds}秒"
                    
                    export_file.write(f"[{timestamp}] 🏁 ゲームが終了しました。勝者: {winner}, 理由: {reason}, プレイ時間: {duration_str}\n")
            
            # ゲーム統計情報の追加
            export_file.write("\n-------- ゲーム統計 --------\n")
            # 各役職の勝敗
            roles_stats = {}
            for player in game_data.get('players', []):
                role = player.get('role', '不明')
                if role not in roles_stats:
                    roles_stats[role] = {"count": 0, "win": 0, "lose": 0}
                
                roles_stats[role]["count"] += 1
                if (player.get("team", "") == game_data.get("winner", "")):
                    roles_stats[role]["win"] += 1
                else:
                    roles_stats[role]["lose"] += 1
            
            for role, stats in roles_stats.items():
                win_rate = stats["win"] / stats["count"] * 100 if stats["count"] > 0 else 0
                export_file.write(f"{role}: {stats['count']}人 (勝利: {stats['win']}, 敗北: {stats['lose']}, 勝率: {win_rate:.1f}%)\n")
            
            # 各プレイヤーの行動回数
            export_file.write("\nプレイヤー行動統計:\n")
            player_actions = {}
            for entry in log_entries:
                if entry.get("type") in ["role_action", "vote"]:
                    details = entry.get("details", {})
                    player_id = details.get("player_id", details.get("voter_id"))
                    if player_id:
                        player_name = self._get_player_name(game_data, player_id)
                        if player_name not in player_actions:
                            player_actions[player_name] = {"votes": 0, "role_actions": 0}
                        
                        if entry.get("type") == "vote":
                            player_actions[player_name]["votes"] += 1
                        else:
                            player_actions[player_name]["role_actions"] += 1
            
            for player_name, actions in player_actions.items():
                export_file.write(f"{player_name}: 投票 {actions['votes']}回, 役職アクション {actions['role_actions']}回\n")
        
        return export_filename
    
    def _get_player_name(self, game_data: Dict[str, Any], player_id: Optional[int]) -> Optional[str]:
        """プレイヤーIDからプレイヤー名を取得"""
        if player_id is None:
            return None
        
        for player in game_data.get('players', []):
            if player.get('id') == player_id:
                return player.get('name', f"不明なプレイヤー(ID:{player_id})")
        
        return f"不明なプレイヤー(ID:{player_id})"
    
    def _get_player_role(self, game_data: Dict[str, Any], player_id: Optional[int]) -> Optional[str]:
        """プレイヤーIDからプレイヤーの役職を取得"""
        if player_id is None:
            return None
        
        for player in game_data.get('players', []):
            if player.get('id') == player_id:
                return player.get('role', "不明")
        
        return "不明"
    
    async def get_game_logs(self, guild_id: Optional[int] = None) -> List[str]:
        """
        ギルドのゲームログファイル一覧を取得
        """
        self.ensure_log_directory()
        log_files = []
        
        for filename in os.listdir(self.log_directory):
            if filename.endswith(".log") and filename.startswith("game_"):
                # ギルドIDが指定されている場合、そのギルドのログのみをフィルタリング
                if guild_id is not None:
                    # ログファイルの先頭行を読んでギルドIDを確認
                    try:
                        with open(os.path.join(self.log_directory, filename), "r", encoding="utf-8") as f:
                            first_line = f.readline().strip()
                            log_data = json.loads(first_line)
                            if "details" in log_data and "guild_id" in log_data["details"]:
                                if log_data["details"]["guild_id"] == guild_id:
                                    log_files.append(filename)
                    except (json.JSONDecodeError, IOError):
                        # エラーが発生した場合はこのファイルをスキップ
                        continue
                else:
                    log_files.append(filename)
        
        # 新しい順にソート
        log_files.sort(reverse=True)
        return log_files
    
    async def delete_game_log(self, game_id: str) -> bool:
        """
        特定のゲームのログを削除
        """
        log_file = f"{self.log_directory}/game_{game_id}.log"
        if os.path.exists(log_file):
            try:
                os.remove(log_file)
                return True
            except OSError:
                return False
        return False
