# Design Document - Literature UI Advanced Features

## Overview

本设计文档描述了文献追踪系统高级UI功能的实现方案，包括布局切换、性能优化、移动端优化和高级分析功能。系统将采用模块化设计，确保各功能独立且可扩展。

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                     │
├─────────────────────────────────────────────────────────────┤
│  Layout Manager  │  Font Manager  │  Shortcut Manager       │
├─────────────────────────────────────────────────────────────┤
│  Preview System  │  Virtual Scroll │  Lazy Load Manager     │
├─────────────────────────────────────────────────────────────┤
│  Incremental Loader │ Cache Manager │ Mobile Adapter        │
├─────────────────────────────────────────────────────────────┤
│  Trend Predictor │  Topic Evolution Analyzer                │
├─────────────────────────────────────────────────────────────┤
│                     Data Layer                               │
│  Local Storage  │  Session Storage  │  IndexedDB            │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction

1. **Layout Manager** 控制文献卡片的显示方式
2. **Font Manager** 管理全局字体大小
3. **Shortcut Manager** 处理键盘快捷键
4. **Preview System** 提供悬停预览功能
5. **Virtual Scroll** 优化大量数据渲染
6. **Lazy Load Manager** 按需加载图片资源
7. **Incremental Loader** 分批加载文献数据
8. **Cache Manager** 缓存搜索结果
9. **Mobile Adapter** 适配移动端布局
10. **Trend Predictor** 预测研究趋势
11. **Topic Evolution Analyzer** 分析主题演化

## Components and Interfaces

### 1. Layout Manager

```javascript
class LayoutManager {
  constructor() {
    this.currentLayout = 'list'; // 'list', 'grid', 'compact'
    this.layouts = {
      list: { columns: 1, spacing: 'normal', details: 'full' },
      grid: { columns: 'auto', spacing: 'normal', details: 'summary' },
      compact: { columns: 1, spacing: 'tight', details: 'minimal' }
    };
  }
  
  setLayout(layoutName) {
    // Switch to specified layout
    // Save to localStorage
    // Apply CSS classes
    // Trigger re-render
  }
  
  getLayout() {
    // Return current layout configuration
  }
  
  restoreLayout() {
    // Load layout from localStorage
  }
}
```

### 2. Font Manager

```javascript
class FontManager {
  constructor() {
    this.sizes = ['xs', 'sm', 'md', 'lg', 'xl'];
    this.currentSize = 'md';
    this.baseSizes = {
      xs: 12, sm: 14, md: 16, lg: 18, xl: 20
    };
  }
  
  setFontSize(size) {
    // Update CSS custom properties
    // Save to localStorage
  }
  
  increaseFontSize() {
    // Move to next larger size
  }
  
  decreaseFontSize() {
    // Move to next smaller size
  }
  
  resetFontSize() {
    // Reset to default 'md'
  }
}
```

### 3. Shortcut Manager

```javascript
class ShortcutManager {
  constructor() {
    this.shortcuts = new Map();
    this.defaultShortcuts = {
      'nextArticle': 'j',
      'prevArticle': 'k',
      'toggleExpand': 'Enter',
      'openLink': 'o',
      'toggleFavorite': 's',
      'toggleRead': 'r',
      'toggleReadLater': 'l',
      'increaseFontSize': 'Ctrl+=',
      'decreaseFontSize': 'Ctrl+-',
      'search': '/',
      'toggleTheme': 't'
    };
  }
  
  registerShortcut(action, keys, handler) {
    // Register a keyboard shortcut
  }
  
  unregisterShortcut(action) {
    // Remove a shortcut
  }
  
  updateShortcut(action, newKeys) {
    // Update shortcut binding
  }
  
  handleKeyPress(event) {
    // Process keyboard events
  }
  
  getConflicts(keys) {
    // Check for conflicting shortcuts
  }
  
  exportShortcuts() {
    // Export custom shortcuts
  }
  
  importShortcuts(data) {
    // Import custom shortcuts
  }
}
```

### 4. Preview System

```javascript
class PreviewSystem {
  constructor() {
    this.tooltip = null;
    this.hoverTimer = null;
    this.hideTimer = null;
    this.hoverDelay = 500;
    this.hideDelay = 200;
  }
  
  showPreview(article, targetElement) {
    // Display preview tooltip
    // Position near target element
    // Avoid screen edges
  }
  
  hidePreview() {
    // Hide tooltip with delay
  }
  
  createTooltip(article) {
    // Create tooltip DOM element
    // Include full abstract
    // Add styling
  }
  
  positionTooltip(tooltip, target) {
    // Calculate optimal position
    // Adjust for screen boundaries
  }
}
```

### 5. Virtual Scroll Manager

```javascript
class VirtualScrollManager {
  constructor(container, items, renderItem) {
    this.container = container;
    this.items = items;
    this.renderItem = renderItem;
    this.visibleRange = { start: 0, end: 0 };
    this.itemHeight = 200; // Average height
    this.buffer = 10;
  }
  
  init() {
    // Setup scroll listener
    // Calculate initial visible range
    // Render initial items
  }
  
  onScroll() {
    // Calculate new visible range
    // Update rendered items
    // Maintain scroll position
  }
  
  calculateVisibleRange() {
    // Determine which items should be visible
  }
  
  renderVisibleItems() {
    // Render only visible items
    // Add buffer items
  }
  
  updateItemHeight(index, height) {
    // Update height cache for item
  }
  
  scrollToIndex(index) {
    // Scroll to specific item
  }
}
```

### 6. Lazy Load Manager

```javascript
class LazyLoadManager {
  constructor() {
    this.observer = null;
    this.loadedImages = new Set();
    this.failedImages = new Set();
  }
  
  init() {
    // Create Intersection Observer
    // Set threshold and rootMargin
  }
  
  observe(imageElement) {
    // Add image to observation
  }
  
  loadImage(imageElement) {
    // Load image source
    // Handle load/error events
    // Update placeholders
  }
  
  unobserve(imageElement) {
    // Remove from observation
  }
  
  retryFailed() {
    // Retry loading failed images
  }
}
```

### 7. Incremental Loader

```javascript
class IncrementalLoader {
  constructor(dataSource, batchSize = 50) {
    this.dataSource = dataSource;
    this.batchSize = batchSize;
    this.currentBatch = 0;
    this.loading = false;
    this.allLoaded = false;
  }
  
  loadNextBatch() {
    // Load next batch of items
    // Update loading state
    // Trigger render
  }
  
  reset() {
    // Reset to first batch
  }
  
  hasMore() {
    // Check if more data available
  }
  
  setupAutoLoad() {
    // Setup scroll-based auto-loading
  }
}
```

### 8. Cache Manager

```javascript
class CacheManager {
  constructor(maxSize = 50) {
    this.cache = new Map();
    this.maxSize = maxSize;
    this.accessOrder = [];
  }
  
  set(key, value) {
    // Store value in cache
    // Implement LRU eviction
  }
  
  get(key) {
    // Retrieve from cache
    // Update access order
  }
  
  has(key) {
    // Check if key exists
  }
  
  clear() {
    // Clear all cache
  }
  
  evict() {
    // Remove least recently used item
  }
  
  getStats() {
    // Return cache statistics
  }
}
```

### 9. Mobile Adapter

```javascript
class MobileAdapter {
  constructor() {
    this.isMobile = false;
    this.touchStartX = 0;
    this.touchStartY = 0;
    this.swipeThreshold = 50;
  }
  
  detectMobile() {
    // Detect mobile device
    // Check screen width
  }
  
  setupTouchHandlers() {
    // Setup swipe gestures
    // Setup pull-to-refresh
  }
  
  handleSwipe(direction, element) {
    // Handle swipe left/right
    // Trigger appropriate actions
  }
  
  setupBottomNav() {
    // Create bottom navigation
    // Replace sidebar
  }
  
  optimizeTouchTargets() {
    // Ensure minimum 44x44px
  }
}
```

### 10. Trend Predictor

```javascript
class TrendPredictor {
  constructor(articles) {
    this.articles = articles;
    this.timeWindow = 6; // months
  }
  
  analyzeGrowthRates() {
    // Calculate topic growth rates
    // Compare time periods
  }
  
  predictTrends() {
    // Use linear regression
    // Calculate confidence intervals
  }
  
  identifyEmergingTopics() {
    // Find topics with rapid growth
  }
  
  identifyDecliningTopics() {
    // Find topics with negative growth
  }
  
  visualizePredictions() {
    // Create trend charts
    // Show confidence levels
  }
}
```

### 11. Topic Evolution Analyzer

```javascript
class TopicEvolutionAnalyzer {
  constructor(articles) {
    this.articles = articles;
    this.timeSlices = [];
  }
  
  createTimeSlices(interval = 'month') {
    // Divide data into time periods
  }
  
  extractTopicsPerSlice() {
    // Extract keywords for each period
  }
  
  calculateTopicSimilarity(topic1, topic2) {
    // Calculate similarity between topics
  }
  
  trackTopicEvolution() {
    // Track how topics change over time
  }
  
  identifyMergers() {
    // Find topics that merged
  }
  
  identifySplits() {
    // Find topics that split
  }
  
  visualizeEvolution() {
    // Create Sankey or stream graph
  }
}
```

## Data Models

### Layout Configuration

```javascript
{
  type: 'list' | 'grid' | 'compact',
  columns: number | 'auto',
  spacing: 'tight' | 'normal' | 'loose',
  details: 'minimal' | 'summary' | 'full'
}
```

### Font Configuration

```javascript
{
  size: 'xs' | 'sm' | 'md' | 'lg' | 'xl',
  baseSize: number, // in pixels
  lineHeight: number // multiplier
}
```

### Shortcut Configuration

```javascript
{
  action: string,
  keys: string, // e.g., 'Ctrl+K', 'Alt+Shift+F'
  description: string,
  category: string,
  handler: Function
}
```

### Cache Entry

```javascript
{
  key: string,
  value: any,
  timestamp: number,
  accessCount: number,
  size: number // estimated size in bytes
}
```

### Trend Prediction

```javascript
{
  topic: string,
  currentCount: number,
  predictedCount: number,
  growthRate: number, // percentage
  confidence: number, // 0-1
  timeframe: string, // '3 months', '6 months'
  status: 'emerging' | 'growing' | 'stable' | 'declining'
}
```

### Topic Evolution

```javascript
{
  topic: string,
  timeline: Array<{
    period: string,
    count: number,
    keywords: string[],
    relatedTopics: string[]
  }>,
  lifecycle: 'emerging' | 'growing' | 'mature' | 'declining',
  mergedFrom: string[], // topics that merged into this
  splitInto: string[] // topics this split into
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Layout Persistence
*For any* layout selection, saving and reloading the page should restore the same layout configuration.
**Validates: Requirements 1.5, 1.6**

### Property 2: Font Size Bounds
*For any* font size adjustment operation, the resulting font size should remain within the defined minimum (12px) and maximum (24px) bounds.
**Validates: Requirements 2.8**

### Property 3: Shortcut Uniqueness
*For any* set of registered shortcuts, no two different actions should be bound to the same key combination.
**Validates: Requirements 3.5, 3.6**

### Property 4: Virtual Scroll Consistency
*For any* scroll position, the set of rendered items should include all visible items plus the buffer zone, with no gaps or duplicates.
**Validates: Requirements 5.2, 5.4, 5.10**

### Property 5: Cache LRU Ordering
*For any* sequence of cache operations, when the cache is full, the least recently accessed item should be evicted first.
**Validates: Requirements 8.4**

### Property 6: Incremental Loading Completeness
*For any* dataset, loading all batches incrementally should result in the same set of items as loading all at once.
**Validates: Requirements 7.1, 7.2, 7.5**

### Property 7: Mobile Detection Consistency
*For any* screen width less than 768px, the system should activate mobile layout mode.
**Validates: Requirements 9.1**

### Property 8: Lazy Load Coverage
*For any* image element within the viewport (plus margin), the image should be loaded or in the process of loading.
**Validates: Requirements 6.2, 6.6**

### Property 9: Trend Prediction Monotonicity
*For any* topic with positive growth rate, the predicted count should be greater than or equal to the current count.
**Validates: Requirements 10.2, 10.3**

### Property 10: Topic Evolution Continuity
*For any* topic tracked across time periods, there should be no gaps in the timeline where the topic exists.
**Validates: Requirements 11.1, 11.2**

## Error Handling

### Layout Manager Errors
- Invalid layout name → fallback to 'list'
- localStorage unavailable → use in-memory state
- CSS class application fails → log error, continue

### Font Manager Errors
- Invalid size value → clamp to valid range
- CSS custom property not supported → fallback to inline styles

### Shortcut Manager Errors
- Invalid key combination → reject with error message
- Conflict detected → prevent registration, show warning
- Handler execution fails → log error, continue

### Virtual Scroll Errors
- Height calculation fails → use default height
- Scroll position invalid → reset to top
- Render function throws → skip item, log error

### Cache Manager Errors
- Storage quota exceeded → force eviction
- Serialization fails → skip caching
- Corrupted cache data → clear cache

### Trend Predictor Errors
- Insufficient data → show warning, skip prediction
- Calculation overflow → cap at maximum value
- Invalid time range → use default range

## Testing Strategy

### Unit Tests
- Test each manager class independently
- Test edge cases (empty data, maximum values, invalid inputs)
- Test error handling paths
- Test state persistence and restoration

### Property-Based Tests
- Generate random sequences of operations
- Verify properties hold across all inputs
- Test with varying data sizes (10, 100, 1000+ items)
- Test with different screen sizes and devices

### Integration Tests
- Test interaction between components
- Test full user workflows (layout switch → font adjust → search)
- Test performance with large datasets
- Test mobile vs desktop behavior

### Performance Tests
- Measure virtual scroll performance with 1000+ items
- Measure cache hit/miss rates
- Measure lazy load efficiency
- Measure trend calculation time

### Configuration
- Minimum 100 iterations per property test
- Each test tagged with feature name and property number
- Performance benchmarks for critical paths
- Visual regression tests for layout changes
