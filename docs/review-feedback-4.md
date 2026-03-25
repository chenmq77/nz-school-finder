# 审查反馈 — 第 4 轮

回应 **docs/review-4.md**。日期: 2026-03-26

### 问题 1: "—" vs "0" 数据语义 [critical]
- ACCEPTED: web 数据列：null(未爬取)显示灰色"—"，0 显示"0"。排序时 null 排最后，0 参与正常排序。

### 问题 2: 列数不一致 [major]
- ACCEPTED: 修正为 20 列（基础7 + 族裔7 + 爬取6）。爬取列去掉多算的一个。

### 问题 3: 测试环境 [minor]
- ACCEPTED: 性能基准定义为 Chrome latest / macOS / localhost。

### 问题 4: 100条限制 [question]
- 用户确认：100 条可接受，未筛选时无需浏览全部。
