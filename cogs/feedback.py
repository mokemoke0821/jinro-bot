import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List
import asyncio
import datetime

from models.feedback import Feedback, FeedbackManager
from utils.embed_creator import EmbedCreator
from utils.validators import is_admin


class FeedbackView(discord.ui.View):
    """フィードバックを送信するためのビュー"""
    
    def __init__(self, author_id: int):
        super().__init__(timeout=300)  # 5分のタイムアウト
        self.author_id = author_id
        self.feedback_type = None
        self.content = None
        self.priority = Feedback.PRIORITY_MEDIUM
    
    @discord.ui.select(
        placeholder="フィードバックの種類を選択してください",
        options=[
            discord.SelectOption(
                label="バグ報告",
                description="不具合や正常に動作しない機能について報告",
                emoji="🐛",
                value=Feedback.TYPE_BUG
            ),
            discord.SelectOption(
                label="機能リクエスト",
                description="新しい機能や改善の提案",
                emoji="💡",
                value=Feedback.TYPE_FEATURE
            ),
            discord.SelectOption(
                label="意見・感想",
                description="Botに関する一般的な意見や感想",
                emoji="💬",
                value=Feedback.TYPE_OPINION
            )
        ]
    )
    async def select_type(self, interaction: discord.Interaction, select: discord.ui.Select):
        """フィードバックの種類を選択"""
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("このメニューは他の人は操作できません。", ephemeral=True)
            return
        
        self.feedback_type = select.values[0]
        await interaction.response.send_message(f"フィードバックの種類: **{select.values[0]}** を選択しました。\n"
                                              f"次に、フィードバックの内容を入力してください。", ephemeral=True)
    
    @discord.ui.select(
        placeholder="優先度を選択してください",
        options=[
            discord.SelectOption(
                label="低",
                description="影響が小さい問題や単なる提案",
                emoji="🟢",
                value=Feedback.PRIORITY_LOW
            ),
            discord.SelectOption(
                label="中",
                description="一般的な問題や機能リクエスト",
                emoji="🟡",
                value=Feedback.PRIORITY_MEDIUM
            ),
            discord.SelectOption(
                label="高",
                description="ゲームプレイに影響する重要な問題",
                emoji="🟠",
                value=Feedback.PRIORITY_HIGH
            ),
            discord.SelectOption(
                label="緊急",
                description="ゲームが全く機能しないなどの致命的な問題",
                emoji="🔴",
                value=Feedback.PRIORITY_CRITICAL
            )
        ]
    )
    async def select_priority(self, interaction: discord.Interaction, select: discord.ui.Select):
        """フィードバックの優先度を選択"""
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("このメニューは他の人は操作できません。", ephemeral=True)
            return
        
        self.priority = select.values[0]
        
        priority_labels = {
            Feedback.PRIORITY_LOW: "低",
            Feedback.PRIORITY_MEDIUM: "中",
            Feedback.PRIORITY_HIGH: "高",
            Feedback.PRIORITY_CRITICAL: "緊急"
        }
        
        await interaction.response.send_message(f"優先度: **{priority_labels[select.values[0]]}** を選択しました。", ephemeral=True)
    
    @discord.ui.button(label="フィードバックを送信", style=discord.ButtonStyle.primary, emoji="📤")
    async def submit(self, interaction: discord.Interaction, button: discord.ui.Button):
        """フィードバックを送信するボタン"""
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("このボタンは他の人は操作できません。", ephemeral=True)
            return
        
        if not self.feedback_type:
            await interaction.response.send_message("フィードバックの種類を選択してください。", ephemeral=True)
            return
        
        if not self.content:
            # モーダルを表示して内容を入力させる
            await interaction.response.send_modal(FeedbackModal(self))
        else:
            # 送信確認
            embed = discord.Embed(
                title="フィードバック送信確認",
                description="以下の内容で送信しますか？",
                color=discord.Color.blue()
            )
            
            type_labels = {
                Feedback.TYPE_BUG: "バグ報告",
                Feedback.TYPE_FEATURE: "機能リクエスト",
                Feedback.TYPE_OPINION: "意見・感想"
            }
            
            priority_labels = {
                Feedback.PRIORITY_LOW: "低",
                Feedback.PRIORITY_MEDIUM: "中",
                Feedback.PRIORITY_HIGH: "高",
                Feedback.PRIORITY_CRITICAL: "緊急"
            }
            
            embed.add_field(name="種類", value=type_labels[self.feedback_type], inline=True)
            embed.add_field(name="優先度", value=priority_labels[self.priority], inline=True)
            embed.add_field(name="内容", value=self.content, inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True, view=FeedbackConfirmView(self))
    
    @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """フィードバック入力をキャンセル"""
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("このボタンは他の人は操作できません。", ephemeral=True)
            return
        
        await interaction.response.send_message("フィードバック送信をキャンセルしました。", ephemeral=True)
        self.stop()


class FeedbackModal(discord.ui.Modal, title="フィードバック内容"):
    """フィードバック内容を入力するモーダル"""
    
    content = discord.ui.TextInput(
        label="フィードバック内容",
        style=discord.TextStyle.paragraph,
        placeholder="バグの詳細、機能リクエスト、または意見・感想を入力してください。",
        max_length=1000,
        required=True
    )
    
    def __init__(self, parent_view: FeedbackView):
        super().__init__()
        self.parent_view = parent_view
    
    async def on_submit(self, interaction: discord.Interaction):
        """モーダル送信時の処理"""
        self.parent_view.content = self.content.value
        
        # 送信確認
        embed = discord.Embed(
            title="フィードバック送信確認",
            description="以下の内容で送信しますか？",
            color=discord.Color.blue()
        )
        
        type_labels = {
            Feedback.TYPE_BUG: "バグ報告",
            Feedback.TYPE_FEATURE: "機能リクエスト",
            Feedback.TYPE_OPINION: "意見・感想"
        }
        
        priority_labels = {
            Feedback.PRIORITY_LOW: "低",
            Feedback.PRIORITY_MEDIUM: "中",
            Feedback.PRIORITY_HIGH: "高",
            Feedback.PRIORITY_CRITICAL: "緊急"
        }
        
        embed.add_field(name="種類", value=type_labels[self.parent_view.feedback_type], inline=True)
        embed.add_field(name="優先度", value=priority_labels[self.parent_view.priority], inline=True)
        embed.add_field(name="内容", value=self.content.value, inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True, view=FeedbackConfirmView(self.parent_view))


class FeedbackConfirmView(discord.ui.View):
    """フィードバック送信確認ビュー"""
    
    def __init__(self, parent_view: FeedbackView):
        super().__init__(timeout=60)
        self.parent_view = parent_view
    
    @discord.ui.button(label="送信する", style=discord.ButtonStyle.success, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        """送信確認ボタン"""
        if interaction.user.id != self.parent_view.author_id:
            await interaction.response.send_message("このボタンは他の人は操作できません。", ephemeral=True)
            return
        
        # フィードバックを保存
        feedback = Feedback(
            user_id=interaction.user.id,
            guild_id=interaction.guild.id,
            feedback_type=self.parent_view.feedback_type,
            content=self.parent_view.content,
            priority=self.parent_view.priority
        )
        
        feedback_manager = FeedbackManager()
        if feedback_manager.save_feedback(feedback):
            # 成功
            await interaction.response.send_message(
                f"フィードバックを送信しました。ID: `{feedback.id}`\n"
                f"開発チームがレビューし、対応します。ありがとうございます！", 
                ephemeral=True
            )
            
            # 管理者に通知（オプション）
            try:
                # 管理者ロールを持つメンバーを検索
                admin_role = discord.utils.find(lambda r: r.permissions.administrator, interaction.guild.roles)
                if admin_role:
                    # 管理者チャンネルがあれば通知（例: bot-adminという名前のチャンネル）
                    admin_channel = discord.utils.find(lambda c: c.name == 'bot-admin', interaction.guild.text_channels)
                    if admin_channel:
                        embed = discord.Embed(
                            title=f"新しいフィードバック: {feedback.id}",
                            description=f"ユーザー: {interaction.user.display_name} ({interaction.user.id})",
                            color=discord.Color.blue(),
                            timestamp=datetime.datetime.now()
                        )
                        
                        type_labels = {
                            Feedback.TYPE_BUG: "バグ報告",
                            Feedback.TYPE_FEATURE: "機能リクエスト",
                            Feedback.TYPE_OPINION: "意見・感想"
                        }
                        
                        priority_colors = {
                            Feedback.PRIORITY_LOW: "🟢",
                            Feedback.PRIORITY_MEDIUM: "🟡",
                            Feedback.PRIORITY_HIGH: "🟠",
                            Feedback.PRIORITY_CRITICAL: "🔴"
                        }
                        
                        embed.add_field(name="種類", value=type_labels[feedback.type], inline=True)
                        embed.add_field(name="優先度", value=f"{priority_colors[feedback.priority]} {feedback.priority}", inline=True)
                        embed.add_field(name="内容", value=feedback.content, inline=False)
                        
                        await admin_channel.send(embed=embed)
            except Exception as e:
                print(f"管理者通知エラー: {e}")
            
            self.parent_view.stop()
        else:
            # 失敗
            await interaction.response.send_message("フィードバックの保存中にエラーが発生しました。後でもう一度お試しください。", ephemeral=True)
    
    @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.danger, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """送信をキャンセル"""
        if interaction.user.id != self.parent_view.author_id:
            await interaction.response.send_message("このボタンは他の人は操作できません。", ephemeral=True)
            return
        
        await interaction.response.send_message("フィードバック送信をキャンセルしました。", ephemeral=True)
        self.parent_view.stop()
        self.stop()


class Feedback(commands.Cog):
    """フィードバック機能を提供するCog"""
    
    def __init__(self, bot):
        self.bot = bot
        self.feedback_manager = FeedbackManager()
        self.embed_creator = EmbedCreator()
    
    @commands.hybrid_group(name="feedback", description="フィードバックや提案を送信します")
    async def feedback(self, ctx):
        if ctx.invoked_subcommand is None:
            # フィードバック送信フォームを表示
            embed = self.embed_creator.create_info_embed(
                title="フィードバックを送信",
                description="以下のメニューからフィードバックの種類を選択し、内容を入力してください。"
            )
            
            await ctx.send(embed=embed, view=FeedbackView(ctx.author.id), ephemeral=True)
    
    @feedback.command(name="list", description="送信したフィードバック一覧を表示")
    async def list_feedback(self, ctx):
        """自分が送信したフィードバック一覧を表示"""
        feedbacks = self.feedback_manager.get_feedback_by_user(ctx.author.id)
        
        if not feedbacks:
            await ctx.send("送信したフィードバックはありません。", ephemeral=True)
            return
        
        embed = self.embed_creator.create_info_embed(
            title="送信したフィードバック一覧",
            description=f"合計 {len(feedbacks)} 件のフィードバックがあります"
        )
        
        for fb in feedbacks[:10]:  # 最大10件まで表示
            status_emojis = {
                Feedback.STATUS_NEW: "🆕",
                Feedback.STATUS_CONFIRMED: "👀",
                Feedback.STATUS_IN_PROGRESS: "🔧",
                Feedback.STATUS_RESOLVED: "✅",
                Feedback.STATUS_CLOSED: "🔒"
            }
            
            type_labels = {
                Feedback.TYPE_BUG: "バグ報告",
                Feedback.TYPE_FEATURE: "機能リクエスト",
                Feedback.TYPE_OPINION: "意見・感想"
            }
            
            created_at = datetime.datetime.fromisoformat(fb.created_at).strftime("%Y/%m/%d")
            
            # 内容を短く切り詰める
            content = fb.content
            if len(content) > 50:
                content = content[:50] + "..."
            
            field_title = f"{status_emojis.get(fb.status, '❓')} {type_labels.get(fb.type, 'Unknown')} (ID: {fb.id[:8]})"
            field_value = f"**作成日**: {created_at}\n**内容**: {content}"
            
            if fb.response:
                field_value += "\n**回答あり** ✉️"
            
            embed.add_field(name=field_title, value=field_value, inline=False)
        
        if len(feedbacks) > 10:
            embed.set_footer(text=f"他 {len(feedbacks) - 10} 件のフィードバックがあります。")
        
        await ctx.send(embed=embed, ephemeral=True)
    
    @feedback.command(name="view", description="フィードバックの詳細を表示")
    async def view_feedback(self, ctx, feedback_id: str):
        """フィードバックの詳細を表示"""
        feedback = self.feedback_manager.get_feedback_by_id(feedback_id)
        
        if not feedback:
            await ctx.send(f"ID: {feedback_id} のフィードバックは見つかりませんでした。", ephemeral=True)
            return
        
        # 自分のフィードバックか管理者のみ表示可能
        if feedback.user_id != ctx.author.id and not await is_admin(ctx):
            await ctx.send("このフィードバックを表示する権限がありません。", ephemeral=True)
            return
        
        embed = self.embed_creator.create_info_embed(
            title=f"フィードバック: {feedback.id}",
            description=""
        )
        
        # 基本情報
        type_labels = {
            Feedback.TYPE_BUG: "バグ報告",
            Feedback.TYPE_FEATURE: "機能リクエスト",
            Feedback.TYPE_OPINION: "意見・感想"
        }
        
        status_labels = {
            Feedback.STATUS_NEW: "新規",
            Feedback.STATUS_CONFIRMED: "確認済み",
            Feedback.STATUS_IN_PROGRESS: "対応中",
            Feedback.STATUS_RESOLVED: "解決済み",
            Feedback.STATUS_CLOSED: "クローズ"
        }
        
        priority_labels = {
            Feedback.PRIORITY_LOW: "低",
            Feedback.PRIORITY_MEDIUM: "中",
            Feedback.PRIORITY_HIGH: "高",
            Feedback.PRIORITY_CRITICAL: "緊急"
        }
        
        user = self.bot.get_user(feedback.user_id) or await self.bot.fetch_user(feedback.user_id)
        user_name = user.display_name if user else f"不明なユーザー (ID: {feedback.user_id})"
        
        created_at = datetime.datetime.fromisoformat(feedback.created_at).strftime("%Y/%m/%d %H:%M:%S")
        updated_at = datetime.datetime.fromisoformat(feedback.updated_at).strftime("%Y/%m/%d %H:%M:%S")
        
        embed.add_field(name="送信者", value=user_name, inline=True)
        embed.add_field(name="種類", value=type_labels.get(feedback.type, "不明"), inline=True)
        embed.add_field(name="ステータス", value=status_labels.get(feedback.status, "不明"), inline=True)
        embed.add_field(name="優先度", value=priority_labels.get(feedback.priority, "不明"), inline=True)
        embed.add_field(name="作成日時", value=created_at, inline=True)
        embed.add_field(name="更新日時", value=updated_at, inline=True)
        
        # フィードバック内容
        embed.add_field(name="内容", value=feedback.content, inline=False)
        
        # 開発者からの回答
        if feedback.response:
            response_time = datetime.datetime.fromisoformat(feedback.response["timestamp"]).strftime("%Y/%m/%d %H:%M:%S")
            embed.add_field(
                name="開発者からの回答",
                value=f"{feedback.response['content']}\n\n*回答日時: {response_time}*",
                inline=False
            )
        
        # コメント
        if feedback.comments:
            comments_text = []
            for comment in feedback.comments:
                comment_user = self.bot.get_user(comment["user_id"]) or await self.bot.fetch_user(comment["user_id"])
                comment_user_name = comment_user.display_name if comment_user else f"不明なユーザー (ID: {comment['user_id']})"
                comment_time = datetime.datetime.fromisoformat(comment["timestamp"]).strftime("%Y/%m/%d %H:%M:%S")
                
                comments_text.append(f"**{comment_user_name}** ({comment_time}):\n{comment['content']}")
            
            embed.add_field(name="コメント", value="\n\n".join(comments_text), inline=False)
        
        await ctx.send(embed=embed, ephemeral=True)
    
    @feedback.command(name="bug", description="バグを報告します")
    async def report_bug(self, ctx):
        """バグを報告"""
        embed = self.embed_creator.create_info_embed(
            title="バグ報告",
            description="ゲーム中に見つけたバグや不具合についての報告を送信します。"
        )
        
        # プリセットでバグ報告の種類を設定したビューを表示
        feedback_view = FeedbackView(ctx.author.id)
        feedback_view.feedback_type = Feedback.TYPE_BUG
        
        await ctx.send(embed=embed, view=feedback_view, ephemeral=True)
    
    @feedback.command(name="feature", description="新機能のリクエストや改善の提案を送信します")
    async def request_feature(self, ctx):
        """機能リクエスト"""
        embed = self.embed_creator.create_info_embed(
            title="機能リクエスト",
            description="新しい機能のリクエストや既存機能の改善提案を送信します。"
        )
        
        # プリセットで機能リクエストの種類を設定したビューを表示
        feedback_view = FeedbackView(ctx.author.id)
        feedback_view.feedback_type = Feedback.TYPE_FEATURE
        
        await ctx.send(embed=embed, view=feedback_view, ephemeral=True)
    
    # 管理者向けコマンド
    @commands.hybrid_group(name="admin_feedback", description="フィードバック管理コマンド")
    @commands.check(is_admin)
    async def admin_feedback(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = self.embed_creator.create_info_embed(
                title="フィードバック管理コマンド",
                description="以下のサブコマンドが利用可能です："
            )
            embed.add_field(name="!admin_feedback list [status]", value="フィードバック一覧を表示", inline=False)
            embed.add_field(name="!admin_feedback respond <feedback_id> <response>", value="フィードバックに回答", inline=False)
            embed.add_field(name="!admin_feedback status <feedback_id> <status>", value="フィードバックのステータスを更新", inline=False)
            embed.add_field(name="!admin_feedback priority <feedback_id> <priority>", value="フィードバックの優先度を更新", inline=False)
            embed.add_field(name="!admin_feedback comment <feedback_id> <comment>", value="フィードバックにコメントを追加", inline=False)
            
            await ctx.send(embed=embed, ephemeral=True)
    
    @admin_feedback.command(name="list", description="フィードバック一覧を表示")
    async def admin_list_feedback(self, ctx, status: Optional[str] = None):
        """管理者向けフィードバック一覧表示"""
        if status and status not in [Feedback.STATUS_NEW, Feedback.STATUS_CONFIRMED, 
                                    Feedback.STATUS_IN_PROGRESS, Feedback.STATUS_RESOLVED, 
                                    Feedback.STATUS_CLOSED]:
            valid_statuses = [Feedback.STATUS_NEW, Feedback.STATUS_CONFIRMED, 
                             Feedback.STATUS_IN_PROGRESS, Feedback.STATUS_RESOLVED, 
                             Feedback.STATUS_CLOSED]
            await ctx.send(f"無効なステータスです。有効なステータス: {', '.join(valid_statuses)}", ephemeral=True)
            return
        
        if status:
            feedbacks = self.feedback_manager.get_feedback_by_status(status)
            status_display = {
                Feedback.STATUS_NEW: "新規",
                Feedback.STATUS_CONFIRMED: "確認済み",
                Feedback.STATUS_IN_PROGRESS: "対応中",
                Feedback.STATUS_RESOLVED: "解決済み",
                Feedback.STATUS_CLOSED: "クローズ"
            }.get(status, status)
        else:
            # ギルドのフィードバックを取得
            feedbacks = self.feedback_manager.get_feedback_by_guild(ctx.guild.id)
        
        if not feedbacks:
            await ctx.send(f"{'指定されたステータスの' if status else ''}フィードバックはありません。", ephemeral=True)
            return
        
        # 新しい順にソート
        feedbacks.sort(key=lambda fb: fb.created_at, reverse=True)
        
        embed = self.embed_creator.create_info_embed(
            title=f"フィードバック一覧{f' (ステータス: {status_display})' if status else ''}",
            description=f"合計 {len(feedbacks)} 件のフィードバックがあります"
        )
        
        for fb in feedbacks[:15]:  # 最大15件まで表示
            status_emojis = {
                Feedback.STATUS_NEW: "🆕",
                Feedback.STATUS_CONFIRMED: "👀",
                Feedback.STATUS_IN_PROGRESS: "🔧",
                Feedback.STATUS_RESOLVED: "✅",
                Feedback.STATUS_CLOSED: "🔒"
            }
            
            type_labels = {
                Feedback.TYPE_BUG: "バグ報告",
                Feedback.TYPE_FEATURE: "機能リクエスト",
                Feedback.TYPE_OPINION: "意見・感想"
            }
            
            priority_emojis = {
                Feedback.PRIORITY_LOW: "🟢",
                Feedback.PRIORITY_MEDIUM: "🟡",
                Feedback.PRIORITY_HIGH: "🟠",
                Feedback.PRIORITY_CRITICAL: "🔴"
            }
            
            created_at = datetime.datetime.fromisoformat(fb.created_at).strftime("%Y/%m/%d")
            
            user = self.bot.get_user(fb.user_id) or await self.bot.fetch_user(fb.user_id)
            user_name = user.display_name if user else f"不明なユーザー (ID: {fb.user_id})"
            
            # 内容を短く切り詰める
            content = fb.content
            if len(content) > 50:
                content = content[:50] + "..."
            
            field_title = f"{status_emojis.get(fb.status, '❓')} {priority_emojis.get(fb.priority, '⚪')} {type_labels.get(fb.type, 'Unknown')} (ID: {fb.id[:8]})"
            field_value = f"**送信者**: {user_name}\n**作成日**: {created_at}\n**内容**: {content}"
            
            if fb.response:
                field_value += "\n**回答済み** ✉️"
            
            embed.add_field(name=field_title, value=field_value, inline=False)
        
        if len(feedbacks) > 15:
            embed.set_footer(text=f"他 {len(feedbacks) - 15} 件のフィードバックがあります。")
        
        await ctx.send(embed=embed, ephemeral=True)
    
    @admin_feedback.command(name="respond", description="フィードバックに回答")
    async def respond_to_feedback(self, ctx, feedback_id: str, *, response: str):
        """フィードバックに開発者として回答"""
        feedback = self.feedback_manager.get_feedback_by_id(feedback_id)
        
        if not feedback:
            await ctx.send(f"ID: {feedback_id} のフィードバックは見つかりませんでした。", ephemeral=True)
            return
        
        feedback.set_response(response)
        
        if self.feedback_manager.save_feedback(feedback):
            await ctx.send(f"フィードバック (ID: {feedback_id}) に回答しました。", ephemeral=True)
            
            # ユーザーに通知
            try:
                user = self.bot.get_user(feedback.user_id) or await self.bot.fetch_user(feedback.user_id)
                if user:
                    embed = self.embed_creator.create_success_embed(
                        title="フィードバックに回答がありました",
                        description=f"あなたが送信したフィードバック (ID: {feedback_id}) に開発チームから回答がありました。"
                    )
                    
                    embed.add_field(name="あなたのフィードバック", value=feedback.content, inline=False)
                    embed.add_field(name="開発チームからの回答", value=response, inline=False)
                    
                    try:
                        await user.send(embed=embed)
                    except discord.Forbidden:
                        print(f"ユーザー {user.id} にDMを送信できませんでした。")
            except Exception as e:
                print(f"ユーザー通知エラー: {e}")
        else:
            await ctx.send("フィードバックの保存中にエラーが発生しました。", ephemeral=True)
    
    @admin_feedback.command(name="status", description="フィードバックのステータスを更新")
    async def update_feedback_status(self, ctx, feedback_id: str, status: str):
        """フィードバックのステータスを更新"""
        valid_statuses = [Feedback.STATUS_NEW, Feedback.STATUS_CONFIRMED, 
                         Feedback.STATUS_IN_PROGRESS, Feedback.STATUS_RESOLVED, 
                         Feedback.STATUS_CLOSED]
        
        if status not in valid_statuses:
            await ctx.send(f"無効なステータスです。有効なステータス: {', '.join(valid_statuses)}", ephemeral=True)
            return
        
        feedback = self.feedback_manager.get_feedback_by_id(feedback_id)
        
        if not feedback:
            await ctx.send(f"ID: {feedback_id} のフィードバックは見つかりませんでした。", ephemeral=True)
            return
        
        if feedback.update_status(status):
            if self.feedback_manager.save_feedback(feedback):
                status_display = {
                    Feedback.STATUS_NEW: "新規",
                    Feedback.STATUS_CONFIRMED: "確認済み",
                    Feedback.STATUS_IN_PROGRESS: "対応中",
                    Feedback.STATUS_RESOLVED: "解決済み",
                    Feedback.STATUS_CLOSED: "クローズ"
                }.get(status, status)
                
                await ctx.send(f"フィードバック (ID: {feedback_id}) のステータスを「{status_display}」に更新しました。", ephemeral=True)
                
                # ユーザーに通知（オプション）
                try:
                    user = self.bot.get_user(feedback.user_id) or await self.bot.fetch_user(feedback.user_id)
                    if user:
                        embed = self.embed_creator.create_info_embed(
                            title="フィードバックのステータスが更新されました",
                            description=f"あなたのフィードバック (ID: {feedback_id}) のステータスが更新されました。"
                        )
                        
                        embed.add_field(name="新しいステータス", value=status_display, inline=False)
                        
                        try:
                            await user.send(embed=embed)
                        except discord.Forbidden:
                            print(f"ユーザー {user.id} にDMを送信できませんでした。")
                except Exception as e:
                    print(f"ユーザー通知エラー: {e}")
            else:
                await ctx.send("フィードバックの保存中にエラーが発生しました。", ephemeral=True)
        else:
            await ctx.send("ステータスの更新に失敗しました。", ephemeral=True)
    
    @admin_feedback.command(name="priority", description="フィードバックの優先度を更新")
    async def update_feedback_priority(self, ctx, feedback_id: str, priority: str):
        """フィードバックの優先度を更新"""
        valid_priorities = [Feedback.PRIORITY_LOW, Feedback.PRIORITY_MEDIUM, 
                           Feedback.PRIORITY_HIGH, Feedback.PRIORITY_CRITICAL]
        
        if priority not in valid_priorities:
            await ctx.send(f"無効な優先度です。有効な優先度: {', '.join(valid_priorities)}", ephemeral=True)
            return
        
        feedback = self.feedback_manager.get_feedback_by_id(feedback_id)
        
        if not feedback:
            await ctx.send(f"ID: {feedback_id} のフィードバックは見つかりませんでした。", ephemeral=True)
            return
        
        if feedback.update_priority(priority):
            if self.feedback_manager.save_feedback(feedback):
                priority_display = {
                    Feedback.PRIORITY_LOW: "低",
                    Feedback.PRIORITY_MEDIUM: "中",
                    Feedback.PRIORITY_HIGH: "高",
                    Feedback.PRIORITY_CRITICAL: "緊急"
                }.get(priority, priority)
                
                await ctx.send(f"フィードバック (ID: {feedback_id}) の優先度を「{priority_display}」に更新しました。", ephemeral=True)
            else:
                await ctx.send("フィードバックの保存中にエラーが発生しました。", ephemeral=True)
        else:
            await ctx.send("優先度の更新に失敗しました。", ephemeral=True)
    
    @admin_feedback.command(name="comment", description="フィードバックにコメントを追加")
    async def add_comment_to_feedback(self, ctx, feedback_id: str, *, comment: str):
        """フィードバックにコメントを追加"""
        feedback = self.feedback_manager.get_feedback_by_id(feedback_id)
        
        if not feedback:
            await ctx.send(f"ID: {feedback_id} のフィードバックは見つかりませんでした。", ephemeral=True)
            return
        
        feedback.add_comment(ctx.author.id, comment)
        
        if self.feedback_manager.save_feedback(feedback):
            await ctx.send(f"フィードバック (ID: {feedback_id}) にコメントを追加しました。", ephemeral=True)
        else:
            await ctx.send("フィードバックの保存中にエラーが発生しました。", ephemeral=True)
    
    @admin_feedback.command(name="delete", description="フィードバックを削除")
    async def delete_feedback(self, ctx, feedback_id: str):
        """フィードバックを削除"""
        feedback = self.feedback_manager.get_feedback_by_id(feedback_id)
        
        if not feedback:
            await ctx.send(f"ID: {feedback_id} のフィードバックは見つかりませんでした。", ephemeral=True)
            return
        
        # 確認メッセージ
        confirm_msg = await ctx.send(
            f"フィードバック (ID: {feedback_id}) を削除しますか？この操作は元に戻せません。\n"
            f"続行するには ✅ を、キャンセルするには ❌ をクリックしてください。",
            ephemeral=True
        )
        
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirm_msg.id
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            
            if str(reaction.emoji) == "✅":
                if self.feedback_manager.delete_feedback(feedback_id):
                    await ctx.send(f"フィードバック (ID: {feedback_id}) を削除しました。", ephemeral=True)
                else:
                    await ctx.send("フィードバックの削除に失敗しました。", ephemeral=True)
            else:
                await ctx.send("フィードバックの削除をキャンセルしました。", ephemeral=True)
        
        except asyncio.TimeoutError:
            await ctx.send("タイムアウトしました。フィードバックの削除をキャンセルします。", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Feedback(bot))
