# 审查反馈 — 爬虫方案第 1 轮

**日期**: 2026-03-22

## 问题回应

### 问题 1: 字段≠能稳定结构化提取
- **处理方式**: ACCEPTED
- **回应**: 每个字段增加"提取难度"和"回退策略"评估

### 问题 2: NCEA 成绩应走官方源
- **处理方式**: ACCEPTED
- **回应**: NCEA 改为从 Education Counts/NZQA 公开数据获取，官网仅作补充

### 问题 3: 数据架构过于扁平
- **处理方式**: ACCEPTED
- **回应**: 改为三层架构：schools（已有）+ source_pages + extracted_facts

### 问题 4-5: 字段优先级重排 + 缺少字段
- **处理方式**: ACCEPTED
- **回应**: 重新分 Tier 1/2/3，补充学生支持、入学流程等

### 问题 6: 过早绑定 Scrapling
- **处理方式**: REFINED
- **回应**: Scrapling 仍作为技术选型，但明确其适用边界（HTML 页面），PDF 用专门工具

### 问题 7: StealthyFetcher 不应默认
- **处理方式**: ACCEPTED
- **回应**: 默认用普通 Fetcher + robots.txt 检查，仅 JS 渲染页面回退 DynamicFetcher

### 问题 8-10: 分层样本 + 测试学校偏乐观
- **处理方式**: ACCEPTED
- **回应**: 扩展到 6 所代表性学校，覆盖不同网站形态

## 摘要
- 已接受: 8 个
- 已改进: 1 个
- 已拒绝: 0 个
