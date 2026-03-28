## 提案：NCEA 区块 i18n 统一

### 1. translations.js 新增 key

```js
// ui 部分新增
ncea_l3_attainment:  { en: "L3 attainment", cn: "L3达标率" },
ncea_l2_attainment:  { en: "L2 attainment", cn: "L2达标率" },
ncea_l1_attainment:  { en: "L1 attainment", cn: "L1达标率" },
ncea_above:          { en: "above ", cn: "高于" },
ncea_below:          { en: "below ", cn: "低于" },
ncea_year_suffix:    { en: "", cn: " 年" },
```

### 2. comparison group 翻译

在 translations.js 的 data 部分新增 `comparison_group` 类别：
```js
comparison_group: {
  "Secondary (Year 9-15)":  { en: "Secondary", cn: "中学" },
  "Secondary (Year 7-15)":  { en: "Secondary", cn: "中学" },
  "Composite (Year 1-15)":  { en: "Composite", cn: "一贯制学校" },
  "Composite (Year 1-10)":  { en: "Composite", cn: "一贯制学校" },
  "State: Not integrated":  { en: "State", cn: "公立" },
  "State: Integrated":      { en: "State Integrated", cn: "公立整合" },
  "Private: Fully Registered":  { en: "Private", cn: "私立" },
  "Private: Provisionally Registered": { en: "Private", cn: "私立" },
  "New Zealand":             { en: "NZ Average", cn: "全国平均" },
}
```

Region 用已有的 `td('region', key)` 翻译。

### 3. index.html 改造

- 删除 `_regionCn` 映射表（重复）
- 删除 `_compLabel` 函数，改用 `td('comparison_group', key)` + `td('region', key)` fallback
- 13 处三元判断改为 `t()` 调用
- 图例 "L3" → "NCEA L3" 等，用 t() key

### 4. 改动文件
| 文件 | 改动 |
|------|------|
| translations.js | 新增 ~15 个翻译 key |
| index.html | renderPerformanceHtml 内约 20 处修改 |
