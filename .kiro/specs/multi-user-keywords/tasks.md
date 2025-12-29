# Implementation Plan: Multi-User Keywords Filter

## Overview

实现多用户关键词筛选功能，按照配置 → 数据导出 → 前端逻辑 → UI组件的顺序逐步实现。

## Tasks

- [x] 1. 更新配置文件添加多用户关键词
  - [x] 1.1 在 config.py 中添加 USER_KEYWORDS 字典配置
    - 添加于宏宇和朱海燕的关键词列表
    - 保持原有 KEYWORDS 变量向后兼容
    - _Requirements: 1.1, 1.3_

- [x] 2. 更新数据管理模块导出用户关键词
  - [x] 2.1 修改 data_manager.py 的 generate_index 函数
    - 在 index_data 中添加 user_keywords 字段
    - 从 config.USER_KEYWORDS 读取数据
    - _Requirements: 6.1, 6.2, 6.3_
  - [x] 2.2 重新生成 index.json 数据文件
    - 运行数据生成脚本更新 docs/data/index.json
    - _Requirements: 6.1_

- [x] 3. 实现前端关键词筛选逻辑
  - [x] 3.1 在 app.js 中添加用户关键词相关全局状态
    - 添加 userKeywords、currentKeywordUser 变量
    - 添加 KEYWORD_USER_STORAGE_KEY 常量
    - _Requirements: 3.5_
  - [x] 3.2 实现 filterByUserKeywords 筛选函数
    - 支持按用户关键词筛选文章
    - 实现大小写不敏感的部分匹配
    - _Requirements: 1.4, 2.1, 2.2, 2.4_
  - [x] 3.3 修改 filterArticles 函数集成用户关键词筛选
    - 在现有筛选流程中添加用户关键词筛选步骤
    - 确保与其他筛选器正确组合
    - _Requirements: 2.5_
  - [x] 3.4 实现关键词高亮函数 highlightUserKeywords
    - 根据当前选中用户的关键词进行高亮
    - 处理正则特殊字符转义
    - _Requirements: 4.1, 4.2_
  - [x] 3.5 实现用户选择持久化函数
    - loadKeywordUser: 从 localStorage 加载
    - saveKeywordUser: 保存到 localStorage
    - setKeywordUser: 设置并触发筛选
    - _Requirements: 3.5_

- [x] 4. 实现前端UI组件
  - [x] 4.1 在 index.html 中添加关键词用户选择器
    - 在筛选区域添加下拉选择框
    - 添加适当的标签和样式类
    - _Requirements: 3.1, 3.2_
  - [x] 4.2 实现 populateKeywordUserSelector 函数
    - 动态填充用户选项
    - 显示用户名和关键词数量
    - _Requirements: 3.4_
  - [x] 4.3 在 loadArticles 中初始化关键词选择器
    - 加载数据后填充选择器
    - 恢复用户之前的选择
    - _Requirements: 3.1, 3.3_

- [x] 5. 更新统计显示
  - [x] 5.1 确保筛选计数正确反映关键词筛选结果
    - updateFilteredCount 函数已有，确认其正确工作
    - _Requirements: 5.1, 5.2, 5.3_

- [x] 6. Checkpoint - 功能测试
  - 手动测试关键词筛选功能
  - 测试与其他筛选器的组合
  - 测试持久化功能
  - 确保所有功能正常工作，如有问题请告知

## Notes

- 任务按依赖顺序排列：配置 → 数据导出 → 前端逻辑 → UI
- 每个任务完成后应可独立验证
- 关键词匹配采用大小写不敏感的部分匹配策略
