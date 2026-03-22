# GPT 挑战 — 跨校比较结构第 1 轮

**日期**: 2026-03-22 | **评分**: 7/10 | **结论**: CHANGES_REQUESTED

## 关键问题
1. [critical] school_count 不应写回字典表 — 应动态计算或按 cohort 聚合
2. [major] 缺 offering_aliases 别名层 — Football/Soccer 等异名问题
3. [major] terms TEXT 太扁平 — 需结构化支持更丰富的比较
4. [major] 稀有度应按覆盖率(比例)而非绝对数 — 且需带分母
5. [minor] 5KB 估算偏低但不影响结论
6. [minor] API 应直接返回 diff 结果而非让前端自己算
