# 实现计划：国际生学费多年份存储与智能展示

## 需求摘要
- 新建 `school_fees` 表支持同一学校存储多年份费用数据，爬虫写入时检测冲突（金额不同则警告人工），API 智能返回当年或最近未来年份的费用，前端显示年份标注。

## 技术栈范围
- [x] 数据库 (SQLite)
- [x] 爬虫 (Python crawlers)
- [x] 后端 API (Python stdlib HTTP server)
- [x] 前端 (vanilla JS/HTML)

## 数据库变更

### 新建表: `school_fees`
```sql
CREATE TABLE IF NOT EXISTS school_fees (
    school_number  INTEGER NOT NULL,
    fee_year       INTEGER NOT NULL,
    tuition_annual REAL,
    homestay_weekly REAL,
    fees_url       TEXT,
    crawled_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (school_number, fee_year),
    FOREIGN KEY (school_number) REFERENCES schools(school_number)
);
```

### 数据迁移
- 将现有 `school_web_data` 中 6 条费用记录迁移到 `school_fees`
- `school_web_data` 中的费用字段保留不删（向后兼容）

## 爬虫变更

### `crawlers/templates/base.py`
- `commit_to_db()` 新增写入 `school_fees` 表的逻辑
- 写入前检测：同一 (school_number, fee_year) 已存在时
  - 金额一致 → 更新 `crawled_at`
  - 金额不一致 → 不覆盖，添加 warning "Fee conflict detected"，打印人工审核提醒

## 后端 API 变更

### `server.py`
- `fetch_school_web()` 新增从 `school_fees` 查询逻辑：
  1. 查当年（如 2026）的记录
  2. 无则查 > 当年的最近年份（如 2027）
  3. 无则查 < 当年的最近年份（如 2025）
- 将查到的费用覆盖到返回的 data dict 中

## 前端变更

### `index.html`
- `renderFees()` 无需改动（已支持 `intl_fees_year` 显示）
- API 返回的数据已包含正确年份，前端自动展示

## 实现顺序
1. `init_db.py` — 添加 `school_fees` 表创建 + 数据迁移脚本
2. `crawlers/templates/base.py` — `commit_to_db()` 写入新表 + 冲突检测
3. `server.py` — `fetch_school_web()` 智能年份查询
4. 迁移现有数据 — 运行迁移脚本

## 风险领域
- 迁移现有数据时，school 54 (Auckland Grammar) 没有 `intl_fees_year`，需要处理 NULL 情况
- `init_db.py` 目前会 DROP + 重建 schools 表，需确保 `school_fees` 建表逻辑是增量的，不破坏已有数据
