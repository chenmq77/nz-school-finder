# 实现计划：NCEA 批量爬取改造（569 所中学）

## 需求摘要
- 将 NCEA 爬取从 11 所扩展到 569 所中学，worktree 隔离，分批执行，3~4 天完成

## 技术栈
- Python 3 + SQLite + Playwright

## 数据库变更
- scrape_log 新增 `status` TEXT 字段
- 迁移已有数据: success=1 → status='success', success=0 → status='failed'

## 文件变更

### crawlers/ncea_crawler.py（小改）
- scrape_log 写入增加 status 字段
- 区分 success / no_data / failed / timeout / parse_error

### crawlers/batch_ncea.py（主要改造）
- 移除硬编码 TARGET_SCHOOLS
- get_target_schools(): 从 DB 动态查询
- --batch-size / --offset 参数
- --strict 模式（学校数偏差 >10% 退出）
- auto_backup_db(): 自动备份（带时分秒）
- circuit_breaker: 连续 5 次失败 → 暂停 10min → 重试 → 退出
- resume: 跳过 success/no_data，重试 failed/timeout/parse_error
- 进度显示 + ETA

### scripts/merge_db.py（新建）
- ATTACH 源 DB
- INSERT OR IGNORE 4 张表
- per-table before/after/delta 统计
- --verify: school_number 级别比对
- 合并前自动备份目标 DB

## 实现顺序
1. ALTER TABLE scrape_log — 无依赖
2. ncea_crawler.py status 写入 — 依赖 #1
3. batch_ncea.py 改造 — 依赖 #2
4. merge_db.py — 独立
