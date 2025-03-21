"""
DMフォールバックモジュール
DMが届かない場合の代替表示機能を提供
"""
import discord
from discord.ext import commands

class DMFallbackSystem:
    """DMフォールバックシステムクラス"""
    
    def __init__(self, bot):
        """初期化"""
        self.bot = bot
        # DMチャンネルのマッピング {user_id: channel_id}
        self.fallback_channels = {}
    
    async def create_fallback_channel(self, guild, member):
        """
        ユーザー専用のチャンネルを作成
        
        Parameters:
        -----------
        guild: discord.Guild
            サーバーオブジェクト
        member: discord.Member
            メンバーオブジェクト
            
        Returns:
        --------
        discord.TextChannel or None
            作成されたチャンネル、または失敗した場合はNone
        """
        try:
            # チャンネル権限を設定
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                member: discord.PermissionOverwrite(read_messages=True)
            }
            
            # カテゴリが存在するかチェック
            category = discord.utils.get(guild.categories, name="人狼ゲームDM")
            if not category:
                # カテゴリを作成
                category = await guild.create_category(
                    "人狼ゲームDM", 
                    overwrites={
                        guild.default_role: discord.PermissionOverwrite(read_messages=False)
                    }
                )
            
            # チャンネル名（特殊文字を除去）
            channel_name = f"dm-{member.display_name}"[:32].replace(' ', '-').lower()
            
            # チャンネルを作成
            channel = await guild.create_text_channel(
                channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"{member.display_name}のDM代替チャンネル"
            )
            
            # マッピングに保存
            self.fallback_channels[str(member.id)] = channel.id
            
            return channel
        
        except discord.Forbidden:
            print(f"Failed to create fallback channel for {member.display_name}: Insufficient permissions")
            return None
        
        except Exception as e:
            print(f"Failed to create fallback channel for {member.display_name}: {str(e)}")
            return None
    
    async def send_dm(self, user, content=None, embed=None, file=None):
        """
        DMを送信、失敗した場合はフォールバックを使用
        
        Parameters:
        -----------
        user: discord.User
            DMを送るユーザー
        content: str
            送信するテキスト
        embed: discord.Embed
            送信する埋め込み
        file: discord.File
            送信するファイル
            
        Returns:
        --------
        bool, discord.Message or None
            成功したか否か、送信されたメッセージ
        """
        # DMを試みる
        try:
            if content and embed and file:
                dm = await user.send(content=content, embed=embed, file=file)
            elif content and embed:
                dm = await user.send(content=content, embed=embed)
            elif content and file:
                dm = await user.send(content=content, file=file)
            elif embed and file:
                dm = await user.send(embed=embed, file=file)
            elif content:
                dm = await user.send(content=content)
            elif embed:
                dm = await user.send(embed=embed)
            elif file:
                dm = await user.send(file=file)
            else:
                return False, None
                
            return True, dm
        
        except discord.Forbidden:
            # DMが送れない場合
            return False, None
        
        except Exception as e:
            print(f"Failed to send DM to {user.name}: {str(e)}")
            return False, None
    
    async def send_fallback(self, member, content=None, embed=None, file=None):
        """
        フォールバックチャンネルを使用してメッセージを送信
        
        Parameters:
        -----------
        member: discord.Member
            フォールバックメッセージを送るメンバー
        content: str
            送信するテキスト
        embed: discord.Embed
            送信する埋め込み
        file: discord.File
            送信するファイル
            
        Returns:
        --------
        bool, discord.Message or None
            成功したか否か、送信されたメッセージ
        """
        # 既存のフォールバックチャンネルがあるか確認
        channel_id = self.fallback_channels.get(str(member.id))
        channel = None
        
        if channel_id:
            channel = self.bot.get_channel(channel_id)
        
        # チャンネルが存在しない場合は新規作成
        if not channel and member.guild:
            channel = await self.create_fallback_channel(member.guild, member)
        
        if not channel:
            return False, None
        
        # メッセージを送信
        try:
            notification = f"{member.mention} **DMの代わりに表示されているメッセージです**"
            
            if content and embed and file:
                msg = await channel.send(notification, content=content, embed=embed, file=file)
            elif content and embed:
                msg = await channel.send(notification, content=content, embed=embed)
            elif content and file:
                msg = await channel.send(notification, content=content, file=file)
            elif embed and file:
                msg = await channel.send(notification, embed=embed, file=file)
            elif content:
                msg = await channel.send(notification, content=content)
            elif embed:
                msg = await channel.send(notification, embed=embed)
            elif file:
                msg = await channel.send(notification, file=file)
            else:
                return False, None
                
            return True, msg
            
        except Exception as e:
            print(f"Failed to send fallback message to {member.display_name}: {str(e)}")
            return False, None
    
    async def send_to_player(self, member, content=None, embed=None, file=None):
        """
        プレイヤーにメッセージを送信（DMまたはフォールバック）
        
        Parameters:
        -----------
        member: discord.Member
            メッセージを送るメンバー
        content: str
            送信するテキスト
        embed: discord.Embed
            送信する埋め込み
        file: discord.File
            送信するファイル
            
        Returns:
        --------
        bool
            成功したか否か
        """
        # DMを試す
        success, message = await self.send_dm(member, content, embed, file)
        
        # DMが失敗したらフォールバックを使用
        if not success:
            success, message = await self.send_fallback(member, content, embed, file)
        
        return success
    
    async def cleanup_fallback_channels(self, guild):
        """
        不要になったフォールバックチャンネルを削除
        
        Parameters:
        -----------
        guild: discord.Guild
            チャンネルがあるサーバー
        """
        # カテゴリを探す
        category = discord.utils.get(guild.categories, name="人狼ゲームDM")
        if not category:
            return
        
        # 7日以上経過したチャンネルを削除
        import datetime
        cutoff_time = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        
        for channel in category.text_channels:
            try:
                # 最後のメッセージの時間を取得
                messages = await channel.history(limit=1).flatten()
                if not messages:
                    await channel.delete(reason="不要なDMフォールバックチャンネル")
                    continue
                
                last_message = messages[0]
                if last_message.created_at < cutoff_time:
                    await channel.delete(reason="7日以上使用されていないDMフォールバックチャンネル")
            
            except Exception as e:
                print(f"Failed to clean up channel {channel.name}: {str(e)}")
