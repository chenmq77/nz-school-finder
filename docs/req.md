# NZ School Finder — 从 Metro Schools 2025 PDF 提取 NCEA 数据

## 背景
当前系统有 2577 所学校的基础数据（schools 表）和 18 所学校的爬取数据（school_web_data 表），但缺少 NCEA 学术表现数据。Metro Magazine 的 "Schools 2025" 报告（met447_schoolsDataONLY_212x277.pdf）包含 Auckland 约 80+ 所高中的 2023 年 NCEA 详细成绩数据，可以显著增强系统的学校对比能力。

## 需求
从 PDF 中提取结构化的学校 NCEA 数据，存入数据库，整合到现有的学校对比系统中。

## PDF 数据源概览
- 来源: Metro Magazine Schools 2025 报告
- 数据年份: 2023 NCEA 成绩
- 覆盖范围: Auckland 地区约 80+ 所高中
- 按 19 个区域（Local Board Areas）分组

## PDF 中可提取的数据

### 核心数据表（第 31-33 页）
每所学校包含：
- School Name（学校名称）
- School Roll (July 2024)（在校总人数）
- School Leavers (2023)（2023 离校生人数）
- University Entrance (2023)（大学入学率 %）
- Leavers not achieving Level 1 (%)
- Leavers achieving Level 1 (%)
- Leavers achieving Level 2 (%)
- Leavers achieving Level 3 (%)
- Scholarships Presented（奖学金数量）
- Students with Outstanding Merit
- Students with Distinction

### 按学科 Top 10 排名（第 7-9 页）
11 个学科的 Level 3 达标率排名：
Engineering, Health, English, Field Māori, Languages, Sciences, Mathematics, Social Sciences, Te Reo Māori, Technology, The Arts

### 区域汇总数据（第 3-6 页）
- 各区域 UE 率
- 学校类型对比（Private/State Integrated/State）
- Equity Index 分组与 UE 关联
- 2020-2023 年度趋势

## 目标用户
- 国际学生家长：关心学校学术表现、大学入学率
- 本地家长：关心 NCEA 各级别达标率、奖学金情况
- 教育中介：需要全面的学校数据对比

## 技术约束
- 技术栈: 纯 HTML + vanilla JS + Python SimpleHTTPServer
- 数据库: SQLite
- 现有 API: `/api/schools` 和 `/api/school/{num}/web`
- 需要与现有 schools 表通过学校名称匹配关联
