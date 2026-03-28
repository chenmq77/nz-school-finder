# 最终需求规格：NCEA 全量批量爬取（569 所中学）

**来源**: docs/req.md
**精炼过程**: 经过 2 轮 Claude + GPT 挑战
**日期**: 2026-03-28
**状态**: PARTIALLY_APPROVED（达到最大轮数，核心问题已解决）

---

## 1. 需求摘要

将 NCEA 数据爬取从已完成的 11 所学校扩展到全部 569 所中学/综合学校。通过 Git Worktree 隔离爬虫工作与日常开发，使用 SQLite 快照 + 分批爬取 + 断点续爬的架构，稳定性优先，预计 3~4 天完成。

## 2. 用户场景

### 场景 1: 分批爬取
- **参与者**: 开发者
- **触发条件**: `python -m crawlers.batch_ncea --batch-size 50 --offset 0`
- **前置条件**: worktree 已创建，DB 已拷贝
- **正常路径**:
  1. 从 DB 查出目标学校（按 school_number 排序）
  2. 按 --offset/--batch-size 取子集（固定排序，确定性切片）
  3. 跳过 scrape_log 中 status=success/no_data 的 (school, metric) 对
  4. 逐校逐指标爬取，写入 DB
  5. 输出进度和 ETA
- **错误路径**:
  - 连续 5 次 failed/timeout → 暂停 10 分钟 → 自动重试一次 → 再失败退出
- **验收标准**:
  - [ ] 每所学校在 scrape_log 中有 5 条记录
  - [ ] 每条 status 为 success/no_data/failed/timeout/parse_error 之一

### 场景 2: 断点续爬
- **触发条件**: 上次中断后重新运行同一命令
- **正常路径**: 读取 scrape_log → 跳过 success/no_data → 重试 failed/timeout/parse_error
- **验收标准**:
  - [ ] 不重复爬取 status=success/no_data 的页面
  - [ ] failed 的会被重试

### 场景 3: 数据合并
- **触发条件**: worktree 爬取完成后
- **前置条件**: 合并前备份主 DB
- **正常路径**: `python scripts/merge_db.py --source ../learning-ncea-crawl/schools.db --verify`
  1. ATTACH worktree DB
  2. INSERT OR IGNORE 4 张 NCEA 表
  3. 输出每张表的 before/after/delta 行数
  4. --verify 模式做 school_number 级别比对
- **错误路径**: 失败 → 从备份恢复
- **验收标准**:
  - [ ] 每张表 delta >= 0
  - [ ] scrape_log 行数 >= worktree DB 行数
  - [ ] 抽样 5 所学校数据一致

### 场景 4: Dry-run 预览
- **触发条件**: `python -m crawlers.batch_ncea --dry-run`
- **验收标准**:
  - [ ] 输出目标学校数、已完成数、待爬数、预估时间
  - [ ] 不发起任何 HTTP 请求

### 场景 5: 无数据学校
- **触发条件**: 页面返回空表格（<2 tables）
- **正常路径**: scrape_log 写入 status=no_data → 永久跳过
- **验收标准**:
  - [ ] no_data 不计入熔断计数器
  - [ ] resume 时跳过

## 3. 非功能性需求

- **性能**: 单线程，~18s/页，~2.5min/校，总计 ~22 小时
- **可靠性**: 熔断 + 断点续爬 + 自动备份
- **数据完整性**: 爬虫内部 INSERT OR REPLACE（幂等），跨 DB 合并 INSERT OR IGNORE（不覆盖）
- **完成率**: (success + no_data) / total >= 95%

## 4. 架构

### scrape_log status 语义

| status | 含义 | resume 行为 |
|--------|------|------------|
| success | 成功入库 | 跳过 |
| no_data | 页面无数据 | 跳过（永久） |
| failed | HTTP 错误/网络问题 | 重试 |
| timeout | 超时/浏览器崩溃 | 重试 |
| parse_error | 有响应但解析异常 | 重试 |

### 熔断错误分类

| 错误类型 | 计入熔断 | status |
|----------|---------|--------|
| HTTP 403/500 | 是 | failed |
| 超时/DNS/网络 | 是 | timeout |
| 浏览器崩溃 | 是（重启后） | timeout |
| 无表格（无数据） | 否 | no_data |
| 有表但解析异常 | 否 | parse_error |

熔断阈值: 连续 5 次 failed/timeout → 暂停 10 分钟 → 自动重试一次 → 再失败退出

### 学校筛选查询

```sql
SELECT school_number, school_name
FROM schools
WHERE school_type LIKE '%Secondary%'
   OR school_type LIKE '%Composite%'
ORDER BY school_number
```

启动时: `Found {N} target schools (expected ~569)`
- N < 500 或 N > 650 → WARNING
- --strict 模式: 偏差 >10% → 退出

### --offset/--batch-size 语义

1. 查询完整有序学校列表（按 school_number）
2. `list[offset : offset + batch_size]` 取子集
3. 对子集中每所学校检查 scrape_log，跳过已完成的
4. 爬取剩余的

这保证 `--offset 50 --batch-size 50` 永远指向同一组学校。

### 技术选型

| 选择 | 理由 |
|------|------|
| Playwright + headless Chrome | 目标站需 JS 渲染（已有） |
| SQLite | 轻量本地存储（已有） |
| Git Worktree | 代码隔离，不影响主目录开发 |
| 单线程 | 稳定性优先，避免政府网站封禁 |

### 文件改动

| 文件 | 改动 |
|------|------|
| `crawlers/batch_ncea.py` | 主要改造：动态查询、分批、备份、熔断、进度 |
| `crawlers/ncea_crawler.py` | 小改：scrape_log 增加 status 字段 |
| 新增 `scripts/merge_db.py` | 合并脚本（ATTACH + INSERT OR IGNORE + 验证） |

## 5. 实施计划

### Phase 1: 环境准备
- 创建分支 `feature/ncea-batch-crawl`
- `git worktree add ../learning-ncea-crawl feature/ncea-batch-crawl`
- `cp schools.db ../learning-ncea-crawl/schools.db`
- ALTER TABLE scrape_log ADD COLUMN status TEXT

### Phase 2: 代码改造
- batch_ncea.py: 动态学校查询 + --batch-size/--offset + 自动备份 + 熔断 + 进度
- ncea_crawler.py: status 字段写入

### Phase 3: 合并脚本
- 编写 scripts/merge_db.py（ATTACH + INSERT OR IGNORE + per-table 统计 + --verify）

### Phase 4: 验证
- dry-run 检查计划
- 第 1 批 50 所试跑

### Phase 5: 执行
- 分批跑完剩余 500+ 所（每天 1~2 批）

### Phase 6: 合并 + 收尾
- 合并数据回主 DB
- 验证完成率
- merge 代码回 main 分支

## 6. 用户决策记录

| 问题 | 决策 | 轮次 |
|------|------|------|
| 爬取范围 | 569 所中学+综合学校 | 0 |
| 速度要求 | 稳定优先，可分多天 | 0 |
| 无数据学校处理 | 标记 no_data，永久跳过 | 1 |
| 主 DB 是否冻结 | 不冻结，合并按表隔离 | 1 |
| 学校列表来源 | 用快照（worktree DB），不刷新 | 2 |

## 7. 已知风险与权衡

| 风险 | 严重程度 | 缓解措施 |
|------|----------|----------|
| 政府网站结构变化 | 中 | parse_error 状态可重试；第 1 批验证 |
| 长时间运行浏览器退化 | 低 | 每批重启进程 |
| 主 DB 与 worktree DB 的 schema 不一致 | 低 | 爬取前确认 schema 版本一致 |
| 部分学校无数据比例过高 | 低 | no_data 不计入失败率 |

## 8. 范围之外
- 并发爬取
- 数据增量更新/定期重爬
- 前端展示改动
- 其他学校类型（小学等）

## 9. 审查记录

| 轮次 | 分数 | 结论 | 文件 |
|------|------|------|------|
| 1 | 5/10 | CHANGES_REQUESTED | review-1.md, review-feedback-1.md |
| 2 | 6/10 | CHANGES_REQUESTED | review-2.md, review-feedback-2.md |
