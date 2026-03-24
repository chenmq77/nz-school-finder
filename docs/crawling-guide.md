# 爬虫指南 — NZ School Finder

从 8 所学校的爬取经验中总结的规则和教训。
（AGS, Rangitoto, Avondale, Westlake Boys, EGGS, Westlake Girls, AGGS, Kelston Girls）

---

## 1. 数据分类（4 大类）

| 分类 | 存储方式 | 说明 |
|------|---------|------|
| **Subjects** | subject_pool + school_subjects（标准化表） | 对照 NZQA 官方科目 pool 匹配 |
| **Sports** | JSON string in school_web_data | 扁平列表，纯名称 |
| **Arts** | JSON string in school_web_data (music 字段) | 表演艺术团体（音乐/戏剧/舞蹈+Kapa Haka） |
| **Activities/Clubs** | JSON string in school_web_data | 社团、cultural clubs、其他活动 |
| **Fees** | school_fees 表（多年份） | `(school_number, year)` 复合主键，支持同校多年费用 |

---

## 2. Subjects 爬取规则

### 匹配流程
1. 爬到 raw_name → 精确匹配 subject_pool（忽略大小写）
2. 匹配到 subject → 建立 school_subjects 关系
3. 匹配到 group → 建立关系（展开时显示子科目）
4. **没匹配到 → 打印警告，不自动加入 pool，等用户批准**

### 层级判断
- **"作为独立课程出现在导航/课程列表中"才算开设**
- 在描述文本中被提到 ≠ 开设（如 AGS 提到 Art History 但没有单独开课）
- 系页面标题 ≠ 科目（如 "Information Services" 是学校支持服务不是学科）

### 多页面合并
- **curriculum 页面不一定完整**：部分学校（如 KGC）的 curriculum 页面只列了宽泛分类
- **international students 页面常有更详细的科目列表**（如 KGC 的 intl 页面列出了 Biology, Chemistry, Physics, Geography, History 等）
- 建议：同时爬 curriculum 页面 + international 页面，合并去重

### 粒度规则
- 优先存细颗粒度（Accounting 而不是 Commerce）
- group 展开仅用于：学校只提供了系名，且确认该系包含标准子科目
- **有子科目时抑制 group**：如果 AGS 已有 Geography/History，不再关联 Social Sciences group
- Visual Arts 是例外：始终展开（因为不同学校的 arts 科目不同）

### 不入 pool 的内容
- 学校支持服务：Learning Support, Information Services, Health Centre, Library, Counselling
- 非学科项目：Careers（职业指导）
- 过于粗粒度的系名：不应作为 subject 存入（用 group）

### 新增 pool 科目
- **必须经过用户批准**
- 来源应为 NZQA 官方科目 或 学校确认开设的职业课程
- 记录 added_from_school（哪所学校首次发现）

---

## 3. Sports 爬取规则

- 存纯名称 JSON list，不存 terms
- 按运动项目计数（Basketball = 1，不管几支队伍）
- 去掉非运动项目（如 "Our Facilities", "Sports Team", "Our People"）
- **多页面合并**：sports 页面可能不完整，international students 页面常有补充（如 WGHS 的 Football、Volleyball 只在 intl 页面提到）
- 来源页面通常：/sport/, /sports/, /extracurricular-activities/

---

## 4. Arts 爬取规则

**Arts = 以表演/演出/乐团/舞台产出为核心目的的团体**

属于 Arts 的：
- 音乐团体：Big Band, Symphony Orchestra, Chamber Choir, Rock Bands...
- 戏剧：Theatresports, School Production, Drama
- 舞蹈：Dance（作为表演团体时）
- **Kapa Haka**（毛利战舞 — 表演性质，放 Arts）

**不属于 Arts 的（放 Activities）：**
- Cultural social clubs：Pasifika Club, Sri Lankan Club, Korean Club, Asian Club, Indian Club
- 这些是社交/兴趣性质，不是表演团体

**命名规则：**
- 合唱团名如果不含 "Choir" 且名字不明显（如 Cantare、Cigno Voce、Nota Bella），**后缀加 "Choir"**（如 "Cantare Choir"）
- 让用户一眼就知道是什么类型的团体

来源页面通常：/performing-arts/, /arts/, /extracurricular-activities/, /music/

---

## 5. Activities/Clubs 爬取规则

包含所有非 Sports、非 Arts 的课外活动：
- Clubs（Coding Club, Chess Club, Debating...）
- Cultural clubs（Pasifika, Korean Culture Club...）
- Service opportunities（如果学校有单独页面）
- 按 club 名计数

来源页面通常：/clubs/, /clubs-activities/, /service-opportunities/
- **PDF 提取**：部分学校（如 WGHS）clubs 全在 PDF 文档里，页面只有链接。用 PyPDF2 提取 PDF 文本，每页通常是一个 club
- 提取后需过滤掉已在 arts/sports 中的项目

---

## 6. 国际生费用

- 只存 2 个数字：**年学费 + 周住宿费**
- 如果官网没有直接显示金额 → Google 搜索 "{学校名} international fees"
- 找学校官网的 PDF 链接（通常在 /international/ 页面下）
- **必须存 intl_fees_url 指向费用来源**

### 多年份存储（school_fees 表）
- 费用存入独立的 `school_fees` 表，`(school_number, year)` 复合主键
- 同一学校可存多个年份的费用（如 WGHS 同时有 2026 和 2027）
- **冲突检测**：重复爬同校同年时，金额一致 → 更新时间戳；金额不一致 → 不覆盖，警告人工审核
- API 智能查询顺序：当年 → 最近未来年 → 最近过去年

### 费用年份判断
- **页面明确标注年份**（如 "2026 Fees"）→ 用标注的年份
- **页面没有标注年份** → 用爬虫运行时的年份（即当年）
- **不要用正则从页面抓年份**：页面中的 "2024" 可能是 WordPress 主题/版权声明的年份，不是费用年份（AGGS 教训）
- **PDF 有年份最可靠**：如 WGHS 的 PDF 标题 "International Fees 2026/2027"，KGC 的 "Fees 2026"

### 住宿费换算
- 有的学校给年费（如 AGGS $19,320/year）→ 除以 46 周换算为周费（≈ $420/week）
- 有的学校直接给周费（如 KGC $420/week）→ 直接存
- 前端用 `× 46 weeks` 计算年化住宿费展示

---

## 7. Curriculum Systems

- 识别 NCEA / IB / A-Level
- 需要带 evidence_url 指向证据页面
- 只有 status=offered 才在前端展示
- **NCEA 不加链接**（所有学校都有），IB/A-Level 加链接
- A-Level（带连字符），不写 Cambridge

---

## 8. 学区信息

- 只存链接（zone_map_url, zone_streets_url, zone_page_url）
- 不嵌入图片，前端只显示可点击的链接

---

## 9. 技术注意事项

### Scrapling 使用
- 默认用 `Fetcher`（普通 HTTP），不用 StealthyFetcher
- 遵守 robots.txt，限速 2 秒/请求
- JS 渲染页面回退 DynamicFetcher

### WordPress 网站（如 AGS）
- 页面返回 200 但 `.css()` 选择器可能拿不到内容
- 用 `page.body.decode()` + 正则提取更可靠

### 数据刷新
- 每次爬虫按 school_number 全量替换 school_subjects（事务内 delete + insert）
- school_web_data 用 INSERT OR REPLACE
- school_fees 用 SELECT 比对后 INSERT/UPDATE/WARN

### Sporty CMS 网站（如 KGC）
- 部分学校使用 sporty.co.nz 平台建站
- 文档/PDF 链接格式：`https://www.sporty.co.nz/asset/downloadasset?id={UUID}`
- Logo 在 `<meta>` 标签中：`https://prodcdn.sporty.co.nz/cms/{id}/logo.jpg`
- 费用 PDF 可能是 Sporty asset link，需要从页面 `data-link-data` 属性提取 UUID

### Logo 选择规则
- **优先用正方形/接近正方形的 crest/shield 图**（宽高比 ≤ 1.5:1）
- **不要用横幅式 banner logo**（如 WGHS 的 2800×574 SVG，AGGS 的 489×119 PNG）— 在 160×160 容器中会被压到很小
- 查找顺序：`apple-touch-icon` > `android-chrome` icon > 页面 `<meta og:image>` > 导航 header `<img>`
- 好的来源：`/wp-content/uploads/*/cropped-android-chrome-512x512*.png`、`WGHS-Shield-crest-only-RGB.png`
- 前端容器：`position:absolute; right:8px; top:8px; max-width:160px; max-height:160px; object-fit:contain; opacity:0.6`

### URL 安全
- 所有 URL 经过 `safeUrl()` 白名单校验（只允许 http:// 和 https://）
- 防止 javascript: scheme 注入

---

## 10. 常见陷阱（经验教训）

| 陷阱 | 案例 | 正确做法 |
|------|------|---------|
| 文本提到 ≠ 开设 | AGS 描述中提到 Art History | 只看导航/课程列表中的独立条目 |
| 系名当科目 | Commerce 存为科目 | 存为 group，展开为 BEA |
| group 过度展开 | AGS 展开 Social Sciences 出现 Sociology | 已有细科目时不展开 group |
| 导航噪音 | 全站导航出现在每个页面 | 过滤掉导航链接 |
| Cultural ≠ Arts | Pasifika Club 放进了 Arts | 社交 club → Activities |
| 支持服务当学科 | Information Services | 排除非学科项目 |
| 自动加 pool | 爬到新名称直接写入 | 打印警告，等用户批准 |
| 费用找不到 | Rangitoto 官网没显示金额 | Google 搜索找 PDF |
| Wix 网站爬不到 | Avondale 用 Wix，普通 Fetcher 拿到空内容 | 用 Playwright sync API 渲染 |
| Art ≠ 所有 Visual Arts | AGS 有 Art 系但没开 Sculpture | 只加学校实际开设的子科目 |
| 科目别名 | Carpentry = Wood Technology, Samoan = Gagana Samoa | 用 pool 标准名，raw_name 保留原始名 |
| Coursebook PDF | 官网看不到细颗粒度科目 | 找学校 prospectus/coursebook PDF 提取 |
| 费用年份误匹配 | AGGS 正则抓到 WordPress 主题的 "2024" | 页面无明确年份时硬编码爬虫运行年份 |
| 横幅 logo 太小 | WGHS 2800×574 SVG 在 160px 容器中只有 30px 高 | 找正方形 crest 图代替 banner logo |
| Clubs 在 PDF 里 | WGHS clubs 页面只有 PDF 链接 | 用 PyPDF2 提取 PDF 文本 |
| 合唱团名不明确 | Cantare、Cigno Voce 不知道是什么 | 加 "Choir" 后缀：Cantare Choir |
| 只爬一个页面 | KGC curriculum 页没列具体科目 | 合并 curriculum + international 页面的科目 |
| Sporty asset 找不到 | KGC 费用 PDF 链接藏在 `data-link-data` 属性 | 从 HTML 源码 `data-link-data` 提取 UUID |

---

## 11. Wix 网站处理（Avondale 经验）

部分学校使用 Wix 建站（JS 渲染），普通 HTTP Fetcher 只能拿到 JS 脚手架代码。

### 解决方案：Playwright sync API

```python
from playwright.sync_api import sync_playwright
import time

p = sync_playwright().start()
browser = p.chromium.launch(headless=True)
page = browser.new_page()
page.goto(url, wait_until='domcontentloaded', timeout=30000)
time.sleep(5)  # Wix 需要时间渲染
text = page.inner_text('body')
browser.close()
p.stop()
```

### 注意事项
- 不要用 `with` 语句（Wix 页面 networkidle 可能超时导致 context manager crash）
- 用 `sync_playwright().start()` + `p.stop()` 代替
- 每个页面独立启动浏览器（避免跨页面 crash）
- `wait_until='domcontentloaded'` + `time.sleep(5)` 比 `networkidle` 更稳定
- Wix 页面的导航噪音更多，需要过滤

---

## 12. Subject 别名映射表

爬虫遇到不同学校对同一科目的不同叫法时，用 pool 标准名匹配：

| 学校原始名 | Pool 标准名 | 说明 |
|-----------|-----------|------|
| Commerce | → 展开为 Accounting, Business Studies, Economics | group 展开 |
| Art | → 展开为 Visual Arts 子科目 | 看学校实际开了哪些 |
| Carpentry | Wood Technology | 别名 |
| Samoan | Gagana Samoa | NZQA 官方名 |
| Travel and Tourism | Tourism | pool 标准名 |
| Physical Education And Health | Physical Education + Health | 拆分为两个 |
| Classics | Classical Studies | NZQA 官方名 |
| Social Sciences | → group，看学校有没有细科目 | 有细科目时不展开 |
| Technology | → group，看学校有没有细科目 | 有细科目时不展开 |
| Building & Construction | Construction | 别名 |
| Product Design | Product Development | 别名 |
| Mechanical Manufacturing | 不匹配 Wood Technology | 机械 ≠ 木工，不能乱映射 |
| Art Design | Design | Visual Arts 下的子科目 |
| Digital Technologies Programming | Digital Technology | pool 标准名 |
| Food and Hospitality | 拆分为 Food Technology + Hospitality | 看学校实际开设 |
| Tongan / Lea-Faka Tonga | Lea Faka-Tonga | 注意连字符位置 |
| Visual Art | Painting | pool 中 Visual Arts 是 group |
| Soft Materials | Textiles | KGC 叫法 |
| Design and Visual Communication | Design & Visual Communication | `and` → `&` |
| Agriculture | Agricultural and Horticultural Science | NZQA 官方名 |
| Earth & Space | Earth and Space Science | pool 标准名 |
| Textiles Technology | Textiles | pool 标准名 |
| Tourism and the Travel Industry | Tourism | AGGS 叫法 |
| Hospitality/Food Technology | Food Technology | 合并科目取主体 |
| Health Studies | Health | pool 标准名 |

---

## 13. Subject Pool 管理规则

- **新增科目必须经过用户批准**
- 来源应为 NZQA 官方科目 或 学校 coursebook PDF 确认的课程
- 不加入 pool 的：支持服务（Learning Support, Counselling）、非学科（Careers）、过细的变体（Music Technology, Fashion Technology）
- Pool 当前状态：11 groups, 60+ subjects
- 不加入 pool 的变体：Music Technology, Fashion Technology, Mechanical Engineering, Outdoor Education

---

## 14. Curriculum Systems 验证规则

- **不能用 JS 变量名匹配**：Westlake 的 `var ib = {}` 不是 International Baccalaureate
- 必须在页面正文（非 JS 代码）中找到 "International Baccalaureate" / "IB Diploma" / "Cambridge" / "A-Level" 等关键词
- 最好有专门的页面（如 /ib-review/, /cambridge-caie/）作为 evidence_url
- 只有 NCEA 的学校不显示 curriculum badge（因为所有学校都有 NCEA）

---

## 15. 数据完整性检查清单

每所学校爬完后，检查以下项目：

| 检查项 | 要求 |
|--------|------|
| Subjects | 有 PDF/coursebook 依据，不能凭猜测 |
| Sports | 来源页面链接有效 |
| Arts | 只含表演团体 + Kapa Haka |
| Clubs | 有来源链接（activities_url） |
| Fees | 有 PDF 来源，金额为最新年度 |
| Curriculum | 有 evidence_url，不能从 JS 代码匹配 |
| 新增 pool 科目 | 必须经过用户批准 |

---

## 16. 已爬学校记录

| # | 学校 | Subjects | Sports | Arts | Clubs | Fees (年学费) | Fee Year | Curriculum | 网站类型 |
|---|------|----------|--------|------|-------|-------------|----------|-----------|---------|
| 54 | Auckland Grammar | 27 | 32 | 16 | 6 | $25,750 | — | NCEA, A-Level | WordPress |
| 28 | Rangitoto College | 40 | 30 | 6 | 87 | $16,500 | 2026 | NCEA, IB | 标准 HTML |
| 78 | Avondale College | 37 | 29 | 14 | 20 | $21,000 | 2027 | NCEA, A-Level | Wix (需 Playwright) |
| 37 | Westlake Boys | 40 | 31 | 15 | 21 | $23,000 | 2027 | NCEA | 标准 HTML |
| 64 | Epsom Girls Grammar | 19+ | 40+ | 12 | 14+ | $23,000 | 2026 | NCEA | 标准 HTML |
| 38 | Westlake Girls | 38 | 36 | 20 | 40 | $23,000 | 2026 | NCEA | WordPress |
| 53 | Auckland Girls Grammar | 35 | 18 | 4 | 7 | $17,900 | 2026 | NCEA | WordPress (Elementor) |
| 84 | Kelston Girls | 26 | 9 | 3 | 7 | $16,800 | 2026 | NCEA | Sporty CMS |

### 特殊经验备注
- **WGHS #38**: logo 用 `WGHS-Shield-crest-only-RGB.png`（正方形），不用横幅 SVG；clubs 全在 PDF 里（73 页，每页一个 club）；fees PDF 同时有 2026 和 2027 两年费用
- **AGGS #53**: logo 用 `android-chrome-512x512` crest，不用横幅 PNG；费用页无年份标注，用爬虫运行年份 2026；homestay 给的是年费需除以 46 转周费
- **KGC #84**: Sporty CMS 平台，费用 PDF 链接藏在 `data-link-data` 属性中；curriculum 页只有宽泛描述，需合并 international 页面补充科目
- **EGGS #64**: 标准 HTML，Year 11-13 科目在图片中无法爬取，需手动读取
