# 📚 RSS文献追踪系统

自动追踪学术RSS源，筛选关键词相关文献，翻译成中文，并通过GitHub Pages展示。

## ✨ 功能特性

- 🔍 **RSS抓取**: 支持50+学术期刊RSS源
- 🎯 **关键词筛选**: 自动筛选包含指定关键词的文献
- 🌐 **自动翻译**: 使用Google翻译将标题和摘要翻译成中文
- 📝 **Markdown存储**: 每篇文献保存为独立Markdown文件
- 🌍 **网页展示**: 通过GitHub Pages展示文献列表
- 🔎 **搜索功能**: 支持标题、摘要、作者搜索
- ⭐ **收藏功能**: 标记喜欢的文献
- 📊 **历史记录**: JSON文件保存所有历史数据
- ⏰ **定时任务**: 每12小时自动抓取
- 📧 **邮件通知**: 新文献自动发送邮件

## 🚀 快速开始

### 1. 创建GitHub仓库

```bash
# 克隆或初始化仓库
git init literature-tracker
cd literature-tracker

# 复制所有文件到仓库
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置邮件（可选）

编辑 `config.py`，填写邮件配置：

```python
EMAIL_CONFIG = {
    "recipient": "your-email@example.com",
    "smtp_server": "smtp.qq.com",
    "smtp_port": 465,
    "sender_email": "your-sender@qq.com",  # 发送邮箱
    "sender_password": "your-auth-code",    # QQ邮箱授权码
}
```

### 4. 本地运行

```bash
# 运行一次
python main.py --once

# 不发送邮件
python main.py --once --no-email

# 启动定时任务（每12小时）
python main.py --schedule
```

### 5. 部署到GitHub

```bash
git add -A
git commit -m "初始化文献追踪系统"
git remote add origin https://github.com/YOUR_USERNAME/literature-tracker.git
git push -u origin main
```

### 6. 配置GitHub Actions

在仓库设置中添加Secrets（用于邮件通知）：
- `EMAIL_SENDER`: 发送邮箱地址
- `EMAIL_PASSWORD`: 邮箱授权码

### 7. 启用GitHub Pages

1. 进入仓库 Settings → Pages
2. Source 选择 "GitHub Actions"
3. 等待部署完成

## 📁 项目结构

```
literature-tracker/
├── main.py              # 主程序
├── config.py            # 配置文件
├── rss_fetcher.py       # RSS抓取模块
├── translator.py        # 翻译模块
├── data_manager.py      # 数据管理模块
├── email_notifier.py    # 邮件通知模块
├── requirements.txt     # Python依赖
├── data/                # 数据目录
│   ├── history.json     # 历史记录
│   ├── favorites.json   # 收藏列表
│   └── index.json       # 网页索引
├── articles/            # Markdown文献
├── docs/                # GitHub Pages网站
│   ├── index.html
│   ├── style.css
│   └── app.js
└── .github/workflows/   # GitHub Actions
    ├── fetch.yml        # 定时抓取
    └── pages.yml        # 部署Pages
```

## 🔧 自定义配置

### 修改关键词

编辑 `config.py` 中的 `KEYWORDS` 列表：

```python
KEYWORDS = [
    "ferro",
    "machine",
    "learning",
    # 添加更多关键词...
]
```

### 添加RSS源

编辑 `config.py` 中的 `RSS_FEEDS` 列表。

### 修改抓取频率

编辑 `.github/workflows/fetch.yml` 中的 cron 表达式：

```yaml
schedule:
  - cron: '0 0,12 * * *'  # 每12小时
  # - cron: '0 */6 * * *'  # 每6小时
  # - cron: '0 8 * * *'    # 每天8点
```

## 📧 QQ邮箱配置说明

1. 登录QQ邮箱 → 设置 → 账户
2. 开启 "POP3/SMTP服务"
3. 生成授权码
4. 将授权码填入配置

## 📄 许可证

MIT License
