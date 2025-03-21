"""
コミュニティ機能を管理するCog
"""
import discord
from discord.ext import commands
import datetime
import asyncio
import os
from discord import app_commands
from typing import Optional, List, Dict, Any, Union
from models.suggestion import Suggestion, SuggestionManager

class SuggestionView(discord.ui.View):
    """提案表示用ビュー"""
    
    def __init__(self, suggestion: Suggestion, suggestion_manager: SuggestionManager, timeout: int = 180):
        super().__init__(timeout=timeout)
        self.suggestion = suggestion
        self.suggestion_manager = suggestion_manager
        
        # 賛成ボタン
        up_button = discord.ui.Button(
            style=discord.ButtonStyle.green,
            label=f"👍 賛成 ({len(suggestion.votes['up'])})",
            custom_id=f"vote_up_{suggestion.id}"
        )
        up_button.callback = self.vote_up_callback
        self.add_item(up_button)
        
        # 反対ボタン
        down_button = discord.ui.Button(
            style=discord.ButtonStyle.red,
            label=f"👎 反対 ({len(suggestion.votes['down'])})",
            custom_id=f"vote_down_{suggestion.id}"
        )
        down_button.callback = self.vote_down_callback
        self.add_item(down_button)
        
        # コメントボタン
        comment_button = discord.ui.Button(
            style=discord.ButtonStyle.blurple,
            label="💬 コメント",
            custom_id=f"comment_{suggestion.id}"
        )
        comment_button.callback = self.comment_callback
        self.add_item(comment_button)
        
    async def vote_up_callback(self, interaction: discord.Interaction) -> None:
        """賛成投票ボタンのコールバック"""
        user_id = str(interaction.user.id)
        suggestion = self.suggestion_manager.vote_suggestion(self.suggestion.id, user_id, "up")
        if suggestion:
            await interaction.response.send_message("賛成票を投票しました！", ephemeral=True)
            
            # ボタンを更新
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    if item.custom_id == f"vote_up_{self.suggestion.id}":
                        item.label = f"👍 賛成 ({len(suggestion.votes['up'])})"
                    elif item.custom_id == f"vote_down_{self.suggestion.id}":
                        item.label = f"👎 反対 ({len(suggestion.votes['down'])})"
                    
            await interaction.message.edit(view=self)
        else:
            await interaction.response.send_message("投票できませんでした。", ephemeral=True)
        
    async def vote_down_callback(self, interaction: discord.Interaction) -> None:
        """反対投票ボタンのコールバック"""
        user_id = str(interaction.user.id)
        suggestion = self.suggestion_manager.vote_suggestion(self.suggestion.id, user_id, "down")
        if suggestion:
            await interaction.response.send_message("反対票を投票しました！", ephemeral=True)
            
            # ボタンを更新
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    if item.custom_id == f"vote_up_{self.suggestion.id}":
                        item.label = f"👍 賛成 ({len(suggestion.votes['up'])})"
                    elif item.custom_id == f"vote_down_{self.suggestion.id}":
                        item.label = f"👎 反対 ({len(suggestion.votes['down'])})"
                    
            await interaction.message.edit(view=self)
        else:
            await interaction.response.send_message("投票できませんでした。", ephemeral=True)
        
    async def comment_callback(self, interaction: discord.Interaction) -> None:
        """コメントボタンのコールバック"""
        # モーダルを作成
        modal = CommentModal(self.suggestion, self.suggestion_manager)
        await interaction.response.send_modal(modal)

class SuggestionModal(discord.ui.Modal):
    """提案入力用モーダル"""
    
    def __init__(self, title: str = "新しい提案"):
        super().__init__(title=title)
        
        # タイトル入力欄
        self.title_input = discord.ui.TextInput(
            label="タイトル",
            placeholder="提案のタイトルを入力してください",
            min_length=5,
            max_length=100,
            required=True
        )
        self.add_item(self.title_input)
        
        # 説明入力欄
        self.description_input = discord.ui.TextInput(
            label="説明",
            placeholder="提案の詳細な説明を入力してください",
            min_length=10,
            max_length=1000,
            style=discord.TextStyle.paragraph,
            required=True
        )
        self.add_item(self.description_input)
        
        # カテゴリ選択欄
        self.category_input = discord.ui.TextInput(
            label="カテゴリ",
            placeholder="機能追加, バグ修正, 役職アイデア, バランス調整, その他",
            min_length=2,
            max_length=20,
            required=True
        )
        self.add_item(self.category_input)
        
        self.result = None
        
    async def on_submit(self, interaction: discord.Interaction) -> None:
        # 結果を保存
        self.result = {
            "title": self.title_input.value,
            "description": self.description_input.value,
            "category": self.category_input.value
        }
        await interaction.response.defer()

class CommentModal(discord.ui.Modal):
    """コメント入力用モーダル"""
    
    def __init__(self, suggestion: Suggestion, suggestion_manager: SuggestionManager):
        super().__init__(title="コメントを追加")
        self.suggestion = suggestion
        self.suggestion_manager = suggestion_manager
        
        # コメント入力欄
        self.comment_input = discord.ui.TextInput(
            label="コメント",
            placeholder="コメントを入力してください",
            min_length=1,
            max_length=500,
            style=discord.TextStyle.paragraph,
            required=True
        )
        self.add_item(self.comment_input)
        
    async def on_submit(self, interaction: discord.Interaction) -> None:
        user_id = str(interaction.user.id)
        user_name = interaction.user.display_name
        
        suggestion = self.suggestion_manager.comment_suggestion(
            self.suggestion.id, 
            user_id, 
            user_name, 
            self.comment_input.value
        )
        
        if suggestion:
            await interaction.response.send_message("コメントを投稿しました！", ephemeral=True)
        else:
            await interaction.response.send_message("コメントを投稿できませんでした。", ephemeral=True)

class CommunityCog(commands.Cog):
    """コミュニティ機能を管理するコグ"""
    
    def __init__(self, bot):
        self.bot = bot
        self.suggestion_manager = SuggestionManager()
        
    @commands.Cog.listener()
    async def on_ready(self):
        """Cogの準備完了時に呼ばれる"""
        print(f"{self.__class__.__name__} Cog is ready.")
        
    @commands.group(name="suggest", invoke_without_command=True)
    async def suggest(self, ctx):
        """提案関連コマンドグループ"""
        embed = discord.Embed(
            title="提案システム",
            description="以下のコマンドで提案を管理できます。",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="提案を作成",
            value=f"`{ctx.prefix}suggest new` - 新しい提案を作成",
            inline=False
        )
        
        embed.add_field(
            name="提案を一覧表示",
            value=f"`{ctx.prefix}suggest list [カテゴリ] [ステータス]` - 提案の一覧を表示",
            inline=False
        )
        
        embed.add_field(
            name="提案の詳細を表示",
            value=f"`{ctx.prefix}suggest view <提案ID>` - 提案の詳細を表示",
            inline=False
        )
        
        embed.add_field(
            name="提案に投票",
            value=(
                f"`{ctx.prefix}suggest upvote <提案ID>` - 提案に賛成票を投じる\n"
                f"`{ctx.prefix}suggest downvote <提案ID>` - 提案に反対票を投じる"
            ),
            inline=False
        )
        
        embed.add_field(
            name="提案にコメント",
            value=f"`{ctx.prefix}suggest comment <提案ID> <コメント>` - 提案にコメントを追加",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @suggest.command(name="new")
    async def new_suggestion(self, ctx):
        """新しい提案を作成"""
        # モーダルを表示してユーザーに入力を求める
        modal = SuggestionModal()
        
        # モーダルを使用してインタラクションが可能な場合
        if isinstance(ctx, discord.Interaction) or hasattr(ctx, 'interaction'):
            interaction = getattr(ctx, 'interaction', ctx)
            await interaction.response.send_modal(modal)
            await modal.wait()
        else:
            # フォールバック：古いコマンドの場合はメッセージでやり取り
            await ctx.send("新しい提案を作成します。タイトルを入力してください（5〜100文字）：")
            
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel
            
            try:
                title_msg = await self.bot.wait_for('message', check=check, timeout=60.0)
                title = title_msg.content
                
                await ctx.send("説明を入力してください（10〜1000文字）：")
                desc_msg = await self.bot.wait_for('message', check=check, timeout=120.0)
                description = desc_msg.content
                
                await ctx.send("カテゴリを入力してください（機能追加, バグ修正, 役職アイデア, バランス調整, その他）：")
                cat_msg = await self.bot.wait_for('message', check=check, timeout=60.0)
                category = cat_msg.content
                
                modal.result = {
                    "title": title,
                    "description": description,
                    "category": category
                }
            except asyncio.TimeoutError:
                await ctx.send("タイムアウトしました。もう一度やり直してください。")
                return
        
        # 提案を作成
        if modal.result:
            suggestion = self.suggestion_manager.create_suggestion(
                str(ctx.author.id),
                ctx.author.display_name,
                modal.result["title"],
                modal.result["description"],
                modal.result["category"]
            )
            
            # 確認メッセージを送信
            embed = discord.Embed(
                title=f"提案 #{suggestion.id}: {suggestion.title}",
                description=suggestion.description,
                color=discord.Color.green()
            )
            
            embed.add_field(name="カテゴリ", value=suggestion.category, inline=True)
            embed.add_field(name="提案者", value=suggestion.user_name, inline=True)
            embed.add_field(name="ステータス", value=suggestion.status, inline=True)
            embed.set_footer(text=f"提案ID: {suggestion.id} | 作成日時: {suggestion.created_at.strftime('%Y/%m/%d %H:%M')}")
            
            view = SuggestionView(suggestion, self.suggestion_manager)
            await ctx.send("提案を作成しました！", embed=embed, view=view)
        else:
            await ctx.send("提案の作成がキャンセルされました。")
    
    @suggest.command(name="list")
    async def list_suggestions(self, ctx, category: Optional[str] = None, status: Optional[str] = None):
        """提案の一覧を表示"""
        # 提案を取得
        suggestions = self.suggestion_manager.get_all_suggestions(status, category)
        
        if not suggestions:
            await ctx.send("該当する提案はありません。")
            return
            
        # 提案一覧を表示
        embed = discord.Embed(
            title="提案一覧",
            description=f"全{len(suggestions)}件の提案があります。",
            color=discord.Color.blue()
        )
        
        # フィルタ情報
        if category or status:
            filter_text = []
            if category:
                filter_text.append(f"カテゴリ: {category}")
            if status:
                filter_text.append(f"ステータス: {status}")
                
            embed.description += f"\nフィルタ: {', '.join(filter_text)}"
        
        # 最大10件まで表示
        for i, suggestion in enumerate(suggestions[:10]):
            vote_score = len(suggestion.votes["up"]) - len(suggestion.votes["down"])
            embed.add_field(
                name=f"#{suggestion.id}: {suggestion.title} ({vote_score:+d})",
                value=(
                    f"カテゴリ: {suggestion.category} | "
                    f"ステータス: {suggestion.status} | "
                    f"コメント: {len(suggestion.comments)}件\n"
                    f"詳細を表示: `{ctx.prefix}suggest view {suggestion.id}`"
                ),
                inline=False
            )
            
        if len(suggestions) > 10:
            embed.set_footer(text=f"他に{len(suggestions) - 10}件の提案があります。")
            
        await ctx.send(embed=embed)
    
    @suggest.command(name="view")
    async def view_suggestion(self, ctx, suggestion_id: str):
        """提案の詳細を表示"""
        # 提案を取得
        suggestion = self.suggestion_manager.get_suggestion(suggestion_id)
        
        if not suggestion:
            await ctx.send(f"提案ID `{suggestion_id}` は存在しません。")
            return
            
        # 提案の詳細を表示
        embed = discord.Embed(
            title=f"提案 #{suggestion.id}: {suggestion.title}",
            description=suggestion.description,
            color=discord.Color.blue()
        )
        
        embed.add_field(name="カテゴリ", value=suggestion.category, inline=True)
        embed.add_field(name="提案者", value=suggestion.user_name, inline=True)
        embed.add_field(name="ステータス", value=suggestion.status, inline=True)
        
        vote_score = len(suggestion.votes["up"]) - len(suggestion.votes["down"])
        embed.add_field(
            name="投票状況",
            value=f"👍 {len(suggestion.votes['up'])} | 👎 {len(suggestion.votes['down'])} | 合計: {vote_score:+d}",
            inline=False
        )
        
        # コメントを表示（最大5件）
        if suggestion.comments:
            comments_text = []
            for i, comment in enumerate(suggestion.comments[-5:]):
                comment_date = comment.get("created_at", "")
                if isinstance(comment_date, str):
                    try:
                        comment_date = datetime.datetime.fromisoformat(comment_date)
                        date_str = comment_date.strftime('%Y/%m/%d %H:%M')
                    except ValueError:
                        date_str = ""
                else:
                    date_str = comment_date.strftime('%Y/%m/%d %H:%M')
                    
                comments_text.append(f"{comment['user_name']} ({date_str}): {comment['content']}")
                
            embed.add_field(
                name=f"コメント（{len(suggestion.comments)}件）",
                value="\n".join(comments_text) if comments_text else "コメントはありません。",
                inline=False
            )
            
        embed.set_footer(text=f"提案ID: {suggestion.id} | 作成日時: {suggestion.created_at.strftime('%Y/%m/%d %H:%M')}")
        
        view = SuggestionView(suggestion, self.suggestion_manager)
        await ctx.send(embed=embed, view=view)
    
    @suggest.command(name="upvote")
    async def upvote_suggestion(self, ctx, suggestion_id: str):
        """提案に賛成票を投じる"""
        suggestion = self.suggestion_manager.vote_suggestion(suggestion_id, str(ctx.author.id), "up")
        
        if not suggestion:
            await ctx.send(f"提案ID `{suggestion_id}` は存在しません。")
            return
            
        await ctx.send(f"提案 `{suggestion.title}` に賛成票を投じました。")
    
    @suggest.command(name="downvote")
    async def downvote_suggestion(self, ctx, suggestion_id: str):
        """提案に反対票を投じる"""
        suggestion = self.suggestion_manager.vote_suggestion(suggestion_id, str(ctx.author.id), "down")
        
        if not suggestion:
            await ctx.send(f"提案ID `{suggestion_id}` は存在しません。")
            return
            
        await ctx.send(f"提案 `{suggestion.title}` に反対票を投じました。")
    
    @suggest.command(name="comment")
    async def comment_suggestion(self, ctx, suggestion_id: str, *, comment: str):
        """提案にコメントを追加"""
        suggestion = self.suggestion_manager.comment_suggestion(
            suggestion_id, 
            str(ctx.author.id), 
            ctx.author.display_name, 
            comment
        )
        
        if not suggestion:
            await ctx.send(f"提案ID `{suggestion_id}` は存在しません。")
            return
            
        await ctx.send(f"提案 `{suggestion.title}` にコメントを追加しました。")
    
    @suggest.command(name="status")
    @commands.has_permissions(administrator=True)
    async def update_status(self, ctx, suggestion_id: str, status: str):
        """提案のステータスを更新（管理者のみ）"""
        valid_statuses = ["pending", "approved", "rejected", "implemented"]
        if status not in valid_statuses:
            await ctx.send(f"無効なステータスです。有効なステータス: {', '.join(valid_statuses)}")
            return
            
        suggestion = self.suggestion_manager.update_suggestion(suggestion_id, status=status)
        
        if not suggestion:
            await ctx.send(f"提案ID `{suggestion_id}` は存在しません。")
            return
            
        await ctx.send(f"提案 `{suggestion.title}` のステータスを `{status}` に更新しました。")
    
    @commands.command(name="roadmap")
    async def show_roadmap(self, ctx):
        """実装予定の提案を表示（ロードマップ）"""
        # 承認済みの提案を取得
        approved_suggestions = self.suggestion_manager.get_all_suggestions(status="approved")
        
        if not approved_suggestions:
            await ctx.send("現在、承認された提案はありません。")
            return
            
        # ロードマップを表示
        embed = discord.Embed(
            title="開発ロードマップ",
            description="以下の機能が実装予定です。",
            color=discord.Color.gold()
        )
        
        for suggestion in approved_suggestions:
            vote_score = len(suggestion.votes["up"]) - len(suggestion.votes["down"])
            embed.add_field(
                name=f"#{suggestion.id}: {suggestion.title} ({vote_score:+d})",
                value=(
                    f"カテゴリ: {suggestion.category} | "
                    f"提案者: {suggestion.user_name} | "
                    f"詳細を表示: `{ctx.prefix}suggest view {suggestion.id}`"
                ),
                inline=False
            )
            
        await ctx.send(embed=embed)
    
    @commands.command(name="suggestions")
    async def show_suggestions(self, ctx):
        """提案コマンドの概要を表示"""
        await self.suggest(ctx)

async def setup(bot):
    await bot.add_cog(CommunityCog(bot))
