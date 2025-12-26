"""
邮件通知模块 - 发送新文献通知
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional


class EmailNotifier:
    """邮件通知器"""
    
    def __init__(self, smtp_server: str, smtp_port: int, 
                 sender_email: str, sender_password: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
    
    def send_notification(self, recipient: str, articles: list) -> bool:
        """发送新文献通知邮件"""
        if not articles:
            print("没有新文献，跳过邮件发送")
            return True
        
        if not self.sender_email or not self.sender_password:
            print("邮件配置不完整，跳过发送")
            return False
        
        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"📚 文献追踪更新 - {len(articles)}篇新文献 ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
            msg['From'] = self.sender_email
            msg['To'] = recipient
            
            # 生成邮件内容
            html_content = self._generate_html(articles)
            text_content = self._generate_text(articles)
            
            msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            # 发送邮件
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipient, msg.as_string())
            
            print(f"邮件发送成功: {len(articles)}篇文献通知已发送到 {recipient}")
            return True
            
        except Exception as e:
            print(f"邮件发送失败: {e}")
            return False
    
    def _generate_html(self, articles: list) -> str:
        """生成HTML格式邮件内容"""
        html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .header h1 { margin: 0; font-size: 24px; }
        .header p { margin: 5px 0 0; opacity: 0.9; }
        .article { background: #f8f9fa; border-radius: 8px; padding: 15px; margin-bottom: 15px; border-left: 4px solid #667eea; }
        .article h2 { margin: 0 0 10px; font-size: 16px; color: #333; }
        .article h3 { margin: 5px 0; font-size: 14px; color: #666; font-weight: normal; }
        .meta { font-size: 12px; color: #888; margin-bottom: 10px; }
        .abstract { font-size: 13px; color: #555; margin-top: 10px; }
        .link { display: inline-block; margin-top: 10px; color: #667eea; text-decoration: none; font-size: 13px; }
        .link:hover { text-decoration: underline; }
        .footer { text-align: center; color: #888; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📚 文献追踪更新</h1>
        <p>发现 {count} 篇符合关键词的新文献</p>
    </div>
""".format(count=len(articles))
        
        for article in articles:
            authors = ", ".join(article.authors[:3]) if article.authors else "未知"
            if len(article.authors) > 3:
                authors += " et al."
            
            abstract_preview = article.abstract_zh[:300] + "..." if len(article.abstract_zh) > 300 else article.abstract_zh
            
            html += f"""
    <div class="article">
        <h2>{article.title}</h2>
        <h3>{article.title_zh}</h3>
        <div class="meta">
            <strong>{article.journal}</strong> | {article.pub_date} | {authors}
        </div>
        <div class="abstract">{abstract_preview}</div>
        <a href="{article.link}" class="link">查看原文 →</a>
    </div>
"""
        
        html += """
    <div class="footer">
        <p>此邮件由文献追踪系统自动发送</p>
    </div>
</body>
</html>
"""
        return html
    
    def _generate_text(self, articles: list) -> str:
        """生成纯文本格式邮件内容"""
        text = f"文献追踪更新 - 发现 {len(articles)} 篇新文献\n"
        text += "=" * 50 + "\n\n"
        
        for i, article in enumerate(articles, 1):
            authors = ", ".join(article.authors[:3]) if article.authors else "未知"
            text += f"{i}. {article.title}\n"
            text += f"   中文: {article.title_zh}\n"
            text += f"   期刊: {article.journal} | 日期: {article.pub_date}\n"
            text += f"   作者: {authors}\n"
            text += f"   链接: {article.link}\n\n"
        
        return text
