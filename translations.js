/**
 * NZ School Finder — Translations
 *
 * Human-editable translation file.
 * To fix a translation: search for the English text, edit the "cn" value, save, refresh browser.
 *
 * Structure: all entries use { en, cn } format.
 * cn: null  = not yet translated (will fallback to English)
 * cn: ""    = intentionally keep English (e.g. proper nouns)
 */

const TRANSLATIONS = {

  // ── UI Labels (Section Headers, Field Labels, Buttons) ─────────────

  ui: {
    // Header & Navigation
    site_title_nz:        { en: "NZ", cn: "新西兰" },
    site_title_main:      { en: "School Finder", cn: "学校查询" },
    search_placeholder:   { en: "Search for schools...", cn: "搜索学校..." },
    lang_en:              { en: "EN", cn: "EN" },
    lang_cn:              { en: "中", cn: "中" },
    lang_both:            { en: "双", cn: "双" },

    // Section Headers (A-G)
    section_a:            { en: "School Identity", cn: "学校身份概览" },
    section_b:            { en: "Location & Admissions", cn: "位置与入学" },
    section_c:            { en: "Subjects & Curriculum", cn: "课程与学科" },
    section_d:            { en: "Activities & Co-curricular", cn: "课外活动" },
    section_e:            { en: "International Fees", cn: "国际生费用" },
    section_f:            { en: "Students", cn: "学生规模与构成" },
    section_g:            { en: "Other Details", cn: "其他信息" },

    // Field Labels — Section A
    school_type:          { en: "Type", cn: "类型" },
    year_level:           { en: "Year Levels", cn: "年级" },
    authority:            { en: "Authority", cn: "性质" },
    gender:               { en: "Gender", cn: "性别" },
    curriculum:           { en: "Curriculum", cn: "课程体系" },
    boarding:             { en: "Boarding", cn: "寄宿设施" },
    website:              { en: "Website", cn: "学校官网" },

    // Field Labels — Section B
    address:              { en: "Address", cn: "详细地址" },
    post:                 { en: "Post", cn: "邮寄地址" },
    area:                 { en: "Area", cn: "城乡属性" },
    location:             { en: "Location", cn: "地理坐标" },
    tel:                  { en: "Tel", cn: "电话" },
    email:                { en: "Email", cn: "邮箱" },
    enrolment:            { en: "Enrolment", cn: "招生计划" },
    zone:                 { en: "Zone", cn: "学区" },
    eqi:                  { en: "EQI", cn: "公平指数" },
    open_map:             { en: "Open Map", cn: "打开地图" },
    zone_map:             { en: "Zone map", cn: "学区地图" },
    streets_pdf:          { en: "Streets PDF", cn: "街道列表" },
    enrolment_link:       { en: "Enrolment", cn: "入学详情" },

    // Field Labels — Section F (Students)
    total_students:       { en: "Total Students", cn: "学校总人数" },
    intl_students:        { en: "International Students", cn: "国际学生" },
    intl_pct:             { en: "of total", cn: "占总人数" },
    ethnic_distribution:  { en: "Ethnic Distribution", cn: "族裔分布" },

    // Field Labels — Section G (Other)
    sub_quality:          { en: "Quality", cn: "质量特色" },
    sub_region:           { en: "Region", cn: "区域管辖" },
    sub_electorate:       { en: "Electorate", cn: "选区信息" },
    sub_community:        { en: "Community", cn: "社区归属" },
    isolation:            { en: "Isolation", cn: "偏远指数" },
    teaching_lang:        { en: "Teaching Language", cn: "教学语言" },
    donations:            { en: "Donations", cn: "捐赠政策" },
    kme:                  { en: "KME Peak Body", cn: "毛利教育机构" },
    principal:            { en: "Principal", cn: "校长" },
    definition:           { en: "Definition", cn: "办学定义" },
    status:               { en: "Status", cn: "运营状态" },
    cohort_entry:         { en: "Cohort Entry", cn: "群体入学" },
    education_region:     { en: "Education Region", cn: "教育大区" },
    takiwa:               { en: "Takiwā", cn: "毛利语区域" },
    territorial_auth:     { en: "Territorial Authority", cn: "领土管理局" },
    regional_council:     { en: "Regional Council", cn: "区域议会" },
    local_office:         { en: "Local Office", cn: "地方办事处" },
    general_electorate:   { en: "General Electorate", cn: "普通选区" },
    maori_electorate:     { en: "Māori Electorate", cn: "毛利选区" },
    neighbourhood:        { en: "Neighbourhood", cn: "社区" },
    ward:                 { en: "Ward", cn: "地方选区" },
    col_id:               { en: "CoL ID", cn: "学习社区 ID" },
    col_name:             { en: "CoL Name", cn: "学习社区名称" },

    // Field Labels — Section C-D
    subjects:             { en: "Subjects", cn: "学科" },
    sports:               { en: "Sports", cn: "体育运动" },
    arts:                 { en: "Performing Arts", cn: "表演艺术" },
    clubs:                { en: "Clubs & Activities", cn: "社团与活动" },

    // Field Labels — Section E (Fees)
    tuition:              { en: "Tuition", cn: "年学费" },
    homestay:             { en: "Homestay", cn: "住宿费" },
    nzd_per_year:         { en: "NZD per year", cn: "新西兰元/年" },
    per_week:             { en: "/week", cn: "/周" },
    full_fees:            { en: "Full fees", cn: "查看完整费用政策" },

    // Dashboard
    dashboard_title:      { en: "Dashboard", cn: "数据总览" },
    schools_count:        { en: "schools", cn: "所学校" },
    filter_region:        { en: "Region", cn: "区域" },
    filter_authority:     { en: "Authority", cn: "管理性质" },
    filter_gender:        { en: "Gender", cn: "性别" },
    filter_year_levels:   { en: "Year Levels", cn: "年级" },
    filter_curriculum:    { en: "Curriculum", cn: "课程体系" },
    filter_eqi:           { en: "EQI", cn: "公平指数" },
    clear_all:            { en: "Clear all", cn: "清除筛选" },
    sort_name:            { en: "Name A-Z", cn: "按名称 A-Z" },
    sort_roll_desc:       { en: "Roll (High-Low)", cn: "人数（多-少）" },
    sort_roll_asc:        { en: "Roll (Low-High)", cn: "人数（少-多）" },
    sort_eqi_asc:         { en: "EQI (Low-High)", cn: "EQI（低-高）" },
    sort_eqi_desc:        { en: "EQI (High-Low)", cn: "EQI（高-低）" },

    // EQI bands
    eqi_fewest:           { en: "Fewest barriers", cn: "最少障碍" },
    eqi_few:              { en: "Few barriers", cn: "较少障碍" },
    eqi_below_avg:        { en: "Below average", cn: "低于平均" },
    eqi_average:          { en: "Average", cn: "平均水平" },
    eqi_above_avg:        { en: "Above average", cn: "高于平均" },
    eqi_many:             { en: "Many barriers", cn: "较多障碍" },
    eqi_most:             { en: "Most barriers", cn: "最多障碍" },
    eqi_group_fewer:      { en: "Fewer", cn: "较少" },
    eqi_group_moderate:   { en: "Moderate", cn: "中等" },
    eqi_group_more:       { en: "More", cn: "较多" },

    // Misc
    no_data:              { en: "No data available", cn: "暂无数据" },
    no_fee_data:          { en: "No fee data available", cn: "暂无费用数据" },
    no_subject_data:      { en: "No subject data available", cn: "暂无课程数据" },
    no_activity_data:     { en: "No activity data available", cn: "暂无活动数据" },
    back:                 { en: "Back", cn: "返回" },
    loading:              { en: "Loading...", cn: "加载中..." },
    person:               { en: "students", cn: "人" },
  },

  // ── Data Value Translations (CSV enum values) ─────────────────────

  data: {
    // school_type split into type_label (school category) and year_range (grade range)
    school_type_label: {
      "Contributing":                    { en: "Contributing", cn: "小学" },
      "Full Primary":                    { en: "Full Primary", cn: "完全小学" },
      "Intermediate":                    { en: "Intermediate", cn: "中间学校" },
      "Composite":                       { en: "Composite", cn: "综合学校" },
      "Composite (Year 1-10)":           { en: "Composite", cn: "综合学校" },
      "Restricted Composite (Year 7-10)":{ en: "Restricted Composite", cn: "限制综合学校" },
      "Secondary (Year 9-15)":           { en: "Secondary", cn: "中学" },
      "Secondary (Year 7-15)":           { en: "Secondary", cn: "中学" },
      "Secondary (Year 7-10)":           { en: "Secondary", cn: "初中" },
      "Secondary (Year 11-15)":          { en: "Secondary", cn: "高中" },
      "Correspondence School":           { en: "Correspondence School", cn: "函授学校" },
    },
    school_type_years: {
      "Contributing":                    { en: "Year 1-6", cn: "1-6 年级" },
      "Full Primary":                    { en: "Year 1-8", cn: "1-8 年级" },
      "Intermediate":                    { en: "Year 7-8", cn: "7-8 年级" },
      "Composite":                       { en: "Year 1-13", cn: "1-13 年级" },
      "Composite (Year 1-10)":           { en: "Year 1-10", cn: "1-10 年级" },
      "Restricted Composite (Year 7-10)":{ en: "Year 7-10", cn: "7-10 年级" },
      "Secondary (Year 9-15)":           { en: "Year 9-13", cn: "9-13 年级" },
      "Secondary (Year 7-15)":           { en: "Year 7-13", cn: "7-13 年级" },
      "Secondary (Year 7-10)":           { en: "Year 7-10", cn: "7-10 年级" },
      "Secondary (Year 11-15)":          { en: "Year 11-13", cn: "11-13 年级" },
      "Correspondence School":           { en: "Year 1-13", cn: "1-13 年级" },
    },

    authority: {
      "State":                           { en: "State", cn: "公立" },
      "State : Integrated":              { en: "State : Integrated", cn: "公立整合" },
      "Private : Fully Registered":      { en: "Private", cn: "私立" },
      "Private : Provisionally Registered": { en: "Private", cn: "私立" },
      "Charter School":                  { en: "Charter School", cn: "特许学校" },
    },

    gender: {
      "Co-Educational":                  { en: "Co-Educational", cn: "男女混校" },
      "Girls School":                    { en: "Girls School", cn: "女校" },
      "Boys School":                     { en: "Boys School", cn: "男校" },
      "Boys/Senior Co-Ed":               { en: "Boys/Senior Co-Ed", cn: "男校/高年级混校" },
      "Primary Co-Ed/Secondary Girls":   { en: "Primary Co-Ed/Secondary Girls", cn: "小学混校/中学女校" },
      "Primary Co-Ed/Secondary Boys":    { en: "Primary Co-Ed/Secondary Boys", cn: "小学混校/中学男校" },
    },

    boarding: {
      "Yes":                             { en: "Yes", cn: "提供寄宿" },
      "No":                              { en: "No", cn: "不提供寄宿" },
    },

    enrolment_scheme: {
      "Yes":                             { en: "Yes", cn: "有学区限制" },
      "No":                              { en: "No", cn: "无学区限制" },
    },

    urban_rural: {
      "Major urban area":                { en: "Major urban area", cn: "大城市" },
      "Large urban area":                { en: "Large urban area", cn: "大型城区" },
      "Medium urban area":               { en: "Medium urban area", cn: "中型城区" },
      "Small urban area":                { en: "Small urban area", cn: "小型城区" },
      "Rural settlement":                { en: "Rural settlement", cn: "乡村" },
      "Rural other":                     { en: "Rural other", cn: "偏远乡村" },
    },
  },
};
