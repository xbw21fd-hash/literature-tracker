# 仓库全面优化设计(2026-06-10)

## 背景

四路只读探索(Python 管线 / CI / 前端 / 仓库卫生)+ 人工核实后的结论:

- `.git` 468MB,其中约 64% 来自 `data/*.json` 与 `docs/data/*.json` **双份追踪**同一内容
  (history.json 21MB、index.json 11MB、ai_relevant.json 12MB 每日重写两份入库);
  而三条 Pages 部署路径中 deploy-on-push.yml 本就有 `cp data/* docs/data/`,
  fetch.yml / weekly-summary.yml 的 deploy job 缺这一步(它们目前依赖已提交的 docs/data)。
- 根目录约 20 个一次性/废弃脚本(fix_*、generate_with_* 实验簇、auto_daily 本地自动化簇)、
  8 份"施工完成总结"MD、空文件(test_system.py、verify-deployment.html)、test_output.txt 等。
- 6 个 workflow `fetch-depth: 0` 每次拉全史;周日 00:00 UTC fetch 与 weekly 必撞车;
  test.yml rebase 逻辑有错;backfill-weekly 无 push 重试;部分 job 无 timeout。
- 前端:sw.js 写了但**从未注册**,且预缓存用绝对路径(`/index.html`)——在项目子路径
  (`/literature-tracker/`)下注册必然安装失败,`/daily/` 匹配同样失效;data JSON 走
  cache-first 会把用户锁死在旧数据上。4 个 test-*.html 死页面公开发布;每日页内联
  CSS 重复(173 页 × ~12KB ≈ 2MB)。
- 代码缺陷:notion_tg_notifier 3 处 requests 无 timeout;rss_generator.py:193 读
  `docs/data/index.json`(解除追踪后 CI 全新 checkout 会缺文件);若干 json.load 裸奔。
- 本地测试:91 通过 / 3 失败,失败全因本机无 bs4(CI 有依赖会全量跑)。

## 目标

在**不改变系统对外行为**(站点功能、管线产出、部署架构)的前提下:

1. 止住 git 膨胀的最大来源:解除 `docs/data/` 追踪,部署时复制
2. 清除死代码与过时文档(全部 git 可恢复)
3. 修复已确认缺陷(网络超时、json 容错、文件句柄)
4. CI 提效:浅克隆、错峰、重试、超时、smoke 全量化
5. 前端修复:sw.js 改相对路径并真正启用、死资源下线、预连接提示
6. 生成器:每日页公共 CSS 外提(仅影响未来页面)、海报懒加载
7. README 重写为反映现状的工程文档;本地测试器对缺失三方依赖优雅降级

## 非目标(刻意不做)

- **git 历史重写**(瘦身 .git 需 force push,破坏性,留给用户决策;附手册)
- weekly_summary.py(2488 行)等大模块拆分——行为风险大,本地无法全量测试
- HTML 模板/工具函数跨文件去重——收益/风险比低,列入后续建议
- 部署架构调整——经核实三条部署路径各司其职(deploy-on-push 以 commit 消息前缀
  排除 fetch/weekly 的自动提交,后两者自带 deploy job),无重复部署

## 批次(每批独立 commit,前后跑 `python3 run_tests.py`)

| 批 | 内容 | 风险 | 关键验证 |
|----|------|------|----------|
| B0 | 本设计 + 实施计划文档 | 无 | — |
| B1 | docs/data 解耦:管线读写改指 data/、workflow 补 cp、git rm --cached、.gitignore | 中 | 枚举全部 `docs/data` 引用;前端 fetch 集合 ⊆ data/;test_rss_generation |
| B2 | 死文件删除 + 文档归档 archive/ | 低 | 逐文件零引用 grep 门禁;test_code_fixes/test_actions 兼容 |
| B3 | 测试基建:run_tests.py 缺依赖降级 skip;test_docs_assets.py 资产存在性回归 | 低 | 本地 3 失败 → 0 失败(变 skip) |
| B4 | 缺陷修复(测试先行):notion 超时、run_optimized_sync json 容错、run_deep with-open、rss_fetcher 报错带类型 | 低 | 新增 mock 测试 |
| B5 | CI:fetch-depth 1×6、weekly 错峰 01:00、backfill-weekly 重试、test.yml rebase 修复、timeout、smoke→run_tests.py | 中(无法本地执行) | YAML 解析校验;test_actions.py 作为 CI 不变量测试更新 |
| B6 | 前端:sw.js 重写+注册、死资源删除、preconnect、(视内联脚本而定)defer | 中 | test_docs_assets 扩展断言;app.js 缓存版本号 bump |
| B7 | 生成器:daily-common.css 外提、海报 loading="lazy" | 中 | test_daily_pages_render 更新;本地渲染对比后还原产物 |
| B8 | README 重写、终验、总结报告 | 低 | 全量测试 + git log 审查 |

## 关键设计决策

1. **docs/data 单一事实源**:`data/` 是权威,`docs/data/` 仅为部署产物。管线一律
   读写 `data/`;三个 deploy job(deploy-on-push 已有、fetch、weekly 补上)在
   upload-pages-artifact 前 `cp -r data/* docs/data/`。fetch/backfill-daily 的
   "复制并提交 docs/data"步骤删除。已验证:站点 JS 只 fetch `data/index.json`
   与 `data/chunk_*.json`(后者需在 B1 核实是否存在/是否死路径)。
2. **删除而非归档死脚本**:git 历史即归档。仅"施工总结 MD"移入 `archive/`
   (根目录,不在 docs/ 下,避免发布到 Pages),因其有人读价值。
3. **sw.js 必须先修后注册**:相对路径预缓存 + 仅含已验证存在的文件 + data/feed
   network-first + 版本号 bump;注册失败静默。这是把"文档承诺但从未生效的 PWA"
   兑现,且策略保证不会锁死旧数据。
4. **defer 仅在安全时加**:index.html:275-277 三个脚本位于 body 尾部,其后 278 行
   还有内联脚本;若内联脚本同步依赖 app.js 全局符号则不加 defer(收益本就小)。
5. **生成器改动只影响未来页面**:不批量重渲染历史页(避免 173 个文件的 git churn
   恰好加剧膨胀——与本次优化目标相悖)。
6. **分支不推送**:全部工作在 `chore/repo-optimization`,合并/推送由用户决定;
   CI 改动需在合并后首个周期人工观察。

## 风险与回滚

- 每批独立 commit,可单独 revert;所有删除 git 可恢复。
- 不触碰 `data/`(管线状态)与 `articles/`(文献库)的内容。
- B1 最大风险是"某处仍读 docs/data 而 CI 新 checkout 缺文件" → 以全仓库枚举
  + 测试套件 + smoke(CI 合并后)三层兜底。
- B5 无法本地执行 → 改动保持最小、逐文件 YAML 校验、test_actions.py 固化不变量。
