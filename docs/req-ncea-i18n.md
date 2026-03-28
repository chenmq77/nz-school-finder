# NCEA 区块多语言修复

## 背景
NCEA 升学成绩区块（renderPerformanceHtml）中约有 25 处中文硬编码，没有走项目已有的 t()/td() 翻译系统。导致英文模式下仍显示中文，且存在与 translations.js 的重复翻译。

## 现有 i18n 系统
- `translations.js`: 集中管理翻译（ui 209 条 + data 枚举）
- `js/i18n.js`: t(key) / td(category, value) / bilingual() 函数
- 支持 en/cn/both 三种模式
- `_lang` 变量全局可用

## 问题清单

### 1. 硬编码三元判断（~13 处）
```js
// 当前写法（硬编码）
_lang === 'en' ? 'L3 attainment' : 'L3达标率'
_lang === 'en' ? 'above ' : '高于'
_lang === 'en' ? 'NZ' : '全国'
```
应改为 `t('ncea_l3_attainment')` 等。

### 2. _regionCn 重复定义
renderPerformanceHtml 中定义了 16 个地区翻译的 _regionCn 映射，但 translations.js 的 data.region 中已有完整翻译。应删掉 _regionCn，改用 td('region', key)。

### 3. comparison group 翻译不一致
| 爬取的值 | _compLabel 当前翻译 | translations.js 翻译 | 应改为 |
|---------|---------------------|---------------------|--------|
| Secondary (Year 9-15) | 同类中学 | 中学 | 中学 |
| Composite (Year 1-15) | （缺失） | 一贯制学校 | 一贯制学校 |
| State: Not integrated | 公立学校 | （无短名） | 公立 |
| State: Integrated | 公立整合学校 | （无短名） | 公立整合 |
| Private: Fully Registered | 私立学校 | （无短名） | 私立 |

### 4. 图例标签不完整
- "L3" → "NCEA L3"
- "L2" → "NCEA L2"（如有）
- 未达 Level 1 / NCEA L1 等也需检查

### 5. 未翻译的 UI 文本
- "Achievement Distribution" / "达标分布"
- 脚注文字
- 年份后缀 "年"

## 改动范围
- `translations.js`: 补 ~10 个 NCEA 翻译 key
- `index.html`: renderPerformanceHtml 函数，三元判断改 t() 调用，删除 _regionCn
