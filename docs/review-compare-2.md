# GPT 挑战 — 跨校比较结构第 2 轮（最终轮）

**日期**: 2026-03-22 | **评分**: 8/10 | **结论**: CHANGES_REQUESTED (接近通过)

## 关键反馈
1. coverage_pct 分母需按 category 计算 — 避免"只爬了 subject 没爬 sport"导致稀有度误判
2. offering_aliases 唯一键改为 UNIQUE(category, normalized_raw_name) — 'Dance' 可能既是 sport 也是 cultural
3. 别名匹配失败不应直接创建 catalog — 应进入 pending review 状态
4. terms_mask 中 0 的语义要明确 — "未知" vs "无学期信息"
5. compare 结果补 "shared but different terms" 子分组
