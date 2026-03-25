# 审查反馈 — 第 1 轮

回应 **docs/review-1.md**。日期: 2026-03-25

## 问题回应

### 问题 1: 族裔构成与双语校名 [critical]
- **处理方式**: ACCEPTED + ASKED_USER
- **回应**: 族裔加入列配置，默认展示"最大族群"聚合列（如 "亚裔 54%"），用户也可在列选择器里切换为特定族裔。双语校名：固定列第一行中文名，第二行灰色小字英文名。

### 问题 2: 排序 null 值 [major]
- **处理方式**: ACCEPTED
- **回应**: null/— 值排序时始终排最后（无论升降序）。复合字段（tags/curriculum）不支持排序。

### 问题 3: 边界场景 [major]
- **处理方式**: ACCEPTED
- **回应**: 新增场景 5（零结果+API失败+localStorage损坏）。

### 问题 4: 全量返回 vs 服务端筛选 [major]
- **处理方式**: REJECTED
- **回应**: 当前已是全量返回+前端筛选的架构，本需求不改变这个模式。JSON payload ~500KB 可接受。

### 问题 5: LEFT JOIN 行唯一性 [major]
- **处理方式**: ACCEPTED
- **回应**: school_web_data 表主键是 school_number，保证一对一。在提案中明确。

### 问题 6: logo_url scope creep [minor]
- **处理方式**: ACCEPTED
- **回应**: 移除 logo_url，表格列不含 logo。Logo 只在详情页展示。

### 问题 7: 列选择器 UX [minor]
- **处理方式**: ACCEPTED
- **回应**: 加"恢复默认"按钮。移动端列选择器用底部抽屉(bottom sheet)。

### 问题 8: 族裔展示方式 [question]
- **处理方式**: ASKED_USER
- **用户决策**: 默认显示最大族群聚合列，用户可在列选择器里切换为特定族裔列。

## 摘要
- 已接受: 5 个问题
- 已改进: 1 个问题
- 已拒绝: 1 个问题
- 用户决策: 1 个
