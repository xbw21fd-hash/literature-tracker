# 文献追踪系统 - 测试指南

## 测试概述

本文档提供完整的测试指南，帮助验证系统的功能和性能。

## 功能测试

### 1. 数据加载测试

**测试场景**: 验证数据加载功能

**测试步骤**:
1. 清除浏览器缓存和IndexedDB
2. 刷新页面
3. 观察加载过程

**预期结果**:
- ✅ 显示"加载中..."提示
- ✅ 数据在3秒内加载完成
- ✅ 显示正确的文献数量
- ✅ 控制台输出"✅ 从缓存加载"或"✅ 已缓存"

**验证命令**:
```javascript
// 在浏览器控制台执行
console.log(`文献总数: ${allArticles.length}`);
console.log(`IndexedDB状态:`, indexedDBManager ? '已初始化' : '未初始化');
```

### 2. 缓存功能测试

**测试场景**: 验证IndexedDB缓存

**测试步骤**:
1. 首次加载页面（从网络加载）
2. 刷新页面（从缓存加载）
3. 比较加载时间

**预期结果**:
- ✅ 首次加载: ~2-3秒
- ✅ 缓存加载: <1秒
- ✅ 控制台显示"✅ 从缓存加载 XXX 篇文献"

**验证命令**:
```javascript
// 查看缓存大小
const size = await indexedDBManager.getStorageSize();
console.log(`缓存使用: ${size.usagePercent}%`);
console.log(`已用空间: ${(size.usage / 1024 / 1024).toFixed(2)}MB`);
```

### 3. 搜索功能测试

**测试场景**: 验证倒排索引搜索

**测试步骤**:
1. 在搜索框输入"machine learning"
2. 观察搜索结果
3. 切换搜索模式（普通/正则/布尔）
4. 测试不同查询

**预期结果**:
- ✅ 搜索响应时间 <100ms
- ✅ 结果准确匹配关键词
- ✅ 支持正则表达式搜索
- ✅ 支持布尔运算符（AND/OR/NOT）

**测试用例**:
```
普通搜索: machine learning
正则搜索: ferro.*electric
布尔搜索: (AI OR ML) AND materials
```

**验证命令**:
```javascript
// 查看索引统计
const stats = invertedIndexSearchEngine.getIndexStats();
console.log(`索引词数: ${stats.totalWords}`);
console.log(`文献数: ${stats.totalDocuments}`);
console.log(`构建时间: ${stats.buildTime.toFixed(2)}ms`);
```

### 4. 虚拟滚动测试

**测试场景**: 验证大数据集滚动性能

**测试步骤**:
1. 加载大量文献（>50篇）
2. 快速滚动列表
3. 观察滚动流畅度
4. 检查内存占用

**预期结果**:
- ✅ 滚动流畅，无卡顿
- ✅ 帧率保持60fps
- ✅ 内存占用稳定
- ✅ 只渲染可见项

**验证命令**:
```javascript
// 查看虚拟滚动状态
if (virtualScrollManager) {
    console.log('虚拟滚动已启用');
    console.log(`总项数: ${filteredArticles.length}`);
}
```

### 5. Service Worker测试

**测试场景**: 验证离线功能

**测试步骤**:
1. 正常访问页面
2. 打开Chrome DevTools → Application → Service Workers
3. 勾选"Offline"模拟离线
4. 刷新页面

**预期结果**:
- ✅ Service Worker已注册
- ✅ 离线时页面正常加载
- ✅ 静态资源从缓存加载
- ✅ 已缓存的数据可访问

**验证命令**:
```javascript
// 查看Service Worker状态
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.getRegistrations().then(regs => {
        console.log(`Service Worker数量: ${regs.length}`);
        regs.forEach(reg => console.log(`状态: ${reg.active ? '已激活' : '未激活'}`));
    });
}
```

### 6. PWA安装测试

**测试场景**: 验证PWA安装功能

**测试步骤**:
1. 在Chrome中访问页面
2. 查看地址栏是否显示安装图标
3. 点击安装
4. 验证独立窗口打开

**预期结果**:
- ✅ 显示安装提示
- ✅ 可以安装到桌面
- ✅ 独立窗口运行
- ✅ 显示应用图标

### 7. 性能监控测试

**测试场景**: 验证性能监控功能

**测试步骤**:
1. 点击右下角⚡按钮
2. 查看性能面板
3. 观察实时指标
4. 导出性能报告

**预期结果**:
- ✅ 显示FCP/LCP/FID/CLS指标
- ✅ 显示内存使用情况
- ✅ 显示性能图表
- ✅ 可以导出JSON报告

**验证命令**:
```javascript
// 查看性能指标
const metrics = performanceMonitor.getMetrics();
console.log('性能指标:', metrics);

// 导出报告
const report = performanceMonitor.exportReport();
console.log('性能报告:', report);
```

## 性能测试

### 1. 加载性能测试

**测试指标**:
- 首次加载时间 (FCP)
- 最大内容绘制 (LCP)
- 首次输入延迟 (FID)
- 累积布局偏移 (CLS)

**测试方法**:
1. 打开Chrome DevTools → Lighthouse
2. 选择"Performance"类别
3. 点击"Generate report"
4. 查看评分和指标

**目标值**:
- FCP: <1.8s ✅
- LCP: <2.5s ✅
- FID: <100ms ✅
- CLS: <0.1 ✅

### 2. 搜索性能测试

**测试方法**:
```javascript
// 测试搜索性能
const testSearch = (query) => {
    const start = performance.now();
    const results = invertedIndexSearchEngine.search(query);
    const duration = performance.now() - start;
    console.log(`搜索"${query}": ${results.length}个结果, 耗时${duration.toFixed(2)}ms`);
    return duration;
};

// 运行测试
testSearch('machine learning');
testSearch('ferroelectric');
testSearch('neural network');
```

**目标值**: <100ms ✅

### 3. 滚动性能测试

**测试方法**:
1. 打开Chrome DevTools → Performance
2. 点击"Record"
3. 快速滚动页面5秒
4. 停止录制
5. 查看帧率图表

**目标值**: 60fps ✅

### 4. 内存性能测试

**测试方法**:
```javascript
// 监控内存使用
if (performance.memory) {
    const memory = performance.memory;
    console.log(`已用内存: ${(memory.usedJSHeapSize / 1024 / 1024).toFixed(2)}MB`);
    console.log(`总内存: ${(memory.totalJSHeapSize / 1024 / 1024).toFixed(2)}MB`);
    console.log(`内存限制: ${(memory.jsHeapSizeLimit / 1024 / 1024).toFixed(2)}MB`);
    console.log(`使用率: ${(memory.usedJSHeapSize / memory.jsHeapSizeLimit * 100).toFixed(2)}%`);
}
```

**目标值**: <500MB ✅

## 兼容性测试

### 浏览器测试矩阵

| 浏览器 | 版本 | 测试项 | 状态 |
|--------|------|--------|------|
| Chrome | 90+ | 全部功能 | ✅ |
| Firefox | 88+ | 全部功能 | ✅ |
| Safari | 14+ | 全部功能 | ✅ |
| Edge | 90+ | 全部功能 | ✅ |
| Opera | 76+ | 全部功能 | ✅ |

### 设备测试

| 设备类型 | 分辨率 | 测试项 | 状态 |
|----------|--------|--------|------|
| 桌面 | 1920x1080 | 全部功能 | ✅ |
| 笔记本 | 1366x768 | 全部功能 | ✅ |
| 平板 | 768x1024 | 响应式布局 | ✅ |
| 手机 | 375x667 | 移动端优化 | ✅ |

## 压力测试

### 大数据集测试

**测试场景**: 10,000篇文献

**测试步骤**:
1. 准备10,000篇测试数据
2. 加载到系统
3. 测试各项功能
4. 监控性能指标

**预期结果**:
- ✅ 加载时间 <3s
- ✅ 搜索响应 <100ms
- ✅ 滚动流畅 60fps
- ✅ 内存占用 <500MB

### 并发操作测试

**测试场景**: 同时执行多个操作

**测试步骤**:
1. 快速切换筛选条件
2. 连续搜索不同关键词
3. 快速滚动列表
4. 批量标记文献

**预期结果**:
- ✅ 操作响应及时
- ✅ 无界面卡顿
- ✅ 无数据错误
- ✅ 无内存泄漏

## 回归测试清单

### 核心功能
- [ ] 文献加载和显示
- [ ] 搜索功能（普通/正则/布尔）
- [ ] 筛选功能（分类/期刊/日期/阅读状态）
- [ ] 排序功能
- [ ] 收藏功能
- [ ] 阅读状态管理
- [ ] 稍后阅读
- [ ] 导出功能（BibTeX/RIS）

### 高级功能
- [ ] 主题切换
- [ ] 键盘快捷键
- [ ] 虚拟滚动
- [ ] 懒加载
- [ ] 搜索历史
- [ ] 悬停预览

### 性能功能
- [ ] IndexedDB缓存
- [ ] 倒排索引搜索
- [ ] 对象池
- [ ] 性能监控
- [ ] Service Worker
- [ ] PWA安装

### UI/UX
- [ ] 响应式布局
- [ ] 移动端适配
- [ ] 深色模式
- [ ] 动画效果
- [ ] 加载提示
- [ ] 错误提示

## 自动化测试脚本

### 快速功能测试

```javascript
// 在浏览器控制台执行
async function quickTest() {
    console.log('=== 快速功能测试 ===');
    
    // 1. 数据加载
    console.log(`✅ 文献总数: ${allArticles.length}`);
    
    // 2. IndexedDB
    if (indexedDBManager) {
        const size = await indexedDBManager.getStorageSize();
        console.log(`✅ 缓存使用: ${size.usagePercent}%`);
    }
    
    // 3. 搜索引擎
    if (invertedIndexSearchEngine) {
        const stats = invertedIndexSearchEngine.getIndexStats();
        console.log(`✅ 索引词数: ${stats.totalWords}`);
    }
    
    // 4. Service Worker
    if ('serviceWorker' in navigator) {
        const regs = await navigator.serviceWorker.getRegistrations();
        console.log(`✅ Service Worker: ${regs.length > 0 ? '已注册' : '未注册'}`);
    }
    
    // 5. 性能监控
    if (performanceMonitor) {
        const metrics = performanceMonitor.getMetrics();
        console.log(`✅ 性能指标: ${Object.keys(metrics).length}项`);
    }
    
    console.log('=== 测试完成 ===');
}

quickTest();
```

### 性能基准测试

```javascript
// 性能基准测试
async function performanceBenchmark() {
    console.log('=== 性能基准测试 ===');
    
    // 1. 搜索性能
    const searchStart = performance.now();
    invertedIndexSearchEngine.search('machine learning');
    const searchTime = performance.now() - searchStart;
    console.log(`搜索耗时: ${searchTime.toFixed(2)}ms ${searchTime < 100 ? '✅' : '❌'}`);
    
    // 2. 筛选性能
    const filterStart = performance.now();
    filterArticles();
    const filterTime = performance.now() - filterStart;
    console.log(`筛选耗时: ${filterTime.toFixed(2)}ms ${filterTime < 500 ? '✅' : '❌'}`);
    
    // 3. 渲染性能
    const renderStart = performance.now();
    renderArticles();
    const renderTime = performance.now() - renderStart;
    console.log(`渲染耗时: ${renderTime.toFixed(2)}ms ${renderTime < 200 ? '✅' : '❌'}`);
    
    // 4. 内存使用
    if (performance.memory) {
        const memoryMB = performance.memory.usedJSHeapSize / 1024 / 1024;
        console.log(`内存使用: ${memoryMB.toFixed(2)}MB ${memoryMB < 500 ? '✅' : '❌'}`);
    }
    
    console.log('=== 测试完成 ===');
}

performanceBenchmark();
```

## 问题排查

### 常见问题

**问题1**: 数据加载失败
- 检查网络连接
- 检查data/index.json文件是否存在
- 查看浏览器控制台错误信息

**问题2**: 搜索无结果
- 确认索引已构建（查看控制台日志）
- 检查搜索关键词拼写
- 尝试切换搜索模式

**问题3**: Service Worker未注册
- 确认使用HTTPS或localhost
- 检查sw.js文件是否存在
- 查看Application → Service Workers面板

**问题4**: 性能下降
- 清除浏览器缓存
- 清除IndexedDB数据
- 检查内存使用情况
- 查看性能监控面板

### 调试命令

```javascript
// 查看所有全局变量
console.log({
    allArticles: allArticles.length,
    filteredArticles: filteredArticles.length,
    indexedDBManager: !!indexedDBManager,
    invertedIndexSearchEngine: !!invertedIndexSearchEngine,
    serviceWorkerManager: !!serviceWorkerManager,
    performanceMonitor: !!performanceMonitor,
    virtualScrollManager: !!virtualScrollManager
});

// 清除所有缓存
async function clearAllCaches() {
    // 清除IndexedDB
    if (indexedDBManager) {
        await indexedDBManager.clear();
        console.log('✅ IndexedDB已清除');
    }
    
    // 清除Service Worker缓存
    if (serviceWorkerManager) {
        await serviceWorkerManager.clearCache();
        console.log('✅ Service Worker缓存已清除');
    }
    
    // 清除搜索缓存
    if (searchCache) {
        searchCache.clear();
        console.log('✅ 搜索缓存已清除');
    }
    
    console.log('✅ 所有缓存已清除，请刷新页面');
}
```

## 测试报告模板

```markdown
# 测试报告

**测试日期**: YYYY-MM-DD
**测试人员**: [姓名]
**测试环境**: [浏览器] [版本] / [操作系统]

## 功能测试结果

| 功能 | 状态 | 备注 |
|------|------|------|
| 数据加载 | ✅/❌ | |
| 搜索功能 | ✅/❌ | |
| 筛选功能 | ✅/❌ | |
| 缓存功能 | ✅/❌ | |
| 离线功能 | ✅/❌ | |

## 性能测试结果

| 指标 | 目标 | 实际 | 状态 |
|------|------|------|------|
| 加载时间 | <3s | | ✅/❌ |
| 搜索响应 | <100ms | | ✅/❌ |
| 滚动帧率 | 60fps | | ✅/❌ |
| 内存占用 | <500MB | | ✅/❌ |

## 发现的问题

1. [问题描述]
   - 严重程度: 高/中/低
   - 复现步骤: ...
   - 预期结果: ...
   - 实际结果: ...

## 总结

[测试总结]
```

---

**版本**: 1.0  
**日期**: 2024-12-28  
**维护者**: Kiro AI Assistant
