import uuid
import datetime
import json
import os
from typing import List, Dict, Any, Optional


class Feedback:
    """フィードバックを表すモデルクラス"""
    
    # フィードバックの状態
    STATUS_NEW = "new"         # 新規
    STATUS_CONFIRMED = "confirmed"  # 確認済み
    STATUS_IN_PROGRESS = "in_progress"  # 対応中
    STATUS_RESOLVED = "resolved"  # 解決済み
    STATUS_CLOSED = "closed"   # クローズ
    
    # フィードバックの種類
    TYPE_BUG = "bug"           # バグ報告
    TYPE_FEATURE = "feature"   # 機能リクエスト
    TYPE_OPINION = "opinion"   # 意見・感想
    
    # フィードバックの優先度
    PRIORITY_LOW = "low"       # 低
    PRIORITY_MEDIUM = "medium" # 中
    PRIORITY_HIGH = "high"     # 高
    PRIORITY_CRITICAL = "critical"  # 緊急
    
    def __init__(self, 
                 user_id: int, 
                 guild_id: int, 
                 feedback_type: str, 
                 content: str, 
                 priority: str = PRIORITY_MEDIUM,
                 feedback_id: Optional[str] = None):
        """
        フィードバックオブジェクトを初期化
        
        Parameters:
        -----------
        user_id: int
            フィードバックを送信したユーザーのID
        guild_id: int
            フィードバックが送信されたサーバーのID
        feedback_type: str
            フィードバックの種類 (bug, feature, opinion)
        content: str
            フィードバックの内容
        priority: str, optional
            優先度 (low, medium, high, critical), デフォルトは medium
        feedback_id: str, optional
            フィードバックID（指定されない場合は自動生成）
        """
        self.id = feedback_id or str(uuid.uuid4())
        self.user_id = user_id
        self.guild_id = guild_id
        self.type = feedback_type
        self.content = content
        self.priority = priority
        self.status = self.STATUS_NEW
        self.created_at = datetime.datetime.now().isoformat()
        self.updated_at = self.created_at
        self.comments = []  # 管理者のコメントなど
        self.response = None  # ユーザーへのレスポンス
    
    def to_dict(self) -> Dict[str, Any]:
        """フィードバックをdict形式に変換"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "guild_id": self.guild_id,
            "type": self.type,
            "content": self.content,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "comments": self.comments,
            "response": self.response
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Feedback':
        """dict形式からフィードバックオブジェクトを生成"""
        feedback = cls(
            user_id=data["user_id"],
            guild_id=data["guild_id"],
            feedback_type=data["type"],
            content=data["content"],
            priority=data["priority"],
            feedback_id=data["id"]
        )
        feedback.status = data["status"]
        feedback.created_at = data["created_at"]
        feedback.updated_at = data["updated_at"]
        feedback.comments = data.get("comments", [])
        feedback.response = data.get("response")
        return feedback
    
    def add_comment(self, user_id: int, content: str):
        """フィードバックにコメントを追加"""
        comment = {
            "user_id": user_id,
            "content": content,
            "timestamp": datetime.datetime.now().isoformat()
        }
        self.comments.append(comment)
        self.updated_at = datetime.datetime.now().isoformat()
    
    def set_response(self, content: str):
        """ユーザーへのレスポンスを設定"""
        self.response = {
            "content": content,
            "timestamp": datetime.datetime.now().isoformat()
        }
        self.updated_at = datetime.datetime.now().isoformat()
    
    def update_status(self, new_status: str):
        """フィードバックのステータスを更新"""
        if new_status in [self.STATUS_NEW, self.STATUS_CONFIRMED, 
                         self.STATUS_IN_PROGRESS, self.STATUS_RESOLVED, 
                         self.STATUS_CLOSED]:
            self.status = new_status
            self.updated_at = datetime.datetime.now().isoformat()
            return True
        return False
    
    def update_priority(self, new_priority: str):
        """フィードバックの優先度を更新"""
        if new_priority in [self.PRIORITY_LOW, self.PRIORITY_MEDIUM, 
                           self.PRIORITY_HIGH, self.PRIORITY_CRITICAL]:
            self.priority = new_priority
            self.updated_at = datetime.datetime.now().isoformat()
            return True
        return False


class FeedbackManager:
    """フィードバックの保存と読み込みを管理するクラス"""
    
    def __init__(self):
        """フィードバックマネージャを初期化"""
        self.feedback_directory = "data/feedback"
        self.feedback_file = f"{self.feedback_directory}/feedback.json"
        self.ensure_directory()
    
    def ensure_directory(self):
        """フィードバックディレクトリが存在することを確認"""
        if not os.path.exists(self.feedback_directory):
            os.makedirs(self.feedback_directory)
        
        if not os.path.exists(self.feedback_file):
            with open(self.feedback_file, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
    
    def save_feedback(self, feedback: Feedback) -> bool:
        """フィードバックを保存する"""
        all_feedback = self.load_all_feedback()
        
        # 既存のフィードバックを更新、または新しいフィードバックを追加
        for i, fb in enumerate(all_feedback):
            if fb["id"] == feedback.id:
                all_feedback[i] = feedback.to_dict()
                break
        else:
            all_feedback.append(feedback.to_dict())
        
        try:
            with open(self.feedback_file, "w", encoding="utf-8") as f:
                json.dump(all_feedback, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"フィードバック保存エラー: {e}")
            return False
    
    def load_all_feedback(self) -> List[Dict[str, Any]]:
        """すべてのフィードバックを読み込む"""
        try:
            with open(self.feedback_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def get_feedback_by_id(self, feedback_id: str) -> Optional[Feedback]:
        """IDからフィードバックを取得する"""
        all_feedback = self.load_all_feedback()
        
        for fb_data in all_feedback:
            if fb_data["id"] == feedback_id:
                return Feedback.from_dict(fb_data)
        
        return None
    
    def get_feedback_by_user(self, user_id: int) -> List[Feedback]:
        """ユーザーIDからフィードバックを取得する"""
        all_feedback = self.load_all_feedback()
        user_feedback = []
        
        for fb_data in all_feedback:
            if fb_data["user_id"] == user_id:
                user_feedback.append(Feedback.from_dict(fb_data))
        
        return user_feedback
    
    def get_feedback_by_guild(self, guild_id: int) -> List[Feedback]:
        """サーバーIDからフィードバックを取得する"""
        all_feedback = self.load_all_feedback()
        guild_feedback = []
        
        for fb_data in all_feedback:
            if fb_data["guild_id"] == guild_id:
                guild_feedback.append(Feedback.from_dict(fb_data))
        
        return guild_feedback
    
    def get_feedback_by_status(self, status: str) -> List[Feedback]:
        """ステータスからフィードバックを取得する"""
        all_feedback = self.load_all_feedback()
        status_feedback = []
        
        for fb_data in all_feedback:
            if fb_data["status"] == status:
                status_feedback.append(Feedback.from_dict(fb_data))
        
        return status_feedback
    
    def delete_feedback(self, feedback_id: str) -> bool:
        """フィードバックを削除する"""
        all_feedback = self.load_all_feedback()
        
        for i, fb in enumerate(all_feedback):
            if fb["id"] == feedback_id:
                all_feedback.pop(i)
                
                try:
                    with open(self.feedback_file, "w", encoding="utf-8") as f:
                        json.dump(all_feedback, f, ensure_ascii=False, indent=2)
                    return True
                except Exception as e:
                    print(f"フィードバック削除エラー: {e}")
                    return False
        
        return False  # フィードバックが見つからなかった
