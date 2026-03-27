# Metro NCEA 板块优化 — UI 修复 + 新旧数据整合

## 背景
Metro NCEA 数据已成功提取并集成到 Section H（NCEA 升学成绩），但存在 3 个问题：

## 问题 1：移除 emoji
Metro NCEA 板块中的奖学金/杰出成绩/优等生行使用了 emoji 图标（奖杯/星星/靶心），需要移除，改用纯文本或 CSS 图标。

## 问题 2：中文支持不完整
当系统语言为中文时，Metro 板块部分文本仍显示英文（如 "University Entrance", "School Leavers", "Scholarships" 等），需要完全跟随 _lang 切换。

## 问题 3：新旧数据视觉不融合（核心问题）
Section H 中同时展示两组 NCEA 数据，但它们测量维度完全不同，容易让用户困惑：

### 数据源 A：school_performance 表（原有，11 所学校）
- **含义**：NCEA L1/L2/L3 达标率 — "该年级学生中多少%通过了该级别"
- **年份**：2022-2024 多年
- **分组**：按性别/族裔
- **示例**：Rangitoto L3 达标率 = 78.4%（Y13 中通过 L3 的比例）

### 数据源 B：school_ncea_summary 表（Metro 新增，91 所学校）
- **含义**：离校生分布 — "离校生的最高成就级别分布"
- **年份**：仅 2023
- **特有字段**：UE 率、奖学金、Outstanding Merit、Distinction、学科 Top10
- **示例**：Rangitoto L3 = 8%（离校生中最高成就为 L3 的占比，不含 UE）

### 关键区别
两组数据的 "L3" 含义完全不同：
- Performance L3 = 78.4%（包含通过 L3 的所有学生，含 UE 达标者）
- Metro L3 = 8%（仅最高成就是 L3 但未达 UE 的离校生）

### 重叠情况
- 仅 11 所学校同时有两组数据
- 80 所学校只有 Metro 数据
- 两组数据互补而非冲突

## 目标
让两组数据在 Section H 中清晰呈现，用户不会混淆它们的含义。

## 技术约束
- 只改 index.html 中的 renderMetroNcea() 和相关渲染逻辑
- 不改数据库结构或 API
