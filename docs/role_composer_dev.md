# 役職構成管理機能の実装詳細

このドキュメントは、Discord人狼Botの役職構成管理機能の実装詳細について説明します。

## 概要

役職構成管理機能は、サーバーごとの役職構成を管理するためのシステムです。この機能は、`direct_compose.py`モジュールに実装されており、Botの起動時に自動的に登録されます。

## ファイル構造

- `direct_compose.py` - 役職構成管理の主要コード（コマンド処理、設定の読み込み/保存など）
- `data/role_config_[guild_id].json` - サーバーごとの役職構成設定保存ファイル

## 主要コンポーネント

### 1. プリセットの定義

`PRESETS`辞書で定義されています。各プリセットには、名前、説明、そして人数ごとの役職構成が含まれています。

```python
PRESETS = {
    "standard": {
        "name": "標準",
        "description": "基本的な役職構成です。",
        "compositions": {
            "5": {"村人": 2, "人狼": 1, "占い師": 1, "狩人": 1},
            # 他の人数の構成...
        }
    },
    # 他のプリセット...
}
```

### 2. 設定の保存と読み込み

設定はサーバー（ギルド）ごとにJSON形式で保存されます。

```python
async def load_config(guild_id):
    """サーバー固有の役職構成設定を読み込む"""
    config_path = os.path.join(CONFIG_DIR, f"role_config_{guild_id}.json")
    # JSONファイルから設定を読み込み

async def save_config(guild_id, config):
    """サーバー固有の役職構成設定を保存する"""
    config_path = os.path.join(CONFIG_DIR, f"role_config_{guild_id}.json")
    # 設定をJSONファイルに保存
```

### 3. バランスチェック

`check_balance`関数で役職構成のバランスをチェックし、不均衡がある場合はエラーメッセージを返します。

```python
def check_balance(roles):
    """役職構成のバランスをチェックする"""
    # 役職の合計数を計算
    # 陣営ごとの人数を計算
    # 最低限の役職確認
    # 比率チェック
    # その他の特殊ルール
    # 結果を返す（True/Falseとメッセージ）
```

### 4. コマンド処理

`setup_commands`関数でBotにコマンドを登録し、各サブコマンド（help, presets, apply, custom, force, recommend, show）の処理を実装しています。

```python
def setup_commands(bot):
    """直接コマンドをBotに登録"""
    # 重複登録チェック
    # メインコマンドの登録
    # サブコマンド処理関数の定義
    # 重複登録防止フラグの設定
```

## データフロー

1. ユーザーがコマンドを実行
2. Botが`on_message`イベントでコマンドを検出
3. `compose_command`メインハンドラーがサブコマンドと引数を解析
4. 対応するサブコマンド処理関数が呼び出される
5. 必要に応じて設定の読み込み・保存・バランスチェックが行われる
6. 結果がユーザーに表示される

## エラーハンドリング

- コマンドパラメーターのバリデーション
- 役職名・人数のチェック
- バランス検証
- 設定ファイルの読み書きエラー処理
- 重複コマンド実行の防止

## 拡張方法

### 新しいプリセットの追加

`PRESETS`辞書に新しいプリセットを追加します：

```python
PRESETS["new_preset"] = {
    "name": "新しいプリセット",
    "description": "新しいプリセットの説明",
    "compositions": {
        "7": {"村人": 2, "人狼": 2, "占い師": 1, "狩人": 1, "狂人": 1},
        # 他の人数の構成...
    }
}
```

### 新しい役職の追加

1. `VALID_ROLES`リストに新しい役職を追加
2. 必要に応じて`ROLE_GROUPS`の適切な陣営に役職を追加
3. `check_balance`関数に特殊ルールがある場合は追加
4. プリセットに新しい役職を含めるように更新

### バランスチェックルールの変更

`check_balance`関数内の条件を修正して、新しいバランスルールを実装します。

## セキュリティと考慮事項

- コマンドは管理者権限を持つユーザーのみが実行できるようにしています
- 設定ファイルはサーバーIDを含む名前で保存され、サーバー間で設定が混同されることを防いでいます
- 入力値（役職名、人数など）は常に検証され、想定外の値が設定されることを防いでいます
- エラーハンドリングを徹底し、例外が発生してもBotが停止しないようにしています

## 今後の改善点

1. UI改善（ボタンやドロップダウンメニューの活用）
2. ゲーム開始時の自動役職割り当て機能との連携強化
3. バランス調整アルゴリズムの高度化
4. カスタム役職の追加サポート
5. 役職構成保存・読み込み機能
6. データベース操作の堅牢化
7. ログ出力の充実化
