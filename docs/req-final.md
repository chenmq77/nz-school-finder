# 最终需求规格说明

**来源**: docs/req.md
**精炼过程**: 经过 8 轮 Claude + GPT 挑战
**日期**: 2026-03-27
**状态**: PARTIALLY_APPROVED (8/10)

---

## 1. 需求摘要

从 Metro Magazine Schools 2025 报告（PDF）中提取 Auckland 约 80 所高中的 2023 年 NCEA 成绩数据，包括核心汇总表和 11 个学科 Top 10 排名，存入 SQLite 数据库，整合到现有学校列表页（UE 列）和详情页（NCEA 板块）。Release 1 不含区域汇总、趋势图和对比功能。

## 2. 用户场景

### 场景 1: 数据提取与导入
- **参与者**: 开发者
- **触发条件**: 运行 `python extract_metro_ncea.py`
- **前置条件**: PDF 文件通过 MD5 checksum 校验
- **正常路径**:
  1. 校验 PDF 文件（文件名 + MD5 checksum），不匹配则 exit 1
  2. PyMuPDF 提取第 31-33 页核心数据表（~80 所学校）
  3. PyMuPDF 提取第 7-9 页学科 Top 10（11 学科 × ≤10 校）
  4. 核心表学校匹配：精确 → 标准化（去标点、"H S"→"High School"）→ MAPPING dict
  5. 多候选匹配（ambiguous）→ 同未匹配处理
  6. 学科 Top10 学校匹配：
     - 匹配成功且有 summary 记录 → 存储
     - 未匹配且在 RANKING_SKIP_ALLOWLIST → 跳过，记录到 skip_report
     - 未匹配且不在 ALLOWLIST → 导入失败
  7. 核心表有未匹配学校 → 输出 unmatched_schools.json + exit 1
  8. 全部匹配后：开启 SQLite 事务（WAL 模式，避免锁定读取）
  9. DELETE FROM school_ncea_summary WHERE source='metro_2025' AND data_year=2023
  10. DELETE FROM school_subject_ranking WHERE source='metro_2025' AND data_year=2023
  11. INSERT 所有记录
  12. 运行自动校验（见下方）
  13. 校验通过 → COMMIT，输出统计报告
  14. 校验失败 → ROLLBACK + exit 1
- **错误路径**:
  - Checksum 不匹配 → exit 1，不修改数据库
  - 未匹配/ambiguous → exit 1 + unmatched_schools.json
  - 正则断言失败 → exit 1
  - 校验失败 → ROLLBACK + exit 1
- **验收标准**:
  - [ ] 100% 核心表学校已处理（匹配 + 已知跳过）
  - [ ] 自动校验全部通过
  - [ ] 10 所学校手动逐字段比对 PDF 一致

**自动校验规则**:
- 核心表行数 = PDF 提取数 - 跳过数
- 所有百分比字段 ∈ [0, 100]
- Below_L1 + L1 + L2 + L3 ∈ [98, 102]（舍入容差）
- UE ∈ [0, 100]（独立校验，不参与分布加和）
- 无重复 school_number
- 学科排名：11 个学科全部存在，每学科 rank 序列连续（1..N, N≥8）
- 跨表一致性：school_subject_ranking 中的 school_number 必须存在于 school_ncea_summary
- Golden data 断言（checksum 绑定）:
  - Auckland Grammar School: UE=74%, school_leavers=484
  - Rangitoto College: 验证全部字段
  - Macleans College: 验证全部字段
  - Sciences 学科 Top 10: 验证完整排名列表
  - Mathematics 学科 Top 10: 验证完整排名列表

### 场景 2: 列表页 UE 列
- **参与者**: 家长/中介
- **触发条件**: 浏览学校列表，在可配置列中勾选"大学入学率(UE)"
- **正常路径**: 列表显示 UE%，支持升降序排序
- **错误路径**: 无 UE 数据 → 显示 "-"，排序时排末尾（无论升降序）
- **验收标准**:
  - [ ] UE 列正确显示百分比值
  - [ ] 排序逻辑正确（NULL 排末尾）

### 场景 3: 详情页 NCEA 板块
- **参与者**: 家长
- **触发条件**: 点击学校详情
- **正常路径**: 显示 UE%、离校生分布（Below L1/L1/L2/L3 条形图）、奖学金数量、Outstanding Merit%、Distinction%、学科排名（仅显示有排名的学科，标注"Metro 2025 Top 10"）
- **错误路径**: 无 Metro 数据 → 隐藏整个 NCEA 板块（不显示空状态提示）
- **验收标准**:
  - [ ] 10 所学校数据与 PDF 逐字段一致
  - [ ] 无数据学校不显示 NCEA 板块
  - [ ] NULL 字段不显示（非显示为 0）
  - [ ] 年份标注正确："2023 NCEA 成绩" / "在校人数 (July 2024)"

## 3. 非功能性需求
- **数据准确性**: Golden data 自动断言 + 10 所学校手动比对
- **数据覆盖**: 仅 Auckland ~80 所高中，其余 2500 所学校不受影响
- **数据来源标注**: UI 显示 "来源: Metro Magazine Schools 2025"
- **导入安全**: SQLite WAL 模式，导入期间不影响读取；导入为离线管理操作
- **与 school_performance 的关系**: 两表独立，不修改现有数据

## 4. 架构

### 数据语义（已从 PDF 第30页方法论 + 实际数据验证）
- **Below_L1 + L1 + L2 + L3** = 100%（±2% 舍入容差），按最高达成级别的互斥离校生分布
- **UE** = University Entrance，是 L3 的子集，独立报告
- **Outstanding Merit**: % of leavers with NCEA endorsed with Merit
- **Distinction**: % of leavers with NCEA endorsed with Excellence
- **Scholarships**: 整数，奖学金展示数量
- **School Roll**: July 2024 在校总人数，独立于 2023 成绩数据

### NULL/空值处理
| PDF 中的值 | 存储 | API 返回 | UI 显示 |
|------------|------|----------|---------|
| 数字值（如 74%） | REAL/INTEGER | 数字 | 数字 |
| 空白/"-"/无值 | NULL | null | 隐藏该字段 |
| "0" 或 "0%" | 0 | 0 | "0" 或 "0%" |

### 存储 Schema

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

CREATE INDEX idx_ncea_summary_year ON school_ncea_summary(data_year);
CREATE INDEX idx_subject_ranking_subject ON school_subject_ranking(subject, data_year);
```

### 学校名匹配策略
1. **精确匹配**: PDF school_name == schools.school_name
2. **标准化匹配**: 去标点、trim、缩写展开（"H S"→"High School", "St"→"Saint"）
3. **MAPPING dict**: 硬编码已知差异的手动映射
4. **多候选（ambiguous）**: 多条 schools 记录匹配 → fail
5. **未匹配**: 输出 unmatched_schools.json + exit 1，人工审核
6. **学科 Top10 跳过**: RANKING_SKIP_ALLOWLIST 白名单

### API

**列表 API** — `/api/schools` SQL 增加:
```sql
LEFT JOIN school_ncea_summary n
  ON CAST(s.school_number AS INTEGER) = n.school_number
  AND n.data_year = (SELECT MAX(data_year) FROM school_ncea_summary)
```

**新增端点** — `GET /api/school/{num}/ncea`:
```json
{
  "ncea_summary": { "data_year": 2023, "ue_percentage": 74.0, "..." : "..." },
  "subject_rankings": [{"subject": "Sciences", "rank": 3, "level3_pct": 58.97}]
}
// 无数据: {"ncea_summary": null, "subject_rankings": []}
```

### 前端
- **列表页**: UE 列（可配置），NULL → "-"
- **详情页**: NCEA 板块（无数据隐藏），学科排名标注"Metro 2025 Top 10"
- **年份标注**: "2023 NCEA 成绩" / "在校人数 (July 2024)"
- **来源标注**: "来源: Metro Magazine Schools 2025"

## 5. 实施计划

### 阶段 1: PDF 提取脚本
- 编写 `extract_metro_ncea.py`
- PyMuPDF 提取 + 正则解析
- 依赖: PyMuPDF (已安装)
- 风险: PDF 列错位 → 正则断言 + golden data

### 阶段 2: 学校名匹配
- 三层匹配 + ambiguous 检测
- MAPPING dict + RANKING_SKIP_ALLOWLIST
- 依赖: 阶段 1 + schools 表
- 风险: 名称不一致 → 手动映射

### 阶段 3: 数据库建表与导入
- 创建两张新表
- 事务式幂等导入（WAL 模式）
- 自动校验 + golden data
- 依赖: 阶段 2

### 阶段 4: 数据验证
- 自动校验通过
- 10 所学校手动比对
- 依赖: 阶段 3

### 阶段 5: API 改造
- `/api/schools` 增加 ue_percentage
- 新增 `/api/school/{num}/ncea`
- 依赖: 阶段 3

### 阶段 6: 前端展示
- 列表页 UE 列 + 排序
- 详情页 NCEA 板块
- 依赖: 阶段 5

## 6. 用户决策记录
| 问题 | 决策 | 轮次 |
|------|------|------|
| 提取范围 | 核心表 + 学科 Top10 | 0 |
| 存储方案 | 仅新表（不动 school_performance） | 0 |
| Release 1 范围 | 仅学校级别数据（列表+详情） | 1 |
| 无数据显示方式 | 隐藏/留白 | 3 |
| 未匹配学校处理 | 人工审核 | 2 |
| Top10 未匹配校 | 直接跳过 | 5 |
| 对比页面 | Release 1 不含 | 4 |

## 7. 已知风险与已接受的权衡
| 风险 | 严重程度 | 缓解措施 |
|------|----------|----------|
| PDF 文本列错位 | 中 | 正则断言 + golden data + 分布交叉校验 |
| 学校名匹配失败/歧义 | 中 | 三层匹配 + ambiguous 检测 + 人工审核 |
| 学科排名部分遗漏 | 中 | 11 科完整性断言 + 连续 rank + golden data |
| 数据截断 | 低 | 行数断言 |
| PDF 版本变更 | 低 | Checksum 锁定 + import_checksum |
| 数据仅覆盖 Auckland | 低 | UI 标注来源和范围 |
| 年份混淆 | 低 | UI 分别标注 2023/July 2024 |

## 8. 范围之外
- 区域汇总视图（第 3-6 页数据）
- 2020-2023 年度趋势图
- 多校对比页面 NCEA 整合
- 非 Auckland 学校数据
- 自动更新/爬取新年度 PDF

## 9. 审查记录
| 轮次 | 分数 | 结论 | 文件 |
|------|------|------|------|
| 1 | 5/10 | CHANGES_REQUESTED | review-1.md |
| 2 | 6/10 | CHANGES_REQUESTED | review-2.md |
| 3 | 7/10 | CHANGES_REQUESTED | review-3.md |
| 4 | 7/10 | CHANGES_REQUESTED | review-4.md |
| 5 | 7/10 | CHANGES_REQUESTED | review-5.md |
| 6 | 8/10 | CHANGES_REQUESTED | review-6.md |
| 7 | 8/10 | CHANGES_REQUESTED | review-7.md |
| 8 | 8/10 | CHANGES_REQUESTED | review-8.md |
