# 审查反馈 — 第 2 轮

本文档回应 **docs/review-2.md**。

**日期**: 2026-03-27 14:00:00

---

## 问题回应

### 问题 1: [critical] 课程名称边界未定义
- **GPT 意见**: junior courses、school-specific courses 如何处理？
- **处理方式**: ASKED_USER
- **回应**: 先用 NZQA 官方框架，学校自定义课程后面再判断是否加入 pool。Overview 只展示 NZQA 官方科目。

### 问题 2: [critical] unmatched 审核后无回填流程
- **GPT 意见**: 审核通过后怎么把数据写回 school_subjects？
- **处理方式**: ACCEPTED
- **回应**: 增加回填流程：审核 approved → 加入 subject_pool → 重新运行 crawler 或手动 INSERT 到 school_subjects。status='mapped' 表示已映射。

### 问题 3: [major] 部分数据 UX 误导
- **GPT 意见**: N schools 没有分母会误导
- **处理方式**: REJECTED
- **回应**: 用户明确说不做特殊处理。14 所学校是学习项目，不会误导。

### 问题 4: [major] subject_pathway 映射必要性
- **GPT 意见**: pathway ↔ subject 映射增加了复杂度
- **处理方式**: ASKED_USER → 移除
- **回应**: 用户确认 pathway 只是信息展示，不需要映射表。前端硬编码 pathway 下的相关课程即可。移除 subject_pathway 表。

### 问题 5: [major] unmatched 缺失频率和新鲜度信息
- **GPT 意见**: UNIQUE + INSERT OR IGNORE 丢失了频率信息
- **处理方式**: ACCEPTED
- **回应**: 增加 first_seen_at, last_seen_at, occurrence_count 字段，用 ON CONFLICT UPDATE 更新

### 问题 6: [major] 模糊匹配规则未定义
- **GPT 意见**: fuzzy match 阈值和规则不清
- **处理方式**: REFINED
- **回应**: 不做 fuzzy match。匹配流程简化为：raw_name → GLOBAL_SUBJECT_MAPPING（精确同义词）→ 未匹配则存 unmatched_subjects。避免误匹配。

### 问题 7: [minor] 前端空状态/排序/中文 fallback
- **GPT 意见**: 未定义
- **处理方式**: ACCEPTED
- **回应**: 排序按 NZQA 官方顺序；name_cn 为空时 fallback 到英文名；API 失败显示错误提示

### 问题 8: [question] Pathway 导航
- **处理方式**: ASKED_USER
- **回应**: 纯信息展示，不需要导航。先做好课程架构。

### 问题 9: [question] 科目范围
- **处理方式**: ASKED_USER
- **回应**: 先 NZQA 官方框架，后续判断学校自定义课程是否加入

## 架构更新
- 移除 subject_pathway 表（Vocational Pathways 前端硬编码展示）
- 移除 vocational_pathway_meta 表（简化为前端配置）
- unmatched_subjects 增加 first_seen_at, last_seen_at, occurrence_count
- 移除 fuzzy match，只用精确同义词映射
- 增加审核回填流程定义

## 摘要
- 已接受: 3 个问题
- 已改进: 1 个问题
- 已拒绝: 1 个问题（部分数据 UX）
- 用户决策: 4 个问题已解决（重大简化：移除 pathway 映射表和 meta 表）
