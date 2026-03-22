# GPT 挑战 — 数据组织方案第 1 轮

**日期**: 2026-03-22 | **评分**: 7/10 | **结论**: CHANGES_REQUESTED

## 关键问题
1. [critical] school_offerings 需要标准字典 — 不同学校同一科目名称不同，需 offering_catalog 统一
2. [critical] school_fees 归一化不够 — 需支持区间价格、可选/必选、年级范围、年化金额
3. [major] school_assets 学区数据 — 只存链接不够，未来需可检索的街道索引
4. [major] F 区太杂 — 应拆为"课程与活动" + "入学与费用"两个模块
5. [major] 标签云不适合高密度数据 — 应用摘要指标卡 + 分组折叠列表
6. [minor] 缺少来源审计字段 — source_page, captured_at, parser_version
7. [minor] 缺少衍生指标层 — subjects_count, sports_count 等用于卡片和筛选
