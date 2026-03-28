# 最终需求规格说明 — NZ School Finder 架构重构

**来源**: docs/req-architecture.md
**精炼过程**: 经过 9 轮 Claude + GPT 挑战（第 10 轮 GPT 幻觉，忽略）
**日期**: 2026-03-28
**状态**: APPROVED（连续 7 轮 8/10，所有核心问题已解决）

---

## 1. 需求摘要

将 NZ School Finder 从 Python `http.server` 原型升级为 **FastAPI + SQLAlchemy + Jinja2** 的专业架构，部署到 **Render**。重构过程中**功能行为不变**——所有 API 响应、页面交互、i18n 行为与现有版本完全一致。

## 2. 表生命周期矩阵

| 表 | 数据归属 | SQLAlchemy Model | 初始迁移(PG) | 年度发布 | 生产环境 |
|----|----------|-----------------|-------------|---------|---------|
| schools | CSV 导入 | ✅ | ✅ | ❌ | ✅ |
| school_fees | 爬虫 | ✅ | ✅ | ✅ | ✅ |
| school_web_data | 爬虫 | ✅ | ✅ | ✅ | ✅ |
| school_performance | 爬虫 | ✅ | ✅ | ✅ | ✅ |
| school_performance_comparison | 爬虫 | ✅ | ✅ | ✅ | ✅ |
| school_vocational_pathways | 爬虫 | ✅ | ✅ | ✅ | ✅ |
| school_ncea_subjects | 爬虫 | ✅ | ✅ | ✅ | ✅ |
| scrape_log | 爬虫 | ✅ | ❌ | ❌ | ❌ |

## 3. 用户场景

### 场景 1: API 请求（功能回归验证）

- **参与者**: 前端 JS
- **触发条件**: 用户搜索/筛选/查看学校
- **正常路径**: JS fetch → FastAPI endpoint → SQLAlchemy query → JSON response
- **API 兼容性规约**:
  - 所有 query params 定义为 `Optional[str] = None`，不使用 FastAPI 自动 422
  - Path params 定义为 `school_number: str`，service 层手动处理
  - 无效/未知参数 → 忽略，返回默认结果
  - 空搜索 `q=` → `{"schools":[],"total":0}`
  - 不存在/非法 school_number → 404 `{"error":"not found"}`
  - 重复参数 → 取最后一个值
  - 分页: page≤0→1 | per_page>100→cap 100
  - 不支持的 sort 字段 → 默认 name ASC
  - 列表排序: `(sort_key, school_number)` 双键保证分页稳定
- **关联数据缺失行为**（匹配现有 server.py）:
  - `/api/school/{id}/ncea` — 无数据 → `{"subjects":[],"summary":{}}`
  - `/api/school/{id}/performance` — 无数据 → `{"years":[]}`
  - `/api/school/{id}/web` — 无数据 → `{"web_data":null,"fees":[]}`
- **验收标准**: golden fixture diff = 0（顺序敏感），含 Unicode 测试和关联数据缺失用例
- **跨引擎差异**: PostgreSQL 为权威引擎

### 场景 2: 页面渲染（SPA include 模式）

- **参与者**: 浏览器用户
- **触发条件**: 访问 / 或 /subjects
- **正常路径**: FastAPI → Jinja2 `{% include %}` 组装 → 完整英文单页 HTML → JS hash router → 客户端切换语言
- **DOM 兼容性规则**: 模板拆分时必须保留所有 id, class, data-* 属性不变
- **静态资源**: FastAPI StaticFiles mount（开发和生产均使用）
- **视图级回归验证**:
  - `#/` — dashboard 加载，统计数据显示
  - `#/schools?type=Secondary` — 列表 + 筛选 + 分页
  - `#/school/42` — 详情页加载，NCEA 数据
  - `/subjects` — 学科页面
  - 每个视图: 页面加载 + 搜索/筛选/分页/语言切换交互
- **验收标准**: HTML diff + hash 路由切换 + 交互正常 + 静态资源 200

### 场景 3: 数据导入

- **参与者**: 开发者
- **触发条件**: 新环境初始化或 CSV 更新
- **正常路径**: `python scripts/seed.py` → 读 CSV → SQLAlchemy bulk insert
- **用途**: 开发/测试环境初始化 + 生产 schools 表更新（与爬虫发布独立）
- **验收标准**: `COUNT(imported) = COUNT(csv_rows)`

### 场景 4: 爬虫运行（仅本地）+ 手动发布

- **参与者**: 开发者（本地机器）
- **触发条件**: NCEA 数据年度更新
- **正常路径**: 爬虫在本地 SQLite 运行 → 手动发布 6 张爬虫表
- **本地约束**: SQLite 不支持并发，爬虫和 app 不同时运行（操作规范）
- **发布操作手册**:
  1. 备份生产 PG（Render Dashboard 或 pg_dump）
  2. 设置维护页面
  3. `python scripts/sync_to_prod.py --source schools.db --target $DATABASE_URL`
     - 内置 Alembic revision 检查，schema 不匹配则退出
     - 6 张爬虫表 truncate + bulk insert
  4. 验证: 全部 7 个 API 端点返回正确数据
  5. 移除维护页面
  6. 失败: 从 PG 备份恢复
- **验收标准**: 发布后数据完整，API 行为正常

### 场景 5: Render 部署

- **参与者**: 开发者
- **触发条件**: git push to main
- **正常路径**:
  1. Build: `pip install -r requirements.txt`
  2. Release Command: `alembic upgrade head`（失败则不切换新版本）
  3. Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **DB 不可用**: 请求返回 503（依赖 Render 自动重启）
- **发布验证**（全部返回 200）:
  - `GET /`, `GET /subjects`
  - `GET /api/stats`, `/api/schools?page=1&per_page=5`, `/api/search?q=auckland`
  - `GET /api/school/{id}`, `/api/school/{id}/ncea`, `/performance`, `/web`
  - `GET /static/js/api.js`
- **验收标准**: 全部 10 项检查通过

### 场景 6: SQLite → PostgreSQL 初始迁移（一次性）

- **参与者**: 开发者
- **触发条件**: 首次部署到 Render
- **权威数据源**: SQLite 数据库
- **脚本**: `python scripts/migrate_to_pg.py --source schools.db --target $DATABASE_URL`
  - 内置 Alembic revision 检查
- **迁移范围**: 7 张表（见矩阵，scrape_log 排除）
- **冲突策略**:

| 表 | 主键/唯一键 | 策略 |
|----|------------|------|
| schools | school_number (UK) | ON CONFLICT DO UPDATE |
| school_fees | (school_number, year) | ON CONFLICT DO NOTHING |
| school_web_data | school_number (PK) | ON CONFLICT DO UPDATE |
| school_performance | (school_number, year, level) | ON CONFLICT DO NOTHING |
| school_performance_comparison | (school_number, year) | ON CONFLICT DO NOTHING |
| school_vocational_pathways | (school_number, year) | ON CONFLICT DO NOTHING |
| school_ncea_subjects | (school_number, subject, level, year) | ON CONFLICT DO NOTHING |

- **验证**: 逐表 COUNT + golden fixture 在 PG 通过
- **验收标准**: 可重复执行

### 场景 7: 回归验证（双引擎门禁）

- **方法**: 录制旧 server.py 响应 → FastAPI 对比 → PG 对比
- **覆盖**: 正常路径 + 边界 + 排序 + Unicode + 关联数据缺失
- **PG 验证作为发布门禁**
- **数据源**: 现有 schools.db

### 场景 8: i18n 保持验证

- **约定**: Jinja2 输出英文 HTML = 原 index.html，JS 客户端切换语言
- **允许首屏短暂英文**（保持现有行为）
- **验收标准**:
  - [ ] translations.js 正确加载
  - [ ] / 和 /subjects 均支持语言切换
  - [ ] en/cn/both 三种模式均可切换
  - [ ] 刷新后语言偏好保持（localStorage）
  - [ ] 模板中无新增硬编码中英文

## 4. 非功能性需求

- **性能**: API < 500ms（~3000 条记录）
- **安全**: SQLAlchemy 参数化查询、环境变量管理（DATABASE_URL）、CORS
- **数据**: SQLite 开发 / PostgreSQL 生产

## 5. 架构

### 组件概览
```
Browser → FastAPI (uvicorn)
            ├── Jinja2 Templates ({% include %} SPA shell)
            ├── API Routes (/api/*) → JSON
            ├── Services (业务逻辑)
            └── SQLAlchemy → SQLite / PostgreSQL
```

### 跨数据库兼容性规则
| 问题 | 方案 |
|------|------|
| 文本匹配 | `func.lower(col).contains(func.lower(term))` |
| NULL 排序 | `nulls_last()` |
| 分页稳定 | `(sort_key, school_number)` 双键 |

### 技术选型
| 选择 | 理由 |
|------|------|
| FastAPI | 自动 OpenAPI 文档、Pydantic 校验、ASGI |
| SQLAlchemy 2.0 | 类型安全 ORM、双引擎、Alembic |
| Jinja2 | FastAPI 原生支持、拆分大 HTML |
| uvicorn | ASGI 标准、Render 支持 |

### 脚本职责
| 脚本 | 用途 | 环境 |
|------|------|------|
| migrate_to_pg.py | 一次性迁移 7 表 + revision 检查 | 生产首次 |
| sync_to_prod.py | 年度发布 6 表 + revision 检查 | 生产维护 |
| seed.py | CSV 初始化 | 开发/测试 + 生产 schools 更新 |
| record_fixtures.py | 录制旧 API 响应 | 阶段 2 前 |

### 文件结构
```
app/
├── main.py, config.py, database.py
├── models/ (school.py, ncea.py)
├── schemas/ (school.py)
├── routes/ (schools.py, ncea.py, stats.py, pages.py)
├── services/ (school_service.py, ncea_service.py)
├── templates/ (base.html, partials/, index.html, subjects.html)
└── static/ (css/, js/, images/)
scripts/ (seed.py, migrate_to_pg.py, sync_to_prod.py, record_fixtures.py)
tests/ (fixtures/, test_api_parity.py)
crawlers/ (SQLAlchemy)
alembic/
requirements.txt
```

**不迁移**: school_finder.py CLI 保持原样

## 6. 实施计划

### 阶段 1: 数据层
- SQLAlchemy models（8 表）+ database.py + config.py + Alembic init
- 风险: 低 | 验证: models 映射现有 schools.db

### 阶段 2: API 层
- FastAPI routes + services + golden fixture 录制 + 回归测试
- 风险: 中（filter_schools 复杂查询）| 验证: 7 端点 fixture 通过

### 阶段 3: 视图层
- Jinja2 模板 + CSS 提取 + StaticFiles + DOM 验证 + i18n
- 风险: 中 | 验证: 视图回归 + 语言切换

### 阶段 4: 爬虫迁移（可与 2-3 并行）
- crawlers/ 改用 SQLAlchemy + sync_to_prod.py
- 风险: 低 | 验证: 爬虫正常写入

### 阶段 5: 部署
- Render 配置 + migrate_to_pg.py + seed.py + 环境变量
- 风险: 中 | 验证: 部署 + 10 项检查 + PG fixture 通过

## 7. 用户决策记录

| 问题 | 决策 | 轮次 |
|------|------|------|
| 前端路由 | SPA include | 0 |
| CLI 工具 | 不迁移 | 0 |
| 数据迁移 | Python 脚本 | 0 |
| 爬虫环境 | 仅本地 | 1 |
| 数据新鲜度 | 手动年更 | 2 |
| 发布范围 | 6 张爬虫表 | 3 |
| seed.py | 保留推迟 | 3 |
| 可用性 | 允许维护窗口 | 4 |
| 权威数据源 | SQLite | 5 |
| 原子性 | 备份恢复 | 6 |
| 静态资源 | FastAPI 服务 | 7 |
| i18n 首屏 | 允许先英文 | 8 |
| 表范围 | scrape_log 不上生产 | 9 |

## 8. 已知风险与权衡

| 风险 | 严重程度 | 缓解措施 |
|------|----------|----------|
| SQLite/PG 行为差异 | 中 | 双引擎 golden fixture 门禁 |
| HTML 拆分破坏 JS | 中 | DOM 兼容规则 + HTML diff |
| filter_schools 转 ORM | 中 | golden fixture 逐字段验证 |
| 年度发布数据不一致 | 低 | 维护窗口 |
| 本地 SQLite 并发 | 低 | 操作规范 |

## 9. 范围之外
- 前端框架升级 | 用户认证 | SSR/SEO | CDN | CLI 迁移 | 爬虫自动调度

## 10. 审查记录

| 轮次 | 分数 | 结论 | 文件 |
|------|------|------|------|
| 1 | 6/10 | CHANGES_REQUESTED | review-1.md, review-feedback-1.md |
| 2 | 7/10 | CHANGES_REQUESTED | review-2.md, review-feedback-2.md |
| 3 | 8/10 | CHANGES_REQUESTED | review-3.md, review-feedback-3.md |
| 4 | 8/10 | CHANGES_REQUESTED | review-4.md, review-feedback-4.md |
| 5 | 8/10 | CHANGES_REQUESTED | review-5.md, review-feedback-5.md |
| 6 | 8/10 | CHANGES_REQUESTED | review-6.md, review-feedback-6.md |
| 7 | 8/10 | CHANGES_REQUESTED | review-7.md, review-feedback-7.md |
| 8 | 8/10 | CHANGES_REQUESTED | review-8.md, review-feedback-8.md |
| 9 | 8/10 | CHANGES_REQUESTED | review-9.md, review-feedback-9.md |
| 10 | 6/10 | GPT 幻觉（忽略） | review-10.md |
