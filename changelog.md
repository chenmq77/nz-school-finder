# Changelog

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
