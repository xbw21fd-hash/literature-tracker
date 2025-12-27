# Service Worker 实现指南

## 概述

本文档描述了文献追踪系统的 Service Worker 实现,提供离线支持和性能优化。

## 架构

### 文件结构

```
docs/
├── sw.js                           # Service Worker 主文件
├── manifest.json                   # PWA 清单文件
├── performance-optimization.js     # 包含 ServiceWorkerManager 类
└── index.html                      # 引用 manifest.json
```

### 核心组件

#### 1. Service Worker (sw.js)

负责拦截网络请求并实现缓存策略。

**缓存策略**:
- **静态资源** (HTML, CSS, JS): Cache First - 优先使用缓存,提高加载速度
- **数据文件** (JSON): Network First - 优先使用网络,确保数据最新
- **其他资源**: Cache First with Network Fallback

**缓存版本**:
- `static-v5.1`: 静态资源缓存
- `data-v5.1`: 数据文件缓存

#### 2. ServiceWorkerManager 类

管理 Service Worker 的生命周期和更新。

**主要方法**:
- `register()`: 注册 Service Worker
- `update()`: 检查更新
- `clearCache()`: 清除缓存
- `applyUpdate()`: 应用更新
- `unregister()`: 注销 Service Worker

## 使用方法

### 自动初始化

Service Worker 在页面加载时自动初始化:

```javascript
// 在 initPerformanceOptimization() 中自动调用
serviceWorkerManager = new ServiceWorkerManager();
await serviceWorkerManager.register();
```

### 手动操作

#### 检查更新

```javascript
if (window.serviceWorkerManager) {
    await window.serviceWorkerManager.update();
}
```

#### 清除缓存

```javascript
if (window.serviceWorkerManager) {
    await window.serviceWorkerManager.clearCache();
}
```

#### 注销 Service Worker

```javascript
if (window.serviceWorkerManager) {
    await window.serviceWorkerManager.unregister();
}
```

## 缓存策略详解

### Cache First (静态资源)

```
请求 → 检查缓存 → 有缓存? 
    ├─ 是 → 返回缓存
    └─ 否 → 网络请求 → 缓存响应 → 返回响应
```

**优点**: 快速加载,减少网络请求
**适用**: HTML, CSS, JS, 图片等不常变化的资源

### Network First (数据文件)

```
请求 → 网络请求 → 成功?
    ├─ 是 → 更新缓存 → 返回响应
    └─ 否 → 检查缓存 → 返回缓存
```

**优点**: 确保数据最新,离线时有备份
**适用**: JSON 数据文件

## 更新机制

### 自动更新检查

Service Worker 每小时自动检查更新:

```javascript
setInterval(() => {
    if (this.registration) {
        this.registration.update();
    }
}, 60 * 60 * 1000);
```

### 更新通知

当检测到新版本时,显示更新通知:

```
┌─────────────────────────────────┐
│ 🔄 发现新版本                    │
│ [立即更新] [稍后]                │
└─────────────────────────────────┘
```

用户点击"立即更新"后:
1. 告诉等待的 Service Worker 跳过等待
2. 监听控制器变化
3. 自动刷新页面

## 离线支持

### 离线可用资源

- ✅ 首页 (index.html)
- ✅ 样式表 (style.css)
- ✅ 脚本文件 (app.js, performance-optimization.js, advanced-features.js)
- ✅ 已缓存的数据文件 (data/index.json)

### 离线不可用

- ❌ 未缓存的数据文件
- ❌ 外部链接
- ❌ 原文链接

## 调试

### Chrome DevTools

1. 打开 DevTools (F12)
2. 切换到 "Application" 标签
3. 左侧选择 "Service Workers"

**可用操作**:
- 查看 Service Worker 状态
- 手动更新
- 注销
- 模拟离线

### 查看缓存

1. 在 "Application" 标签中
2. 左侧选择 "Cache Storage"
3. 展开查看缓存内容

### 控制台日志

Service Worker 会输出详细日志:

```
✅ Service Worker 注册成功: /
✅ Service Worker 初始化完成
[SW] Installing...
[SW] Caching static assets
[SW] Activating...
```

## 性能指标

### 首次加载

- 注册时间: < 100ms
- 缓存静态资源: < 500ms

### 后续加载

- 静态资源加载: < 50ms (从缓存)
- 数据文件加载: < 200ms (网络) 或 < 50ms (缓存)

### 离线加载

- 完整页面加载: < 100ms (全部从缓存)

## 最佳实践

### 1. 缓存版本管理

每次更新时修改缓存版本:

```javascript
const STATIC_CACHE = 'static-v5.2';  // 递增版本号
const DATA_CACHE = 'data-v5.2';
```

### 2. 清理旧缓存

在 activate 事件中清理旧版本缓存:

```javascript
caches.keys().then((cacheNames) => {
    return Promise.all(
        cacheNames
            .filter((name) => name !== STATIC_CACHE && name !== DATA_CACHE)
            .map((name) => caches.delete(name))
    );
});
```

### 3. 跳过等待

新版本 Service Worker 立即激活:

```javascript
self.addEventListener('install', (event) => {
    event.waitUntil(
        // ... 缓存操作
        .then(() => self.skipWaiting())
    );
});
```

### 4. 立即接管

激活后立即接管所有客户端:

```javascript
self.addEventListener('activate', (event) => {
    event.waitUntil(
        // ... 清理操作
        .then(() => self.clients.claim())
    );
});
```

## 故障排除

### Service Worker 未注册

**可能原因**:
- 浏览器不支持 Service Worker
- 非 HTTPS 环境 (localhost 除外)
- 文件路径错误

**解决方法**:
1. 检查浏览器兼容性
2. 确保使用 HTTPS 或 localhost
3. 检查 sw.js 文件路径

### 缓存未更新

**可能原因**:
- Service Worker 未更新
- 缓存版本未修改

**解决方法**:
1. 手动注销 Service Worker
2. 清除浏览器缓存
3. 修改缓存版本号

### 离线功能不工作

**可能原因**:
- 资源未缓存
- 缓存策略错误

**解决方法**:
1. 检查 Cache Storage 中的内容
2. 确认资源在 STATIC_ASSETS 列表中
3. 检查 fetch 事件处理逻辑

## 浏览器兼容性

| 浏览器 | 版本 | 支持 |
|--------|------|------|
| Chrome | 40+ | ✅ |
| Firefox | 44+ | ✅ |
| Safari | 11.1+ | ✅ |
| Edge | 17+ | ✅ |
| Opera | 27+ | ✅ |
| IE | - | ❌ |

## 安全考虑

### HTTPS 要求

Service Worker 只能在 HTTPS 环境下运行 (localhost 除外)。

### 同源策略

Service Worker 只能控制同源的请求。

### 缓存敏感数据

避免缓存包含敏感信息的响应。

## 未来改进

### 计划功能

- [ ] 后台同步 (Background Sync)
- [ ] 推送通知 (Push Notifications)
- [ ] 预缓存策略优化
- [ ] 缓存大小限制
- [ ] 缓存过期策略

### 性能优化

- [ ] 使用 Workbox 库
- [ ] 实现更智能的缓存策略
- [ ] 添加缓存分析工具

## 参考资料

- [Service Worker API - MDN](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [Progressive Web Apps - Google](https://web.dev/progressive-web-apps/)
- [Workbox - Google](https://developers.google.com/web/tools/workbox)

---

**版本**: 1.0  
**日期**: 2024-12-28  
**作者**: 于宏宇（Hongyu Yu）with AI
