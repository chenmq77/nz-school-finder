# 审查反馈 — 第 2 轮（NCEA 批量爬取）

本文档回应 **docs/review-2.md**。

**日期**: 2026-03-28

---

## 问题回应

### 问题 1: [critical] 批次分区不确定
- **GPT 意见**: --offset 在 resume 过滤前后的应用顺序不明确
- **处理方式**: ACCEPTED
- **回应**: --offset/--batch-size 作用于完整的 569 所有序列表（按 school_number 排序），resume 过滤在 slice 之后。即 offset=50 batch-size=50 永远取第 51-100 所学校，跳过其中已完成的。

### 问题 2: [critical] 解析失败标为 success 不安全
- **处理方式**: ACCEPTED
- **回应**: 移除 warning+success 组合。新增 status=parse_error，含义：页面有响应但解析异常。resume 时标记为可重试。

### 问题 3: [major] 合并验证太弱
- **处理方式**: ACCEPTED
- **回应**: merge_db.py 输出每张表的 before/after/delta 行数。加 --verify 参数做 school_number 级别的逐行比对。

### 问题 4: [major] 学校数异常时的行为
- **处理方式**: ACCEPTED
- **回应**: 查询结果 <500 或 >650 时打印 WARNING。加 --strict 模式：数量偏差 >10% 时直接退出。

### 问题 5: [question] 快照还是刷新
- **处理方式**: ASKED_USER
- **回应**: 用户确认用快照（worktree 拷贝的 DB），整个爬取期间学校列表固定。

## 摘要
- 已接受: 4 个 | 用户决策: 1 个
