# 审查反馈 — 第 1 轮

本文档回应 **docs/review-1.md**。

**日期**: 2026-03-27 13:30:00

---

## 问题回应

### 问题 1: [critical] 学校计数语义不明确
- **GPT 意见**: subject count 是 distinct schools 还是 raw course rows？
- **处理方式**: ACCEPTED
- **回应**: 明确为 COUNT(DISTINCT school_number) FROM school_subjects，一个学校一个科目只算一次

### 问题 2: [major] NZQA 权威数据源未明确
- **GPT 意见**: 需要指定 NZQA 来源、提取方式、更新策略
- **处理方式**: REFINED
- **回应**: 使用 NZQA 官网 Learning Areas 页面作为权威源，手动维护快照，不需要自动更新（学习项目，分类变化极慢）

### 问题 3: [major] unmatched_subjects 与 raw 表矛盾
- **GPT 意见**: 用户说存 raw 表但提案建了 unmatched_subjects 专用表
- **处理方式**: REFINED
- **回应**: unmatched_subjects 就是 raw 表，命名统一为 unmatched_subjects，无矛盾

### 问题 4: [major] 两级层级未强制约束
- **GPT 意见**: subject_pool 允许更深嵌套
- **处理方式**: ACCEPTED
- **回应**: 加 CHECK 约束或在代码中校验：group 的 parent_id 必须为 NULL，subject 的 parent_id 必须指向 group

### 问题 5: [major] 审核流程缺失
- **GPT 意见**: unmatched_subjects 没有审核机制和去重策略
- **处理方式**: ACCEPTED
- **回应**: 去重键 = (school_number, raw_name)，ON CONFLICT IGNORE。审核通过 CLI 脚本或手动 SQL

### 问题 6: [major] Vocational 卡片指标不明确
- **GPT 意见**: 卡片上显示什么统计数据？
- **处理方式**: ASKED_USER
- **回应**: 用户要求显示每个 pathway 下的相关课程。需要新增 pathway → subject 映射表

### 问题 7: [major] 发布时序与不完整数据
- **GPT 意见**: 14 所学校数据不完整时页面如何展示
- **处理方式**: ASKED_USER
- **回应**: 用户决定不做特殊处理，直接展示当前数据

### 问题 8: [minor] 搜索栏范围蔓延
- **GPT 意见**: 搜索栏是新增功能，无需求支撑
- **处理方式**: ACCEPTED
- **回应**: 移到 P4+ 可选功能，核心页面先不做搜索

### 问题 9: [question] 零数据科目显示
- **处理方式**: ASKED_USER
- **回应**: 显示但灰色样式，保持 NZQA 完整分类

### 问题 10: [question] unmatched 审核开销
- **处理方式**: REFINED
- **回应**: ~50 所学校量级很小，手动 SQL 审核足够

### 问题 11: [question] Pathway 卡片指标
- **处理方式**: ASKED_USER
- **回应**: 显示每个 pathway 下的相关课程列表（需要 pathway_subject 映射）

## 架构更新
- 新增 `subject_pathway` 映射表：subject_id + pathway_id，实现 pathway → subject 关联
- subject_pool 加层级校验约束
- 搜索栏移至可选功能
- unmatched_subjects 加 UNIQUE(school_number, raw_name) 去重

## 用户决策
- 问: 零数据科目显示？ → 答: 显示但灰色
- 问: Pathway 卡片指标？ → 答: 显示相关课程（需要映射表）
- 问: 部分数据？ → 答: 不做特殊处理

## 摘要
- 已接受: 4 个问题
- 已改进: 3 个问题
- 已拒绝: 0 个问题
- 用户决策: 4 个问题已解决（含 1 个重大变更：pathway 需关联 subject）
