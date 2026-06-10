# 仓库全面优化实施计划(2026-06-10)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按 specs/2026-06-10-repo-optimization-design.md,在 `chore/repo-optimization` 分支上分 8 批完成仓库优化,每批独立 commit 且 `python3 run_tests.py` 通过。

**Architecture:** data/ 为单一事实源,docs/data 退化为部署期复制产物;死代码直接删除(git 即归档);CI 不变量固化进 test_actions.py;sw.js 修复后才注册。

**Tech Stack:** Python 3.11(本地仅 stdlib + requests,无 bs4/pip)、GitHub Actions、GitHub Pages、原生 JS/Service Worker。

**执行约束:** 用户离线,自治执行;不 push;遇验证门禁不通过 → 缩小该项范围并在总结中说明,不得跳过门禁。

---

### Task 1: docs/data 解耦(B1)

**Files:**
- Modify: `rss_generator.py:193`、所有 `grep -n "docs/data" *.py` 命中的存活文件
- Modify: `.github/workflows/fetch.yml`、`weekly-summary.yml`、`backfill-daily.yml`
- Modify: `.gitignore`
- Untrack: `docs/data/**`

- [ ] **Step 1.1 枚举与核实(门禁)**
```bash
grep -n "docs/data" *.py                 # 全量清单,逐条分类:读/写/死脚本(Task 2 删)
ls docs/data/chunk_*.json data/chunk_*.json 2>/dev/null   # chunk 加载路径是否真实存在
git ls-files docs/data | sed 's|docs/data/||' | sort > /tmp/tracked_docs_data.txt
ls data/ | sort > /tmp/data_files.txt
comm -23 /tmp/tracked_docs_data.txt /tmp/data_files.txt   # docs/data 独有文件 → 必须证实无人引用
```
判定规则:存活管线文件**读** docs/data → 改读 data/;**写** docs/data(站点消费的数据文件)→ 改写 data/(部署 cp 兜底)。docs/data 独有且被引用的文件 → 中止解耦该文件并记录。

- [ ] **Step 1.2 改代码**(已知:rss_generator.py:193 `'docs/data/index.json'` → `'data/index.json'`;其余按 1.1 清单同规则处理)
- [ ] **Step 1.3 改 workflow**
  - fetch.yml fetch job:删除"复制数据到docs目录"步骤
  - fetch.yml deploy job:在"设置Pages"前插入同名 cp 步骤(`mkdir -p docs/data && cp -r data/* docs/data/`)
  - weekly-summary.yml deploy job:同上插入
  - backfill-daily.yml:删除其 cp→commit 步骤(grep `docs/data` 定位)
- [ ] **Step 1.4 解除追踪**
```bash
git rm -r -q --cached docs/data
printf '\n# 部署期从 data/ 复制,不入库\ndocs/data/\n' >> .gitignore
```
- [ ] **Step 1.5 验证** `python3 run_tests.py`(重点 test_rss_generation)+ 每个改动 yml 过 YAML 解析(本地无 pyyaml 则用 `node -e` + 简易缩进检查,或仅人工双查 diff)
- [ ] **Step 1.6 Commit** `git add -A && git commit -m "♻️ docs/data 退化为部署产物:管线只读写 data/,deploy job 部署期复制,解除 33MB×2 重复追踪"`

### Task 2: 死文件删除 + 文档归档(B2)

**Files:** Delete ~24 个文件;Create `archive/`;Modify `.gitignore`、`DEPLOYMENT_GUIDE.md`(若引用 deploy.bat)

- [ ] **Step 2.1 逐文件零引用门禁**(对下列每个 NAME)
```bash
grep -rn "NAME" --include="*.py" --include="*.yml" --include="*.sh" --include="*.md" --include="*.json" . \
  | grep -v -e "^\./archive/" -e "本计划/设计文档" -e "待删文件互引"
```
删除清单(互引视为同簇一起删):
高置信:`fix_data.py` `comprehensive_fix.py` `revert_aps_fix.py` `fix_journal_names.py` `prepare_ai_prompt.py` `gen_prompt.py` `import_zotero_bib.py` `test_system.py`(空)`test_output.txt` `verify-deployment.html`(0B)`deploy.bat` `daily_cron.sh` `cron_config.json` `.kiro/settings/`
中置信(grep 通过才删):`generate_with_openrouter.py` `generate_with_ai.py` `generate_with_local_ai.py` `generate_html_existing.py` `generate_html_only.py` `generate_ai_summary.py` `generate_recent_weeklies.py`;auto_daily 簇:`auto_daily.py` `auto_daily_stage1.py` `ai_daily_helper.py` `regenerate_daily.py`
特别核查:`test_code_fixes.py` 与 `test_actions.py` 是否 import/引用以上模块 → 若是,同步修剪对应测试。
- [ ] **Step 2.2 归档** `mkdir -p archive && git mv V5_IMPLEMENTATION_SUMMARY.md V5.1_PERFORMANCE_OPTIMIZATION_SUMMARY.md V5.1_PERFORMANCE_OPTIMIZATION_COMPLETE.md FAST_LOAD_OPTIMIZATION.md SERVICE_WORKER_IMPLEMENTATION_SUMMARY.md PROJECT_COMPLETION_SUMMARY.md FINAL_PROJECT_STATUS.md AI_DAILY_SETUP.md WEEKLY_SUMMARY_GUIDE.md archive/`
- [ ] **Step 2.3 untrack ai_responses/** `git rm -r -q --cached ai_responses && printf 'ai_responses/\ntest_output.txt\n*.log\n*.tmp\n*.bak\n' >> .gitignore`
- [ ] **Step 2.4 验证+提交** `python3 run_tests.py` → `git add -A && git commit -m "🧹 清除一次性脚本/空文件/本地遗留自动化,施工总结归档 archive/"`

### Task 3: 测试基建(B3)

**Files:** Modify `run_tests.py`;Create `test_docs_assets.py`

- [ ] **Step 3.1 run_tests.py 缺依赖降级**:import 失败时若异常为 ModuleNotFoundError 且缺的顶层模块不是仓库内文件 → 记 skipped 并打印 `⊘ {name} (missing optional dep: {mod} — skipped locally)`,不计 failed。
```python
        except ModuleNotFoundError as e:
            missing = (e.name or "").split(".")[0]
            local = os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), missing + ".py"))
            if missing and not local:
                skipped += 1
                print(f"⊘ {name} (missing optional dep: {missing} — skipped locally)")
                continue
            failures.append((name, "<import>", traceback.format_exc())); failed += 1
            print(f"✗ {name}: import error: {e}"); continue
        except Exception as e:
            ...(原逻辑保留)
```
- [ ] **Step 3.2 验证**:`python3 run_tests.py` 期望 `91 passed, 0 failed, 3+ skipped`
- [ ] **Step 3.3 新建 test_docs_assets.py**(stdlib):断言 index.html / analytics.html 中本地 `src=|href=` 资源都存在于 docs/(跳过 http(s)、data:、锚点、feed.xml 由生成器产出可豁免已存在);运行应立即通过。
- [ ] **Step 3.4 Commit** `git commit -am "✅ 本地测试器对缺失三方依赖降级为 skip;新增 docs 资产存在性回归测试"`

### Task 4: 缺陷修复,测试先行(B4)

**Files:** Create `test_notion_tg_notifier.py`;Modify `notion_tg_notifier.py`、`run_optimized_sync.py:301`、`run_deep.py:196,204,215,262`、`rss_fetcher.py:143`

- [ ] **Step 4.1 读 notion_tg_notifier.py,写失败测试**:unittest.mock.patch 模块内 `requests`,调用触发 :57/:77/:86 的最小公开函数,断言每次调用 `kwargs.get("timeout")` 非空。先跑确认 FAIL。
- [ ] **Step 4.2 实现**:三处调用补 `timeout=15`(与库内其他显式超时风格一致,以实际代码为准)。跑测试 PASS。
- [ ] **Step 4.3 run_optimized_sync.py:301**:`json.load` 包 try/except(ValueError/OSError → 空结构 + 打印警告);**run_deep.py** 四处 `json.load(open(p))` → `with open(p, encoding="utf-8") as f: json.load(f)`;**rss_fetcher.py:143** except 打印追加 `type(e).__name__`。
- [ ] **Step 4.4 验证+提交** `python3 run_tests.py` → `git commit -am "🐛 网络请求补超时;json/文件句柄健壮化;抓取失败日志带异常类型"`

### Task 5: CI 优化(B5)

**Files:** Modify 全部 9 个 workflow 中涉及项、`test_actions.py`

- [ ] **Step 5.1 先读 test_actions.py**,把它升级为 CI 不变量测试(先改测试,期望 FAIL):所有 checkout 步骤 `fetch-depth: 1`;每个 push 步骤带重试循环;fetch/weekly deploy job 含 cp data 步骤(Task 1 已加,此处断言);每个 job 有 timeout-minutes。
- [ ] **Step 5.2 改 workflow 使测试通过**:
  - 6 处 `fetch-depth: 0` → `1`(fetch、generate-deep、weekly-summary、backfill-daily、backfill-weekly、backfill-zh;代码已验证零处依赖 git 历史)
  - weekly-summary cron `'0 0 * * 0'` → `'0 1 * * 0'`(注释:错峰 fetch.yml 的 00:00)
  - backfill-weekly push 改为 fetch.yml 同款 5 次 rebase 重试循环
  - test.yml `git rebase origin/main || git rebase --abort` → `git rebase origin/main || { git rebase --abort; exit 1; }`
  - 缺 timeout 的 job 补:smoke 20 / test 30 / deploy-on-push 30 / fetch.fetch 120、fetch.deploy 30 / weekly 两 job 视现状
  - smoke.yml:py_compile 显式清单 → `python -m py_compile $(git ls-files '*.py')`;9 个单测步骤 → 单步 `python run_tests.py`
- [ ] **Step 5.3 验证+提交** YAML 解析全过 + `python3 run_tests.py` → `git commit -am "⚡ CI:浅克隆、错峰、push 重试、超时保护;smoke 全量化;test_actions 固化不变量"`

### Task 6: 前端修复(B6)

**Files:** Modify `docs/sw.js`(重写)、`docs/app.js`(注册+末尾)、`docs/index.html`;Delete `docs/test-*.html`×3、`docs/performance-test.html`、`docs/search-worker.js`、`docs/fast-loader.js`;Modify `test_docs_assets.py`

- [ ] **Step 6.1 扩展 test_docs_assets.py(先红)**:解析 sw.js STATIC_ASSETS:全部 `./` 相对路径且文件存在;index.html 含 `rel="preconnect" href="https://cdn.jsdelivr.net"`;app.js 含 `serviceWorker.register`。
- [ ] **Step 6.2 重写 sw.js**:`v5` 缓存名;STATIC_ASSETS 相对路径仅含已验证存在文件;fetch 策略——`/daily/|/weekly/` 的 .html 与 `/data/`、`.json`、`feed.xml` → network-first(成功回填缓存,失败回缓存);其余 GET → cache-first;activate 清旧版本缓存;删除未用的 cacheFirst/networkFirst/sync/push 段。
- [ ] **Step 6.3 app.js 末尾追加**:
```javascript
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('sw.js').catch(() => {});
    });
}
```
index.html `app.js?v=18` → `?v=19`。
- [ ] **Step 6.4 死资源删除(逐个零引用 grep 门禁,范围 docs/ 全部 html/js + *.py 生成器)**:test-performance.html、test-advanced-features.html、test-bookmarks.html、performance-test.html、search-worker.js、fast-loader.js
- [ ] **Step 6.5 index.html**:`<head>` katex css 前加 `<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>`;读 :278 内联脚本——若不同步引用三脚本符号则三者加 defer,否则不动并记录。
- [ ] **Step 6.6 验证+提交** `python3 run_tests.py` → `git commit -am "🛠️ SW 修复(相对路径/网络优先数据)并启用;下线死资源;CDN 预连接"`

### Task 7: 生成器优化(B7)

**Files:** Create `docs/daily-common.css`;Modify `generate_daily_pages.py`、(视情况)`daily_page_enhancer.py`、`test_daily_pages_render.py`

- [ ] **Step 7.1 定位内联 CSS 来源**(render_daily_html 的 `<style>` 与 enhancer 的 `daily-enhancement-style`),确认逐页恒定部分。
- [ ] **Step 7.2 外提**:恒定 CSS → `docs/daily-common.css`;生成器输出 `<link rel="stylesheet" href="../daily-common.css">`;enhancer 注入的恒定段同样外提(若其测试本地不可跑则仅当改动可由 CI smoke 覆盖时进行,否则缩小范围只动 generate_daily_pages.py)。
- [ ] **Step 7.3 海报 `<img>` 补 `loading="lazy"`**(生成器内海报/信息图 emit 点)。
- [ ] **Step 7.4 更新 test_daily_pages_render.py 断言**(link 替代内联段、lazy 属性),本地跑通;用仓内最近一日数据 `--rerender-only` 渲染对比体积差,然后 `git checkout -- docs/daily docs/data` 还原产物(forward-only 策略)。
- [ ] **Step 7.5 验证+提交** `python3 run_tests.py` → `git commit -am "📉 每日页公共 CSS 外提为 daily-common.css(新页面生效);海报懒加载"`

### Task 8: README 重写 + 终验(B8)

**Files:** Modify `README.md`(重写)、`DEPLOYMENT_GUIDE.md`/`README_CONFIG.md`(链接核对);总结报告(对话输出)

- [ ] **Step 8.1 重写 README**:章节=系统是什么/架构与数据流(fetch→筛选→富化→日报/周报/深读→Pages)/workflow 一览表(含 cron、UTC/北京时间)/本地开发与测试(run_tests.py、无 pip 约束)/配置(指向 README_CONFIG)/目录结构(现状)/历史文档见 archive/。删除 V3-V5.1 营销式清单。
- [ ] **Step 8.2 链接核对**:其余保留 MD 中指向已删/已移文件的引用全部修正。
- [ ] **Step 8.3 终验**:`python3 run_tests.py` 全绿(0 failed);`git log --oneline main..HEAD` 与 `git diff main --stat` 审查;若网络可达:`git fetch origin && git rebase origin/main` 后复跑测试。
- [ ] **Step 8.4 Commit + 总结报告**(优化前后对比、合并指引、合并后首周期观察清单、未做事项清单)。

---

## Self-Review 记录

- 覆盖:设计 8 批全部映射为 Task 0(已完成的文档 commit)+ Task 1-8 ✓
- 占位符:决策分支均为显式判定规则(门禁不过→缩小范围),非 TBD ✓
- 一致性:cp 步骤在 Task 1 添加、Task 5 断言;v=19 与 6.3 对应 ✓
