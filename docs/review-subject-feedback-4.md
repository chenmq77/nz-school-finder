# 审查反馈 — 第 4 轮

本文档回应 **docs/review-4.md**。

**日期**: 2026-03-27 15:00:00

---

## 问题回应

### 问题 1: [critical] subject_alias 全局唯一导致跨学校误匹配
- **GPT 意见**: 一个 alias 全局映射到一个 subject，但同名课程在不同学校可能指不同科目
- **处理方式**: ACCEPTED
- **回应**: 改 subject_alias 为 (alias, school_number) 复合键。school_number=NULL 表示全局映射，非 NULL 表示学校特定映射。匹配时先查学校特定，再查全局。冲突时存入 unmatched_subjects。

### 问题 2: [major] 原需求要求 fuzzy matching 但选了 no fuzzy
- **GPT 意见**: 需要明确 scope sign-off
- **处理方式**: REFINED
- **回应**: "优化模糊匹配规则" 实际意图是改善匹配覆盖率，不一定是 fuzzy string matching。通过 subject_alias 表（~100+ 条已知映射）+ 基础正则化（大小写、&/and、复数/单数）实现。这比 fuzzy matching 更精确、可控。正式 sign-off：不做 Levenshtein 或 token 级别的 fuzzy match。

### 问题 3: [major] NZQA 排序/级别/Te Reo 变体缺 schema
- **GPT 意见**: 需要字段来支持
- **处理方式**: ACCEPTED
- **回应**: subject_pool 增加 3 个字段：sort_order INT (NZQA 官方顺序), ncea_level TEXT ('all','L1','L2','L3' 或 NULL), medium TEXT ('en','mi' 默认 'en')。Te Reo medium 科目 medium='mi'。

### 问题 4: [question] 部分数据标注
- **处理方式**: REJECTED
- **回应**: 用户已 3 次明确表示不做特殊处理。这是学习项目，不会误导。不再讨论此话题。

## 架构更新
- subject_alias 改为 (alias, school_number) 复合键，支持学校特定映射
- subject_pool 增加 sort_order, ncea_level, medium 字段
- 匹配增加基础正则化层（大小写、&/and、复数变体）

## 摘要
- 已接受: 2 个问题
- 已改进: 1 个问题
- 已拒绝: 1 个问题（部分数据标注 — 用户已多次明确拒绝）
