# 提案 v7（Final）：从 Metro Schools 2025 PDF 提取 NCEA 数据

## 1. Release 1 范围
- **包含**：PDF 数据提取 → SQLite → 列表页 UE 列 + 详情页 NCEA 板块
- **排除**：区域汇总、趋势图、对比页面（用户已确认3次：Release 1 不含对比功能）

## 2. 数据语义
- **Below_L1 + L1 + L2 + L3** ≈ 100%（±2%），互斥离校生分布
- **UE**：独立指标，不参与分布加和
- **Outstanding Merit**：REAL%，离校生中 Merit endorsement 比例
- **Distinction**：REAL%，离校生中 Excellence endorsement 比例
- **Scholarships**：INTEGER 数量
- **School Roll**：July 2024，独立于 data_year=2023

### NULL/空值处理规则
| PDF 中的值 | 存储 | API 返回 | UI 显示 |
|------------|------|----------|---------|
| 数字值（如 74%） | REAL/INTEGER | 数字 | 数字 |
| 空白/"-"/无值 | NULL | null | 隐藏该字段 |
| "0" 或 "0%" | 0 | 0 | "0" 或 "0%" |

**规则**：NULL = "数据未报告/不适用"，0 = "明确为零"。不混淆。

## 3. 场景

### 场景 1：数据提取与导入
**前置**：PDF checksum 校验
**正常路径**：
1. PyMuPDF 提取第 31-33 页核心表 + 第 7-9 页学科 Top10
2. 核心表匹配：精确→标准化→MAPPING dict。多候选=ambiguous→fail
3. 学科 Top10 匹配：
   - 匹配到 schools 表 → 存储
   - 未匹配 → 检查 RANKING_SKIP_ALLOWLIST（已知非 Auckland 学校白名单）
   - 在白名单 → 跳过，记录到 skip_report
   - 不在白名单 → 报错退出（可能是匹配 bug）
4. 未匹配核心表 → unmatched_schools.json + exit 1
5. 事务 DELETE+INSERT → 校验 → COMMIT

**自动校验**：
- 核心表：行数断言、百分比[0,100]、分布和[98,102]、无重复
- **学科排名：expected 11 个学科，每学科 ≤10 行。断言学科集合完整**
- Golden data：3 所学校完整字段值 checksum 绑定
- UE 独立 [0,100]、rank [1,10]

### 场景 2：列表页 UE 列
- UE% 显示，NULL → "-"，排序排末尾

### 场景 3：详情页 NCEA 板块
- 无 Metro 数据 → 隐藏板块
- 有数据 → UE%、离校生分布图、奖学金数、merit%、distinction%
- NULL 字段不显示（非显示 0）
- 学科排名：仅显示有记录的学科，标注"Metro 2025 Top 10"
- 年份标注："2023 NCEA 成绩" / "在校人数 (July 2024)"

## 4. 架构

### 存储
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
    import_checksum      TEXT,
    imported_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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

### 匹配
- 核心表：精确→标准化→MAPPING dict。多候选=fail。未匹配=exit 1+人工
- 学科 Top10：匹配→存储，未匹配+在白名单→跳过，未匹配+不在白名单→fail

### 导入：checksum→事务→DELETE(source,data_year)→INSERT→校验(含学科完整性)→COMMIT
### API：`/api/schools` → ue_percentage; `/api/school/{num}/ncea` → {ncea_summary: obj|null, subject_rankings: []}
### UI：列表 UE 列 + 详情板块（无数据隐藏），NULL 字段隐藏，年份标注

## 5. 风险
| 风险 | 严重度 | 缓解 |
|------|--------|------|
| PDF 列错位 | 中 | 正则+golden data+分布校验 |
| 学校名匹配 | 中 | 标准化+MAPPING+ambiguous检测 |
| 学科排名遗漏 | 中 | 学科集合完整性断言(11科) |
| Top10 未知学校 | 低 | RANKING_SKIP_ALLOWLIST |
| 空值混淆 | 低 | NULL vs 0 规则明确 |
