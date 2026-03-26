# 提案 v2：从 Metro Schools 2025 PDF 提取 NCEA 数据

## 1. 需求摘要
- **核心目标**：从 Metro Schools 2025 PDF 提取 Auckland ~80 所高中的 2023 NCEA 数据，存入 SQLite，整合到学校列表和详情页
- **Release 1 范围**：仅学校级别数据（核心表 + 学科 Top10）→ 列表页 UE 列 + 详情页 NCEA 全景
- **明确排除**：区域汇总、趋势图、对比页面（Future Release）

## 2. 用户场景

### 场景 1：数据提取与导入
- **参与者**：开发者
- **触发条件**：运行 `python extract_metro_ncea.py`
- **正常路径**：
  1. PyMuPDF 读取 PDF 第 31-33 页 → 核心数据表（~80 所学校）
  2. PyMuPDF 读取 PDF 第 7-9 页 → 学科 Top10（11 学科 × 10 校）
  3. 正则/文本解析 → 结构化 dict 列表
  4. 自动匹配 school_name → school_number（精确 → 标准化 → 模糊）
  5. 未匹配学校 → 输出 `unmatched_schools.json`，脚本暂停等待手动映射
  6. 开启 SQLite 事务，DELETE WHERE source='metro_2025' AND data_year=2023（幂等）
  7. INSERT school_ncea_summary + school_subject_ranking
  8. COMMIT，输出统计报告（匹配数/插入数/跳过数）
- **错误路径**：
  - 未匹配学校 → 脚本暂停，输出 unmatched 列表，需手动在 MAPPING dict 中补充后重跑
  - PDF 列错位 → 正则断言失败 → 脚本报错退出，不提交事务
  - 事务中任何错误 → 自动 ROLLBACK
- **验收标准**：100% 学校已处理（匹配 + 已知跳过），0 条未处理记录

### 场景 2：列表页 UE 列
- **参与者**：家长/中介
- **触发条件**：浏览学校列表，勾选"大学入学率"列
- **正常路径**：列表显示 UE%，支持排序
- **错误路径**：无 UE 数据 → 显示 "-"，排序时排末尾（无论升降序）
- **验收标准**：UE 列显示正确值，排序逻辑正确

### 场景 3：详情页 NCEA 全景
- **参与者**：家长
- **触发条件**：点击学校详情
- **正常路径**：显示 UE 率、离校生分布（Below L1/L1/L2/L3）、奖学金统计、学科排名（如入选 Top10）
- **错误路径**：该校无 Metro 数据 → 不显示 NCEA 板块
- **验收标准**：数据与 PDF 逐字段一致（10 所学校抽样验证通过）

### Release 1 明确排除
- 区域汇总视图（第 3-6 页数据）
- 2020-2023 年度趋势图
- 多校对比页面

## 3. 非功能性需求
- **数据准确性**：10 所学校逐字段比对，100% 匹配 PDF
- **数据覆盖**：仅 Auckland ~80 所高中，其余 2500 所无影响
- **数据源标注**：API 返回 source 字段，UI 显示"数据来源: Metro Magazine 2025"
- **与 school_performance 的关系**：两表独立，数据角度不同（school_performance=族裔/性别分组达标率，school_ncea_summary=离校生分布百分比），无冲突

## 4. 架构提案

### 存储方案

```sql
CREATE TABLE school_ncea_summary (
    school_number        INTEGER NOT NULL,
    data_year            INTEGER NOT NULL,     -- 成绩年份 (2023)
    source               TEXT DEFAULT 'metro_2025',
    school_roll_july2024 INTEGER,              -- 在校总人数 (明确标注时间)
    school_leavers       INTEGER,              -- 离校生人数
    ue_percentage        REAL,                 -- 大学入学率 %
    below_l1_pct         REAL,                 -- 未达 L1 %
    l1_pct               REAL,                 -- L1 %
    l2_pct               REAL,                 -- L2 %
    l3_pct               REAL,                 -- L3 %
    scholarships         INTEGER,              -- 奖学金数
    outstanding_merit    REAL,                 -- Outstanding Merit %
    distinction          REAL,                 -- Distinction %
    region               TEXT,                 -- Local Board Area
    PRIMARY KEY (school_number, data_year)
);

CREATE TABLE school_subject_ranking (
    school_number     INTEGER NOT NULL,
    data_year         INTEGER NOT NULL,
    subject           TEXT NOT NULL,
    rank              INTEGER,
    level3_pct        REAL,
    source            TEXT DEFAULT 'metro_2025',
    PRIMARY KEY (school_number, data_year, subject)
);
```

### 学校名匹配策略
1. 精确匹配 school_name
2. 标准化：去标点、"H S" → "High School"、"St" → "Saint"、trim
3. 未匹配 → 输出 unmatched_schools.json，脚本暂停
4. 手动映射 MAPPING dict（硬编码在脚本中）
5. 目标：100% 处理率

### 导入策略
- 单个 SQLite 事务
- 先 DELETE source='metro_2025' AND data_year=2023 → 再 INSERT（幂等）
- 任何错误 → ROLLBACK
- 完成后输出报告：matched/inserted/skipped/errors

### API 改造
- `/api/schools` LEFT JOIN school_ncea_summary → 返回 ue_percentage
- `/api/school/{num}/ncea` 新端点 → 返回完整 NCEA + 学科排名
- null UE 值在排序时排末尾

### 前端改造
- 列表页：可配置列增加"大学入学率(UE)"
- 详情页：新增 NCEA 板块（UE、离校生分布条形图、奖学金、学科排名）
- 数据来源标注："来源: Metro Magazine Schools 2025"
