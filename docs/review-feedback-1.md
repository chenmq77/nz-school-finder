# 审查反馈 — 第 1 轮（NCEA 批量爬取）

本文档回应 **docs/review-1.md**。

**日期**: 2026-03-28

---

## 问题回应

### 问题 1: [critical] 无数据学校的完成状态语义
- **GPT 意见**: 没有定义 success/no_data/failed 状态，resume 和验收标准会出错
- **处理方式**: ACCEPTED
- **回应**: scrape_log 新增 status 字段（success/no_data/failed/timeout），resume 跳过 success 和 no_data

### 问题 2: [critical] 多天爬取期间主 DB 变化导致合并冲突
- **GPT 意见**: INSERT OR IGNORE 不处理并发变化
- **处理方式**: REFINED
- **回应**: 用户确认主 DB 会有改动。NCEA 相关的 4 张表只有爬虫写入，其他功能不会碰，所以合并时按表隔离即可。合并前先备份主 DB。

### 问题 3: [major] INSERT OR IGNORE vs INSERT OR REPLACE 矛盾
- **处理方式**: ACCEPTED
- **回应**: 爬虫内部写入用 INSERT OR REPLACE（重跑覆盖），跨 DB 合并用 INSERT OR IGNORE（不覆盖主 DB 已有）

### 问题 4: [major] 熔断机制定义不完整
- **处理方式**: ACCEPTED
- **回应**: 扩展错误分类 + 阈值：连续 5 次失败（全局）→ 暂停 10 分钟后重试一次，再失败退出

### 问题 5: [major] 学校筛选查询不明确
- **处理方式**: ACCEPTED
- **回应**: 明确 SQL 查询，启动时输出实际数量

### 问题 6: [major] 验收标准太弱
- **处理方式**: ACCEPTED
- **回应**: 每校 5 条 scrape_log 记录，完成率 (success+no_data)/total >= 95%

### 问题 7: [minor] 备份覆盖
- **处理方式**: ACCEPTED → 改为带时分秒时间戳

### 问题 8: [minor] UA 伪装合规性
- **处理方式**: REJECTED — 已有代码，非本次新增

### 问题 9-10: [question] 用户决策
- 无数据 → 标记 no_data 跳过
- 主 DB → 会有改动，合并按表隔离

## 摘要
- 已接受: 6 个 | 已改进: 1 个 | 已拒绝: 1 个 | 用户决策: 2 个
