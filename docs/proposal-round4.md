# 提案 v5（Final）：从 Metro Schools 2025 PDF 提取 NCEA 数据

## 1. Release 1 范围
- **包含**：PDF 数据提取 → SQLite 存储 → 列表页 UE 列 + 详情页 NCEA 板块
- **排除**：区域汇总、趋势图、对比页面、compare workflow（用户已确认）

## 2. 数据语义
- Below_L1 + L1 + L2 + L3 ≈ 100%（±2% 容差），互斥离校生分布
- UE 独立指标，不参与分布加和
- Outstanding Merit / Distinction：REAL 百分比
- Scholarships：INTEGER 数量
- School Roll：July 2024，与 data_year=2023 独立

## 3. 场景

### 场景 1：数据提取与导入
- PDF checksum 校验 → PyMuPDF 提取 → 匹配（精确→标准化→MAPPING dict，多候选=ambiguous→失败）→ 未匹配则 exit 1 + unmatched_schools.json → 全匹配后事务 DELETE+INSERT → 自动校验 → COMMIT → 报告
- 校验规则：行数断言、百分比[0,100]、分布和[98,102]、UE独立[0,100]、无重复、rank[1,10]
- **学科排名一致性**：Top10 中的学校不要求必须在 school_ncea_summary 中存在（因为 Top10 包含非 Auckland 学校的可能性），但如果存在则 school_number 必须匹配
- **导入元数据**：在 school_ncea_summary 表增加 `import_checksum TEXT` 和 `imported_at TIMESTAMP` 字段记录导入来源

### 场景 2：列表页 UE 列
- 显示 UE%，无数据显示"-"，排序排末尾
- 已明确、可实现

### 场景 3：详情页 NCEA 板块
- 无 Metro 数据 → 隐藏整个板块
- 有数据 → 显示：UE%、离校生分布图、奖学金数、merit%、distinction%
- 学科排名：仅显示有记录的学科，无排名不显示
- **年份标注**：UI 明确标注 "2023 NCEA 成绩" 和 "在校人数 (July 2024)"，避免混淆

### API 合约
```
GET /api/school/{num}/ncea

# 有数据时 200:
{
  "ncea_summary": {
    "data_year": 2023,
    "ue_percentage": 74.0,
    "below_l1_pct": 5.0,
    "l1_pct": 5.0,
    "l2_pct": 13.0,
    "l3_pct": 3.0,
    "school_leavers": 484,
    "school_roll_july2024": 2696,
    "scholarships": 22,
    "outstanding_merit": 3.0,
    "distinction": 26.0,
    "region": "Albert-Eden",
    "source": "metro_2025"
  },
  "subject_rankings": [
    {"subject": "Sciences", "rank": 3, "level3_pct": 58.97}
  ]
}

# 无数据时 200:
{
  "ncea_summary": null,
  "subject_rankings": []
}
```

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

### 匹配：精确→标准化→MAPPING dict，多候选=ambiguous→fail，最终未匹配→人工
### 导入：checksum→事务→DELETE+INSERT→校验→COMMIT，失败→ROLLBACK
### API：`/api/schools` JOIN → ue_percentage; `/api/school/{num}/ncea` → 完整数据（200 + null 表示无数据）
### UI：列表 UE 列 + 详情 NCEA 板块（无数据隐藏），年份分别标注

## 5. 风险
| 风险 | 严重度 | 缓解 |
|------|--------|------|
| PDF 列错位 | 中 | 正则断言+交叉校验 |
| 学校名匹配 | 中 | 标准化+MAPPING+ambiguous检测 |
| 数据截断 | 低 | 行数断言 |
| PDF 版本变更 | 低 | Checksum 锁定+import_checksum记录 |
| 混淆年份 | 低 | UI 明确标注 2023/2024 |
