# 审查反馈 — 第 3 轮

本文档回应 **docs/review-3.md**。

**日期**: 2026-03-27 14:30:00

---

## 问题回应

### 问题 1: [critical] 审核映射未反馈到爬虫
- **GPT 意见**: status='mapped' 不影响未来爬虫匹配，同名课程会再次 unmatched
- **处理方式**: ACCEPTED
- **回应**: 审核通过后，将映射关系写入 GLOBAL_SUBJECT_MAPPING。工作流改为：审核 → 加入 subject_pool 或更新 GLOBAL_SUBJECT_MAPPING → 下次爬虫自动匹配。GLOBAL_SUBJECT_MAPPING 从数据库加载（新增 subject_alias 表），不再是 Python 硬编码。

### 问题 2: [major] NZQA 对齐无可验证快照
- **GPT 意见**: 没有定义"完全对齐"的含义
- **处理方式**: ACCEPTED
- **回应**: 已从 NZQA 官网获取完整科目列表（97 个科目）。将作为 v1 快照存入代码，附快照日期 2026-03-27。对齐验证 = subject_pool 包含 NZQA 列表中所有适用科目。

### 问题 3: [minor] raw_name 正则化和空状态
- **GPT 意见**: 去重前需要正则化 raw_name
- **处理方式**: ACCEPTED
- **回应**: raw_name 存储前做基本正则化：strip + 合并空格 + 统一引号。API 错误返回 {error: message}，前端显示错误提示。

### 问题 4: [question] Pathway 内容来源
- **处理方式**: ASKED_USER
- **回应**: 用户要求从 NZQA 获取数据存数据库。经调研发现 NZQA vocational pathways 是通过 assessment standards 关联到 subjects 的，不是直接 subject 映射。方案：vocational_pathway_meta 表存 6 个 pathway 的基本信息和 focus areas（描述性关联），pathway 与 subject 的精确映射需要后续爬 NZQA Profile Builder 工具。

## 架构更新
- 新增 `subject_alias` 表替代硬编码的 GLOBAL_SUBJECT_MAPPING（alias → subject_id）
- 恢复 `vocational_pathway_meta` 表（存 NZQA 数据，非硬编码）
- subject_pool 需要从 78 个对齐到 NZQA 的 97 个科目
- 审核回填流程闭环：review → 写入 subject_alias 或 subject_pool → 下次爬虫自动匹配

## 摘要
- 已接受: 3 个问题
- 用户决策: 1 个问题（pathway 内容存数据库，从 NZQA 获取）
