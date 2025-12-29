# Requirements Document

## Introduction

本功能为文献追踪系统添加多用户关键词筛选能力。系统将支持多个用户各自定义的关键词列表，用户可以在网页界面上选择按特定用户的关键词进行文献筛选，从而快速找到与自己研究方向相关的文献。

## Glossary

- **Keyword_Filter_System**: 关键词筛选系统，负责根据用户选择的关键词列表筛选文献
- **User_Keywords**: 用户关键词配置，包含用户名称和对应的关键词列表
- **Article**: 文献条目，包含标题、摘要等可被关键词匹配的字段
- **Keyword_Selector**: 网页上的关键词选择器组件，允许用户选择按哪个用户的关键词筛选

## Requirements

### Requirement 1: 多用户关键词配置

**User Story:** As a system administrator, I want to configure multiple users' keyword lists in the config file, so that different researchers can have their own keyword sets for filtering.

#### Acceptance Criteria

1. THE Config_System SHALL support defining multiple user keyword lists with user names and their associated keywords
2. WHEN a new user keyword list is added to the configuration, THE Config_System SHALL make it available for filtering without code changes
3. THE Config_System SHALL maintain backward compatibility with the existing single KEYWORDS list (于宏宇's keywords)
4. WHEN parsing user keywords, THE Keyword_Filter_System SHALL treat keywords as case-insensitive partial matches

### Requirement 2: 关键词筛选逻辑

**User Story:** As a researcher, I want to filter articles by a specific user's keywords, so that I can quickly find literature relevant to my research interests.

#### Acceptance Criteria

1. WHEN a user selects a specific user's keyword list, THE Keyword_Filter_System SHALL filter articles that match ANY keyword in that list
2. WHEN filtering articles, THE Keyword_Filter_System SHALL search in article title, title_zh, abstract, and abstract_zh fields
3. WHEN no user keyword filter is selected (or "all" is selected), THE Keyword_Filter_System SHALL show all articles without keyword filtering
4. WHEN multiple keywords match an article, THE Keyword_Filter_System SHALL count the article only once in the results
5. THE Keyword_Filter_System SHALL support combining user keyword filter with existing filters (date, journal, favorites, read status)

### Requirement 3: 网页关键词选择器

**User Story:** As a user, I want to select which researcher's keywords to use for filtering on the web interface, so that I can easily switch between different keyword sets.

#### Acceptance Criteria

1. WHEN the page loads, THE Keyword_Selector SHALL display a dropdown with all available user keyword lists
2. THE Keyword_Selector SHALL include an "全部" (All) option that disables keyword filtering
3. WHEN a user selects a keyword list from the dropdown, THE Keyword_Filter_System SHALL immediately filter the article list
4. THE Keyword_Selector SHALL display the user name and keyword count for each option (e.g., "于宏宇 (8个关键词)")
5. THE Keyword_Selector SHALL persist the user's selection in localStorage across page reloads

### Requirement 4: 关键词高亮显示

**User Story:** As a user, I want to see matched keywords highlighted in article titles and abstracts, so that I can quickly identify why an article was included in the results.

#### Acceptance Criteria

1. WHEN a user keyword filter is active, THE Keyword_Filter_System SHALL highlight matching keywords in article titles and abstracts
2. WHEN switching between different user keyword lists, THE Keyword_Filter_System SHALL update the highlighting to reflect the new keywords
3. THE Keyword_Filter_System SHALL use a visually distinct style for keyword highlights that works in both light and dark themes

### Requirement 5: 筛选结果统计

**User Story:** As a user, I want to see statistics about how many articles match the selected keywords, so that I can understand the relevance of my keyword set.

#### Acceptance Criteria

1. WHEN a user keyword filter is active, THE Keyword_Filter_System SHALL display the count of matching articles
2. THE Keyword_Filter_System SHALL update the filtered count in real-time when the keyword selection changes
3. WHEN combined with other filters, THE Keyword_Filter_System SHALL show the count of articles matching all active filters

### Requirement 6: 数据导出支持

**User Story:** As a system administrator, I want the user keywords configuration to be exported to the frontend data file, so that the web interface can access the keyword lists.

#### Acceptance Criteria

1. WHEN generating the index.json data file, THE Data_Manager SHALL include the user keywords configuration
2. THE Data_Manager SHALL export user keywords in a format that includes user name and keyword list
3. WHEN the configuration changes, THE Data_Manager SHALL update the exported data on the next data generation run
