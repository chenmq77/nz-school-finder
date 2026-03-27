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

### 2. 爬虫规则优化
目前爬虫在匹配课程时，有些课程被忽略了（匹配不上 subject_pool 就跳过）。需要：
- 未匹配课程存入 unmatched_subjects 表暂存，定期人工审核
- 优化模糊匹配规则（同义词、缩写、学校自定义名称）
- 统一各爬虫的 SUBJECT_MAPPING 到 base.py

### 3. Vocational Pathways 展示
6 个 Vocational Pathways 作为独立维度展示，不与 subject 强关联。

### 4. 新增课程 Overview 页面
- 展示 NZQA Learning Areas 树形分类（大类→小类）
- 每个 subject 显示开设学校数量
- 点击 subject 可查看开设该课程的学校列表
- 展示 6 个 Vocational Pathways 卡片
- 中英双语

### 5. 数据存储优化
- subject_pool 增加 name_cn（中文课程名）
- 新增 unmatched_subjects 表
- 新增 vocational_pathway_meta 表

## 约束
- 个人学习项目，SQLite 数据库
- 前端是纯 HTML/CSS/JS 单页应用，无框架
- 目前只覆盖了 14 所学校，计划扩展到 ~50 所奥克兰学校
- 数据源: NZQA 官网 + 各学校官网 + Education Counts

## 用户决策
- 层级深度: 两级（Learning Area → Subject）
- 未匹配课程: 存到 raw 表定期审核
- Vocational Pathways: 独立展示，不关联 subject
- 页面入口: 后续决定
- 点击 subject: 跳转学校列表自动筛选
