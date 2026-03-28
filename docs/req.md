# NCEA 全量数据批量爬取方案（569 所中学）

## 背景

NZ School Finder 项目数据库有 2,577 所学校，其中 569 所中学/综合学校有 NCEA 数据。
目前已成功爬取 11 所学校（55 条记录，全部成功），需要扩展到全部 569 所。

## 当前状态

| 项目 | 数值 |
|------|------|
| 数据库总学校数 | 2,577 |
| 中学 + 综合学校 | 569 |
| 已爬取学校 | 11 所（5 指标全部完成） |
| 待爬取学校 | 558 所 |
| 待爬取页面数 | ~2,790（558 × 5 指标） |
| 数据库大小 | 2MB |

## 爬取目标

来源: educationcounts.govt.nz，5 个指标：
1. retention — 留校率
2. ncea1 — NCEA Level 1
3. ncea2 — NCEA Level 2
4. ncea3 — NCEA Level 3 / UE
5. vocational — 职业路径奖

## 核心需求

### 1. 代码隔离 — Git Worktree

- 新建分支 `feature/ncea-batch-crawl`，用 worktree 隔离
- 主目录继续日常开发，worktree 专门跑爬虫
- DB 不被 git 追踪（在 .gitignore 中），worktree 需拷贝一份 DB 副本
- 爬完后通过 SQL ATTACH 将新数据导回主目录 DB

### 2. 批量爬取改造

- 当前 `batch_ncea.py` 硬编码了 10 所学校列表
- 改为从 DB 动态查询 569 所中学/综合学校
- 添加 `--batch-size` 和 `--offset` 参数支持分批执行
- 保留现有的 `scrape_log` 断点续爬机制

### 3. 稳定性优先

- 不做并发，单线程顺序爬取
- 页间延迟 10~15s，校间延迟 30~60s
- 添加熔断机制：连续 N 次失败后暂停
- 分批执行，预计分 3~4 天完成

### 4. 数据库备份

- 爬取前自动备份 `schools.db` → `schools_backup_YYYYMMDD.db`
- DB 仅 2MB，直接文件拷贝

### 5. 数据合并

爬完后用 SQL 合并：
```sql
ATTACH 'worktree/schools.db' AS src;
INSERT OR IGNORE INTO school_performance SELECT * FROM src.school_performance;
INSERT OR IGNORE INTO scrape_log SELECT * FROM src.scrape_log;
-- 同理其它表
DETACH src;
```

## 现有代码基础

- `crawlers/ncea_crawler.py` — 单校爬取，Playwright + headless Chrome
- `crawlers/batch_ncea.py` — 批量入口，有 dry-run 模式和 scrape_log 跳过逻辑
- 数据库表已就绪：`school_performance`, `school_performance_comparison`, `school_vocational_pathways`, `scrape_log`

## 执行步骤

1. 新建分支 + worktree
2. 拷贝 DB 到 worktree
3. 改造 `batch_ncea.py`（动态查询学校、分批参数、自动备份、熔断）
4. dry-run 验证计划
5. 第 1 批 50 所验证稳定性
6. 分批跑完剩余
7. SQL ATTACH 合并数据回主 DB

## 约束

- 稳定性 > 速度，可以分几天完成
- educationcounts.govt.nz 是政府网站，需礼貌爬取
- 部分小型学校可能无 NCEA 数据（需容错处理）
