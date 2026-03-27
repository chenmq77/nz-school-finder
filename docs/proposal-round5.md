# 提案 v6（Final）：从 Metro Schools 2025 PDF 提取 NCEA 数据

## 1. Release 1 范围
- **包含**：PDF 数据提取 → SQLite → 列表页 UE 列 + 详情页 NCEA 板块
- **排除**：区域汇总、趋势图、对比页面

## 2. 数据语义（已从 PDF 第30页方法论验证）
- **Below_L1 + L1 + L2 + L3** ≈ 100%（±2%），互斥离校生分布（按最高达成级别）
- **UE**：独立指标，不参与分布加和
- **Outstanding Merit**：REAL 百分比，表示离校生中获得 NCEA endorsed with Merit 的比例（分母=school_leavers）
- **Distinction**：REAL 百分比，表示离校生中获得 NCEA endorsed with Excellence 的比例（分母=school_leavers）
- **Scholarships**：INTEGER，奖学金展示数量
- **School Roll**：July 2024 在校人数，独立于 data_year=2023

## 3. 场景

### 场景 1：数据提取与导入
**前置**：PDF checksum 校验
**正常路径**：
1. PyMuPDF 提取第 31-33 页核心表 + 第 7-9 页学科 Top10
2. 匹配 school_name → school_number（精确→标准化→MAPPING dict）
3. 多候选=ambiguous → 同 unmatched 处理
4. **学科 Top10 中无法匹配到 schools 表的学校 → 直接跳过，不存储**
5. 未匹配核心表学校 → unmatched_schools.json + exit 1
6. 事务 DELETE+INSERT → 自动校验 → COMMIT

**自动校验**：
- 行数断言（核心表导入数 = 提取数 - 跳过数）
- 百分比 [0,100]、分布和 [98,102]、rank [1,10]
- 无重复 school_number
- **Golden data 断言**：硬编码 3 所已知学校的完整字段值（如 Auckland Grammar: UE=X%, leavers=Y），checksum 绑定，解析必须完全匹配

**验收**：自动校验全通过 + 10 所手动比对

### 场景 2：列表页 UE 列
- UE% 显示，无数据 "-"，排序排末尾

### 场景 3：详情页 NCEA 板块
- 无数据 → 隐藏板块
- 有数据 → UE%、离校生分布图、奖学金数、merit%、distinction%
- 学科排名仅显示有记录的学科
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
    ue_percentage        REAL,       -- % of leavers achieving UE
    below_l1_pct         REAL,       -- % of leavers, highest level < L1
    l1_pct               REAL,       -- % of leavers, highest level = L1
    l2_pct               REAL,       -- % of leavers, highest level = L2
    l3_pct               REAL,       -- % of leavers, highest level = L3
    scholarships         INTEGER,    -- count of scholarships presented
    outstanding_merit    REAL,       -- % of leavers with Merit endorsement
    distinction          REAL,       -- % of leavers with Excellence endorsement
    region               TEXT,
    import_checksum      TEXT,
    imported_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (school_number, data_year)
);

CREATE TABLE school_subject_ranking (
    school_number     INTEGER NOT NULL,  -- must exist in schools table
    data_year         INTEGER NOT NULL,
    subject           TEXT NOT NULL,
    rank              INTEGER,
    level3_pct        REAL,
    source            TEXT DEFAULT 'metro_2025',
    PRIMARY KEY (school_number, data_year, subject)
);
```

### 匹配：精确→标准化→MAPPING dict。多候选=fail。Top10 未匹配=跳过。核心表未匹配=exit 1+人工。
### 导入：checksum→事务→DELETE(source,data_year)→INSERT→golden data+range校验→COMMIT
### API：`/api/schools` → ue_percentage; `/api/school/{num}/ncea` → {ncea_summary: obj|null, subject_rankings: []}
### UI：列表 UE 列 + 详情板块（无数据隐藏），年份分别标注

## 5. 风险
| 风险 | 严重度 | 缓解 |
|------|--------|------|
| PDF 列错位 | 中 | 正则断言+golden data |
| 学校名匹配 | 中 | 标准化+MAPPING+ambiguous |
| 数据截断 | 低 | 行数断言 |
| 解析器漂移 | 低 | Checksum+golden data 绑定 |
