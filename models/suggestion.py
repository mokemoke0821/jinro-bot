"""
コミュニティの提案を管理するモデル
"""
import datetime
import uuid
import json
from typing import Dict, List, Optional, Any, Union

class Suggestion:
    """ユーザー提案を管理するクラス"""
    
    def __init__(self, user_id: str, user_name: str, title: str, description: str, category: str):
        self.id = str(uuid.uuid4())[:8]  # 短いID
        self.user_id = user_id
        self.user_name = user_name
        self.title = title
        self.description = description
        self.category = category
        self.created_at = datetime.datetime.now()
        self.status = "pending"  # pending, approved, rejected, implemented
        self.votes: Dict[str, List[str]] = {"up": [], "down": []}
        self.comments: List[Dict[str, Any]] = []
        
    def add_vote(self, user_id: str, vote_type: str) -> bool:
        """投票を追加"""
        # 既存の投票を削除
        if user_id in self.votes["up"]:
            self.votes["up"].remove(user_id)
        if user_id in self.votes["down"]:
            self.votes["down"].remove(user_id)
        
        # 新しい投票を追加
        if vote_type in ["up", "down"]:
            self.votes[vote_type].append(user_id)
            return True
        return False
            
    def add_comment(self, user_id: str, user_name: str, content: str) -> Dict[str, Any]:
        """コメントを追加"""
        comment = {
            "user_id": user_id,
            "user_name": user_name,
            "content": content,
            "created_at": datetime.datetime.now()
        }
        self.comments.append(comment)
        return comment
        
    def update_status(self, status: str) -> bool:
        """ステータスを更新"""
        valid_statuses = ["pending", "approved", "rejected", "implemented"]
        if status in valid_statuses:
            self.status = status
            return True
        return False
            
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "votes": self.votes,
            "comments": self.comments,
            "vote_score": len(self.votes["up"]) - len(self.votes["down"])
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Suggestion':
        """辞書からSuggestionオブジェクトを作成"""
        suggestion = cls(
            data["user_id"],
            data["user_name"],
            data["title"],
            data["description"],
            data["category"]
        )
        suggestion.id = data["id"]
        suggestion.created_at = datetime.datetime.fromisoformat(data["created_at"])
        suggestion.status = data["status"]
        suggestion.votes = data["votes"]
        suggestion.comments = data["comments"]
        return suggestion

class SuggestionManager:
    """提案を管理するクラス"""
    
    def __init__(self, data_path: str = "data/suggestions.json"):
        self.data_path = data_path
        self.suggestions: Dict[str, Suggestion] = {}
        self.load_suggestions()
        
    def load_suggestions(self) -> None:
        """ファイルから提案をロード"""
        import os
        if not os.path.exists(self.data_path):
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump([], f)
            return
            
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                suggestions_data = json.load(f)
                
            for data in suggestions_data:
                suggestion = Suggestion.from_dict(data)
                self.suggestions[suggestion.id] = suggestion
        except (json.JSONDecodeError, FileNotFoundError):
            self.suggestions = {}
            
    def save_suggestions(self) -> None:
        """提案をファイルに保存"""
        suggestions_data = [suggestion.to_dict() for suggestion in self.suggestions.values()]
        
        import os
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(suggestions_data, f, ensure_ascii=False, indent=2)
        
    def save_suggestion(self, suggestion: Suggestion) -> None:
        """提案を保存"""
        self.suggestions[suggestion.id] = suggestion
        self.save_suggestions()
        
    def create_suggestion(self, user_id: str, user_name: str, title: str, description: str, category: str) -> Suggestion:
        """新しい提案を作成"""
        suggestion = Suggestion(user_id, user_name, title, description, category)
        self.suggestions[suggestion.id] = suggestion
        self.save_suggestions()
        return suggestion
        
    def get_suggestion(self, suggestion_id: str) -> Optional[Suggestion]:
        """IDから提案を取得"""
        return self.suggestions.get(suggestion_id)
        
    def get_all_suggestions(self, status: Optional[str] = None, category: Optional[str] = None) -> List[Suggestion]:
        """提案の一覧を取得（フィルタ可能）"""
        suggestions = list(self.suggestions.values())
        
        # ステータスでフィルタ
        if status:
            suggestions = [s for s in suggestions if s.status == status]
            
        # カテゴリでフィルタ
        if category:
            suggestions = [s for s in suggestions if s.category == category]
            
        # 投票スコア順にソート
        suggestions.sort(key=lambda s: len(s.votes["up"]) - len(s.votes["down"]), reverse=True)
        
        return suggestions
        
    def update_suggestion(self, suggestion_id: str, **kwargs) -> Optional[Suggestion]:
        """提案を更新"""
        suggestion = self.get_suggestion(suggestion_id)
        if not suggestion:
            return None
            
        # 更新可能なフィールド
        updatable_fields = ["title", "description", "category", "status"]
        
        # フィールドを更新
        for field, value in kwargs.items():
            if field in updatable_fields and hasattr(suggestion, field):
                setattr(suggestion, field, value)
                
        self.save_suggestions()
        return suggestion
        
    def vote_suggestion(self, suggestion_id: str, user_id: str, vote_type: str) -> Optional[Suggestion]:
        """提案に投票"""
        suggestion = self.get_suggestion(suggestion_id)
        if not suggestion:
            return None
            
        suggestion.add_vote(user_id, vote_type)
        self.save_suggestions()
        return suggestion
        
    def comment_suggestion(self, suggestion_id: str, user_id: str, user_name: str, content: str) -> Optional[Suggestion]:
        """提案にコメント"""
        suggestion = self.get_suggestion(suggestion_id)
        if not suggestion:
            return None
            
        suggestion.add_comment(user_id, user_name, content)
        self.save_suggestions()
        return suggestion
        
    def delete_suggestion(self, suggestion_id: str) -> bool:
        """提案を削除"""
        if suggestion_id in self.suggestions:
            del self.suggestions[suggestion_id]
            self.save_suggestions()
            return True
        return False
