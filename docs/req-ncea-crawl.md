# NCEA 全量数据爬取方案

## 背景
NZ School Finder 项目需要为 10 所奥克兰学校（EQI 344-429 范围）爬取完整的 NCEA 数据。目前只有 Macleans College (#41) 有完整数据，Botany Downs (#6930) 只爬了 ncea3。

## 目标学校（10 所缺数据）
| 学校 | 编号 |
|------|------|
| Botany Downs Secondary College | 6930 |
| Glendowie College | 65 |
| Long Bay College | 27 |
| Lynfield College | 75 |
| Mt Albert Grammar School | 69 |
| Northcote College | 32 |
| Rangitoto College | 28 |
| Selwyn College | 49 |
| Takapuna Grammar School | 36 |
| Western Springs College | 48 |

## 需要爬取的 Metrics
来源: educationcounts.govt.nz

1. **retention** — School leavers staying until 17th birthday
2. **ncea1** — NCEA Level 1 qualifications
3. **ncea2** — NCEA Level 2 qualifications
4. **ncea3** — NCEA Level 3 / UE qualifications
5. **vocational** — Vocational Pathway Awards

每个 metric 产出 3 类数据：
- Table 1: 学校自身表现（按性别、族裔分组，3 年数据）
- Table 2: 对比数据（与 Decile/区域/全国平均比较）
- Table 3: 仅 vocational 有 pathway 分类

## 现有基础
- `crawlers/ncea_crawler.py` 已实现，支持 `--school N --only metric1,metric2`
- 数据库表已建好：`school_performance`、`school_performance_comparison`、`school_vocational_pathways`、`scrape_log`
- 前端 NCEA section 已实现，但判断逻辑要求 `perf.ncea1` 存在才显示

## 需要解决的问题
1. 批量爬取 10 所学校 x 5 个 metrics = 50 个页面的策略（反爬、延迟、容错）
2. Botany Downs 已有 ncea3 数据，需要补爬 retention/ncea1/ncea2/vocational
3. 前端判断逻辑需要修复：不应只检查 ncea1，应检查任意 metric
4. 存储方案是否需要调整（当前 schema 是否够用）
5. 爬取顺序和错误恢复策略
