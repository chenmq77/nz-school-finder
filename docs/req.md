# NZ School Finder — 可配置列数据表格

## 背景
当前学校列表页每行只显示：学校名 + 年级标签 + 性别标签 + 学生人数。信息太少，用户无法在列表页直接对比学校，必须逐个点进详情页。

## 需求
将学校列表从简单列表改为**可配置列的数据表格**，让用户：
1. 在列表页一行看到足够多的信息来比较学校
2. 可以自定义选择显示哪些列（字段）
3. 用户的列选择偏好保存在 localStorage，下次打开自动恢复

## 目标用户
- 国际学生家长（中国为主）：关心 EQI、学费、课程体系
- 本地家长：关心 EQI、学区、区域位置
- 教育中介：需要同时对比多所学校的全面数据

## 可用字段

### 基础数据（schools 表，所有 2577 所学校都有）
- 学校名（中+英）— 固定列，不可隐藏
- 区域 (suburb)
- 类型标签（年级/性别/公私立）
- EQI 评分 (equity_index_eqi)
- 学生总人数 (total_school_roll)
- 是否有学区 (enrolment_scheme)
- 族裔构成（European, Maori, Pacific, Asian, MELAA, Other, International）

### 爬取数据（school_web_data 表，目前 18 所学校有数据）
- 课程体系（NCEA/IB/CIE）
- 国际生学费 (intl_tuition_annual)
- 科目数 (subjects_count)
- 运动数 (sports_count)
- 表演艺术数 (music_count)
- 俱乐部数 (activities_count)

## 交互设计
- 排序栏右侧有 "自定义列" 齿轮按钮
- 点击弹出 checkbox 列表，用户勾选想看的列
- 学校名列固定（不可取消）
- 默认显示：学校名、区域、类型、EQI、人数
- 用户选择保存到 localStorage
- 列头可点击排序（文本列 A-Z，数字列高→低/低→高）
- 移动端：表格可横向滚动，学校名列 sticky

## 技术约束
- 技术栈：纯 HTML + vanilla JS + Python SimpleHTTPServer，无框架
- 数据库：SQLite
- 当前 API：`/api/schools` 返回基础数据；`/api/school/{num}/web` 返回爬取数据
- 需改造 `/api/schools` 加 LEFT JOIN school_web_data 返回额外字段
- 筛选后通常 <50 所学校，无分页需求
