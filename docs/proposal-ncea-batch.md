## 1. 需求摘要
- **核心目标**: 将 NCEA 数据爬取从 11 所学校扩展到全部 569 所中学/综合学校
- **目标用户**: NZ School Finder 的使用者（家长、学生、教育中介）
- **关键约束**: 稳定性优先，政府网站礼貌爬取，可分多天完成

## 2. 用户场景

**场景 1: 分批爬取**
- 参与者: 开发者
- 触发条件: `python -m crawlers.batch_ncea --batch-size 50 --offset 0`
- 正常路径: 从 DB 查出目标学校 → 跳过 scrape_log 中 status=success/no_data 的 → 逐校逐指标爬取 → 写入 DB
- 错误路径: 连续 5 次失败触发熔断 → 暂停 10 分钟 → 自动重试一次 → 再失败则退出并输出日志
- 验收标准: 每所学校在 scrape_log 中有 5 条记录（每个指标一条），status 为 success/no_data/failed 之一

**场景 2: 断点续爬**
- 参与者: 开发者
- 触发条件: 上次中断后重新运行同一命令
- 正常路径: 读取 scrape_log → 跳过 status=success 或 status=no_data 的 (school, metric) 对 → 重试 status=failed/timeout 的
- 错误路径: scrape_log 表不存在 → 报错退出（不静默全量爬）
- 验收标准: 不重复爬取已成功/无数据的页面；failed 的会被重试

**场景 3: 数据合并**
- 参与者: 开发者
- 触发条件: worktree 爬取完成后
- 前置条件: 合并前备份主 DB
- 正常路径: 运行 `scripts/merge_db.py` → ATTACH worktree DB → 只合并 4 张 NCEA 相关表 → 输出合并统计
- 错误路径: 合并失败 → 从备份恢复
- 验收标准: 合并后主 DB 的 scrape_log 行数 >= worktree DB 行数；抽样 5 所学校比对数据一致

**场景 4: Dry-run 预览**
- 触发条件: `python -m crawlers.batch_ncea --dry-run`
- 正常路径: 列出目标学校数、已完成数、待爬数、预估时间
- 验收标准: 不发起任何 HTTP 请求

**场景 5: 无数据学校处理**
- 触发条件: 爬取某校某指标时页面返回空表格（<2 tables）
- 正常路径: scrape_log 写入 status=no_data → 以后跳过该 (school, metric) → 继续下一个
- 验收标准: no_data 不计入熔断，不触发重试

## 3. 非功能性需求
- **性能**: 单线程，~18s/页，~2.5min/校，总计 ~22 小时
- **可靠性**: 熔断（连续 5 次 failed/timeout → 暂停 10min → 重试一次 → 再失败退出）；断点续爬
- **数据完整性**: 爬取前自动备份；爬虫内部用 INSERT OR REPLACE（幂等）；跨 DB 合并用 INSERT OR IGNORE（不覆盖）
- **完成率目标**: (success + no_data) / total_attempts >= 95%

## 4. 架构提案

### 4.1 scrape_log status 语义

| status | 含义 | resume 行为 |
|--------|------|------------|
| success | 爬取成功并入库 | 跳过 |
| no_data | 页面无数据（<2 tables） | 跳过 |
| failed | HTTP 错误/解析失败 | 重试 |
| timeout | 请求超时/浏览器崩溃 | 重试 |

### 4.2 熔断错误分类

| 错误类型 | 计入熔断 | 处理 |
|----------|---------|------|
| HTTP 403/500 | 是 | 记录 failed |
| 请求超时/DNS | 是 | 记录 timeout |
| 浏览器崩溃 | 是 | 重启浏览器 + 记录 timeout |
| 页面无表格 (no_data) | 否 | 记录 no_data |
| HTML 结构变化（有表但解析异常） | 否 | 记录 warning + success |

### 4.3 学校筛选查询

```sql
SELECT school_number, school_name
FROM schools
WHERE school_type LIKE '%Secondary%'
   OR school_type LIKE '%Composite%'
ORDER BY school_number
```
启动时输出: `Found {N} target schools (expected ~569)`

### 4.4 文件改动

| 文件 | 改动 |
|------|------|
| `crawlers/batch_ncea.py` | 改造：动态学校查询、--batch-size/--offset、自动备份、熔断、进度显示 |
| `crawlers/ncea_crawler.py` | 小改：scrape_log 增加 status 字段写入 |
| 新增 `scripts/merge_db.py` | Python 合并脚本（ATTACH + INSERT OR IGNORE + 统计输出） |

### 4.5 数据流

```
DB(schools) → SQL查询569所 → 减去scrape_log(success/no_data) → 分批 → Playwright爬取 → 写入DB
```

## 5. 实施计划

| 阶段 | 任务 | 复杂度 |
|------|------|--------|
| Phase 1 | 创建 worktree + 拷贝 DB | 低 |
| Phase 2 | scrape_log 加 status 字段（ALTER TABLE） | 低 |
| Phase 3 | 改造 batch_ncea.py + ncea_crawler.py | 中 |
| Phase 4 | 编写 merge_db.py | 低 |
| Phase 5 | dry-run 验证 | 低 |
| Phase 6 | 第 1 批 50 所试跑验证 | 低（等待长） |
| Phase 7 | 分批跑完剩余 500+ 所 | 低（重复执行） |
| Phase 8 | 合并数据 + 验证 | 低 |

## 6. Worktree + DB 策略

- 新建分支 `feature/ncea-batch-crawl`
- `git worktree add ../learning-ncea-crawl feature/ncea-batch-crawl`
- 创建后: `cp schools.db ../learning-ncea-crawl/schools.db`
- 爬虫在 worktree 中运行，写入 worktree 的 DB
- NCEA 相关 4 张表（school_performance, school_performance_comparison, school_vocational_pathways, scrape_log）只有爬虫写入，主 DB 其他功能不会碰这些表，所以合并安全

## 7. 数据库备份
- 爬取前: `cp schools.db schools_backup_YYYYMMDD_HHMMSS.db`
- 合并前: 再备份一次主 DB
- 恢复: `cp schools_backup_xxx.db schools.db`

## 8. 用户决策记录
| 问题 | 决策 |
|------|------|
| 无数据学校处理 | 标记 no_data，跳过，不重试 |
| 主 DB 是否冻结 | 不冻结，会有其他改动，合并按表隔离 |
| 爬取范围 | 569 所中学+综合学校 |
| 速度要求 | 稳定优先，可分多天 |
