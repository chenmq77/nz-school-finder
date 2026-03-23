#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NZ School Finder — 轻量 API 服务器
纯 Python 标准库，零依赖。提供学校搜索和详情 API。

启动方式: python3 server.py
访问地址: http://localhost:8000
"""

import http.server
import json
import os
import sqlite3
import urllib.parse

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schools.db")
HOST = "localhost"
PORT = 8000

# ── 数据库操作 ─────────────────────────────────────────

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def search_schools(keyword, limit=50):
    """模糊搜索学校名称，返回列表和总匹配数"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        # 先查总数
        cur.execute(
            "SELECT COUNT(*) FROM schools WHERE school_name LIKE ?",
            (f"%{keyword}%",),
        )
        total = cur.fetchone()[0]
        # 再查数据（限制返回数量）
        cur.execute(
            "SELECT school_number, school_name, school_type, authority, "
            "gender_of_students, town_city, total_school_roll "
            "FROM schools WHERE school_name LIKE ? ORDER BY school_name LIMIT ?",
            (f"%{keyword}%", limit),
        )
        return [dict(row) for row in cur.fetchall()], total
    finally:
        conn.close()


def fetch_school(school_number):
    """按学校编号获取完整记录"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM schools WHERE school_number = ?", (school_number,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def fetch_stats():
    """返回各维度的学校数量统计（region, type, gender, school_type, eqi, curriculum）"""
    conn = get_connection()
    try:
        cur = conn.cursor()

        # 总数
        cur.execute("SELECT COUNT(*) FROM schools")
        total = cur.fetchone()[0]

        # 按 regional_council 分布
        cur.execute(
            "SELECT regional_council, COUNT(*) as cnt FROM schools "
            "WHERE regional_council IS NOT NULL AND regional_council != '' "
            "GROUP BY regional_council ORDER BY cnt DESC"
        )
        region = [{"name": r[0], "count": r[1]} for r in cur.fetchall()]

        # 按 authority 分布（合并 Private 子类）
        cur.execute(
            "SELECT authority, COUNT(*) as cnt FROM schools "
            "GROUP BY authority ORDER BY cnt DESC"
        )
        authority_raw = {r[0]: r[1] for r in cur.fetchall()}
        # 合并 Private 类别
        private_count = sum(v for k, v in authority_raw.items() if k and 'Private' in k)
        authority = []
        seen_private = False
        for k, v in sorted(authority_raw.items(), key=lambda x: -x[1]):
            if k and 'Private' in k:
                if not seen_private:
                    authority.append({"name": "Private", "count": private_count})
                    seen_private = True
            else:
                authority.append({"name": k or "Unknown", "count": v})
        authority.sort(key=lambda x: -x["count"])

        # 按 gender 分布
        cur.execute(
            "SELECT gender_of_students, COUNT(*) as cnt FROM schools "
            "GROUP BY gender_of_students ORDER BY cnt DESC"
        )
        gender = [{"name": r[0] or "Unknown", "count": r[1]} for r in cur.fetchall()]

        # 按 school_type 分布
        cur.execute(
            "SELECT school_type, COUNT(*) as cnt FROM schools "
            "GROUP BY school_type ORDER BY cnt DESC"
        )
        school_type = [{"name": r[0], "count": r[1]} for r in cur.fetchall()]

        # EQI 分段统计
        eqi_bands = [
            {"name": "Fewest", "cn": "最少障碍", "min": 344, "max": 402, "group": "fewer", "color": "#6ee7b7"},
            {"name": "Few", "cn": "较少障碍", "min": 403, "max": 429, "group": "fewer", "color": "#a7f3d0"},
            {"name": "Below Average", "cn": "低于平均", "min": 430, "max": 448, "group": "moderate", "color": "#fde68a"},
            {"name": "Average", "cn": "平均水平", "min": 449, "max": 469, "group": "moderate", "color": "#fcd34d"},
            {"name": "Above Average", "cn": "高于平均", "min": 470, "max": 493, "group": "moderate", "color": "#fbbf24"},
            {"name": "Many", "cn": "较多障碍", "min": 494, "max": 521, "group": "more", "color": "#fca5a5"},
            {"name": "Most", "cn": "最多障碍", "min": 522, "max": 569, "group": "more", "color": "#f87171"},
        ]
        for band in eqi_bands:
            cur.execute(
                "SELECT COUNT(*) FROM schools WHERE CAST(equity_index_eqi AS REAL) BETWEEN ? AND ?",
                (band["min"], band["max"]),
            )
            band["count"] = cur.fetchone()[0]
        # 无 EQI 数据的学校数量
        cur.execute(
            "SELECT COUNT(*) FROM schools WHERE equity_index_eqi IS NULL "
            "OR equity_index_eqi = '' OR equity_index_eqi = 'not applicable'"
        )
        eqi_na = cur.fetchone()[0]

        # Curriculum 统计（从 school_web_data）
        cur.execute("SELECT curriculum_systems FROM school_web_data WHERE curriculum_systems IS NOT NULL")
        curriculum_counts = {}
        for row in cur.fetchall():
            try:
                systems = json.loads(row[0])
                for sys_info in systems:
                    if sys_info.get("status") == "offered":
                        name = sys_info.get("system", "Unknown")
                        curriculum_counts[name] = curriculum_counts.get(name, 0) + 1
            except (json.JSONDecodeError, TypeError):
                pass
        curriculum = [{"name": k, "count": v} for k, v in
                      sorted(curriculum_counts.items(), key=lambda x: -x[1])]

        # 有 web data 的学校编号
        cur.execute("SELECT school_number FROM school_web_data")
        web_schools = [r[0] for r in cur.fetchall()]

        return {
            "total": total,
            "region": region,
            "authority": authority,
            "gender": gender,
            "school_type": school_type,
            "eqi_bands": eqi_bands,
            "eqi_na": eqi_na,
            "curriculum": curriculum,
            "web_schools": web_schools,
        }
    finally:
        conn.close()


def filter_schools(params):
    """根据筛选条件返回学校列表，支持分页"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        conditions = []
        values = []

        # 辅助：支持逗号分隔多值
        def multi_val(param_name):
            raw = params.get(param_name, [""])[0].strip()
            return [v.strip() for v in raw.split(",") if v.strip()] if raw else []

        # region 筛选（支持多选）
        regions = multi_val("region")
        if regions:
            placeholders = ",".join("?" * len(regions))
            conditions.append(f"regional_council IN ({placeholders})")
            values.extend(regions)

        # authority 筛选（支持多选 + 合并 Private）
        authorities = multi_val("authority")
        if authorities:
            auth_parts = []
            for a in authorities:
                if a == "Private":
                    auth_parts.append("authority LIKE '%Private%'")
                else:
                    auth_parts.append("authority = ?")
                    values.append(a)
            conditions.append("(" + " OR ".join(auth_parts) + ")")

        # gender 筛选（支持多选，含混合类型展开）
        genders = multi_val("gender")
        if genders:
            # 展开混合类型：Girls 包含 Primary Co-Ed/Secondary Girls 等
            expanded = set(genders)
            for g in genders:
                if g == 'Girls School':
                    expanded.add('Primary Co-Ed/Secondary Girls')
                elif g == 'Boys School':
                    expanded.update(['Boys/Senior Co-Ed', 'Primary Co-Ed/Secondary Boys'])
                elif g == 'Co-Educational':
                    expanded.update(['Boys/Senior Co-Ed', 'Primary Co-Ed/Secondary Girls', 'Primary Co-Ed/Secondary Boys'])
            all_g = list(expanded)
            placeholders = ",".join("?" * len(all_g))
            conditions.append(f"gender_of_students IN ({placeholders})")
            values.extend(all_g)

        # school_type 筛选（支持多选）
        school_types = multi_val("school_type")
        if school_types:
            placeholders = ",".join("?" * len(school_types))
            conditions.append(f"school_type IN ({placeholders})")
            values.extend(school_types)

        # curriculum 筛选：通过 school_web_data 的 curriculum_systems 匹配
        curricula = multi_val("curriculum")
        if curricula:
            cur_parts = []
            for c in curricula:
                cur_parts.append("school_number IN (SELECT school_number FROM school_web_data WHERE curriculum_systems LIKE ?)")
                values.append(f'%"{c}"%')
            conditions.append("(" + " OR ".join(cur_parts) + ")")

        # year_level 筛选：找所有年级范围包含 [year_min, year_max] 的学校
        year_min = params.get("year_min", [""])[0].strip()
        year_max = params.get("year_max", [""])[0].strip()
        if year_min and year_max:
            try:
                ymin, ymax = int(year_min), int(year_max)
                # 学校类型 → 年级范围映射
                type_ranges = {
                    'Contributing': (1, 6),
                    'Full Primary': (1, 8),
                    'Intermediate': (7, 8),
                    'Composite': (1, 13),
                    'Composite (Year 1-10)': (1, 10),
                    'Restricted Composite (Year 7-10)': (7, 10),
                    'Secondary (Year 9-15)': (9, 13),
                    'Secondary (Year 7-15)': (7, 13),
                    'Secondary (Year 7-10)': (7, 10),
                    'Secondary (Year 11-15)': (11, 13),
                    'Correspondence School': (1, 13),
                }
                # 找所有包含用户选择范围的学校类型
                matching_types = [t for t, (lo, hi) in type_ranges.items() if lo <= ymin and hi >= ymax]
                if matching_types:
                    placeholders = ",".join("?" * len(matching_types))
                    conditions.append(f"school_type IN ({placeholders})")
                    values.extend(matching_types)
                else:
                    conditions.append("1=0")  # 没有匹配的类型
            except ValueError:
                pass

        # EQI band 筛选
        eqi_band = params.get("eqi_band", [""])[0].strip()
        if eqi_band:
            band_ranges = {
                "Fewest": (344, 402), "Few": (403, 429),
                "Below Average": (430, 448), "Average": (449, 469),
                "Above Average": (470, 493), "Many": (494, 521), "Most": (522, 569),
            }
            if eqi_band in band_ranges:
                lo, hi = band_ranges[eqi_band]
                conditions.append("CAST(equity_index_eqi AS REAL) BETWEEN ? AND ?")
                values.extend([lo, hi])

        # EQI group 筛选（支持多选）
        eqi_groups = multi_val("eqi_group")
        if eqi_groups:
            group_ranges = {
                "fewer": (344, 429), "moderate": (430, 493), "more": (494, 569),
            }
            eqi_parts = []
            for g in eqi_groups:
                if g in group_ranges:
                    lo, hi = group_ranges[g]
                    eqi_parts.append("CAST(equity_index_eqi AS REAL) BETWEEN ? AND ?")
                    values.extend([lo, hi])
            if eqi_parts:
                conditions.append("(" + " OR ".join(eqi_parts) + ")")

        where = " AND ".join(conditions) if conditions else "1=1"

        # 总数
        cur.execute(f"SELECT COUNT(*) FROM schools WHERE {where}", values)
        total = cur.fetchone()[0]

        # 排序
        sort = params.get("sort", ["name"])[0].strip()
        sort_map = {
            "name": "school_name ASC",
            "roll_desc": "CAST(total_school_roll AS INTEGER) DESC",
            "roll_asc": "CAST(total_school_roll AS INTEGER) ASC",
            "eqi_asc": "CAST(equity_index_eqi AS REAL) ASC",
            "eqi_desc": "CAST(equity_index_eqi AS REAL) DESC",
        }
        order_by = sort_map.get(sort, "school_name ASC")

        # 分页
        page = max(1, int(params.get("page", ["1"])[0]))
        limit = min(100, max(1, int(params.get("limit", ["20"])[0])))
        offset = (page - 1) * limit

        cur.execute(
            f"SELECT school_number, school_name, school_type, authority, "
            f"gender_of_students, town_city, total_school_roll, regional_council, "
            f"equity_index_eqi "
            f"FROM schools WHERE {where} ORDER BY {order_by} LIMIT ? OFFSET ?",
            values + [limit, offset],
        )
        results = [dict(row) for row in cur.fetchall()]

        return {
            "results": results,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
        }
    finally:
        conn.close()


def fetch_school_web(school_number):
    """获取学校官网爬取的额外数据，subjects 从标准化表读取"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM school_web_data WHERE school_number = ?", (school_number,))
        row = cur.fetchone()
        if not row:
            return None
        data = dict(row)

        # subjects 从 school_subjects + subject_pool 读取
        # 如果学校关联的是 group，展开为该 group 下的所有子科目
        cur.execute("""SELECT sp.id, sp.name, sp.node_type FROM school_subjects ss
            JOIN subject_pool sp ON ss.subject_id = sp.id
            WHERE ss.school_number = ?""", (school_number,))
        subject_rows = cur.fetchall()
        if subject_rows:
            names = set()
            for sid, name, ntype in subject_rows:
                if ntype == 'group':
                    # 展开 group 为子科目
                    cur.execute("SELECT name FROM subject_pool WHERE parent_id = ? AND node_type = 'subject' ORDER BY name", (sid,))
                    children = [r[0] for r in cur.fetchall()]
                    if children:
                        names.update(children)
                    else:
                        names.add(name)  # 没有子科目的 group 保留原名
                else:
                    names.add(name)
            sorted_names = sorted(names)
            data['subjects'] = json.dumps(sorted_names)
            data['subjects_count'] = len(sorted_names)

        return data
    finally:
        conn.close()


# ── HTTP 处理器 ─────────────────────────────────────────

class SchoolFinderHandler(http.server.SimpleHTTPRequestHandler):
    """处理 API 请求和静态文件"""

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if path == "/api/stats":
            self._handle_stats()
        elif path == "/api/schools":
            self._handle_schools(params)
        elif path == "/api/search":
            self._handle_search(params)
        elif path.startswith("/api/school/") and path.endswith("/web"):
            school_number = path.split("/")[-2]
            self._handle_school_web(school_number)
        elif path.startswith("/api/school/"):
            school_number = path.split("/")[-1]
            self._handle_school(school_number)
        elif path == "/" or path == "/index.html":
            self._serve_file("index.html", "text/html; charset=utf-8")
        elif path.endswith(".png") and "/" not in path[1:]:
            self._serve_file(path[1:], "image/png")
        else:
            # 不暴露任意文件，未知路由返回 404
            self.send_error(404, "Not Found")

    def _handle_stats(self):
        data = fetch_stats()
        self._json_response(data)

    def _handle_schools(self, params):
        data = filter_schools(params)
        self._json_response(data)

    def _handle_search(self, params):
        keyword = params.get("q", [""])[0].strip()
        if not keyword:
            self._json_response({"error": "Missing query parameter 'q'"}, 400)
            return
        results, total = search_schools(keyword)
        self._json_response({"results": results, "count": len(results), "total": total})

    def _handle_school(self, school_number):
        school = fetch_school(school_number)
        if school:
            self._json_response(school)
        else:
            self._json_response({"error": "School not found"}, 404)

    def _handle_school_web(self, school_number):
        data = fetch_school_web(school_number)
        self._json_response(data or {})

    def _json_response(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, filename, content_type):
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        if not os.path.exists(filepath):
            self.send_error(404, f"{filename} not found")
            return
        with open(filepath, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", len(content))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        """简化日志格式"""
        print(f"  [{self.log_date_time_string()}] {format % args}")


# ── 启动服务器 ─────────────────────────────────────────

def main():
    if not os.path.exists(DB_PATH):
        print(f"错误：数据库文件不存在: {DB_PATH}")
        print("请先运行 python3 init_db.py 初始化数据库")
        return

    server = http.server.HTTPServer((HOST, PORT), SchoolFinderHandler)
    print()
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║   NZ School Finder — API Server             ║")
    print("  ╠══════════════════════════════════════════════╣")
    print(f"  ║   地址: http://{HOST}:{PORT:<21}║")
    print("  ║   按 Ctrl+C 停止服务器                      ║")
    print("  ╚══════════════════════════════════════════════╝")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  服务器已停止。")
        server.server_close()


if __name__ == "__main__":
    main()
