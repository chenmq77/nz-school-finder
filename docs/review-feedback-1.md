# 审查反馈 — 第 1 轮

本文档回应 **docs/review-1.md**（PDF NCEA 数据提取需求）。

**日期**: 2026-03-26

---

## 问题回应

### 问题 1: [critical] 数据模型语义 — year 字段混合 2023 成绩和 2024 roll
- **GPT 意见**: school_roll 是 July 2024，其余是 2023，用同一个 year 字段会误导
- **处理方式**: ACCEPTED
- **回应**: 将 school_roll 字段改名为 `school_roll_july2024`，year 字段明确为 `data_year=2023`（成绩年份），roll 自带年份标注

### 问题 2: [critical] 匹配/完整性 — 未匹配学校的处理策略
- **GPT 意见**: >95% 匹配率不够明确，未定义未匹配学校的处理方式
- **处理方式**: REFINED
- **回应**: 提取脚本分两步：(1) 自动匹配 (2) 输出 unmatched_schools.json 报告。导入前必须手动处理所有未匹配学校（补充映射或标记 skip）。目标：100% 处理率

### 问题 3: [major] 数据源冲突 — school_performance 已有 NCEA 数据
- **GPT 意见**: 当 Metro PDF 和现有 school_performance 数据冲突时，哪个优先？
- **处理方式**: REFINED
- **回应**: 两张表独立，不修改 school_performance。school_ncea_summary 有 source 字段标注来源。两表数据角度不同（school_performance 是按族裔/性别分组的达标率，school_ncea_summary 是离校生分布百分比），不存在直接冲突

### 问题 4: [major] 范围模糊 — 区域汇总/趋势数据
- **GPT 意见**: 第3-6页数据未明确 in/out of scope
- **处理方式**: ACCEPTED
- **回应**: 明确标注 OUT OF SCOPE for Release 1。用户已确认仅做学校级别数据

### 问题 5: [major] 导入可靠性 — 缺少幂等性和事务
- **GPT 意见**: 没有事务边界、回滚行为、重跑策略
- **处理方式**: ACCEPTED
- **回应**: 增加事务 + DELETE-before-INSERT 幂等策略 + 统计报告

### 问题 6: [minor] Schema/可测试性 — outstanding_merit 和 distinction 应为数值
- **处理方式**: ACCEPTED
- **回应**: 改为 REAL 类型。验证标准：抽样 10 所学校逐字段比对

### 问题 7: [question] Release 1 范围
- **处理方式**: ASKED_USER
- **回应**: 用户确认 Release 1 仅学校级别数据（列表+详情页）

## 摘要
- 已接受: 4 个问题 (#1, #4, #5, #6)
- 已改进: 2 个问题 (#2, #3)
- 用户决策: 1 个问题 (#7 → Release 1 仅学校级别)

---

# 审查反馈 — 第 2 轮

本文档回应 **docs/review-2.md**。

**日期**: 2026-03-26

---

## 问题回应

### 问题 1: [critical] 数据语义 — Below L1/L1/L2/L3 是否互斥 + merit/distinction 单位
- **处理方式**: REFINED
- **回应**: 已验证 PDF 第 30 页方法论说明 + 实际数据。Below L1 + L1 + L2 + L3 + UE 确实构成离校生 100% 分布（互斥分组）。Outstanding Merit 和 Distinction 在 PDF 中显示为百分比（如 "3%", "26%"），但部分学校显示为整数（如 "22%"=奖学金百分比）。统一存为 REAL 百分比值。

### 问题 2: [critical] 匹配策略矛盾
- **处理方式**: ACCEPTED
- **回应**: 统一为：精确 → 标准化 → 手动映射 dict（硬编码）。不使用模糊匹配（避免误匹配）。未匹配学校由人工审核决定处理方式（用户确认）。

### 问题 3: [major] 可测试性 — 10校抽样不够
- **处理方式**: ACCEPTED
- **回应**: 增加自动化校验：(1) 行数断言（导入数 = PDF 提取数 - 跳过数）(2) 百分比范围 0-100 (3) Below_L1 + L1 + L2 + L3 ≈ 100%-UE% 交叉校验 (4) 无重复 school_number (5) 手动抽样 10 所作为最终确认

### 问题 4: [major] Schema source 列与主键不一致
- **处理方式**: ACCEPTED
- **回应**: 移除 source 列从主键外的歧义。保留 source 列作为元数据标注，明确：一个 school_number+data_year 只有一条记录。如果将来有其他数据源，通过 UPDATE 覆盖。

### 问题 5: [minor] 脚本"暂停"行为不适合自动化
- **处理方式**: REFINED
- **回应**: 改为：脚本不暂停。如有未匹配学校，输出 unmatched_schools.json 并以非零退出码退出。开发者补充 MAPPING dict 后重跑。

### 问题 6: [question] 未匹配学校处理
- **处理方式**: ASKED_USER
- **回应**: 用户确认由人工审核决定。脚本输出未匹配列表供人工判断。

## 摘要
- 已接受: 3 个问题 (#2, #3, #4)
- 已改进: 2 个问题 (#1, #5)
- 用户决策: 1 个问题 (#6 → 人工审核)
