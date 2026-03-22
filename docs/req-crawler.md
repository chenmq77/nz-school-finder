# 爬虫架构讨论需求

## 背景
NZ School Finder 项目目前有 2577 所学校的基础数据（MOE CSV），但只有 5 所学校的官网数据（subjects, sports, music, activities, fees 等）是通过手动/Claude 辅助爬取的。

## 当前实现
- 框架: Scrapling (Python)
- 规范文档: docs/crawling-guide.md (16 章, 2000+ 行)
- 无独立爬虫脚本 — 每次爬取都是手动在 Claude 对话中执行
- 数据存储: SQLite school_web_data 表 + subject_pool + school_subjects
- 每个学校的网站结构不同（WordPress / Wix / 标准 HTML / PDF 等）

## 核心问题
1. 每所学校网站结构都不一样，是否需要为每所学校写单独的爬虫代码？
2. 爬虫代码是否需要持久化保存？还是每次用 AI 辅助生成即可？
3. 如何从手动爬取 5 所 → 覆盖 2577 所学校？
4. Scrapling 是否是最佳选择？是否需要更重量级的框架？
5. 是否需要定时更新机制？

## 约束
- 个人学习项目，非商业用途
- 每所学校网站结构差异大，难以完全通用化
- 需要遵守 robots.txt，限速 2秒/请求
- 部分数据需要人工判断（如科目分类）
