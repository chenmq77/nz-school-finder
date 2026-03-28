# 最终需求规格：Subject Pool 重构

**来源**: docs/req-subject-structure.md
**精炼过程**: 经过 14 轮 Claude + GPT 挑战
**日期**: 2026-03-28
**状态**: APPROVED（Claude 判定收敛，GPT 最终评分 7/10，剩余问题均为实现细节）

---

## 1. 需求摘要

将 NZ School Finder 的课程分类体系从手动整理的 11 个 group 重构为 NZ Curriculum 官方 8 大 Learning Areas + Te Ao Māori（共 9 组），同时新建 vocational_pathway 表存储 NZQA 6 大职业路径（v1 纯展示）。

---

## 2. 最终 Schema

### 2.1 subject_pool（学术科目）

```sql
PRAGMA foreign_keys = ON;

CREATE TABLE subject_pool (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  name          TEXT NOT NULL,
  name_cn       TEXT,
  node_type     TEXT NOT NULL CHECK(node_type IN ('group','item')),
  parent_id     INTEGER REFERENCES subject_pool(id),
  sort_order    INTEGER DEFAULT 0,
  reference_url TEXT,
  CHECK (
    (node_type = 'group' AND parent_id IS NULL) OR
    (node_type = 'item' AND parent_id IS NOT NULL)
  ),
  CHECK (parent_id IS NULL OR parent_id != id),
  UNIQUE(name, node_type)
);

CREATE TRIGGER trg_subject_pool_insert_parent
BEFORE INSERT ON subject_pool WHEN NEW.parent_id IS NOT NULL
BEGIN
  SELECT RAISE(ABORT, 'parent must be a group')
  WHERE (SELECT node_type FROM subject_pool WHERE id = NEW.parent_id) != 'group';
END;

CREATE TRIGGER trg_subject_pool_update_parent
BEFORE UPDATE ON subject_pool WHEN NEW.parent_id IS NOT NULL
BEGIN
  SELECT RAISE(ABORT, 'parent must be a group')
  WHERE (SELECT node_type FROM subject_pool WHERE id = NEW.parent_id) != 'group';
END;
```

### 2.2 vocational_pathway（职业路径，v1 纯展示）

```sql
CREATE TABLE vocational_pathway (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  name          TEXT NOT NULL,
  name_cn       TEXT,
  node_type     TEXT NOT NULL CHECK(node_type IN ('group','item')),
  parent_id     INTEGER REFERENCES vocational_pathway(id),
  sort_order    INTEGER DEFAULT 0,
  reference_url TEXT,
  CHECK (
    (node_type = 'group' AND parent_id IS NULL) OR
    (node_type = 'item' AND parent_id IS NOT NULL)
  ),
  CHECK (parent_id IS NULL OR parent_id != id),
  UNIQUE(name, node_type)
);

CREATE TRIGGER trg_vocational_insert_parent
BEFORE INSERT ON vocational_pathway WHEN NEW.parent_id IS NOT NULL
BEGIN
  SELECT RAISE(ABORT, 'parent must be a group')
  WHERE (SELECT node_type FROM vocational_pathway WHERE id = NEW.parent_id) != 'group';
END;

CREATE TRIGGER trg_vocational_update_parent
BEFORE UPDATE ON vocational_pathway WHEN NEW.parent_id IS NOT NULL
BEGIN
  SELECT RAISE(ABORT, 'parent must be a group')
  WHERE (SELECT node_type FROM vocational_pathway WHERE id = NEW.parent_id) != 'group';
END;
```

### 2.3 school_subjects（学校-科目关联）

```sql
CREATE TABLE school_subjects (
  school_number INTEGER NOT NULL,
  subject_id    INTEGER NOT NULL REFERENCES subject_pool(id),
  raw_name      TEXT,
  PRIMARY KEY (school_number, subject_id)
);

CREATE TRIGGER trg_school_subjects_leaf_insert
BEFORE INSERT ON school_subjects
BEGIN
  SELECT RAISE(ABORT, 'must reference an item, not a group')
  WHERE (SELECT node_type FROM subject_pool WHERE id = NEW.subject_id) != 'item';
END;

CREATE TRIGGER trg_school_subjects_leaf_update
BEFORE UPDATE ON school_subjects
BEGIN
  SELECT RAISE(ABORT, 'must reference an item, not a group')
  WHERE (SELECT node_type FROM subject_pool WHERE id = NEW.subject_id) != 'item';
END;
```

### 2.4 subject_alias（课程别名映射，全局）

```sql
CREATE TABLE subject_alias (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  alias      TEXT NOT NULL UNIQUE,
  subject_id INTEGER NOT NULL REFERENCES subject_pool(id)
);
```

爬虫匹配顺序：精确匹配 subject_pool.name → 查 subject_alias → 都不中 → 存入 unmatched_subjects

### 2.5 unmatched_subjects（未匹配课程暂存）

```sql
CREATE TABLE unmatched_subjects (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  school_number   INTEGER NOT NULL,
  raw_name        TEXT NOT NULL,
  normalized_name TEXT NOT NULL,
  source_url      TEXT,
  created_at      TEXT DEFAULT (datetime('now')),
  resolved        INTEGER DEFAULT 0,
  UNIQUE(school_number, normalized_name)
);
```

### 2.6 DB 连接规范

所有脚本通过统一函数连接数据库：
```python
def get_db_connection(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
```

---

## 3. 数据内容

### 3.1 subject_pool — 9 groups + ~55 subjects

| # | Learning Area (一级) | Subjects (二级) |
|---|---|---|
| 1 | English | English, ESOL, English for Academic Purposes, English Language |
| 2 | The Arts | Visual Arts, Art History, Dance, Drama, Music |
| 3 | Health and Physical Education | Health, Physical Education |
| 4 | Learning Languages | French, Japanese, Spanish, Chinese, German, Korean, Latin, Cook Islands Māori, Gagana Sāmoa, Gagana Tokelau, Lea Faka-Tonga, Vagahau Niue, New Zealand Sign Language |
| 5 | Mathematics and Statistics | Mathematics and Statistics |
| 6 | Science | Biology, Chemistry, Physics, Science, Earth and Space Science, Agricultural and Horticultural Science |
| 7 | Social Sciences | Geography, History, Social Studies, Economics, Accounting, Business Studies, Classical Studies, Legal Studies, Psychology, Sociology, Media Studies, Religious Studies, Pacific Studies, Education for Sustainability |
| 8 | Technology | Digital Technologies, Design and Visual Communication, Food Technology, Materials and Processing Technology |
| 9 | Te Ao Māori | Te Reo Māori, Te Reo Rangatira, Te Ao Haka, Māori Performing Arts, Tikanga ā-Iwi |

### 3.2 vocational_pathway — 6 pathways + ~52 sectors

| # | Pathway (一级) | Sectors (二级) |
|---|---|---|
| 1 | Construction & Infrastructure | Access Trades, Civil Infrastructure, Construction Services, Electricity Supply, Electrotechnology, Finishing Trades, Gas Infrastructure, Off Site Construction, On Site Construction, Plumbing & Gasfitting, Water Services |
| 2 | Creative Industries | Art & Design, Broadcast Screen & Interactive Media, Enabling Technologies, Expressive Arts, Sports Recreation & Culture, Taonga Practitioners |
| 3 | Manufacturing & Technology | Engineering, Logistics, Manufacturing |
| 4 | Primary Industries | Apiculture, Arable, Dairy Farming, Equine & Racing, Forestry, Fruit, Grapes & Wine, Nursery & Gardening, Seafood, Sheep Beef Deer & Wool, Vegetables, Veterinary & Animal Care |
| 5 | Services Industries | Aviation & Airport Services, Business & Professional Services, Cleaning Services, Contact Centres, Financial & Advisory Services, Government & Security Services, Hospitality & Food Services, Real Estate, Retail & Distribution, Tourism & Travel |
| 6 | Social & Community Services | Beauty & Nail Services, Emergency Services, Education & Support, Funeral Services, Health Care & Disability, Public Order & Safety, Social Services, Youth Services |

---

## 4. 迁移策略

1. `cp schools.db schools.db.bak`
2. `seed_nzqa.py` 创建新表 + 填充数据（INSERT OR REPLACE，幂等）
3. `migrate_learning_areas.py` 重映射 school_subjects；无法映射的行 → unmatched_subjects（warning 日志，不阻断）
4. 验证断言：9 groups, 6 pathways, 0 orphan subjects/sectors, all school_subjects FK valid

---

## 5. 用户决策记录

| 问题 | 决策 | 轮次 |
|---|---|---|
| Commerce 是否独立 Learning Area | 否，并入 Social Sciences | 6 |
| Visual Arts + Performing Arts | 合并为 The Arts | 6 |
| Vocational 科目放 subject_pool 还是独立 | 独立表 vocational_pathway | 7 |
| vocational_pathway v1 功能 | 纯展示，不关联学校 | 7 |
| DVC 归属 | Technology（NZQA 官方归类） | 7 |
| Seed catalog 是否冻结 | 灵活，seed_nzqa.py 可迭代 | 9 |
| 非零 unmatched 是否阻断 | 不阻断，人工审核 | 10 |

---

## 6. v1 范围排除

- 无 school ↔ vocational_pathway 关联
- 无 L1-only 组合科目（Chemistry and Biology 等）
- 无 Te Reo medium 系列（Hangarau, Pāngarau 等）
- 无 Literacy/Numeracy/Core Skills/Adult Education
- 无 fuzzy string matching
- 表为 seed-managed，不支持 UI 编辑

---

## 7. 审查记录

| 轮次 | 分数 | 结论 | 关键问题 |
|---|---|---|---|
| 1-5 | — | CHANGES_REQUESTED | seed_nzqa.py, subject_alias, unmatched_subjects, sort_order/ncea_level/medium |
| 6 | 7 | CHANGES_REQUESTED | Vocational orphan 矛盾 |
| 7 | 7 | CHANGES_REQUESTED | CHECK 约束、school→vocational 关联 |
| 8 | 7 | CHANGES_REQUESTED | UPDATE trigger、PRAGMA |
| 9 | 7 | CHANGES_REQUESTED | UPDATE trigger 补充 |
| 10 | 8 | CHANGES_REQUESTED | PRAGMA 统一、unmatched schema |
| 11 | 8 | CHANGES_REQUESTED | PRAGMA 落地、unmatched 验收 |
| 12 | 8 | CHANGES_REQUESTED | 重复 raw_name 去重 |
| 13 | 7 | CHANGES_REQUESTED | 自引用防护 |
| 14 | 7 | CHANGES_REQUESTED | 匹配规则、review 流程（实现细节） |
