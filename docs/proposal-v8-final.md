# 提案 v8（最终版）：从 Metro Schools 2025 PDF 提取 NCEA 数据

## 1. Release 1 范围
- **包含**：PDF 数据提取 → SQLite → 列表页 UE 列 + 详情页 NCEA 板块
- **排除**：区域汇总、趋势图、对比页面

## 2. 数据语义（已从 PDF 实际数据验证）
- **Below_L1 + L1 + L2 + L3** ≈ 100%（±2%），互斥分布。**验证证据**：Auckland Grammar 数据 = 1%+1%+4%+20%+74%(UE) = Below_L1(1)+L1(1)+L2(4)+L3(94)=100%，其中L3包含UE达标的学生
- **UE**：L3 子集，独立报告
- **Outstanding Merit / Distinction**：% of leavers
- **Scholarships**：INTEGER 数量
- **NULL vs 0**：NULL=未报告，0=明确为零

## 3. 核心规则

### 跨表一致性规则
**school_subject_ranking 中的 school_number 必须满足以下之一：**
1. 存在于 school_ncea_summary 中 → 正常存储
2. 不存在且在 RANKING_SKIP_ALLOWLIST 中 → 跳过
3. 不存在且不在 ALLOWLIST 中 → **导入失败**

**即：不允许 ranking-only 状态存在。** 学科排名记录必须有对应的汇总记录，或被明确跳过。

### 学科排名完整性校验
- 断言 11 个学科全部存在
- 每学科断言 rank 序列连续（1,2,3...N），N ≥ 8（允许少量跳过）
- Golden data：至少 2 个学科的完整 Top 10 列表 checksum 绑定

## 4. 场景

### 场景 1：数据提取与导入
1. PDF checksum 校验
2. 提取核心表（第31-33页）+ 学科 Top10（第7-9页）
3. 核心表匹配：精确→标准化→MAPPING dict，多候选=fail，未匹配=exit 1
4. 学科 Top10 匹配：matched+有summary→存，allowlist→跳过，其他→fail
5. 事务 DELETE+INSERT → 校验 → COMMIT
6. 校验：行数、百分比范围、分布和[98,102]、学科完整性（11科+连续rank）、golden data（3所学校+2个学科）、无重复、跨表一致性
7. 任何失败→ROLLBACK

### 场景 2：列表页 — UE% 列，NULL→"-"，排序排末尾
### 场景 3：详情页 — 无数据隐藏板块，有数据显示全部，NULL字段隐藏，年份标注

## 5. 存储 Schema
（同 v7，含 import_checksum + imported_at）

## 6. API
- `/api/schools` → ue_percentage (LEFT JOIN)
- `/api/school/{num}/ncea` → {ncea_summary: obj|null, subject_rankings: []}
- 200 + null = 无数据

## 7. 风险
| 风险 | 严重度 | 缓解 |
|------|--------|------|
| PDF 列错位 | 中 | 正则+golden data+分布校验 |
| 学校名匹配 | 中 | 标准化+MAPPING+ambiguous |
| 学科排名遗漏 | 中 | 11科断言+连续rank+golden data |
| 跨表不一致 | 低 | ranking必须有summary或在allowlist |
| 空值混淆 | 低 | NULL vs 0 规则 |
