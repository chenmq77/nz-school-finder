# 提案：从 Metro Schools 2025 PDF 提取 NCEA 数据

## 1. 需求摘要
- **核心目标**：从 Metro Schools 2025 PDF 提取 Auckland ~80 所高中的 2023 NCEA 数据，存入 SQLite，整合到学校对比系统
- **目标用户**：学生家长、教育中介
- **关键约束**：现有 school_performance 表有 ncea1/2/3 数据（11所学校），但完全没有 UE 数据；PDF 补充 ~80 所学校的 UE + 离校生分布 + 奖学金 + 学科排名

## 2. 用户场景

### 场景 1：数据提取与导入
- **参与者**：开发者
- **触发条件**：运行 Python 提取脚本
- **正常路径**：
  1. PyMuPDF 读取 PDF 第 31-33 页提取核心数据表（~80 所学校）
  2. PyMuPDF 读取 PDF 第 7-9 页提取学科 Top10 排名（11 个学科）
  3. 正则/文本解析 → 结构化 dict 列表
  4. 通过 school_name 匹配 schools 表的 school_number
  5. 插入 school_ncea_summary 表（核心数据）
  6. 插入 school_subject_ranking 表（学科排名）
- **错误路径**：
  - 学校名不匹配（如 PDF "Auckland Seventh-Day Adventist H S" vs DB "Auckland Seventh-Day Adventist High School"）→ 模糊匹配 + 手动映射
  - PDF 文本提取列错位 → 人工验证 + 修正
  - 第 32 页末尾数据截断 → 标记缺失数据
- **验收标准**：80+ 所学校数据成功导入，匹配率 >95%

### 场景 2：用户在列表页对比 UE 率
- **参与者**：家长/中介
- **触发条件**：浏览学校列表
- **正常路径**：用户在可配置列中勾选 "大学入学率(UE)"，列表显示 UE% 并可排序
- **错误路径**：某学校无 UE 数据 → 显示 "-"
- **验收标准**：UE 列正确显示，支持升降序排序

### 场景 3：学校详情页展示 NCEA 全景
- **参与者**：家长
- **触发条件**：点击学校详情
- **正常路径**：详情页显示 UE 率、各级别离校生比例（Below L1/L1/L2/L3）、奖学金/优秀学生统计、学科排名（如该校进入 Top10）
- **验收标准**：数据与 PDF 一致

## 3. 非功能性需求
- **数据准确性**：提取后人工抽样验证至少 10 所学校
- **数据覆盖**：仅 Auckland ~80 所高中，其余 2500 所学校不受影响
- **数据一致性**：school_number 为关联键，确保 PDF 学校全部映射到现有 schools 表

## 4. 架构提案

### 数据提取方案
- **工具**：PyMuPDF（已安装）提取文本 → Python 正则/字符串解析
- **核心表（第 31-33 页）**：结构化表格，文本提取已验证质量良好
- **学科 Top10（第 7-9 页）**：格式规整，每学科 10 行 RANK/SCHOOL/LEVEL3%

### 存储方案 — 新建两张表

```sql
-- 表 1：学校 NCEA 汇总数据
CREATE TABLE school_ncea_summary (
    school_number     INTEGER NOT NULL,
    year              INTEGER NOT NULL,
    source            TEXT DEFAULT 'metro_2025',
    school_roll       INTEGER,          -- 在校总人数 (July 2024)
    school_leavers    INTEGER,          -- 离校生人数
    ue_percentage     REAL,             -- 大学入学率 %
    below_l1_pct      REAL,             -- 未达 L1 %
    l1_pct            REAL,             -- L1 %
    l2_pct            REAL,             -- L2 %
    l3_pct            REAL,             -- L3 %
    scholarships      INTEGER,          -- 奖学金数
    outstanding_merit TEXT,             -- Outstanding Merit %
    distinction       TEXT,             -- Distinction %
    region            TEXT,             -- Local Board Area (如 Albert-Eden)
    PRIMARY KEY (school_number, year)
);

-- 表 2：学校学科排名
CREATE TABLE school_subject_ranking (
    school_number     INTEGER NOT NULL,
    year              INTEGER NOT NULL,
    subject           TEXT NOT NULL,     -- 学科名 (如 'Sciences', 'Mathematics')
    rank              INTEGER,           -- 排名 (1-10)
    level3_pct        REAL,             -- Level 3 达标率 %
    source            TEXT DEFAULT 'metro_2025',
    PRIMARY KEY (school_number, year, subject)
);
```

### 学校名匹配策略
1. 精确匹配 school_name
2. 标准化匹配（去标点、统一缩写如 "H S" → "High School", "St" → "Saint"）
3. 未匹配的 → 输出未匹配列表，手动建立映射 dict

### API 改造
- `/api/schools` 的 SQL 加入 LEFT JOIN school_ncea_summary，返回 ue_percentage 字段
- `/api/school/{num}/ncea` 新端点返回完整 NCEA 数据 + 学科排名

## 5. 实施计划

| 阶段 | 任务 | 依赖 | 复杂度 |
|------|------|------|--------|
| 1 | 编写 PDF 文本提取脚本（核心表 + 学科 Top10） | PyMuPDF | 中 |
| 2 | 学校名匹配映射 | 阶段1 + schools 表 | 中 |
| 3 | 建表 + 数据导入 | 阶段2 | 低 |
| 4 | 数据验证（抽样 10 所学校） | 阶段3 | 低 |
| 5 | API 改造（加入 UE 字段） | 阶段3 | 低 |
| 6 | 前端展示（列表列 + 详情页） | 阶段5 | 中 |

### 风险评估
| 风险 | 严重程度 | 缓解措施 |
|------|----------|----------|
| PDF 文本提取列错位 | 中 | 人工验证 + 正则断言 |
| 学校名匹配失败 | 中 | 模糊匹配 + 手动映射表 |
| 第 32 页数据截断 | 低 | 标记缺失，手动补充 |
| 数据仅覆盖 Auckland | 低 | UI 明确标注数据来源和范围 |

## 6. 待确认问题
- 已确认：提取核心表 + 学科 Top10
- 已确认：仅用新表 B（不动现有 school_performance 表）
