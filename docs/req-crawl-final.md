# 最终需求：学校官网数据爬取方案

**精炼过程**: 经过 2 轮 Claude + GPT 挑战
**日期**: 2026-03-22
**状态**: APPROVED (8.5/10)

---

## 1. 需求摘要

为奥克兰 Year 9-15 Secondary 学校（约50所）补充 CSV 未覆盖的选校关键信息。
采用「**官方源优先 → 官网补充 → 人工校验兜底**」策略，使用 Scrapling 框架作为爬虫工具。

---

## 2. 字段分级 + 数据源矩阵

### Tier 1：选校决策核心

| 字段 | 首选数据源 | 备选来源 | 提取难度 | 归一化规则 |
|------|-----------|---------|---------|-----------|
| 课程体系 | 官网 /curriculum | 手动 | 中 | 枚举：NCEA / Cambridge / IB / Mixed |
| 学区/入学规则 | 官网 /enrolment | MOE Zone Map | 中 | 保存链接 + 文字摘要 |
| 费用/捐赠 | 官网 /fees, /enrolment | PDF 手册 | 高 | 金额 + 币种 + 年份 |
| NCEA 学业成绩 | **NZQA / Education Counts** | 官网补充 | 低 | L1/L2/L3/UE 通过率 |
| 入学流程与截止 | 官网 /enrolment | — | 中 | 日期 + 步骤摘要 |

### Tier 2：重要参考

| 字段 | 首选数据源 | 提取难度 |
|------|-----------|---------|
| 科目列表 (Yr11-13) | 官网 /subjects | 高（常在PDF） |
| 课外活动 | 官网 /sports, /activities | 中 |
| 国际生项目/ESOL | 官网 /international | 中 |
| 学生支持/Wellbeing | 官网 /wellbeing, /support | 中 |

### Tier 3：补充信息（低优先级）

校服、开放日、宗教/特色 — 视 POC 结果决定是否纳入。
校历 — MOE 统一发布，不需要爬。

---

## 3. 技术方案

### 分层抓取策略
1. **官方公开数据** — Python 下载 NZQA/Education Counts CSV，无需爬虫
2. **学校官网 HTML** — Scrapling Fetcher（普通模式），遵守 robots.txt，限速 2s/请求
3. **JS 渲染页面** — Scrapling DynamicFetcher（仅需要时回退）
4. **PDF 文档** — 下载后用 pdfplumber 提取
5. **无法自动化** — 标记 needs_manual_review

**不使用 StealthyFetcher** — 学校官网非对抗目标。

### 数据存储三层架构

```sql
-- 已有
schools (school_number PK, ...49 columns...)

-- 新增：爬取的源页面
source_pages (
  id INTEGER PK,
  school_number INTEGER FK,
  url TEXT,
  page_type TEXT,        -- curriculum/enrolment/international/...
  crawled_at TIMESTAMP,
  http_status INTEGER
)

-- 新增：提取的事实
extracted_facts (
  id INTEGER PK,
  source_id INTEGER FK,
  field_name TEXT,       -- curriculum_type/fees/zone_info/...
  value TEXT,
  confidence REAL,       -- 0.0-1.0
  as_of_year INTEGER,
  last_verified_at TIMESTAMP
)
```

---

## 4. POC 样本学校（6+1所）

| # | 学校 | 为什么选 |
|---|------|---------|
| 1 | Auckland Grammar (ags.school.nz) | 传统名校，内容丰富 |
| 2 | Rangitoto College (rangitoto.school.nz) | 最大校，现代网站 |
| 3 | Avondale College (avcol.school.nz) | 中等规模 |
| 4 | Manurewa High School (manurewa.school.nz) | 高 EQI 区域 |
| 5 | Kelston Boys High (kbhs.school.nz) | 较小规模 |
| 6 | Hobsonville Point Secondary (hpss.school.nz) | 新建校，可能用现代前端 |
| 备用 | Epsom Girls Grammar (eggs.school.nz) | 女校 + 不同形态 |

---

## 5. 验证标准

每个 Tier 1 字段在 6 所学校中：
- **覆盖率 ≥ 4/6 且准确率 ≥ 80%** → 可自动化
- **覆盖率 3/6 或准确率 < 80%** → 半自动（爬虫 + 人工校验）
- **覆盖率 < 3/6** → 仅人工或放弃

准确率 = 人工抽检提取值与官网实际值一致的比例。

---

## 6. GPT 挑战关键洞察

| 洞察 | 处理 |
|------|------|
| 不要以官网爬虫为主路径 | 改为：官方源优先 → 官网补充 |
| NCEA 走 NZQA 不走官网 | 已采纳 |
| 数据架构需三层 | schools + source_pages + extracted_facts |
| 不要用 StealthyFetcher | 已采纳，普通 Fetcher + robots.txt |
| 测试学校应覆盖不同形态 | 6+1 所，含高/低 EQI、大/小、新/旧 |
| 需要准确率指标 | 已加入验证标准 |

---

## 7. 实施计划

### Step 1: NZQA/Education Counts 数据
- 下载公开 NCEA 成绩 CSV
- 按 school_number 关联到 schools 表

### Step 2: 6 所学校官网 POC
- 安装 Scrapling
- 爬取 Tier 1 字段的关键页面
- 记录覆盖率和准确率

### Step 3: 评估与决策
- 根据 POC 结果决定哪些字段自动化、哪些半自动
- 决定是否扩展到全部 50 所学校

---

## 8. 审查记录

| 轮次 | 分数 | 结论 | 文件 |
|------|------|------|------|
| 1 | 6/10 | CHANGES_REQUESTED | review-crawl-1.md, review-crawl-feedback-1.md |
| 2 | 8.5/10 | APPROVED | review-crawl-2.md |
