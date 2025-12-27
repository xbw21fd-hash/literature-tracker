# Implementation Tasks

## Phase 1: 数据分析与可视化

### Task 1.1: 创建分析页面基础结构
- **File**: `docs/analytics.html`
- **Requirements**: REQ-1
- **Description**: 创建独立的数据分析页面，包含基础HTML结构、导航、主题切换支持
- **Acceptance Criteria**:
  - [x] 创建 analytics.html 页面
  - [x] 添加返回主页的导航按钮
  - [x] 支持深色/浅色主题切换
  - [x] 响应式布局适配

### Task 1.2: 实现统计数据计算模块
- **File**: `docs/analytics.js`
- **Requirements**: REQ-1, REQ-2, REQ-3, REQ-5
- **Description**: 实现从文献数据计算各种统计指标的函数
- **Acceptance Criteria**:
  - [x] 计算总文献数、AI相关/非AI分类统计
  - [x] 计算月度/周度发表趋势
  - [x] 计算期刊分布
  - [x] 计算AI文献增长率

### Task 1.3: 实现趋势图表
- **File**: `docs/analytics.js`
- **Requirements**: REQ-2, REQ-5
- **Description**: 使用 Chart.js 实现文献发表趋势图表
- **Acceptance Criteria**:
  - [x] 引入 Chart.js 库
  - [x] 实现按月统计折线图
  - [x] 实现按周统计柱状图
  - [x] 支持月/周切换
  - [x] 区分AI/非AI文献趋势
  - [x] 鼠标悬停显示详细信息

### Task 1.4: 实现期刊分布饼图
- **File**: `docs/analytics.js`
- **Requirements**: REQ-3
- **Description**: 实现期刊分布饼图，显示前10个期刊
- **Acceptance Criteria**:
  - [x] 实现饼图显示前10期刊
  - [x] 显示数量和百分比
  - [x] 其他期刊合并为"其他"
  - [x] 点击可跳转搜索该期刊文献

### Task 1.5: 实现关键词云
- **File**: `docs/analytics.js`
- **Requirements**: REQ-4
- **Description**: 使用 wordcloud2.js 实现关键词云
- **Acceptance Criteria**:
  - [x] 引入 wordcloud2.js 库
  - [x] 从标题和摘要提取关键词
  - [x] 过滤停用词
  - [x] 显示前50个高频词
  - [x] 点击关键词可搜索

### Task 1.6: 实现数据导出功能
- **File**: `docs/analytics.js`
- **Requirements**: REQ-13
- **Description**: 实现统计数据导出为CSV和图表导出为PNG
- **Acceptance Criteria**:
  - [x] 导出统计数据为CSV
  - [x] 导出图表为PNG
  - [x] 添加导出按钮到界面

### Task 1.7: 主页添加分析入口
- **File**: `docs/index.html`, `docs/app.js`
- **Requirements**: REQ-1
- **Description**: 在主页添加进入数据分析页面的入口
- **Acceptance Criteria**:
  - [x] 添加"数据分析"按钮/链接
  - [x] 样式与现有界面一致

## Phase 2: 高级搜索

### Task 2.1: 实现正则表达式搜索
- **File**: `docs/app.js`
- **Requirements**: REQ-6
- **Description**: 添加正则表达式搜索模式
- **Acceptance Criteria**:
  - [x] 添加正则模式切换按钮
  - [x] 实现正则表达式匹配
  - [x] 无效正则显示错误提示
  - [x] 显示正则模式指示器

### Task 2.2: 实现布尔运算符搜索
- **File**: `docs/app.js`
- **Requirements**: REQ-7
- **Description**: 支持 AND/OR/NOT 布尔运算符
- **Acceptance Criteria**:
  - [x] 实现布尔表达式解析器
  - [x] 支持 AND 运算符
  - [x] 支持 OR 运算符
  - [x] 支持 NOT 运算符
  - [x] 支持括号分组
  - [ ] 显示解析后的查询逻辑
  - [ ] 提供语法帮助提示

### Task 2.3: 更新搜索UI
- **File**: `docs/index.html`, `docs/style.css`
- **Requirements**: REQ-6, REQ-7
- **Description**: 更新搜索界面，添加模式切换和帮助
- **Acceptance Criteria**:
  - [x] 添加搜索模式切换（普通/正则/布尔）
  - [ ] 添加语法帮助弹窗
  - [x] 显示当前搜索模式

## Phase 3: 性能优化

### Task 3.1: 实现虚拟滚动
- **File**: `docs/app.js`
- **Requirements**: REQ-8
- **Description**: 实现虚拟滚动，只渲染可见区域
- **Acceptance Criteria**:
  - [ ] 只渲染可见区域的卡片
  - [ ] 动态加载/卸载卡片
  - [ ] 维护滚动位置准确性
  - [ ] 支持10000+文献流畅滚动
  - [ ] 预加载上下各一屏内容

### Task 3.2: 实现PWA离线支持
- **File**: `docs/sw.js`, `docs/manifest.json`
- **Requirements**: REQ-9
- **Description**: 添加Service Worker和manifest实现PWA
- **Acceptance Criteria**:
  - [x] 创建 Service Worker
  - [x] 缓存静态资源
  - [x] 缓存文献数据
  - [x] 创建 manifest.json
  - [x] 离线时显示提示
  - [x] 网络恢复自动更新

### Task 3.3: 注册PWA
- **File**: `docs/index.html`, `docs/app.js`
- **Requirements**: REQ-9
- **Description**: 在主页注册Service Worker和添加manifest
- **Acceptance Criteria**:
  - [x] 注册 Service Worker
  - [x] 添加 manifest 链接
  - [ ] 添加 PWA 安装提示

### Task 3.4: 实现性能监控
- **File**: `docs/app.js`
- **Requirements**: REQ-14
- **Description**: 添加性能监控和日志
- **Acceptance Criteria**:
  - [x] 记录页面加载时间
  - [x] 记录搜索响应时间
  - [ ] 记录渲染性能指标
  - [x] 控制台输出性能日志
  - [x] 性能低于阈值时警告

## Phase 4: RSS输出

### Task 4.1: 创建RSS生成器
- **File**: `rss_generator.py`
- **Requirements**: REQ-11
- **Description**: 创建Python模块生成RSS 2.0 feed
- **Acceptance Criteria**:
  - [x] 生成符合RSS 2.0标准的XML
  - [x] 包含最近100篇文献
  - [x] 每篇包含标题、摘要、链接、日期
  - [x] 保存为 docs/feed.xml

### Task 4.2: 集成RSS生成到主流程
- **File**: `main.py`
- **Requirements**: REQ-11
- **Description**: 在数据更新后自动生成RSS
- **Acceptance Criteria**:
  - [x] 数据更新后调用RSS生成
  - [x] 错误处理和日志

### Task 4.3: 添加RSS链接到主页
- **File**: `docs/index.html`
- **Requirements**: REQ-11
- **Description**: 在HTML head添加RSS feed链接
- **Acceptance Criteria**:
  - [x] 添加 RSS autodiscovery 链接
  - [ ] 添加可见的RSS订阅按钮

## Phase 5: AI每日摘要

### Task 5.1: 创建AI摘要生成器
- **File**: `ai_summarizer.py`
- **Requirements**: REQ-12
- **Description**: 创建使用免费AI API的摘要生成器
- **Acceptance Criteria**:
  - [x] 支持多个免费API提供商（Gemini/SiliconFlow/Groq/DeepSeek）
  - [x] 生成每日摘要内容
  - [x] 包含文献总览、热点分析、核心要点
  - [x] 每篇文献包含可点击链接
  - [x] API失败时降级为简单统计

### Task 5.2: 实现摘要HTML生成
- **File**: `ai_summarizer.py`
- **Requirements**: REQ-12
- **Description**: 将摘要保存为HTML文件
- **Acceptance Criteria**:
  - [x] 生成美观的HTML摘要页面
  - [x] 保存到 docs/daily/YYYY-MM-DD.html
  - [x] 支持深色/浅色主题
  - [x] 文献链接可点击

### Task 5.3: 集成AI摘要到主流程
- **File**: `main.py`, `config.py`
- **Requirements**: REQ-12
- **Description**: 在每日运行时生成AI摘要
- **Acceptance Criteria**:
  - [x] 配置文件添加AI API设置
  - [x] 每日运行时调用摘要生成
  - [ ] 可选发送邮件通知

### Task 5.4: 添加每日摘要入口
- **File**: `docs/index.html`, `docs/app.js`
- **Requirements**: REQ-12
- **Description**: 在主页添加每日摘要入口
- **Acceptance Criteria**:
  - [x] 添加"每日摘要"按钮/链接
  - [x] 显示最近摘要列表

## Phase 6: 增量索引

### Task 6.1: 实现增量索引模块
- **File**: `incremental_index.py`
- **Requirements**: REQ-10
- **Description**: 实现只更新变化数据的增量索引
- **Acceptance Criteria**:
  - [x] 记录上次更新时间戳
  - [x] 过滤出新增文献
  - [x] 合并新旧文献数据
  - [x] 显示新增/更新/跳过数量

### Task 6.2: 集成增量索引到主流程
- **File**: `main.py`, `data_manager.py`
- **Requirements**: REQ-10
- **Description**: 在数据处理流程中使用增量索引
- **Acceptance Criteria**:
  - [ ] 抓取时使用增量更新
  - [x] 保留现有数据
  - [x] 日志显示处理统计

## Phase 7: 样式和文档更新

### Task 7.1: 更新分析页面样式
- **File**: `docs/style.css`
- **Requirements**: REQ-1, REQ-2, REQ-3, REQ-4
- **Description**: 为分析页面添加样式
- **Acceptance Criteria**:
  - [x] 图表容器样式
  - [x] 响应式布局
  - [x] 深色/浅色主题支持

### Task 7.2: 更新README文档
- **File**: `README.md`
- **Requirements**: All
- **Description**: 更新README包含所有新功能说明
- **Acceptance Criteria**:
  - [x] 添加高级功能说明
  - [x] 添加配置说明
  - [x] 更新版本号
