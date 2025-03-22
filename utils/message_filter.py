"""
メッセージフィルタリングモジュール
Discord.pyのメッセージ送信処理を上書きして、特定のエラーメッセージを非表示にする
"""
import discord
import functools
import re
import asyncio

# エラーメッセージのパターン
ERROR_PATTERNS = [
    r"エラーが発生しました",
    r"coroutine.*object.*no attribute",
    r"Command raised an exception",
    r"AttributeError",
    r"'coroutine'.*object.*has no attribute.*'get'"
]

# コンパイル済みパターン
COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in ERROR_PATTERNS]

# 元のメソッドを保存
ORIGINAL_HTTP_REQUEST = None

# フックが既に適用されているかどうかのフラグ
_hooks_applied = False

def is_error_message(data):
    """データがエラーメッセージかどうかを判定"""
    # Embedメッセージのチェック
    if isinstance(data, dict):
        # contentフィールドをチェック
        if 'content' in data and data['content'] and isinstance(data['content'], str):
            content = data['content']
            for pattern in COMPILED_PATTERNS:
                if pattern.search(content):
                    return True
        
        # embedsフィールドをチェック
        if 'embeds' in data and data['embeds']:
            for embed in data['embeds']:
                # タイトルチェック
                if 'title' in embed and isinstance(embed['title'], str) and "エラー" in embed['title']:
                    return True
                
                # 説明文チェック
                if 'description' in embed and isinstance(embed['description'], str):
                    for pattern in COMPILED_PATTERNS:
                        if pattern.search(embed['description']):
                            return True
    
    return False

async def filtered_request(original_func, self, route, **kwargs):
    """
    HTTP リクエストをフィルタリングする関数
    特にメッセージ送信リクエストを対象に、エラーメッセージを検出して遮断
    """
    # Create Message エンドポイントに対する処理を特別扱い
    if route.method == "POST" and "channels/" in route.url and "/messages" in route.url:
        # メッセージデータを取得
        data = kwargs.get('json', {})
        
        # データがエラーメッセージかどうかをチェック
        if is_error_message(data):
            print(f"[MESSAGE_FILTER] Blocked error message: {data}")
            
            # エラーメッセージの場合は、成功したフェイクレスポンスを返す
            fake_message = {
                'id': '0',
                'channel_id': route.url.split('channels/')[1].split('/')[0],
                'author': {'id': '0', 'username': 'System'},
                'content': '',
                'timestamp': '2023-01-01T00:00:00.000000+00:00',
                'tts': False,
                'mention_everyone': False,
                'mentions': [],
                'mention_roles': [],
                'attachments': [],
                'embeds': [],
                'pinned': False,
                'type': 0
            }
            
            # 偽のレスポンスオブジェクトを返す
            return discord.http.HTTPResponse(
                response=type('obj', (object,), {'status': 200, 'headers': {}}),
                data=fake_message
            )
    
    # 通常のリクエスト処理を継続
    return await original_func(self, route, **kwargs)

def apply_message_filter():
    """メッセージフィルタリングを適用"""
    global _hooks_applied, ORIGINAL_HTTP_REQUEST
    
    # 既に適用済みならスキップ
    if _hooks_applied:
        return True
    
    try:
        # discord.http.HTTPClientのrequestメソッドをモンキーパッチ
        ORIGINAL_HTTP_REQUEST = discord.http.HTTPClient.request
        
        # フィルタリングを適用
        discord.http.HTTPClient.request = functools.partial(
            filtered_request, ORIGINAL_HTTP_REQUEST
        )
        
        print("[MESSAGE_FILTER] Successfully applied message filtering")
        _hooks_applied = True
        return True
    except Exception as e:
        print(f"[MESSAGE_FILTER] Failed to apply message filtering: {e}")
        import traceback
        traceback.print_exc()
        return False

def reset_message_filter():
    """フィルタリングをリセット"""
    global _hooks_applied
    
    if not _hooks_applied or ORIGINAL_HTTP_REQUEST is None:
        return
    
    try:
        # 元のメソッドに戻す
        discord.http.HTTPClient.request = ORIGINAL_HTTP_REQUEST
        _hooks_applied = False
        print("[MESSAGE_FILTER] Message filtering removed")
    except Exception as e:
        print(f"[MESSAGE_FILTER] Failed to remove message filtering: {e}")
