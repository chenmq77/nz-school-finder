# 课程数据结构优化需求

## 背景

NZ School Finder 项目目前有:
- `subject_pool` 表: 11 个 group + 78 个 subject（手动整理的 NZQA 课程分类）
- 14 所学校已爬取课程数据，存在 `school_subjects` 关联表
- `school_vocational_pathways` 表: 6 个 vocational pathway 分类（construction, creative, manufacturing, primary, service, social）
- NCEA 成绩数据: retention, ncea1, ncea2, ncea3, vocational

## 核心问题

### 1. 课程分类体系（NZQA 官方标准）
NZQA 对 NCEA 课程有官方的分类体系（Learning Areas → Subjects），目前的 subject_pool 是手动整理的，可能不完整或不准确。需要：
- 对齐 NZQA 官方的 Learning Areas 分类
- 确保大类（group）和小类（subject）的层级关系正确
- 考虑是否需要更深的层级（如 subject → standards/credits）

### 2. 爬虫规则优化
目前爬虫在匹配课程时，有些课程被忽略了（匹配不上 subject_pool 就跳过）。需要：
- 分析哪些课程被忽略了，是否应该加入 subject_pool
- 优化模糊匹配规则（同义词、缩写、学校自定义名称）
- 处理跨学科课程（如 "Science and Technology"）的归类

### 3. Vocational Pathways 与课程的关联
Vocational Pathways 是 NZQA 定义的 6 个职业路径，每个 pathway 下有相关的 standards 和 subjects。需要：
- 理清 vocational pathway 与 NCEA subject 之间的关系
- 考虑是否在 subject_pool 中体现这种关联
- 前端如何同时展示学术分类和职业路径分类

### 4. 数据存储结构
现有表结构是否足以支撑上述需求？是否需要新增表或字段？

### 5. 前端展示
- 课程在学校详情页怎么展示？按学术分类还是职业路径？还是两种视图？
- 列表页是否需要按课程筛选？
- 课程数量统计是否需要更细粒度？

## 约束
- 个人学习项目，SQLite 数据库
- 前端是纯 HTML/CSS/JS 单页应用，无框架
- 目前只覆盖了 14 所学校，计划扩展到 ~50 所奥克兰学校
- 数据源: NZQA 官网 + 各学校官网 + Education Counts
