# 实现计划 — NCEA 批量爬取

## 需求摘要
为 10 所学校批量爬取 5 个 NCEA metrics，支持跳过已成功的 metric。

## 变更

### 1. 新建 `crawlers/batch_ncea.py`
- 定义目标学校列表
- 查询 scrape_log 跳过已成功的 (school, metric) 组合
- 逐校串行调用 `ncea_crawler.scrape_school()`
- 学校间额外休息 30-60 秒
- 打印进度和最终汇总

### 2. 前端修复 `index.html:1792`
- 爬完后检查显示效果，如有问题再修

## 实现顺序
1. 编写 batch_ncea.py
2. 先爬一所验证
3. 全量爬取
4. 检查前端显示
