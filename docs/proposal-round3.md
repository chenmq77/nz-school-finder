# 提案 v4：从 Metro Schools 2025 PDF 提取 NCEA 数据

## 1. 需求摘要
- **核心目标**：从 Metro Schools 2025 PDF 提取 Auckland ~80 所高中的 2023 NCEA 数据，存入 SQLite，整合到学校列表和详情页
- **Release 1 范围**：仅学校级别数据（核心表 + 学科 Top10）→ 列表页 UE 列 + 详情页 NCEA 全景
- **明确排除**：区域汇总、趋势图、对比页面

## 2. 数据语义（已验证）

**离校生分布**：Below L1 + L1 + L2 + L3 ≈ 100%（±2% 舍入容差），这是按最高达成级别的互斥分布。
**UE**：University Entrance 是独立指标，不属于上述分布。达到 UE 的学生通常也计入 L3 分组，但 UE 有额外要求（特定科目组合）。因此 UE ≤ L3+部分L2 是可能的，UE 不参与分布加和校验。
**Outstanding Merit / Distinction**：REAL 百分比 (0-100)。
**Scholarships**：INTEGER 数量。
**School Roll**：July 2024 在校人数，与 2023 成绩年份独立。

## 3. 用户场景

### 场景 1：数据提取与导入
- **参与者**：开发者
- **触发条件**：`python extract_metro_ncea.py`
- **前置条件**：PDF 文件校验（文件名 + MD5 checksum match）
- **正常路径**：
  1. 校验 PDF 文件（checksum）→ 不匹配则 exit
  2. PyMuPDF 提取第 31-33 页核心表 + 第 7-9 页学科 Top10
  3. 匹配 school_name → school_number
     - 精确 → 标准化（去标点、缩写展开）→ MAPPING dict
     - 多条候选匹配（同名学校）→ 作为 ambiguous match 报错，同 unmatched 处理
  4. 如有 unmatched 或 ambiguous → 输出 unmatched_schools.json，非零退出
  5. 全部匹配后：事务 → DELETE → INSERT → 自动校验 → COMMIT
  6. 输出统计报告
- **自动校验规则**：
  - 行数 = PDF 提取数 - 跳过数
  - 所有百分比字段 ∈ [0, 100]
  - Below_L1 + L1 + L2 + L3 ∈ [98, 102]（舍入容差）
  - UE ∈ [0, 100] 且独立校验（不参与分布加和）
  - 无重复 school_number
  - 学科排名 rank ∈ [1, 10]
- **错误路径**：
  - Checksum 不匹配 → exit 1
  - Unmatched/ambiguous → exit 1 + unmatched_schools.json
  - 校验失败 → ROLLBACK + exit 1
- **验收标准**：100% 处理，自动校验全通过，10 所手动比对

### 场景 2：列表页 UE 列
- **正常路径**：勾选"大学入学率"列，显示 UE%，排序
- **无数据**：显示 "-"，排序排末尾
- **验收标准**：UE 显示正确，排序正确

### 场景 3：详情页 NCEA 全景
- **正常路径**：显示 UE%、离校生分布条形图、奖学金、merit、distinction、学科排名
- **无 Metro 数据**：隐藏整个 NCEA 板块（不显示空状态提示）
- **某学科无 Top10 排名**：不显示该学科条目（仅显示有排名的学科）
- **验收标准**：10 所学校逐字段比对

## 4. 架构

### 存储方案
```sql
CREATE TABLE school_ncea_summary (
    school_number        INTEGER NOT NULL,
    data_year            INTEGER NOT NULL,
    source               TEXT DEFAULT 'metro_2025',
    school_roll_july2024 INTEGER,
    school_leavers       INTEGER,
    ue_percentage        REAL,
    below_l1_pct         REAL,
    l1_pct               REAL,
    l2_pct               REAL,
    l3_pct               REAL,
    scholarships         INTEGER,
    outstanding_merit    REAL,
    distinction          REAL,
    region               TEXT,
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

### 匹配策略
- 精确 → 标准化 → MAPPING dict
- 多候选（ambiguous）→ 同 unmatched 处理
- 最终未匹配 → 人工审核

### 导入策略
- PDF checksum 验证
- 单事务 DELETE+INSERT（幂等）
- 自动校验 → 失败则 ROLLBACK

### API
- `/api/schools` LEFT JOIN school_ncea_summary → ue_percentage
- `/api/school/{num}/ncea` → NCEA 汇总 + 学科排名（仅有数据时返回）

### UI
- 列表页：UE 列（可配置），无数据显示 "-"
- 详情页：NCEA 板块（仅有数据时显示），学科排名（仅显示有排名的）
- 来源标注："来源: Metro Magazine Schools 2025"

## 5. 风险
| 风险 | 严重度 | 缓解 |
|------|--------|------|
| PDF 文本列错位 | 中 | 正则断言 + 分布交叉校验 |
| 学校名不匹配/歧义 | 中 | 标准化 + MAPPING + ambiguous 检测 |
| 数据截断 | 低 | 行数断言 |
| PDF 版本变更 | 低 | Checksum 锁定 |
