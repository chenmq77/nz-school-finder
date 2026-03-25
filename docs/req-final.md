# 最终需求规格 — 可配置列数据表格

**来源**: docs/req.md
**精炼**: 5 轮 Claude + GPT 挑战
**日期**: 2026-03-26
**状态**: APPROVED (9/10)

---

## 1. 需求摘要
将学校列表从简单列表改为可配置列的数据表格（20 列），用户可自定义显示哪些列，在列表页一行对比多所学校。纯 vanilla JS + Python SimpleHTTPServer + SQLite，无框架。

## 2. 用户场景

### 场景 1：默认浏览
- 默认 5 列：名称(固定)、区域、类型、EQI、人数
- 未筛选：全量排序 → 显示前 100 条 → 提示"显示排序后的前 100 所，请筛选查看更多"
- 筛选后：取消 100 条限制，显示全部匹配结果
- 验收：Chrome latest / macOS / localhost — 加载 <2s，100 行×5 列渲染 <200ms

### 场景 2：自定义列
- 齿轮按钮 → 分组 checkbox 面板（基础信息 / 族裔构成 / 课外活动）
- 勾选即时生效；点外部区域关闭面板
- [恢复默认] 按钮
- localStorage(key=schoolColumns) 持久化；不可用→内存降级；损坏/无效 key→过滤回退
- 验收：刷新后恢复列选择；勾选响应 <100ms

### 场景 3：排序
| 列 | 可排序 | 首次方向 | 备注 |
|----|--------|---------|------|
| name | ✅ | A-Z | school_name_cn → school_name 拼音序 |
| suburb | ✅ | A-Z | |
| tags | ❌ | — | 复合字段 |
| eqi | ✅ | 升序(低→高) | tooltip"越低=社区条件越好" |
| roll | ✅ | 降序 | |
| zone | ❌ | — | |
| ethnicity | ✅ | 降序 | 最大族群% |
| eth_* (7 列) | ✅ | 降序 | |
| curriculum | ❌ | — | 复合字段 |
| fee | ✅ | 升序 | 便宜优先 |
| subjects/sports/arts/clubs | ✅ | 降序 | |

行为：
- 点击循环：首次→默认方向 → 再点→反向 → 三点→清除(回名称 A-Z)
- null/— 始终排最后（无论升降序）
- 排序指示器 ▲/▼ 显示在列头
- 隐藏排序列 → 清除排序 → 回退默认
- 排序作用于全量 → 未筛选时 cap 100
- 验收：1000 行排序 <100ms

### 场景 4：移动端(<768px)
- 学校名列 sticky left:0 + box-shadow 分隔
- overflow-x:auto 横向滚动
- 列选择器：bottom sheet + backdrop
- 最小列宽：数字 60px，文本 100px
- 验收：学校名始终可见；滑动无卡顿

### 场景 5：边界与错误
- 零结果："没有匹配的学校"
- API 失败："加载失败" + 重试按钮
- localStorage 不可用/损坏/write 失败：try-catch，降级内存
- 多 tab：不处理，最后写入胜出
- 验收：所有错误场景无 JS 控制台报错

## 3. 数据语义

### Web 数据列 null vs 0
| 数据库值 | 含义 | 显示 | 排序 |
|----------|------|------|------|
| NULL (无 web_data 行) | 未爬取 | 灰色 "—" | 排最后 |
| 0 | 确实为零 | "0" | 正常参与 |
| >0 | 有数据 | 格式化数值 | 正常参与 |

基础数据列：所有 2577 所学校都有，不存在 null。

## 4. 列定义（20 列）

### 基础列(7)
| key | label | fixed | default | sortable | render |
|-----|-------|-------|---------|----------|--------|
| name | 学校名 | ✅ | ✅ | text | 中文名(行1) + 灰色英文名(行2) |
| suburb | 区域 | — | ✅ | text | 原值 |
| tags | 类型 | — | ✅ | — | 年级+性别+公私立标签 |
| eqi | EQI | — | ✅ | number | 原值 |
| roll | 人数 | — | ✅ | number | 千分位 |
| zone | 学区 | — | — | — | ✅/— |
| ethnicity | 族裔 | — | — | number | "亚裔 54%" 最大族群 |

### 族裔子列(7)
eth_european, eth_maori, eth_pacific, eth_asian, eth_melaa, eth_other, eth_intl — 全部可排序(降序)，默认不显示

### 爬取数据列(6) — 无数据显示灰色 "—"
| key | label | sortable |
|-----|-------|----------|
| curriculum | 课程 | — |
| fee | 学费/年 | number |
| subjects | 科目 | number |
| sports | 运动 | number |
| arts | 表演艺术 | number |
| clubs | 俱乐部 | number |

## 5. API 改造
- `/api/schools`: LEFT JOIN school_web_data ON school_number (PK 一对一)
- 新增返回：curriculum_systems, intl_tuition_annual, subjects_count, sports_count, music_count, activities_count

## 6. 实施计划
| Phase | 内容 | 文件 |
|-------|------|------|
| 1 | API LEFT JOIN | server.py |
| 2 | COLUMNS 定义 + table 渲染 | index.html |
| 3 | 列选择器 + localStorage | index.html |
| 4 | 排序(null/cap) | index.html |
| 5 | 移动端 CSS | index.html |

## 7. 用户决策记录
| 问题 | 决策 | 轮次 |
|------|------|------|
| 族裔展示方式 | 默认最大族群聚合列 + 可切换特定族裔列 | R1 |
| tags/curriculum 排序 | 不排序（复合字段） | R2 |
| 未筛选时 100 条限制 | 可接受 | R4 |

## 8. 不做
logo 列、分页、服务端筛选、列拖拽、CSV 导出、多 tab 同步

## 9. 审查记录
| 轮次 | 分数 | 结论 | 文件 |
|------|------|------|------|
| 1 | 6/10 | CHANGES_REQUESTED | review-1.md, review-feedback-1.md |
| 2 | 7/10 | CHANGES_REQUESTED | review-2.md, review-feedback-2.md |
| 3 | 7/10 | CHANGES_REQUESTED | review-3.md, review-feedback-3.md |
| 4 | 7/10 | CHANGES_REQUESTED | review-4.md, review-feedback-4.md |
| 5 | 9/10 | APPROVED | review-5.md |
