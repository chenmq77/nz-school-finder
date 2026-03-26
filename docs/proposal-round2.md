# 提案 v3：从 Metro Schools 2025 PDF 提取 NCEA 数据

## 1. 需求摘要
- **核心目标**：从 Metro Schools 2025 PDF 提取 Auckland ~80 所高中的 2023 NCEA 数据，存入 SQLite，整合到学校列表和详情页
- **Release 1 范围**：仅学校级别数据（核心表 + 学科 Top10）→ 列表页 UE 列 + 详情页 NCEA 全景
- **明确排除**：区域汇总、趋势图、对比页面（Future Release）

## 2. 数据语义确认

PDF 第 30 页方法论说明：
- **离校生定义**：2023 年永久离校进入职场/高等教育的学生
- **UE%**：达到大学入学标准的离校生占比
- **Below L1 + L1 + L2 + L3**：离校生按最高达成级别分布，互斥分组，加上 UE 近似 100%
- **Outstanding Merit / Distinction**：百分比值（如 3% = 3.0），表示获得该荣誉的学生比例
- **Scholarships Presented**：整数值，表示奖学金数量（非百分比）
- **School Roll**：July 2024 在校总人数（不同于 2023 成绩数据年份）

## 3. 用户场景

### 场景 1：数据提取与导入
- **参与者**：开发者
- **触发条件**：运行 `python extract_metro_ncea.py`
- **正常路径**：
  1. PyMuPDF 读取 PDF 第 31-33 页 → 解析核心数据表
  2. PyMuPDF 读取 PDF 第 7-9 页 → 解析学科 Top10
  3. 匹配 school_name → school_number（精确 → 标准化 → MAPPING dict）
  4. 如有未匹配学校 → 输出 unmatched_schools.json，非零退出码退出
  5. 开发者补充 MAPPING dict 后重跑
  6. 全部匹配后：SQLite 事务 → DELETE source='metro_2025' AND data_year=2023 → INSERT → COMMIT
  7. 自动校验：行数断言、百分比范围 0-100、分布交叉校验、无重复
  8. 输出统计报告
- **错误路径**：
  - 未匹配学校 → 非零退出，不修改数据库
  - 正则断言失败 → 报错退出
  - 校验失败 → ROLLBACK
- **验收标准**：100% 学校已处理，自动校验全部通过，10 所学校手动比对 PDF

### 场景 2：列表页 UE 列
- **参与者**：家长/中介
- **正常路径**：勾选"大学入学率"列，显示 UE%，支持排序
- **错误路径**：无数据 → 显示 "-"，排序时排末尾
- **验收标准**：UE 列显示正确，排序正确

### 场景 3：详情页 NCEA 全景
- **参与者**：家长
- **正常路径**：显示 UE%、离校生分布（Below L1/L1/L2/L3 条形图）、奖学金数、Outstanding Merit%、Distinction%、学科排名
- **错误路径**：无 Metro 数据 → 不显示 NCEA 板块
- **验收标准**：10 所学校逐字段比对 PDF 一致

### Release 1 明确排除
- 区域汇总视图、2020-2023 趋势图、多校对比页面

## 4. 架构提案

### 存储方案

```sql
CREATE TABLE school_ncea_summary (
    school_number        INTEGER NOT NULL,
    data_year            INTEGER NOT NULL,     -- 成绩年份 (2023)
    source               TEXT DEFAULT 'metro_2025',  -- 元数据标注
    school_roll_july2024 INTEGER,
    school_leavers       INTEGER,
    ue_percentage        REAL,                 -- 0-100
    below_l1_pct         REAL,                 -- 0-100，互斥分组
    l1_pct               REAL,
    l2_pct               REAL,
    l3_pct               REAL,
    scholarships         INTEGER,              -- 整数数量
    outstanding_merit    REAL,                 -- 百分比 0-100
    distinction          REAL,                 -- 百分比 0-100
    region               TEXT,
    PRIMARY KEY (school_number, data_year)
);

CREATE TABLE school_subject_ranking (
    school_number     INTEGER NOT NULL,
    data_year         INTEGER NOT NULL,
    subject           TEXT NOT NULL,           -- 如 'Sciences', 'Mathematics'
    rank              INTEGER,                -- 1-10
    level3_pct        REAL,                   -- 0-100
    source            TEXT DEFAULT 'metro_2025',
    PRIMARY KEY (school_number, data_year, subject)
);
```

### 匹配策略（无模糊匹配，避免误匹配）
1. 精确匹配 school_name
2. 标准化匹配：去标点、"H S" → "High School"、trim
3. MAPPING dict（硬编码已知差异）
4. 仍未匹配 → 输出到 unmatched_schools.json，脚本退出，人工审核后决定

### 导入策略
- 单个 SQLite 事务
- DELETE WHERE source='metro_2025' AND data_year=2023 → INSERT（幂等）
- 自动校验：行数断言、百分比 0-100、分布交叉校验、无重复 school_number
- 任何错误/校验失败 → ROLLBACK

### API 改造
- `/api/schools` LEFT JOIN school_ncea_summary → 返回 ue_percentage
- `/api/school/{num}/ncea` 新端点 → NCEA 汇总 + 学科排名
- 数据来源标注在 response 中

### 风险评估
| 风险 | 严重度 | 缓解 |
|------|--------|------|
| PDF 文本列错位 | 中 | 正则断言 + 交叉校验 |
| 学校名不匹配 | 中 | 标准化 + MAPPING dict + 人工审核 |
| 数据截断 | 低 | 行数断言 vs PDF 目视统计 |
| 数据仅覆盖 Auckland | 低 | UI 标注来源和范围 |
