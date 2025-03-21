"""
ドキュメントを管理するCog
"""
import discord
from discord.ext import commands
import io
import os
from typing import Optional

class DocumentationCog(commands.Cog):
    """ドキュメントを管理するコグ"""
    
    def __init__(self, bot):
        self.bot = bot
        self.docs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Cogの準備完了時に呼ばれる"""
        print(f"{self.__class__.__name__} Cog is ready.")
    
    @commands.group(name="docs", invoke_without_command=True)
    async def docs(self, ctx):
        """ドキュメント関連コマンドグループ"""
        embed = discord.Embed(
            title="人狼Bot ドキュメント",
            description="以下のコマンドでドキュメントにアクセスできます。",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="ユーザーガイド",
            value=f"`{ctx.prefix}docs guide [トピック]` - 使い方ガイドを表示",
            inline=False
        )
        
        embed.add_field(
            name="API リファレンス",
            value=f"`{ctx.prefix}docs api [トピック]` - API ドキュメントを表示",
            inline=False
        )
        
        embed.add_field(
            name="コマンドリスト",
            value=f"`{ctx.prefix}docs commands` - 使用可能なコマンド一覧を表示",
            inline=False
        )
        
        embed.add_field(
            name="ダウンロード",
            value=f"`{ctx.prefix}docs download [guide/api]` - ドキュメントをダウンロード",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @docs.command(name="guide")
    async def show_user_guide(self, ctx, topic: Optional[str] = None):
        """ユーザーガイドを表示"""
        guide_path = os.path.join(self.docs_path, "user_guide.md")
        
        if not os.path.exists(guide_path):
            await ctx.send("ユーザーガイドが見つかりません。")
            return
            
        with open(guide_path, "r", encoding="utf-8") as f:
            guide_content = f.read()
            
        # トピック指定がある場合、該当部分を抽出
        if topic:
            sections = self._extract_sections(guide_content)
            
            topic_lower = topic.lower()
            matching_sections = [s for s in sections if topic_lower in s["title"].lower()]
            
            if not matching_sections:
                await ctx.send(f"トピック `{topic}` に関する情報が見つかりません。")
                return
                
            # 最も関連度の高いセクションを選択
            section = matching_sections[0]
            
            embed = discord.Embed(
                title=section["title"],
                description=section["content"][:4000] if len(section["content"]) > 4000 else section["content"],
                color=discord.Color.blue()
            )
            
            if len(section["content"]) > 4000:
                embed.set_footer(text="内容が長すぎるため、一部省略されています。完全な内容を見るには !docs download guide を使用してください。")
                
            await ctx.send(embed=embed)
            return
            
        # トピック指定がない場合、目次を表示
        toc = self._extract_toc(guide_content)
        
        embed = discord.Embed(
            title="人狼Bot ユーザーガイド",
            description="以下のトピックが利用可能です。特定のトピックを表示するには `!docs guide [トピック]` を使用してください。",
            color=discord.Color.blue()
        )
        
        for section in toc:
            embed.add_field(name=section["title"], value=section["summary"], inline=False)
            
        embed.set_footer(text=f"完全なガイドをダウンロードするには {ctx.prefix}docs download guide を使用してください。")
        await ctx.send(embed=embed)
    
    @docs.command(name="api")
    async def show_api_docs(self, ctx, topic: Optional[str] = None):
        """API ドキュメントを表示"""
        api_path = os.path.join(self.docs_path, "api_reference.md")
        
        if not os.path.exists(api_path):
            await ctx.send("API リファレンスが見つかりません。")
            return
            
        with open(api_path, "r", encoding="utf-8") as f:
            api_content = f.read()
            
        # トピック指定がある場合、該当部分を抽出
        if topic:
            sections = self._extract_sections(api_content)
            
            topic_lower = topic.lower()
            matching_sections = [s for s in sections if topic_lower in s["title"].lower()]
            
            if not matching_sections:
                await ctx.send(f"トピック `{topic}` に関するAPIドキュメントが見つかりません。")
                return
                
            # 最も関連度の高いセクションを選択
            section = matching_sections[0]
            
            embed = discord.Embed(
                title=section["title"],
                description=section["content"][:4000] if len(section["content"]) > 4000 else section["content"],
                color=discord.Color.blue()
            )
            
            if len(section["content"]) > 4000:
                embed.set_footer(text=f"内容が長すぎるため、一部省略されています。完全な内容を見るには {ctx.prefix}docs download api を使用してください。")
                
            await ctx.send(embed=embed)
            return
            
        # トピック指定がない場合、目次を表示
        toc = self._extract_toc(api_content)
        
        embed = discord.Embed(
            title="人狼Bot API リファレンス",
            description="以下のAPIトピックが利用可能です。特定のトピックを表示するには `!docs api [トピック]` を使用してください。",
            color=discord.Color.blue()
        )
        
        for section in toc:
            embed.add_field(name=section["title"], value=section["summary"], inline=False)
            
        embed.set_footer(text=f"完全なAPIリファレンスをダウンロードするには {ctx.prefix}docs download api を使用してください。")
        await ctx.send(embed=embed)
    
    @docs.command(name="commands")
    async def show_commands(self, ctx):
        """使用可能なコマンド一覧を表示"""
        embed = discord.Embed(
            title="人狼Bot コマンド一覧",
            description="以下のコマンドが使用可能です。",
            color=discord.Color.blue()
        )
        
        # コマンドをカテゴリごとに分類
        categories = {
            "基本コマンド": ["help", "start", "join", "vote"],
            "管理者コマンド": ["admin", "config", "compose"],
            "ゲーム情報": ["status", "roles", "stats"],
            "コミュニティ機能": ["suggest", "balance", "feedback", "roadmap"],
            "ドキュメント": ["docs"]
        }
        
        # カテゴリごとにコマンドを表示
        for category, command_list in categories.items():
            commands_text = []
            
            for command_name in command_list:
                command = self.bot.get_command(command_name)
                if command:
                    commands_text.append(f"`{ctx.prefix}{command.name}` - {command.help or '説明なし'}")
                else:
                    commands_text.append(f"`{ctx.prefix}{command_name}` - 説明なし")
            
            if commands_text:
                embed.add_field(name=category, value="\n".join(commands_text), inline=False)
        
        embed.set_footer(text=f"各コマンドの詳細は {ctx.prefix}help [コマンド名] で確認できます。")
        await ctx.send(embed=embed)
    
    @docs.command(name="download")
    async def download_docs(self, ctx, doc_type: str = "guide"):
        """ドキュメントをダウンロードする"""
        if doc_type.lower() == "guide":
            doc_path = os.path.join(self.docs_path, "user_guide.md")
            file_name = "user_guide.md"
            title = "ユーザーガイド"
        elif doc_type.lower() == "api":
            doc_path = os.path.join(self.docs_path, "api_reference.md")
            file_name = "api_reference.md"
            title = "API リファレンス"
        else:
            await ctx.send(f"ドキュメントタイプ `{doc_type}` は無効です。`guide` または `api` を指定してください。")
            return
            
        if not os.path.exists(doc_path):
            await ctx.send(f"{title}が見つかりません。")
            return
            
        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # ファイルを送信
        buffer = io.BytesIO(content.encode('utf-8'))
        file = discord.File(buffer, filename=file_name)
        
        await ctx.send(f"{title}ドキュメント:", file=file)
    
    def _extract_sections(self, content):
        """マークダウンからセクションを抽出"""
        sections = []
        lines = content.split('\n')
        
        current_section = None
        current_content = []
        
        for line in lines:
            if line.startswith('# '):
                # 新しいセクションが始まったら、前のセクションを保存
                if current_section:
                    sections.append({
                        "title": current_section,
                        "content": '\n'.join(current_content).strip()
                    })
                    
                current_section = line[2:].strip()
                current_content = []
            elif line.startswith('## '):
                # サブセクションも新しいセクションとして扱う
                if current_section:
                    sections.append({
                        "title": current_section,
                        "content": '\n'.join(current_content).strip()
                    })
                    
                current_section = line[3:].strip()
                current_content = []
            else:
                if current_section:
                    current_content.append(line)
        
        # 最後のセクションを保存
        if current_section:
            sections.append({
                "title": current_section,
                "content": '\n'.join(current_content).strip()
            })
            
        return sections
    
    def _extract_toc(self, content):
        """マークダウンから目次を抽出"""
        sections = self._extract_sections(content)
        toc = []
        
        for section in sections:
            # 各セクションの最初の段落を要約として使用
            paragraphs = section["content"].split('\n\n')
            summary = paragraphs[0] if paragraphs else "説明なし"
            
            # 要約が長すぎる場合は切り詰める
            if len(summary) > 100:
                summary = summary[:97] + "..."
                
            toc.append({
                "title": section["title"],
                "summary": summary
            })
            
        return toc

async def setup(bot):
    await bot.add_cog(DocumentationCog(bot))
