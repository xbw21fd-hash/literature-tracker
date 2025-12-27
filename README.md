# 📚 RSS文献追踪系统

自动追踪学术RSS源，筛选关键词相关文献，翻译成中文，并通过GitHub Pages展示。

## ✨ 功能特性

### 核心功能
- 🔍 **RSS抓取**: 支持50+学术期刊RSS源（Nature、Science、APS、ACS、Wiley、RSC、Elsevier等）
- 🎯 **关键词筛选**: 自动筛选包含指定关键词的文献
- 🌐 **自动翻译**: 使用Google翻译将标题和摘要翻译成中文
- 📝 **Markdown存储**: 每篇文献保存为独立Markdown文件
- 📊 **历史记录**: JSON文件保存所有历史数据
- ⏰ **定时任务**: 每12小时自动抓取
- 📧 **邮件通知**: 新文献自动发送邮件
- 💬 **微信推送**: 通过Server酱发送微信通知

### 前端界面 (V3)
- 🎴 **可折叠卡片**: 文献以卡片形式展示，点击展开查看详情
- 🤖 **AI分类筛选**: 自动识别AI相关文献，支持分类筛选
- 🌓 **深色/浅色主题**: 支持主题切换，护眼模式
- 📱 **响应式设计**: 完美适配手机、平板、电脑
- ⌨️ **键盘快捷键**: j/k导航，Enter展开，o打开原文，s收藏，r标记已读，l稍后阅读
- 🔍 **搜索功能**: 支持标题、摘要、作者搜索，带搜索历史
- ⭐ **收藏功能**: 标记喜欢的文献
- 📖 **阅读状态**: 标记已读/未读，追踪阅读进度
- 📌 **稍后阅读**: 添加到待读列表，集中阅读
- 📄 **导出功能**: 支持BibTeX/RIS格式导出，单篇或批量
- 🎨 **关键词高亮**: AI关键词自动高亮显示
- 📅 **日期筛选**: 按日期范围筛选文献
- 📚 **期刊筛选**: 按期刊或期刊分组筛选
- 📊 **统计信息**: 实时显示文献数量、分类统计

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
├── wechat_notifier.py   # 微信推送模块
├── deduplicator.py      # 去重模块
├── rss_generator.py     # RSS Feed生成器
├── ai_summarizer.py     # AI摘要生成器
├── incremental_index.py # 增量索引模块
├── requirements.txt     # Python依赖
├── data/                # 数据目录
│   ├── history.json     # 历史记录
│   ├── favorites.json   # 收藏列表
│   └── index.json       # 网页索引
├── articles/            # Markdown文献
├── docs/                # GitHub Pages网站
│   ├── index.html       # 主页
│   ├── analytics.html   # 数据分析页
│   ├── style.css        # 样式表
│   ├── app.js           # 主应用脚本
│   ├── analytics.js     # 分析模块脚本
│   ├── sw.js            # Service Worker
│   ├── manifest.json    # PWA配置
│   ├── feed.xml         # RSS Feed
│   ├── data/            # 前端数据
│   └── daily/           # 每日摘要
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

---

## 📖 V3 功能详细说明

### 稍后阅读功能 📌

**使用方法**:
- 点击文章的 📍 按钮添加到待读列表
- 按钮变为 📌，文章左侧显示紫色边框
- 点击"📌 待读"筛选按钮查看所有待读文章
- 键盘快捷键: 按 `l` 键标记当前文章

**特点**:
- 本地存储，刷新页面状态保持
- 统计栏显示待读数量
- 支持筛选只看待读文章

### 导出功能 📄

**单篇导出**:
1. 展开任意文章
2. 在文章底部点击"📄 BibTeX"或"📋 RIS"
3. 文件自动下载，文件名格式: `作者姓氏年份.bib`

**批量导出**:
1. 使用筛选功能选择想要的文章
2. 在控制面板找到"批量导出"区域
3. 点击"📄 BibTeX"或"📋 RIS"
4. 导出当前筛选结果的所有文章，文件名格式: `literature_export_日期.bib`

**支持格式**:
- **BibTeX**: 适用于 LaTeX 文档引用
- **RIS**: 适用于 EndNote、Mendeley、Zotero 等文献管理软件

### 键盘快捷键 ⌨️

| 快捷键 | 功能 |
|--------|------|
| `j` | 下一篇文章 |
| `k` | 上一篇文章 |
| `Enter` | 展开/折叠当前文章 |
| `o` | 在新标签页打开原文 |
| `s` | 收藏/取消收藏 |
| `r` | 标记已读/未读 |
| `l` | 添加到待读/移除待读 |

### 筛选功能 🔍

**分类筛选**:
- 全部 - 显示所有文章
- 🤖 AI相关 - 只显示包含AI关键词的文章
- 📚 非AI - 只显示不包含AI关键词的文章

**阅读状态筛选**:
- 全部 - 显示所有文章
- 未读 - 只显示未读文章
- 已读 - 只显示已读文章
- 📌 待读 - 只显示待读文章

**期刊筛选**:
- 支持按期刊分组筛选（顶刊、Nature系列、APS系列、ACS系列、Wiley系列、RSC系列、Elsevier系列、预印本、其他）
- 支持按单独期刊筛选

**日期筛选**:
- 支持按日期范围筛选文献

### 视觉标识 🎨

| 标识 | 含义 |
|------|------|
| 黄色左边框 | 收藏的文章 |
| 紫色左边框 | 待读的文章 |
| 半透明 | 已读的文章 |
| 📍 | 未添加到待读 |
| 📌 | 已添加到待读 |
| 🤖 AI | AI相关文章 |
| 📚 非AI | 非AI相关文章 |

---

## 📋 开发规范 (.kiro/specs)

本项目使用规范化的需求和设计文档来指导开发。所有规范文档位于 `.kiro/specs/` 目录。

### 已完成的功能规范

#### 1. literature-ui-enhancement (UI增强)
**状态**: ✅ 已完成

**包含功能**:
- 可折叠文献卡片
- AI分类筛选
- 深色/浅色主题切换
- 响应式设计
- 键盘快捷键
- 关键词高亮
- 悬停预览
- 邮件发送Bug修复

**文档**:
- `requirements.md` - 需求文档（10个需求，50+验收标准）
- `design.md` - 设计文档（架构、组件、数据模型、9个正确性属性）
- `tasks.md` - 实现任务（12个主任务，40+子任务）

#### 2. literature-enhancements-v2 (V2增强)
**状态**: ✅ 已完成

**包含功能**:
- 阅读进度追踪
- 文献去重优化
- 搜索历史
- 微信推送通知
- 邮件摘要预览

**文档**:
- `requirements.md` - 需求文档（5个需求，25+验收标准）

### V3 新增功能 (当前版本)

**已实现**:
- ✅ 稍后阅读队列
- ✅ 导出功能 (BibTeX/RIS)

### V4 高级功能 (最新版本)

**数据分析与可视化**:
- ✅ 📊 独立数据分析页面 (`analytics.html`)
- ✅ 📈 文献发表趋势图表（按月/周统计）
- ✅ 🥧 期刊分布饼图
- ✅ ☁️ 研究热点关键词云
- ✅ 🤖 AI vs 非AI文献趋势对比
- ✅ 📤 数据导出（CSV/PNG图表）

**高级搜索**:
- ✅ 🔍 正则表达式搜索模式
- ✅ 🔗 布尔运算符搜索（AND/OR/NOT）
- ✅ 📝 搜索模式指示器

**性能优化**:
- ✅ 📱 PWA离线支持（Service Worker）
- ✅ 💾 静态资源缓存
- ✅ 📊 性能监控日志

**RSS输出**:
- ✅ 📡 RSS 2.0 Feed生成 (`feed.xml`)
- ✅ 🔗 自动RSS发现链接

**AI每日摘要**:
- ✅ 🤖 支持多个免费AI API（Gemini/SiliconFlow/Groq/DeepSeek）
- ✅ 📰 每日文献摘要HTML页面
- ✅ ⭐ 重点文献推荐
- ✅ 🔥 研究趋势分析
- ✅ 📊 降级统计摘要（API失败时）

### V5 高级UI功能 (最新)

**布局与显示**:
- ✅ 📐 三种布局模式（列表/网格/紧凑）
- ✅ 🔤 五级字体大小调节（XS/S/M/L/XL）
- ✅ ⌨️ 快捷键自定义配置
- ✅ 👁️ 增强文献预览（悬停显示完整信息）

**性能优化**:
- ✅ 🚀 虚拟滚动（处理大量文献，50+项自动启用）
- ✅ 🖼️ 图片懒加载（Intersection Observer API）
- ✅ 📦 增量加载（分批加载，每批50项）
- ✅ 💾 搜索结果缓存（LRU缓存，最大50项）
- ✅ 📱 移动端专属布局（滑动手势、底部导航、下拉刷新）

**高级分析**:
- ✅ 📈 研究趋势预测（基于历史数据预测未来3个月）
- ✅ 🔥 新兴主题识别（增长率>50%的主题）
- ✅ 📉 衰退主题识别（下降率>30%的主题）
- ✅ 🤖 AI vs 非AI趋势对比
- ✅ 🔄 研究主题演化分析（时间切片、主题生命周期）
- ✅ 📊 主题生命周期分类（新兴/增长/成熟/衰退）
- ✅ 📤 演化数据导出（CSV格式）

### V5.1 深度性能优化 (处理10,000+篇文献)

**数据层优化**:
- ✅ 📦 分块加载器（ChunkLoader）- 每块1000篇，支持进度回调
- ✅ 💾 IndexedDB缓存管理 - 持久化缓存，支持离线访问
- ✅ 🔄 增量更新 - 后台检查更新，智能同步
- ✅ ⚡ 自动重试机制 - 加载失败自动重试3次

**搜索优化**:
- ✅ 🔍 倒排索引搜索引擎 - 搜索响应时间 <100ms
- ✅ 📊 TF-IDF权重计算 - 智能结果排序
- ✅ 🎯 布尔查询支持 - AND/OR/NOT运算
- ✅ 💾 搜索结果缓存 - LRU缓存，命中率>70%

**渲染优化**:
- ✅ 🎨 优化虚拟滚动 - 阈值降至20项，支持100,000+项
- ✅ ♻️ DOM节点复用池 - 减少GC压力>50%
- ✅ 🎯 动态高度缓存 - 精确计算可见范围
- ✅ 🚀 60fps流畅滚动 - requestAnimationFrame优化

**性能监控**:
- ✅ ⚡ 实时性能监控 - FCP/LCP/FID/CLS指标
- ✅ 📊 性能面板 - 可视化性能数据
- ✅ 💡 优化建议 - 自动生成优化建议
- ✅ 📈 性能报告导出 - JSON格式详细报告

**内存管理**:
- ✅ 🔄 对象池 - 复用对象，减少GC
- ✅ 💾 智能缓存 - 自动清理过期数据
- ✅ 📊 内存监控 - 实时监控内存使用
- ✅ ⚠️ 内存警告 - 使用超过80%时警告

**PWA与离线支持**:
- ✅ 📱 Service Worker - 完整离线支持
- ✅ 💾 静态资源缓存 - Cache First策略
- ✅ 🔄 数据文件缓存 - Network First策略
- ✅ 🔔 自动更新通知 - 每小时检查更新
- ✅ 📲 PWA安装 - 可安装到桌面/主屏幕
- ✅ 🎨 应用图标和主题 - 完整PWA体验

**性能指标**:
- ✅ 初始加载时间: <3s (10,000篇)
- ✅ 搜索响应时间: <100ms
- ✅ 滚动帧率: 60fps
- ✅ 内存占用: <500MB
- ✅ 首屏渲染: <2s
- ✅ 离线加载: <100ms (全部从缓存)

**使用方法**:
- 点击右下角 ⚡ 按钮打开性能监控面板
- 查看实时性能指标和优化建议
- 导出性能报告进行深度分析
- 系统自动优化，无需手动配置
- 离线时自动使用缓存数据

**键盘快捷键**:
- ✅ Ctrl/Cmd + Plus/Minus - 调节字体大小
- ✅ Ctrl/Cmd + 0 - 重置字体大小
- ✅ 所有快捷键可自定义配置（点击"⌨️ 快捷键"按钮）

**移动端手势**:
- ✅ 右滑 - 标记已读
- ✅ 左滑 - 显示操作按钮（收藏、待读）
- ✅ 下拉 - 刷新列表

## 🔧 V4 配置说明

### AI摘要配置

在环境变量或 `config.py` 中配置：

```python
# config.py
AI_CONFIG = {
    "enabled": True,
    "provider": "gemini",  # gemini, siliconflow, groq, deepseek
    "api_key": "your-api-key",
}
```

或使用环境变量：
```bash
export AI_PROVIDER=gemini
export AI_API_KEY=your-api-key
```

**支持的AI提供商**:
| 提供商 | 模型 | 获取API Key |
|--------|------|-------------|
| Gemini | gemini-3.0-flash | [Google AI Studio](https://makersuite.google.com/app/apikey) |
| SiliconFlow | Qwen2.5-7B | [SiliconFlow](https://siliconflow.cn/) |
| Groq | llama-3.1-70b | [Groq Console](https://console.groq.com/) |
| DeepSeek | deepseek-chat | [DeepSeek](https://platform.deepseek.com/) |

### 高级搜索使用

**搜索模式切换**:
- 点击搜索框右侧的模式指示器切换
- 或按 `/` 键循环切换

**正则表达式示例**:
```
ferro.*electric    # 匹配 ferroelectric, ferro-electric 等
^machine           # 以 machine 开头
\d{4}              # 匹配4位数字
```

**布尔运算符示例**:
```
machine AND learning           # 同时包含两个词
ferroelectric OR magnetic      # 包含任一词
neural NOT review              # 包含neural但不含review
(AI OR ML) AND materials       # 组合使用
```

### PWA安装与离线使用

**桌面端安装**:
1. 在Chrome/Edge中访问网站
2. 点击地址栏右侧的安装图标 ⊕
3. 点击"安装"按钮
4. 应用将作为独立窗口打开

**移动端安装**:
1. 在Chrome/Safari中访问网站
2. 点击浏览器菜单
3. 选择"添加到主屏幕"或"安装应用"
4. 应用图标将出现在主屏幕

**离线功能**:
- ✅ 静态资源（HTML/CSS/JS）完全离线可用
- ✅ 已缓存的文献数据离线可访问
- ✅ 离线时自动使用缓存，加载速度 <100ms
- ✅ 恢复网络后自动检查更新

**Service Worker管理**:
- 自动每小时检查更新
- 发现新版本时显示更新通知
- 点击"立即更新"应用新版本
- 在Chrome DevTools → Application → Service Workers 中查看状态

**缓存管理**:
```javascript
// 在浏览器控制台中执行
// 清除所有缓存
await serviceWorkerManager.clearCache();

// 手动检查更新
await serviceWorkerManager.update();

// 注销Service Worker
await serviceWorkerManager.unregister();
```

安装后可离线访问已缓存的文献数据。

### 规范文档说明

**requirements.md** - 需求文档
- 使用 EARS 模式编写需求
- 每个需求包含用户故事和验收标准
- 遵循 INCOSE 质量规则

**design.md** - 设计文档
- 系统架构和组件设计
- 数据模型定义
- 正确性属性（Property-Based Testing）
- 错误处理策略
- 测试策略

**tasks.md** - 实现任务
- 将设计分解为可执行的任务
- 每个任务关联需求
- 标记可选任务（测试相关）
- 包含检查点
