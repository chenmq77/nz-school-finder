#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NZ School Finder / 新西兰择校助手
从 schools.db 查询学校信息，按 A-E 五大分类展示
"""

import re
import sqlite3
import os
import sys
import unicodedata

# ── 常量 ──────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schools.db")
WIDTH = 72  # 终端显示宽度
BAR_MAX = 35  # 条形图最大字符宽度


# ── 终端对齐辅助（处理中英混排宽度）───────────────────────
def display_width(text):
    """估算终端等宽字体下的显示宽度（中文等全角按 2 计）。"""
    if text is None:
        return 0
    s = str(text)
    w = 0
    for ch in s:
        if unicodedata.combining(ch):
            continue
        eaw = unicodedata.east_asian_width(ch)
        w += 2 if eaw in ("F", "W") else 1
    return w


def fit_display(text, width):
    """按显示宽度截断/补空格，使最终显示宽度恰好为 width。"""
    s = "" if text is None else str(text)
    if width <= 0:
        return ""
    if display_width(s) == width:
        return s
    if display_width(s) < width:
        return s + (" " * (width - display_width(s)))

    # 需要截断：预留 1 个字符给省略号
    if width == 1:
        return "…"
    out = []
    w = 0
    for ch in s:
        if unicodedata.combining(ch):
            out.append(ch)
            continue
        ch_w = 2 if unicodedata.east_asian_width(ch) in ("F", "W") else 1
        if w + ch_w > width - 1:
            break
        out.append(ch)
        w += ch_w
    return "".join(out) + "…"


def center_display(text, width):
    s = "" if text is None else str(text)
    w = display_width(s)
    if w >= width:
        return fit_display(s, width)
    left = (width - w) // 2
    right = width - w - left
    return (" " * left) + s + (" " * right)


def rjust_display(text, width):
    s = "" if text is None else str(text)
    w = display_width(s)
    if w >= width:
        return fit_display(s, width)
    return (" " * (width - w)) + s


def safe(val):
    """处理空值，返回 '--' 或去除首尾空白"""
    if val is None:
        return "--"
    s = str(val).strip()
    return s if s else "--"


def safe_int(val):
    """安全转为整数"""
    if val is None:
        return 0
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def safe_float(val):
    """安全转为浮点数"""
    if val is None:
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


# ── 数据库操作 ─────────────────────────────────────────
def get_connection():
    if not os.path.exists(DB_PATH):
        print(f"\n  [错误] 数据库文件不存在: {DB_PATH}")
        sys.exit(1)
    return sqlite3.connect(DB_PATH)


def search_schools(keyword):
    """模糊搜索学校名称，返回 (school_number, school_name) 列表"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT school_number, school_name FROM schools "
            "WHERE school_name LIKE ? ORDER BY school_name",
            (f"%{keyword}%",),
        )
        return cur.fetchall()
    except sqlite3.Error as e:
        print(f"\n  [错误] 数据库查询失败：{e}")
        return []
    finally:
        if conn is not None:
            conn.close()


def fetch_school(school_number):
    """按学校编号获取完整记录，返回字典"""
    conn = None
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM schools WHERE school_number = ?", (school_number,))
        row = cur.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        print(f"\n  [错误] 数据库读取失败：{e}")
        return None
    finally:
        if conn is not None:
            conn.close()


# ── 显示辅助 ─────────────────────────────────────────
def line(ch="═"):
    return ch * WIDTH


def section_header(title, folded=False, key=None):
    """打印分区标题"""
    if folded and key:
        tag = f"[按 {key} 展开]"
    else:
        tag = ""
    inner_w = WIDTH - 4  # 保持原脚本的缩进与视觉宽度
    title_w = display_width(title)
    tag_w = display_width(tag)
    gap = inner_w - title_w - tag_w
    if gap < 1:
        content = fit_display(title, inner_w)  # 太长时直接截断标题
    else:
        content = f"{title}{' ' * gap}{tag}"
    print(f"  {content}")
    print(f"  {'=' * inner_w}")


def row_pair(label_en, label_cn, value, indent=4):
    """打印一行中英双语字段"""
    prefix = " " * indent
    combined_label = f"{label_en} / {label_cn}"
    label_cell = fit_display(combined_label, 30)
    print(f"{prefix}{label_cell} {safe(value)}")


def bar_chart(label_cn, label_en, count, total, bar_max=BAR_MAX):
    """绘制 ASCII 条形图行"""
    count = safe_int(count)
    total = safe_int(total)
    if total <= 0:
        pct = 0.0
    else:
        pct = count / total * 100
    filled = int(round(pct / 100 * bar_max)) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_max - filled)
    # 格式化标签和数值
    label = f"{label_cn}/{label_en}"
    label_cell = fit_display(label, 20)
    print(f"    {label_cell} {count:>5}  {bar}  {pct:>5.1f}%")


def eqi_interpret(val):
    """EQI 公平指数解读"""
    v = safe_float(val)
    if v <= 0:
        return "--"
    if v < 400:
        return "社区条件较优越 / Advantaged"
    elif v <= 500:
        return "社区条件中等 / Mid-range"
    else:
        return "社区条件较弱 / Disadvantaged"


def eqi_bar(val):
    """EQI 进度条（范围大约 300-700）"""
    if val is None or str(val).strip() == "":
        return "[" + " " * 20 + "]"
    v = safe_float(val)
    if v <= 0:
        return "[" + " " * 20 + "]"
    # 归一化到 0-1（300=0, 700=1）
    ratio = max(0, min(1, (v - 300) / 400))
    filled = int(round(ratio * 20))
    filled = max(0, min(20, filled))
    if filled <= 0:
        return "[" + ">" + " " * 19 + "]"
    if filled >= 20:
        return "[" + "=" * 20 + "]"
    return "[" + "=" * (filled - 1) + ">" + " " * (20 - filled) + "]"


def isolation_bar(val):
    """偏远指数进度条（范围 0-15 左右）"""
    if val is None or str(val).strip() == "":
        return "[" + " " * 20 + "]"
    v = safe_float(val)
    if v <= 0:
        return "[" + ">" + " " * 19 + "]"
    ratio = max(0, min(1, v / 15))
    filled = int(round(ratio * 20))
    if filled == 0:
        filled = 1
    return "[" + "=" * (filled - 1) + ">" + " " * (20 - filled) + "]"


def isolation_interpret(val):
    if val is None or str(val).strip() == "":
        return "--"
    v = safe_float(val)
    if v < 1:
        return "靠近市中心 / Near city centre"
    elif v < 5:
        return "郊区 / Suburban"
    elif v < 10:
        return "偏远地区 / Remote"
    else:
        return "极偏远 / Very remote"


# ── 各分区展示 ─────────────────────────────────────────
def show_section_a(s):
    """A. 学校身份概览（7列）"""
    print()
    section_header("A. 学校身份概览 / School Identity")
    print()
    # 学校名 + 编号
    name = safe(s.get("school_name"))
    number = safe(s.get("school_number"))
    print(f"    {fit_display(name, 50)} No. {number}")
    print()

    # 三个标签卡片：类型、管理性质、学生性别
    t1 = safe(s.get("school_type"))
    t2 = safe(s.get("authority"))
    t3 = safe(s.get("gender_of_students"))

    # 管理性质中文
    auth_cn = {"State": "公立学校", "State: Integrated": "公立整合",
               "Private": "私立学校"}.get(t2, t2)
    # 性别中文
    gender_cn = {"Boys School": "男校", "Girls School": "女校",
                 "Co-Ed": "混校"}.get(t3, t3)
    # 学校类型中文（尽量翻译，无法识别则原样显示）
    # 翻译学校类型，保留原始年级范围信息
    t1_norm = t1.lower()
    # 提取括号中的年级范围（如 "(Year 9-15)"）
    year_match = re.search(r'\(Year\s+[\d\-]+\)', t1, re.IGNORECASE)
    year_range = f" {year_match.group()}" if year_match else ""
    if "full primary" in t1_norm:
        type_cn = f"全小学{year_range}"
    elif "contributing" in t1_norm:
        type_cn = f"小学{year_range}"
    elif "intermediate" in t1_norm:
        type_cn = f"初中{year_range}"
    elif "secondary" in t1_norm:
        type_cn = f"中学{year_range}"
    elif "composite" in t1_norm:
        type_cn = f"综合学校{year_range}"
    elif "special" in t1_norm:
        type_cn = f"特殊学校{year_range}"
    elif "restricted" in t1_norm:
        type_cn = f"特教学校{year_range}"
    elif "teen parent" in t1_norm:
        type_cn = f"青少年家长学校{year_range}"
    else:
        type_cn = t1

    # 动态计算卡片宽度（同时保证整体不超出版面宽度）
    desired = [
        max(18, display_width(t1) + 2, display_width(type_cn) + 2),
        max(18, display_width(t2) + 2, display_width(auth_cn) + 2),
        max(18, display_width(t3) + 2, display_width(gender_cn) + 2),
    ]
    sum_max = WIDTH - 8  # 3 张卡片边框与间隔会额外占用 8 个字符
    max_each = max(18, sum_max // 3)
    cws = [min(d, max_each) for d in desired]
    # 如果仍超出，优先从更宽的卡片逐步缩小
    while sum(cws) > sum_max:
        i = max(range(3), key=lambda k: cws[k])
        if cws[i] <= 18:
            break
        cws[i] -= 1
    cw1, cw2, cw3 = cws

    def card_line(text, cw):
        return f"| {fit_display(text, max(1, cw - 1))}|"

    print(f"    +{'-' * cw1}+ +{'-' * cw2}+ +{'-' * cw3}+")
    print(f"    {card_line(t1, cw1)} {card_line(t2, cw2)} {card_line(t3, cw3)}")
    print(f"    {card_line(type_cn, cw1)} {card_line(auth_cn, cw2)} {card_line(gender_cn, cw3)}")
    print(f"    +{'-' * cw1}+ +{'-' * cw2}+ +{'-' * cw3}+")
    print()

    # 寄宿
    boarding = safe(s.get("boarding_facilities"))
    b = boarding.lower()
    boarding_cn = "提供寄宿" if b == "yes" else "不提供寄宿" if b == "no" else boarding
    print(f"    Boarding / 寄宿设施:       {boarding}  ({boarding_cn})")

    # 官网
    website = safe(s.get("school_website"))
    print(f"    Website / 学校官网:        {website}")
    print()


def show_section_b(s):
    """B. 位置与联系方式（10列）"""
    section_header("B. 位置与联系方式 / Location & Contact")
    print()

    # 合并详细地址
    street = safe(s.get("street"))
    suburb = safe(s.get("suburb"))
    city = safe(s.get("town_city"))
    parts = [p for p in [street, suburb, city] if p != "--"]
    address = ", ".join(parts) if parts else "--"

    # 合并邮寄地址
    pa = safe(s.get("postal_address"))
    pa_sub = safe(s.get("postal_address_suburb"))
    pa_city = safe(s.get("postal_address_city"))
    pcode = safe(s.get("postal_code"))
    pparts = [p for p in [pa, pa_sub, pa_city] if p != "--"]
    if pcode != "--":
        pparts.append(pcode)
    postal = ", ".join(pparts) if pparts else "--"

    print(f"    Address / 详细地址:        {address}")
    print(f"    Post / 邮寄地址:           {postal}")

    urban = safe(s.get("urban_rural"))
    print(f"    Area / 城乡属性:           {urban}")
    print(f"    {'─' * (WIDTH - 8)}")

    tel = safe(s.get("telephone"))
    email = safe(s.get("email"))
    print(f"    Tel / 电话:                {tel}")
    print(f"    Email / 邮箱:              {email}")
    print()


def show_section_c(s):
    """C. 学生规模与构成（9列）"""
    section_header("C. 学生规模与构成 / Students")
    print()

    total = safe_int(s.get("total_school_roll"))
    total_display = f"{total:,}" if total > 0 else safe(s.get("total_school_roll"))

    print(f"    Total Students / 总人数")
    print(f"    ╔═══════════════════╗")
    print(f"    ║  {str(total_display):^17} ║")
    print(f"    ╚═══════════════════╝")
    print()

    print(f"    Ethnic Distribution / 族裔分布")
    print(f"    +{'-' * (WIDTH - 8)}+")

    # 族裔数据（按人数降序排列）
    ethnicities = [
        ("欧洲裔", "European", s.get("european_pakeha")),
        ("毛利裔", "Maori", s.get("maori")),
        ("太平洋岛裔", "Pacific", s.get("pacific")),
        ("亚裔", "Asian", s.get("asian")),
        ("中东/拉丁/非洲", "MELAA", s.get("melaa")),
        ("其他", "Other", s.get("other")),
    ]
    # 按人数降序
    ethnicities.sort(key=lambda x: safe_int(x[2]), reverse=True)

    for cn, en, val in ethnicities:
        bar_chart(cn, en, val, total)

    print(f"    +{'-' * (WIDTH - 8)}+")
    print()

    # 国际学生
    intl = safe_int(s.get("international"))
    if total > 0:
        intl_pct = intl / total * 100
        intl_str = f"{intl} ({intl_pct:.1f}%)"
    else:
        intl_str = safe(s.get("international"))
    enrol = safe(s.get("enrolment_scheme"))
    enrol_cn = "有学区限制" if enrol == "Yes" else "无学区限制" if enrol == "No" else enrol

    print(f"    International / 国际学生:  {intl_str}")
    print(f"    Enrolment / 招生计划:      {enrol}  ({enrol_cn})")
    print()


def show_section_d(s):
    """D. 学校质量与特色（11列）"""
    section_header("D. 学校质量与特色 / Quality & Features")
    print()

    # EQI
    eqi = s.get("equity_index_eqi")
    eqi_v = safe(eqi)
    print(f"    EQI / 公平指数:            {eqi_v}")
    print(f"                               {eqi_bar(eqi)}")
    print(f"                               {eqi_interpret(eqi)}")
    print()

    # 偏远指数
    iso = s.get("isolation_index")
    iso_v = safe(iso)
    print(f"    Isolation / 偏远指数:      {iso_v}")
    print(f"                               {isolation_bar(iso)}")
    print(f"                               {isolation_interpret(iso)}")
    print()

    # 其他字段
    row_pair("Teaching Language", "教学语言",
             s.get("language_of_instruction"))
    row_pair("Donations", "捐赠政策",
             s.get("donations"))
    row_pair("KME Peak Body", "毛利教育机构",
             s.get("kme_peak_body"))

    # 坐标
    lat = safe(s.get("latitude"))
    lng = safe(s.get("longitude"))
    # 只要任一坐标有值就显示
    coord_parts = [p for p in [lat, lng] if p != "--"]
    coord = ", ".join(coord_parts) if coord_parts else "--"
    row_pair("Location", "地理坐标", coord)

    row_pair("Principal", "校长",
             s.get("principal"))
    row_pair("Definition", "办学定义",
             s.get("definition"))

    # 状态
    status = safe(s.get("status"))
    status_map = {
        "open": "Open (运营中)",
        "closed": "Closed (已关闭)",
        "merger": "Merger (合并中)",
        "new": "New (筹建中)",
        "not yet open": "Not Yet Open (未开放)",
        "proposed": "Proposed (规划中)",
    }
    status_display = status_map.get(status.lower(), status)
    row_pair("Status", "运营状态", status_display)

    # 群体入学
    cohort = safe(s.get("cohort_entry"))
    cohort_cn = "群体入学" if cohort == "Yes" else "非群体入学" if cohort == "No" else cohort
    row_pair("Cohort Entry", "群体入学", f"{cohort}  ({cohort_cn})")
    print()


def show_section_e(s):
    """E. 行政与区域归属（12列）"""
    section_header("E. 行政与区域归属 / Administrative")
    print()

    # 子模块1：区域管辖
    print(f"    Region / 区域管辖")
    print(f"    +{'-' * (WIDTH - 8)}+")
    row_pair("Education Region", "教育大区",
             s.get("education_region"))
    row_pair("Takiwa", "毛利语区域",
             s.get("takiwa"))
    row_pair("Territorial Auth", "领土管理局",
             s.get("territorial_authority"))
    row_pair("Regional Council", "区域议会",
             s.get("regional_council"))
    row_pair("Local Office", "地方办事处",
             s.get("local_office"))
    print(f"    +{'-' * (WIDTH - 8)}+")
    print()

    # 子模块2：选区
    print(f"    Electorate / 选区信息")
    print(f"    +{'-' * (WIDTH - 8)}+")
    row_pair("General Electorate", "普通选区",
             s.get("general_electorate"))
    row_pair("Maori Electorate", "毛利选区",
             s.get("maori_electorate"))
    print(f"    +{'-' * (WIDTH - 8)}+")
    print()

    # 子模块3：社区
    print(f"    Community / 社区归属")
    print(f"    +{'-' * (WIDTH - 8)}+")
    sa2_name = safe(s.get("neighbourhood_sa2"))
    sa2_code = safe(s.get("neighbourhood_sa2_code"))
    if sa2_name != "--" and sa2_code != "--":
        nb_display = f"{sa2_name} ({sa2_code})"
    elif sa2_name != "--":
        nb_display = sa2_name
    elif sa2_code != "--":
        nb_display = sa2_code
    else:
        nb_display = "--"
    row_pair("Neighbourhood", "社区", nb_display)
    row_pair("Ward", "地方选区",
             s.get("ward"))
    print(f"    +{'-' * (WIDTH - 8)}+")
    print()

    # 子模块4：学习社区
    print(f"    Learning Community / 学习社区")
    print(f"    +{'-' * (WIDTH - 8)}+")
    row_pair("CoL ID", "学习社区ID",
             s.get("community_of_learning_id"))
    row_pair("CoL Name", "学习社区名称",
             s.get("community_of_learning_name"))
    print(f"    +{'-' * (WIDTH - 8)}+")
    print()


# ── 主界面 ─────────────────────────────────────────────
def show_banner():
    print()
    print(f"  +{line()}+")
    print(f"  |{center_display('NZ School Finder / 新西兰择校助手', WIDTH)}|")
    print(f"  +{line()}+")
    print()


def show_school(s, expand_d=False, expand_e=False):
    """完整展示一所学校的信息"""
    print()
    print(f"  +{line()}+")
    print(f"  |{rjust_display('NZ School Finder', WIDTH)}|")
    print(f"  +{line()}+")
    print()

    # A - 默认展开
    show_section_a(s)

    # B - 默认展开
    show_section_b(s)

    # C - 默认展开
    show_section_c(s)

    # D - 默认折叠
    if expand_d:
        show_section_d(s)
    else:
        section_header("D. 学校质量与特色 / Quality & Features",
                       folded=True, key="D")
        print(f"    (输入 D 展开: 公平指数、偏远指数、教学语言、校长等)")
        print()

    # E - 默认折叠
    if expand_e:
        show_section_e(s)
    else:
        section_header("E. 行政与区域归属 / Administrative",
                       folded=True, key="E")
        print(f"    (输入 E 展开: 教育大区、选区、社区归属等)")
        print()

    print(f"  +{line()}+")
    print()


def select_school(results):
    """当搜索到多个结果时，让用户选择"""
    print(f"\n  找到 {len(results)} 所匹配的学校：\n")
    for i, (num, name) in enumerate(results, 1):
        print(f"    {i:>3}. [{safe(num)}] {safe(name)}")
    print()
    while True:
        choice = input("  请输入序号选择学校 (Q 退出): ").strip()
        if choice.upper() == "Q":
            return None
        try:
            idx = int(choice)
            if 1 <= idx <= len(results):
                return results[idx - 1][0]  # 返回 school_number
            else:
                print(f"  请输入 1-{len(results)} 之间的数字")
        except ValueError:
            print("  请输入有效的数字")


def main():
    show_banner()

    while True:
        keyword = input("  输入学校英文名称搜索 (Q 退出): ").strip()
        if not keyword:
            continue
        if keyword.upper() == "Q":
            print("\n  再见! / Goodbye!\n")
            break

        # 搜索
        results = search_schools(keyword)
        if not results:
            print(f"\n  未找到包含 \"{keyword}\" 的学校，请重试。\n")
            continue

        # 选择学校
        if len(results) == 1:
            school_number = results[0][0]
            print(f"\n  找到: {results[0][1]}")
        else:
            school_number = select_school(results)
            if school_number is None:
                continue

        # 获取完整数据
        school = fetch_school(school_number)
        if not school:
            print("\n  [错误] 无法加载学校数据\n")
            continue

        # 展示（D/E 默认折叠）
        expand_d = False
        expand_e = False
        show_school(school, expand_d, expand_e)

        # 交互：展开/折叠 D/E
        while True:
            cmd = input("  输入 D/E 展开详情, 其他内容重新搜索, Q 退出: ").strip()
            if not cmd:
                continue
            if cmd.upper() == "Q":
                print("\n  再见! / Goodbye!\n")
                return
            elif cmd.upper() == "D":
                expand_d = True
                show_school(school, expand_d, expand_e)
            elif cmd.upper() == "E":
                expand_e = True
                show_school(school, expand_d, expand_e)
            else:
                # 当作新搜索关键词
                results = search_schools(cmd)
                if not results:
                    print(f"\n  未找到包含 \"{cmd}\" 的学校，请重试。\n")
                    continue
                if len(results) == 1:
                    school_number = results[0][0]
                    print(f"\n  找到: {results[0][1]}")
                else:
                    school_number = select_school(results)
                    if school_number is None:
                        continue
                school = fetch_school(school_number)
                if not school:
                    print("\n  [错误] 无法加载学校数据\n")
                    continue
                expand_d = False
                expand_e = False
                show_school(school, expand_d, expand_e)


if __name__ == "__main__":
    main()
