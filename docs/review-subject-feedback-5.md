# 审查反馈 — 第 5 轮

本文档回应 **docs/review-5.md**。

**日期**: 2026-03-27 15:30:00

---

## 问题回应

### 问题 1: [critical] NZQA 层级关系未显式持久化
- **GPT 意见**: subject_pool 的 Learning Area → Subject 关系依赖遗留手动结构，没有和 NZQA 权威源显式对齐
- **处理方式**: ACCEPTED
- **回应**: P1 阶段创建 NZQA seed 脚本（seed_nzqa.py），从权威快照生成 subject_pool 数据。脚本本身就是持久化的 source of truth。包含：所有 Learning Areas + Subjects + parent_id 关系 + sort_order + ncea_level + medium。脚本运行后可用 assert 验证层级正确性（每个 group 无 parent，每个 subject 有 parent 指向 group）。

### 问题 2: [major] SQLite NULL 唯一性问题 + normalized key
- **GPT 意见**: SQLite 中 UNIQUE(alias, school_number) 当 school_number=NULL 时不生效（NULL != NULL）
- **处理方式**: ACCEPTED
- **回应**:
  - subject_alias: 用 school_number=0 代替 NULL 表示全局映射。UNIQUE(alias, school_number) 正常生效。
  - unmatched_subjects: 增加 normalized_name 字段，去重键改为 UNIQUE(school_number, normalized_name)。raw_name 保留原始值。

### 问题 3: [minor] 空种子/并发写入边界
- **GPT 意见**: seed 缺失或并发 SQLite 写入未定义
- **处理方式**: ACCEPTED
- **回应**: seed 缺失 → API 返回空数组（前端显示空树，不崩溃）。SQLite 写入 → 单线程爬虫，无并发问题。Review 是手动 SQL，不会和爬虫同时运行。

### 问题 4: [question] NZQA 更新策略
- **处理方式**: REFINED
- **回应**: 保持 pinned 到快照版本。手动刷新时更新 seed 脚本并运行迁移。NZQA 分类变化极少（年级别），学习项目不需要自动跟踪。

## 架构更新
- 新增 seed_nzqa.py 种子脚本作为 NZQA 层级的 source of truth
- subject_alias 全局映射用 school_number=0 代替 NULL
- unmatched_subjects 增加 normalized_name 字段，去重基于 normalized_name
- 明确 seed 缺失时的 fallback 行为

## 摘要
- 已接受: 3 个问题
- 已改进: 1 个问题（NZQA 更新策略 = pinned snapshot + 手动迁移）
