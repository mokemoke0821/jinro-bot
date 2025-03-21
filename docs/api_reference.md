# 人狼Bot API リファレンス

このドキュメントでは、Discord人狼Botの拡張開発者向けのAPI情報を提供します。

## 目次
- [はじめに](#はじめに)
- [基本構造](#基本構造)
- [ゲーム管理API](#ゲーム管理API)
- [役職システムAPI](#役職システムAPI)
- [データ管理API](#データ管理API)
- [コミュニティ機能API](#コミュニティ機能API)
- [カスタム役職の作成](#カスタム役職の作成)
- [プラグイン開発](#プラグイン開発)

## はじめに

Discord人狼Botは拡張可能なアーキテクチャを採用しており、開発者は新しい役職やルール、機能を追加することができます。このAPIリファレンスでは、Botの内部構造や拡張方法について説明します。

### 必要な環境

- Python 3.8以上
- discord.py 2.0以上
- SQLiteデータベース（または他のストレージ）

### 開発の始め方

1. GitHubリポジトリをクローン: `git clone https://github.com/mokemoke0821/jinro-bot.git`
2. 仮想環境を作成: `python -m venv venv`
3. 必要なパッケージをインストール: `pip install -r requirements.txt`
4. 開発用の`.env`ファイルを設定

## 基本構造

Discord人狼Botは以下のディレクトリ構造を持っています：

```
jinro/
├── main.py                # メインエントリーポイント
├── cogs/                  # コマンド処理コグ
│   ├── game_management.py # ゲーム管理コマンド
│   ├── night_actions.py   # 夜の行動コマンド
│   ├── voting.py          # 投票コマンド
│   ├── admin.py           # 管理者コマンド
│   ├── stats.py           # 統計コマンド
│   ├── community.py       # コミュニティ機能コマンド
│   ├── balance.py         # バランス調整コマンド
│   └── ...
├── models/                # データモデル
│   ├── game.py            # ゲーム状態管理
│   ├── player.py          # プレイヤークラス
│   ├── roles/             # 役職クラス
│   ├── feedback.py        # フィードバックモデル
│   ├── suggestion.py      # 提案管理モデル
│   └── ...
├── utils/                 # ユーティリティ
│   ├── config.py          # 設定管理
│   ├── embed_creator.py   # 埋め込みメッセージ作成
│   ├── validators.py      # 入力検証
│   ├── log_manager.py     # ログ管理
│   ├── stats_manager.py   # 統計管理
│   ├── balance_analyzer.py# バランス分析
│   └── ...
└── docs/                  # ドキュメント
    ├── user_guide.md      # ユーザーガイド
    └── api_reference.md   # このAPI参照
```

### 主要クラス

- `GameManager`: ゲーム状態を管理するクラス
- `Player`: プレイヤー情報を管理するクラス
- `BaseRole`: すべての役職の基底クラス
- `StatManager`: 統計データを管理するクラス
- `SuggestionManager`: コミュニティ提案を管理するクラス
- `BalanceAnalyzer`: ゲームバランスを分析するクラス

## ゲーム管理API

ゲーム管理APIは、ゲームの状態やプレイヤーの管理を行うためのインターフェースを提供します。

### GameManager クラス

```python
class GameManager:
    def __init__(self, bot):
        self.bot = bot
        self.games = {}  # サーバーIDをキーとするゲーム情報
    
    async def start_game(self, ctx, role_composition=None):
        """ゲームを開始する準備"""
        # ...
    
    async def add_player(self, ctx, player):
        """プレイヤーをゲームに追加"""
        # ...
    
    async def begin_game(self, ctx):
        """ゲームを開始し、プレイヤーに役職を割り当てる"""
        # ...
    
    async def end_game(self, guild_id, winner=None, force=False):
        """ゲームを終了し、結果を表示する"""
        # ...
    
    async def process_night_action(self, player, target):
        """夜のアクションを処理する"""
        # ...
    
    async def process_vote(self, player, target):
        """投票を処理する"""
        # ...
    
    async def check_win_condition(self, guild_id):
        """勝利条件をチェックする"""
        # ...
```

### 使用例

```python
# ゲームマネージャーの取得
game_manager = bot.get_cog("GameManagementCog")

# ゲームの開始
await game_manager.start_game(ctx)

# プレイヤーの追加
await game_manager.add_player(ctx, player)

# ゲームの開始
await game_manager.begin_game(ctx)

# 夜のアクション処理
await game_manager.process_night_action(player, target)

# 勝利条件チェック
result = await game_manager.check_win_condition(guild_id)
```

## 役職システムAPI

役職システムAPIは、各役職の能力や行動を定義するためのインターフェースを提供します。

### BaseRole クラス

```python
from abc import ABC, abstractmethod

class BaseRole(ABC):
    """すべての役職の基底クラス"""
    
    def __init__(self, player):
        self.player = player
        self.name = self.get_name()
        self.team = self.get_team()
    
    @abstractmethod
    def get_name(self):
        """役職名を返す"""
        pass
    
    @abstractmethod
    def get_description(self):
        """役職の説明を返す"""
        pass
    
    @abstractmethod
    def get_team(self):
        """所属陣営を返す"""
        pass
    
    @abstractmethod
    async def night_action(self, target):
        """夜のアクション"""
        pass
    
    @abstractmethod
    def can_use_night_action(self, game_state):
        """夜のアクションが使用可能かどうか"""
        pass
    
    @abstractmethod
    def win_condition_met(self, game_state):
        """勝利条件を満たしているかどうか"""
        pass
```

### 役職実装例

```python
class Villager(BaseRole):
    """村人クラス"""
    
    def get_name(self):
        return "村人"
    
    def get_description(self):
        return "特殊な能力を持たない一般村民です。"
    
    def get_team(self):
        return "village"
    
    async def night_action(self, target):
        """村人には夜のアクションはない"""
        return None
    
    def can_use_night_action(self, game_state):
        return False
    
    def win_condition_met(self, game_state):
        """村人陣営の勝利条件：人狼が全滅していること"""
        return game_state.are_all_werewolves_dead()
```

## データ管理API

データ管理APIは、ゲーム設定や統計情報を永続化するためのインターフェースを提供します。

### StatsManager クラス

```python
class StatsManager:
    def __init__(self, data_path="data/stats.json"):
        self.data_path = data_path
        self.stats = self._load_stats()
    
    def _load_stats(self):
        """統計データをロードする"""
        # ...
    
    def save_stats(self):
        """統計データを保存する"""
        # ...
    
    def update_game_result(self, game_data):
        """ゲーム結果を更新する"""
        # ...
    
    def get_player_stats(self, user_id):
        """プレイヤーの統計を取得"""
        # ...
    
    def get_role_stats(self):
        """役職ごとの統計を取得"""
        # ...
    
    def get_game_logs(self, limit=100):
        """ゲームログを取得"""
        # ...
```

### 使用例

```python
# 統計マネージャーの取得
stats_manager = bot.get_cog("StatsCog")

# プレイヤー統計の取得
player_stats = stats_manager.get_player_stats(user_id)

# 役職統計の取得
role_stats = stats_manager.get_role_stats()

# ゲーム結果の更新
stats_manager.update_game_result({
    "winner": "village",
    "duration": 1800,  # 30分
    "players": [
        {"user_id": "123", "role": "villager", "survived": True},
        {"user_id": "456", "role": "werewolf", "survived": False}
    ]
})
```

## コミュニティ機能API

コミュニティ機能APIは、提案管理やフィードバック収集のためのインターフェースを提供します。

### SuggestionManager クラス

```python
class SuggestionManager:
    def __init__(self, data_path="data/suggestions.json"):
        self.data_path = data_path
        self.suggestions = {}
        self.load_suggestions()
    
    def load_suggestions(self):
        """提案をロード"""
        # ...
    
    def save_suggestions(self):
        """提案を保存"""
        # ...
    
    def create_suggestion(self, user_id, user_name, title, description, category):
        """新しい提案を作成"""
        # ...
    
    def get_suggestion(self, suggestion_id):
        """IDから提案を取得"""
        # ...
    
    def get_all_suggestions(self, status=None, category=None):
        """提案の一覧を取得（フィルタ可能）"""
        # ...
    
    def update_suggestion(self, suggestion_id, **kwargs):
        """提案を更新"""
        # ...
    
    def vote_suggestion(self, suggestion_id, user_id, vote_type):
        """提案に投票"""
        # ...
    
    def comment_suggestion(self, suggestion_id, user_id, user_name, content):
        """提案にコメント"""
        # ...
```

### バランス分析API

```python
class BalanceAnalyzer:
    def __init__(self, stats_manager):
        self.stats_manager = stats_manager
    
    def analyze_role_win_rates(self, min_games=10):
        """役職ごとの勝率を分析"""
        # ...
    
    def analyze_team_balance(self):
        """陣営バランスを分析"""
        # ...
    
    def generate_win_rate_chart(self):
        """役職勝率のグラフを生成"""
        # ...
    
    def generate_team_win_chart(self):
        """陣営勝率のグラフを生成"""
        # ...
    
    def suggest_role_adjustments(self):
        """役職バランス調整の提案"""
        # ...
    
    def generate_detailed_report(self, role_analysis, team_analysis, suggestions):
        """詳細なレポートテキストを生成"""
        # ...
```

## カスタム役職の作成

カスタム役職を作成するには、`BaseRole`クラスを継承し、必要なメソッドを実装します。

### 基本的な手順

1. `models/roles/`ディレクトリに新しいPythonファイルを作成
2. `BaseRole`クラスを継承した新しい役職クラスを定義
3. 抽象メソッドをすべて実装
4. 役職を登録

### 実装例

```python
# models/roles/custom_role.py
from models.roles.base_role import BaseRole

class CustomRole(BaseRole):
    """カスタム役職クラス"""
    
    def get_name(self):
        return "カスタム役職"
    
    def get_description(self):
        return "カスタム役職の説明文です。"
    
    def get_team(self):
        return "village"  # 村人陣営の場合
    
    async def night_action(self, target):
        """夜のアクション実装"""
        # カスタムの能力を実装
        return {"success": True, "message": "アクション成功"}
    
    def can_use_night_action(self, game_state):
        """夜のアクションが使用可能かどうか"""
        return True
    
    def win_condition_met(self, game_state):
        """勝利条件の実装"""
        # カスタムの勝利条件を実装
        return game_state.are_all_werewolves_dead()
```

### 役職の登録方法

役職を登録するために、`cogs/role_composer.py`の`ROLE_CLASSES`ディクショナリに追加します。

```python
# cogs/role_composer.py の一部
from models.roles.villager import Villager
from models.roles.werewolf import Werewolf
from models.roles.seer import Seer
from models.roles.custom_role import CustomRole  # カスタム役職をインポート

ROLE_CLASSES = {
    "villager": Villager,
    "werewolf": Werewolf,
    "seer": Seer,
    # ...
    "custom_role": CustomRole  # カスタム役職を登録
}
```

## プラグイン開発

プラグイン開発では、新しい機能や拡張を実装するためのディスコード.pyのCogシステムを使用します。

### プラグインの基本構造

```python
# cogs/custom_plugin.py
import discord
from discord.ext import commands

class CustomPluginCog(commands.Cog):
    """カスタムプラグインのCog"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="custom")
    async def custom_command(self, ctx):
        """カスタムコマンドの実装"""
        await ctx.send("カスタムコマンドが実行されました！")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """メッセージイベントのリスナー"""
        # メッセージイベントを処理
        pass

async def setup(bot):
    await bot.add_cog(CustomPluginCog(bot))
```

### プラグインの登録

`main.py`の`load_extensions`関数に新しいCogを追加します：

```python
# main.py の一部
async def load_extensions():
    """すべてのCogを読み込む"""
    cogs = [
        'cogs.game_management',
        'cogs.night_actions',
        'cogs.day_actions',
        'cogs.voting',
        'cogs.admin',
        'cogs.stats',
        'cogs.feedback',
        'cogs.rules_manager',
        'cogs.role_composer',
        'cogs.custom_plugin',  # カスタムプラグインを追加
        'utils.role_balancer'
    ]
    
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f'Loaded extension: {cog}')
        except Exception as e:
            print(f'Failed to load extension {cog}: {e}')
```

### ゲームイベントフック

ゲームの様々な段階で処理を追加するためのイベントフックを実装できます：

```python
# ゲーム開始時のイベントフック
@commands.Cog.listener()
async def on_game_start(self, ctx, game_state):
    """ゲーム開始時のイベントハンドラ"""
    channel = ctx.channel
    await channel.send("ゲームが開始されました！カスタムプラグインがアクティブです。")

# 夜フェーズ開始時のイベントフック
@commands.Cog.listener()
async def on_night_phase_start(self, ctx, game_state):
    """夜フェーズ開始時のイベントハンドラ"""
    # 夜フェーズのカスタム処理
    pass

# プレイヤー死亡時のイベントフック
@commands.Cog.listener()
async def on_player_death(self, ctx, player, reason):
    """プレイヤー死亡時のイベントハンドラ"""
    # プレイヤー死亡時のカスタム処理
    pass
```

### コマンド拡張の例

特定のコマンドを拡張するには、既存のCogの機能を利用できます：

```python
@commands.command(name="custom_role_info")
async def custom_role_info(self, ctx, role_name=None):
    """役職情報を表示するカスタムコマンド"""
    
    role_composer = self.bot.get_cog("RoleComposerCog")
    if not role_composer:
        await ctx.send("役職コンポーザーCogが読み込まれていません。")
        return
    
    if not role_name:
        # 役職一覧を表示
        roles = role_composer.get_available_roles()
        embed = discord.Embed(
            title="利用可能な役職一覧",
            description="すべての役職一覧です。詳細は `!custom_role_info [役職名]` で確認できます。",
            color=discord.Color.blue()
        )
        
        for role in roles:
            embed.add_field(name=role, value=f"`!custom_role_info {role}` で詳細を表示", inline=True)
            
        await ctx.send(embed=embed)
        return
    
    # 特定の役職の情報を表示
    role_class = role_composer.get_role_class(role_name)
    if not role_class:
        await ctx.send(f"役職 `{role_name}` は存在しません。")
        return
    
    # 役職情報の表示ロジック
    # ...
```

以上がDiscord人狼BotのAPI概要です。より詳細な情報やサンプルコードについては、GitHubリポジトリをご参照ください。
