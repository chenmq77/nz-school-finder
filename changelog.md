# Changelog

## 2026-03-27 — refactor: 数据库路径支持环境变量，适配 worktree 共享

### Why
SQLite 数据库 `schools.db` 放在项目目录内，不同 git worktree 各自独立，无法共享同一份数据。

### What
所有 `DB_PATH` 定义改为优先读取环境变量 `SCHOOLS_DB`，未设置时 fallback 到原来的相对路径（向后兼容）。

### How
修改 5 个文件中的 `DB_PATH`：`school_finder.py`、`init_db.py`、`crawlers/templates/base.py`、`crawlers/batch_ncea.py`、`crawlers/ncea_crawler.py`。用法：`export SCHOOLS_DB="$HOME/.local/share/nz-school-finder/schools.db"`

---

## 2026-03-27 — refactor: Alpine.js 渐进迁移 (Phase 1)

### Why
index.html 4400+ 行单文件，代码无模块化，全局变量 9 个，innerHTML 拼接 69 处，相同模式重复多次（折叠面板 7 个、导出函数 3 个、i18n 判断 34 处）。需要拆分模块并引入轻量响应式框架。

### What
1. 引入 Alpine.js (CDN) + ES modules，零构建步骤
2. 抽出 6 个 JS 模块文件（共 706 行）:
   - js/utils.js — esc, safe, showToast 等工具函数
   - js/i18n.js — t, td, bilingual 翻译函数
   - js/api.js — 统一 fetch 封装 + AbortController + 错误处理
   - js/table.js — 列定义、getCellValue、formatCell、排序逻辑
   - js/ncea.js — Metro NCEA 荣誉板块 + 加载逻辑
   - js/export.js — 共享导出基础设施（html2canvas 封装）
3. 7 个折叠面板从 onclick="toggleSection()" 迁移到 Alpine x-data="{ open }"
4. server.py 增加 /js/ 和 /css/ 静态文件路由
5. 所有模块通过 window.* 桥接，现有代码不受影响

### How
渐进式迁移：每个模块先抽出、桥接、测试，确保原有功能不断。index.html 中的原始代码暂时保留作为 fallback。

---

## 2026-03-27 — fix: Scholarships 数据修正 + 荣誉板块重构

### Why
Scholarships Presented 在 PDF 中是百分比（22%=毕业生中通过 Scholarship 考试的比例），之前错误地解析为整数（22 个）。同时荣誉板块展示顺序和解释文案需要优化。

### What
1. 修正 extract_metro_ncea.py：一次读取 10 个值而非 8+2，scholarships 存为 REAL 百分比
2. 荣誉指标按含金量排序：NZQA Scholarship > Excellence > Merit
3. 每个指标加 [?] 问号弹窗解释含义
4. 学科排名从 tag 标签改为 mini 表格，更易阅读
5. 重建数据库表并重新导入

### How
修改解析逻辑统一处理 10 个百分比值，schema 中 scholarships 从 INTEGER 改为 REAL

---

## 2026-03-27 — fix: Metro NCEA 板块 UI 优化

### Why
Metro NCEA 板块存在 3 个问题：(1) 使用了 emoji 图标 (2) 中文模式下部分文本仍显示英文 (3) 与原有 NCEA 达标率数据放在一起容易混淆（两组数据统计口径不同：离校生分布 vs 在校生达标率）。

### What
1. 移除所有 emoji，改用纯文本 + 分隔符
2. 完善中英双语支持（用 `_lang === 'en'` 条件判断所有文本）
3. Metro 数据用独立卡片样式（bg-secondary 圆角背景）与 Performance 数据视觉分离
4. 条形图标签改为"最高成就"语义（如 "最高: Level 3"），避免与达标率的 L3 混淆
5. 两组数据同时存在时显示"统计口径不同，不可直接对比"提示

### How
重写 `renderMetroNcea()` 函数 + 在 `loadPerformanceData()` 中增加条件提示逻辑

---

## 2026-03-27 — feat: 从 Metro Schools 2025 PDF 提取 NCEA 数据并集成到系统

### Why
系统缺少 University Entrance (UE) 大学入学率数据。Metro Magazine Schools 2025 报告包含 Auckland 91 所高中的 2023 NCEA 详细成绩（UE 率、各级别达标率、奖学金、学科 Top10 排名），可以显著增强学校对比能力。

### What
1. **新建 `extract_metro_ncea.py`** — PDF 数据提取脚本，PyMuPDF 解析核心数据表（第 31-33 页）和学科 Top10 排名（第 7-9 页），包含 MD5 校验、三层学校名匹配（精确→标准化→手动映射）、事务式导入、golden data 自动校验
2. **新建 2 张数据库表** — `school_ncea_summary`（91 所学校的 UE、离校生分布、奖学金等）和 `school_subject_ranking`（11 学科 × 10 校排名）
3. **server.py API 改造** — `/api/schools` 增加 `ue_percentage` 字段；新增 `/api/school/{num}/ncea` 端点
4. **index.html 前端改造** — 列表页新增"大学入学率(UE)"可配置列；详情页新增 Metro NCEA 板块（UE 大数字、离校生分布条形图、奖学金统计、学科排名标签）

### How
- PDF 文本提取用 PyMuPDF，正则解析结构化表格数据
- 学校名匹配通过 KNOWN_REGIONS 集合区分区域标题和学校名
- 多行学校名（如 "Sir Edmund Hillary Collegiate Senior School"）通过 look-ahead 合并
- 导入策略：WAL 模式 + DELETE-before-INSERT 幂等 + 分布交叉校验 + golden data 断言

---

## 2026-03-26 — 修复颜色系统：消除重复定义 + 统一 EQI 千里江山配色

### Why
index.html 的 `:root` 和 colors.css 同时定义了颜色变量，存在重复且容易不一致。EQI Dashboard 中多处 JS 硬编码颜色仍使用旧的 Google 风格色值（绿/橙/红），与千里江山配色体系不统一。

### What
1. **删除 index.html `:root` 中的颜色变量**，仅保留非颜色变量（--radius, --shadow*, --transition），让 colors.css 成为唯一颜色定义来源
2. **更新 colors.css**，补充完整注释和蓝/青绿/金色系变量，明确标注各色系用途
3. **修复 EQI 颜色**（共 6 处）：
   - HTML band-color 内联样式：Fewer 段从 `#5dbdad/#88cfc5` 改为 `#3d8e86/#88bfb8`（teal-1/teal-3）
   - JS eqiColors 数组：7 色全部替换为千里江山配色
   - JS buildEqiBandBar：Fewer 段同步修改
   - JS EQI groups 颜色（Row2 标签色）：从旧绿/黄/红改为 `#2a6560/#7a5c3a/#8a3038`
   - JS EQI 数值着色（2处）：从 `#16a34a/#d97706/#dc2626` 改为 `#2a6560/#7a5c3a/#8a3038`
   - EQI 帮助文本中 Fewer/Moderate/More 文字色同步修改

### How
逐一 Read 确认后用 Edit 替换。最后用 Grep 扫描确认旧色值已全部清除。

## 2026-03-26 — CSS 硬编码颜色值替换为 CSS 变量引用

### Why
之前 `<style>` 中大量硬编码的十六进制颜色值（如 `#d4ece9`、`#c04851` 等），与 `:root` 中已定义的 CSS 变量重复。这导致后续调色需要逐一查找替换，维护成本高且容易遗漏。统一引用 CSS 变量后，修改一处即可全局生效。

### What
将 `<style>` 标签内 18 处硬编码颜色替换为 `var(--xxx)` 引用：
- **EQI band tags**（fewer/moderate/more）：背景色和文字色 → `--success-light/dark`、`--neutral-light/dark`、`--warning-light/dark`
- **EQI group labels**（fewer/moderate/more）：文字色 → `--success-dark`、`--neutral-dark`、`--warning-dark`
- **EQI 分段条** 7 段：背景色 → `--success-bar1/bar2`、`--neutral-bar1/neutral/neutral-bar2`、`--warning-bar1/warning`
- **Status badges**（open/closed/other）：背景色和文字色 → 对应 success/warning/neutral 变量
- **gauge-bar.eqi** 渐变：→ `var(--success), var(--neutral), var(--warning)`
- **gauge-bar.iso** 渐变：→ `var(--success), var(--primary), var(--primary-dark)`

### How
在 `index.html` 的 `<style>` 块中，逐一将硬编码的 `#xxxxxx` 值替换为对应的 `var(--变量名)`。JS 中的颜色值保留硬编码不做修改。

## 2026-03-26 — 整站配色从 Google 风格改为千里江山图中国传统色系

### Why
原有配色使用 Google Material / Tailwind 默认色值（如 #10b981、#3b82f6 等），视觉上偏现代西方风格。为了与"千里江山图"主题统一，需要全面替换为中国传统色系（铜青、胭脂、驼色等）。

### What
- **NCEA 图表**：堆叠条颜色替换为青蓝色系（#a2d2e2 → #296fab）
- **NCEA 对比箭头**：上涨色改为铜青 #3d8e86，下跌色改为胭脂 #c04851
- **EQI/ISO 渐变条**：绿→黄→红 改为 铜青→驼色→胭脂
- **EQI 分段条**：7 段颜色全部替换为传统色对应的渐变
- **EQI band tags / group labels**：背景色和文字色替换为传统色系
- **Status badges**：open/closed/other 三种状态颜色替换
- **族裔饼图**：5 个族裔颜色替换为传统色系
- **EQI 弹窗色块 & FAQ 色条**：内联样式和 JS 中的色值全部替换
- **Warning badge**：full-profile 标签颜色替换

### How
在 `index.html` 中逐一替换 CSS 样式、内联 style、JavaScript 变量中的所有颜色值（共 12 类、约 50+ 处替换）

## 2026-03-26 — NCEA 升学成绩 section 重构（信息架构优化）

### Why
原来的左右并排布局（堆叠图+对比表）信息优先级不对：图表在左侧先被看到但需要 NCEA 知识才能理解，对比表才是家长真正需要的"这学校好不好"的答案。

### What
- **布局重构**：从左右并排改为垂直布局（总结语 → 对比表 → 堆叠图）
- **新增总结语**：`L3达标率 83.9% · 奥克兰 +16.9 · 全国 +28.4`，绿色正/红色负，动态适配高于/低于/混合场景
- **对比表增强**：每个基准行加 +/- 差值（绿色/红色），脚注说明"彩色数值为百分点差距"
- **堆叠图简化**：移除奥克兰对比条（已在表格中），只保留学校自身 3 年趋势
- **Fallback 机制**：L3 无数据时自动降级到 L2/L1 作为总结指标
- **移动端适配**：表格 overflow-x:auto，小屏隐藏 delta 值，紧凑间距
- **Bug 修复**：curriculumBadges 嵌套 info-row 导致间距翻倍

### How
修改 `index.html` 中的 `renderPerformance()` 函数，新增 CSS media query（640px breakpoint）

## 2026-03-25 — 新增 3 所学校爬虫（Long Bay #27, Northcote #32, Selwyn #49）

### Why
继续扩展学校覆盖范围，新增 3 所不同 CMS 平台（WordPress、Drupal）的 Auckland 学校。

### What
- **school_27_long_bay.py**: Long Bay College — WordPress/Elementor, ~28 subjects (confidence 0.7, 课程详情在 SchoolBridge 登录后), sports/arts/clubs 需页面内容验证, 费用未公开, NCEA
- **school_32_northcote.py**: Northcote College — Drupal, ~27 subjects, 25 sports（含 AFL、Underwater Hockey 等特色项目）, 费用未公开, NCEA
- **school_49_selwyn.py**: Selwyn College — WordPress/Elementor, ~30 subjects（来源于 10 个学科部门页面）, sports 在外部 sporty.co.nz 平台, 费用未公开, NCEA

### How
- 所有 3 个爬虫继承 `StandardHtmlCrawler`
- Long Bay: 课程列表在 SchoolBridge 登录后，公开页面信息有限，confidence 设为 0.7；logo 是宽横幅(2280x440) 无正方形替代，留 None + warning
- Northcote: Drupal 站点，科目从 course-directory + 各部门页面汇总；logo 用 `/sites/default/files/logo.png`；zone map 为 JPG 格式
- Selwyn: 科目从 10 个 `/our-curriculum/` 子页面逐一提取；logo 用 Selwyn-badge.gif (269x254 接近正方形)；Engineering 映射到 Electronics 需人工确认
- Subjects 标准化：Fashion and Textiles → Textiles, Carpentry → Construction, Nutrition → Food Technology, Art Design → Design 等
- 3 所学校费用均未在官网公开显示，留 None 不猜测

---

## 2026-03-25 — 新增 3 所学校爬虫（GDC #65, Lynfield #75, TGS #36）

### Why
继续扩展学校覆盖范围，新增 3 所不同 CMS 平台的 Auckland 学校。

### What
- **school_65_glendowie.py**: Glendowie College — SchoolBridge 平台, 22 subjects, 26 sports, 33 clubs, NCEA + IB MYP, 费用未公开
- **school_75_lynfield.py**: Lynfield College — Zeald CMS, 27 subjects, 32 sports, NCEA, 费用 2026（金额在图片中无法爬取）
- **school_36_takapuna.py**: Takapuna Grammar School — Next.js, 28 subjects, 10 sports, 48 clubs, NCEA + IB Diploma, 费用未公开

### How
- 所有 3 个爬虫继承 `StandardHtmlCrawler`，分别设置 `SITE_TYPE` 为 schoolbridge / zeald / nextjs
- GDC 科目来源于 /international 页面（最完整的列表），IB MYP 为 Years 9-10
- Lynfield 费用页标注 2026 但金额在图片中，需手动提取 PDF
- Takapuna 科目通过 11 个学科部门子页面逐一提取，IB Diploma（首个公立学校 2013 年获认证）
- Subjects 对照 subject_pool 标准化：Spatial Design → DVC, Building and Construction → Construction, Mandarin → Chinese 等
- 费用未公开的学校留 None + warning，不硬编码猜测值

---

## 2026-03-25 — 新增 3 所学校爬虫（BDSC #6930, MAGS #69, WSC #48）

### Why
扩展学校覆盖范围，新增 3 所 Auckland 地区的 WordPress 网站学校。

### What
- **school_6930_botany_downs.py**: Botany Downs Secondary College — 27 subjects, 18 sports, fees $21,000/yr tuition + $400/wk homestay (2026)
- **school_69_mags.py**: Mt Albert Grammar School — 33 subjects, 33 sports, 50+ clubs, fees $20,000/yr tuition + $420/wk homestay (2026)
- **school_48_western_springs.py**: Western Springs College — 30 subjects, 29 sports, fees $20,000/yr tuition + $400/wk homestay (2026)

### How
- 所有 3 个爬虫继承 `StandardHtmlCrawler`，设置 `SITE_TYPE = "wordpress"`
- 遵循现有爬虫模式（school_53_aggs.py 为模板）
- Subjects 对照 subject_pool 标准化，使用 SUBJECT_MAPPING 映射别名
- Fees 从 PDF 提取后硬编码（避免正则匹配年份的陷阱）
- Logo 优先选择近正方形图片（BDSC 1080×900, MAGS 暂用 banner, WSC 用 favicon）
- Sports/Arts/Clubs 通过 known_* 列表 + 页面内容匹配

---

## 2026-03-25 — Logo 自适应宽高比布局修复

### Why
横幅式 logo（如 WGHS 2800×574 SVG、AGGS 489×119 PNG）在固定 180×180 正方形容器中被 object-fit:contain 压缩到很小，用户几乎看不清。

### What
- 将 logo 从 `position:absolute` 浮层改为 flexbox 并排布局，与校名同行
- JS onload 根据宽高比动态调整 `max-width/max-height`（>4:1 用 380×90，>2:1 用 300×90，其余 200×120）
- 消除了 logo 遮挡 tag 卡片的问题

### How
- `index.html`：section A 头部改为 `display:flex;align-items:center;justify-content:space-between`
- `logoEl.onload` 检测 `naturalWidth/naturalHeight` 比例，动态设置尺寸
- 4 轮截图迭代验证（Playwright headless），所有学校 logo 均达到 8/10 以上

---

## 2026-03-23 — 国际生学费多年份存储与智能展示

### Why
原来 `school_web_data` 每校只存一行费用数据，无法保留多年份的历史费用。需要支持同一学校存储不同年份的费用，前端智能展示最相关年份。

### What
- **新建 `school_fees` 表**：`(school_number, year)` 复合主键，支持多年份费用
- **爬虫冲突检测**：同校同年金额不一致时不覆盖，警告人工审核
- **API 智能查询**：当年 → 最近未来年 → 最近过去年 三级回退
- **数据迁移**：`init_db.py` 增量建表 + 从 `school_web_data` 迁移已有 5 条记录

### How
- `init_db.py`：`ensure_school_fees_table()` 幂等建表 + 迁移
- `crawlers/templates/base.py`：`commit_to_db()` 写入新表，SELECT 比对后决定 INSERT/UPDATE/WARN
- `server.py`：`fetch_school_web()` 三段式年份查询覆盖返回值
- 前端无需改动（`renderFees()` 已支持 `intl_fees_year` 显示）

---

## 2026-03-23 — Dashboard 首页 + 学校列表视图 + Hash 路由 + 筛选系统

### Why
首页只有一个空白的 empty-state，用户不知道有什么数据可以探索。需要一个可视化的 Dashboard 展示数据全貌，并支持点击筛选浏览学校列表。

### What
- **Dashboard 首页**：Region/Authority/Gender Treemap、Year Level Band Map、Curriculum+EQI 并列、FAQ
- **LinkedIn 风格筛选栏**：Header 内 sticky filter bar，支持多选、Year Levels 年级范围筛选
- **学校列表视图**：筛选卡片 + 排序 + 分页
- **Hash 路由**：`#/` Dashboard、`#/schools?...` 列表、`#/school/54` 详情
- **API 扩展**：`/api/stats`、`/api/schools`（多维度多选筛选 + 年级范围 + curriculum）
- **配色系统**：每区域一色相深浅渐变 + 自动文字对比度

### How
- Treemap：方角 1px gap、absolute 定位百分比对齐（Region）、CSS Grid（EQI）
- Year Level：CSS Grid 13 列 Band Map，点击用 year_min/year_max 筛选
- Filter Bar：LinkedIn 风格 pill + dropdown 多选，dashboard 和 list view 共享

---

## 2026-03-23 — 支持选择性爬取（--only 参数）

### Why
用户需要只重新爬取某一部分数据（如只更新 subjects 或 fees），不需要每次全量爬取。

### What
- `crawl(only=["subjects", "fees"])` — BaseCrawler 支持选择性提取
- CLI: `python -m crawlers.crawler --school 41 --only subjects,fees`

### How
- `crawl()` 方法新增 `only` 参数，过滤 extract 步骤

---

## 2026-03-23 — 搭建爬虫框架（feat/crawler 分支）

### Why
将手动 AI 辅助爬取升级为结构化的爬虫框架。

### What
- BaseCrawler 抽象基类 + StandardHtml/WordPress/Wix 模板 + 每校脚本 + CLI 入口

### How
- 继承体系 + review 报告 + commit 前人工审核

---
## 2026-03-23 — 搜索下拉支持键盘导航（↑/↓/Enter/Escape）

### Why
用户希望纯键盘操作即可完成"搜索 → 选择学校"的流程，提升交互效率。

### What
在搜索结果下拉列表中增加键盘导航功能：↑/↓ 方向键上下移动高亮、Enter 选中当前高亮项、Escape 关闭下拉。键盘与鼠标 hover/click 共存，互不冲突，谁最后操作谁生效。到达边界时循环跳转。

### How
- CSS：`.result-item.active` 与 `:hover` 共用同一高亮样式
- JS：新增 `_activeIndex` 状态变量和 `_setActiveIndex()` 函数管理高亮 + 滚动
- `keydown` 事件：处理 ArrowUp/ArrowDown/Enter/Escape
- `mouseenter/mouseleave`：鼠标悬停时同步 `_activeIndex`，离开时清除高亮
- 搜索结果刷新、清除搜索、点击外部时均重置 `_activeIndex`

---

## 2026-03-23 — 修复 clearSearch 后详情无法再次显示的 bug

### Why
点击 "NZ School Finder" 标题或搜索框的 × 按钮回到首页后，再次搜索学校时详情页无法显示。

### What
`clearSearch()` 中用 inline style (`style.display = 'none'`) 隐藏详情，但 `loadSchool()` 用 CSS class (`.show`) 显示详情。inline style 优先级高于 class，导致一旦 clearSearch 执行后，后续加 `.show` class 永远无法覆盖 inline `display: none`。

### How
将 `$detail.style.display = 'none'` 改为 `$detail.classList.remove('show')`，统一使用 class 切换显示状态。

---

## 2026-03-22 — 信息架构重排 A-H + 新增 C/D/E 区展示爬取数据

### Why
按家长决策漏斗重排信息：身份→位置/入学→费用→课程→课外→学生构成→质量→行政。把爬取到的官网数据（科目、课外活动、费用、学区）整合进 UI。

### What
- **信息架构从 A-E 扩展为 A-H**：
  - A: 学校身份（不变）
  - B: 位置+入学+学区（合并，含学区地图）
  - C: 费用（新 — 年学费+周住宿费卡片）
  - D: 课程/科目（新 — 网格列表）
  - E: 课外活动（新 — 摘要卡片+分类列表：体育/音乐/文化/其他）
  - F: 学生构成（原C）
  - G: 质量特色（原D，折叠）
  - H: 行政归属（原E，折叠）
- **server.py** 新增 `/api/school/<num>/web` 端点
- 测试同步更新

### How
- `index.html`: HTML sections 重排、新增 loadWebData/renderSectionC/D/E/appendZoneToB 函数
- `server.py`: 新增 fetch_school_web() + _handle_school_web()
- `test_server.py`: 测试适配 A-H 八区结构

---

## 2026-03-22 — 学校官网数据爬取 POC + 数据存储

### Why
CSV 49 列只有基础信息，家长选校还需要科目、课外活动、费用、学区等信息。需要从学校官网爬取补充数据。

### What
- 使用 **Scrapling** 框架爬取 Auckland Grammar School 官网
- 新建 `school_web_data` 表存储爬取数据（JSON + 链接可追溯）
- AGS 数据已导入：27 科目、32 体育、12 音乐、4 文化、4 活动、国际生费用、学区链接
- 经过 Claude + GPT 多轮协作精炼：爬取方案、数据结构、跨校比较设计

### How
- `Scrapling.Fetcher.get()` 抓取 HTML → 正则提取结构化数据
- 数据存为 JSON 扁平列表（不预分小类），后期分类在展示层做
- 费用简化为 2 个数字（年学费 + 周住宿费）+ 来源链接
- 每类数据带 `_url` 字段指向来源页面

---

## 2026-03-22 — 修正 Git 配置邮箱以匹配 GitHub 账号

### Why
本地 Git 邮箱 (chen.mengqi7@qq.com) 与 GitHub 账号邮箱 (chenmq77@foxmail.com) 不一致，导致 GitHub profile 不显示 contribution 绿格子。

### What
- 执行 `git config --global user.email "chenmq77@foxmail.com"` 统一邮箱

### How
- 修改全局 Git 配置，此后所有新 commit 将使用与 GitHub 账号匹配的邮箱

---

## 2026-03-22 — EQI 和 Location 布局调整 + EQI 帮助弹窗

### Why
家长查看学校时，地理位置和社区经济条件（EQI）是最先关心的信息，不应该藏在默认折叠的 D 区。同时 EQI 指数对普通家长不够直观，需要提供官方分段说明的入口。

### What
- **Location（地理坐标 + Google Map 链接）从 D 区移到 B 区** — 和地址、城乡属性放在一起，形成完整的"位置"信息块
- **EQI 公平指数从 D 区移到 B 区** — 默认展开可见，不再需要手动展开 D 区
- **EQI 显示升级**：
  - 采用 NZ 教育部官方 2026 年 7 Band / 3 Group 分段标准（Fewest 344-402 → Most 522-569）
  - 数值旁显示所属 Band 标签（带 Group 对应色：绿/黄/红）
  - 进度条范围从 300-700 修正为官方 344-569
- **EQI 帮助弹窗（Modal）** — 卡片右上角 `?` 按钮，点击弹出：
  - EQI 定义说明（不是学校质量评分）
  - 7 段彩色分段条，当前学校 EQI 位置标记
  - 3 Group × 7 Band 完整列表（含中英文名和数值范围）

### How
- 修改 `index.html`：
  - `renderSectionB()` — 新增 Location、EQI gauge card、`?` 帮助按钮
  - `renderSectionD()` — 移除 EQI 和 Location（只保留 Isolation Index 等）
  - 新增 CSS：EQI help button、band tag、modal overlay、segmented bar、marker
  - 新增 JS：`EQI_BANDS`/`EQI_GROUPS` 常量、`getEqiBand()`、`openEqiModal()`/`closeEqiModal()`
  - 新增 Modal HTML：分段说明、颜色图例、当前位置标记

---

## 2026-03-21 — 新建 Web 版 NZ School Finder（index.html + server.py）

### Why
家长/学生需要一个可视化的 Web 界面来搜索和查看学校信息，比终端 CLI 更直观易用。

### What
- **`server.py`** — 纯 Python 标准库 HTTP 服务器（零依赖），提供：
  - `GET /api/search?q=keyword` — 模糊搜索，返回匹配列表 + 真实总数
  - `GET /api/school/<number>` — 按编号返回完整学校记录
  - 只允许访问 index.html 和 API 路由，未知路由返回 404（安全）
- **`index.html`** — 单页面现代 UI 前端，特性：
  - 实时搜索（250ms 防抖）+ 下拉结果列表
  - A-E 五大分类卡片式布局，A/B/C 默认展开，D/E 可折叠
  - 族裔分布彩色条形图 + 国际学生高亮卡片
  - EQI/偏远指数进度条 + 中文解读
  - 中英双语、响应式适配移动端
  - AbortController 防止异步竞态
  - XSS 防护：DOM API 构建搜索结果、esc() 转义、URL scheme 验证

### How
- 5 轮 Claude + GPT 协作审查（gpt-5.4-xhigh-fast），从 Score 6 提升到 Score 9
- 修复了 11 个问题：HTTP 错误处理、文件暴露、竞态条件、类型安全、XSS 防护等
- 审查记录：`docs/review-{1-5}.md` + `docs/review-feedback-{1-4}.md`

## 2026-03-21 — Co-Review 代码审查修复（school_finder.py + init_db.py）

### Why
通过 Claude + GPT 协作审查（cc-cursor-co-review），对照 req.md 需求文档发现了 7 个代码问题：空值误导用户、数据展示丢失、导入器安全隐患等，需要逐一修复以确保代码质量和需求一致性。

### What
- **school_finder.py**:
  - `isolation_interpret()` / `isolation_bar()`：空值/无效值不再误显为"靠近市中心"，改为返回 "--" 和空进度条
  - `eqi_bar()`：空值/零值返回空进度条，与 isolation 保持一致
  - 学校类型翻译：用正则提取年级范围（如 `(Year 9-15)`）并保留在中文翻译中，新增 Special/Restricted/Teen Parent 类型
  - Status 渲染：从 if/elif 改为字典映射，覆盖 Open/Closed/Merger/New/Not Yet Open/Proposed 六种状态
  - 坐标合并：改为显示任何非空部分，不再要求经纬度同时存在
  - 社区合并：增加 name-only / code-only 分支，避免丢失部分数据
  - 顶部新增 `import re`
- **init_db.py**:
  - CSV 表头验证移到数据库操作之前，缺列时立即报错返回，不再先 DROP TABLE 再验证

### How
- 3 轮 GPT 审查（gpt-5.4-xhigh-fast），从 Score 6 提升到 Score 9，最终 APPROVED
- 审查记录保存在 `docs/review-{1,2,3}.md` 和 `docs/review-feedback-{1,2}.md`

## 2026-03-21 — 创建 school_finder.py（学校信息查询终端工具）

### Why
家长/学生需要一个直观的工具，输入学校英文名称即可查看学校的完整信息。按照 req.md 定义的 A-E 五大分类（学校身份、位置联系、学生构成、质量特色、行政归属）分区展示，以终端 ASCII 界面呈现，降低信息过载。

### What
- 新建 `school_finder.py`，从 `schools.db` 查询并展示学校信息
- 支持模糊搜索（LIKE %keyword%），多条匹配时列出供用户选择
- 按 A-E 五大分类分区展示，中英双语并排：
  - A. 学校身份概览：名称大字标题 + 编号、类型/管理性质/性别用标签卡片、寄宿、官网
  - B. 位置与联系方式：地址合并为一行、邮寄地址合并、城乡属性、电话、邮箱
  - C. 学生规模与构成：总人数突出框、族裔分布 ASCII 条形图（按人数降序）、国际学生、招生计划
  - D. 学校质量与特色：默认折叠，展开后含 EQI 进度条+解读、偏远指数进度条+解读等 11 项
  - E. 行政与区域归属：默认折叠，展开后分 4 个子模块（区域管辖、选区、社区、学习社区）
- 交互流程：搜索 → 展示(A/B/C展开, D/E折叠) → 输入 D/E 切换展开 → Q 退出或输入新关键词搜索
- 空值统一显示为 "--"，条形图最大宽度 35 字符，百分比基于 total_school_roll 计算

### How
- 使用 Python 标准库 `sqlite3` 连接同目录下的 `schools.db`
- `search_schools()` 执行 `LIKE %keyword%` 模糊查询
- `fetch_school()` 用 `sqlite3.Row` 按编号获取完整记录为字典
- 各 `show_section_X()` 函数负责对应分区的格式化输出
- `bar_chart()` 函数绘制 ASCII 条形图，`eqi_bar()` / `isolation_bar()` 绘制进度条
- 标签卡片宽度动态适配内容长度，避免溢出

## 2026-03-21 — 创建 init_db.py（数据库初始化脚本）

### Why
需要将 directory.csv（2577 所新西兰学校、49 列数据）导入 SQLite 数据库，为后续的学校信息查询系统提供结构化数据支撑。

### What
- 新建 `init_db.py`，读取 `directory.csv` 并创建 `schools.db`
- 建 `schools` 表，49 列全部使用 TEXT 类型保留原始数据
- 列名从 CSV 原始名映射为下划线命名法（如 `Email^` → `email`，`Principal*` → `principal`）
- 每列映射加注释标注所属分类（A-E 五大类）
- 处理 CSV 的 BOM 头（utf-8-sig 编码）
- 导入完成后打印统计信息和数据预览

### How
- 使用 Python 标准库 `csv.DictReader` + `sqlite3`
- 定义 `COLUMN_MAPPING` 列表维护 49 列的映射关系和分类注释
- 全部列用 TEXT 类型，不做数据类型转换，保留原始值
- 导入结果：成功导入 2577 条记录，0 条跳过
