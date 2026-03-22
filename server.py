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

        if path == "/api/search":
            self._handle_search(params)
        elif path.startswith("/api/school/") and path.endswith("/web"):
            school_number = path.split("/")[-2]
            self._handle_school_web(school_number)
        elif path.startswith("/api/school/"):
            school_number = path.split("/")[-1]
            self._handle_school(school_number)
        elif path == "/" or path == "/index.html":
            self._serve_file("index.html", "text/html; charset=utf-8")
        else:
            # 不暴露任意文件，未知路由返回 404
            self.send_error(404, "Not Found")

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
        if data:
            self._json_response(data)
        else:
            self._json_response({"error": "No web data available"}, 404)

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
