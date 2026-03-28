# 实现反馈 — 第 1 轮

本文档回应 **docs/impl-review-1.md**。

**日期**: 2026-03-28
**技术栈**: backend (Python + SQLite)

---

## 问题回应

### 问题 1: [major] --verify 双重 ATTACH 导致崩溃
- **GPT 反馈**: verify_merge() 重复 ATTACH src，会报 database src is already in use
- **处理方式**: FIXED
- **解决方案**: verify_merge() 不再自行 ATTACH/DETACH，由 merge() 统一管理生命周期。verify 在 DETACH 前调用。还增加了 scrape_log 行数对比检查。
- **变更文件**: scripts/merge_db.py

### 问题 2: [major] 缺少 schema migration
- **GPT 反馈**: 代码假设 scrape_log.status 已存在，旧 DB 会失败
- **处理方式**: FIXED
- **解决方案**: 新增 ensure_status_column()，在 run_batch() 开头自动检查并迁移。用 PRAGMA table_info 检查列是否存在，不存在则 ALTER TABLE + backfill。
- **变更文件**: crawlers/batch_ncea.py

### 问题 3: [major] 熔断基于 school 级别而非 metric 级别
- **GPT 反馈**: 应该追踪连续 metric 失败，不是 school 异常
- **处理方式**: FIXED
- **解决方案**: scrape_school() 现在返回 results["statuses"]（per-metric 状态列表）。batch 层面读取每个 metric 的 status，failed/timeout 递增计数器，success/no_data 重置。第二次触发熔断则退出。
- **变更文件**: crawlers/ncea_crawler.py, crawlers/batch_ncea.py

### 问题 4: [minor] dry-run 缺少聚合统计
- **GPT 反馈**: 需要输出 target/completed/pending schools 总数
- **处理方式**: FIXED
- **解决方案**: dry-run 和正常模式都输出 Summary 区块：Target schools / Completed schools / Pending schools / Pending pages / Estimated time
- **变更文件**: crawlers/batch_ncea.py

## 补充修复
- school count 验证改为明确的 500-650 范围（不再用百分比偏差）

## 摘要
- 已修复: 4 个问题
- 已拒绝: 0 个
- 已延后: 0 个
