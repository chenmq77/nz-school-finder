#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NZ School Finder — API 测试
测试 server.py 的数据库函数和 HTTP 端点
"""

import http.client
import json
import os
import sqlite3
import threading
import time
import unittest
import http.server

# 导入被测模块
import server


# ── 测试用 DB 和服务器 ────────────────────────────────

TEST_PORT = 18765  # 避免与正式服务器冲突


def setUpModule():
    """启动测试用 HTTP 服务器（后台线程）"""
    global _test_server, _test_thread
    _test_server = http.server.HTTPServer(("localhost", TEST_PORT), server.SchoolFinderHandler)
    _test_thread = threading.Thread(target=_test_server.serve_forever, daemon=True)
    _test_thread.start()
    time.sleep(0.3)


def tearDownModule():
    """关闭测试服务器"""
    _test_server.shutdown()


def api_get(path):
    """向测试服务器发送 GET 请求，返回 (status, data_dict)"""
    conn = http.client.HTTPConnection("localhost", TEST_PORT, timeout=5)
    conn.request("GET", path)
    resp = conn.getresponse()
    body = resp.read().decode("utf-8")
    conn.close()
    status = resp.status
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        data = body
    return status, data


# ══════════════════════════════════════════════════════
# 1. 数据库函数单元测试
# ══════════════════════════════════════════════════════

class TestSearchSchools(unittest.TestCase):
    """测试 search_schools() 函数"""

    def test_search_returns_list_and_total(self):
        results, total = server.search_schools("Grammar")
        self.assertIsInstance(results, list)
        self.assertIsInstance(total, int)
        self.assertGreater(total, 0)
        self.assertEqual(len(results), min(total, 50))

    def test_search_results_have_expected_fields(self):
        results, _ = server.search_schools("Auckland")
        self.assertGreater(len(results), 0)
        first = results[0]
        for field in ["school_number", "school_name", "school_type", "authority",
                      "gender_of_students", "town_city", "total_school_roll"]:
            self.assertIn(field, first)

    def test_search_no_match_returns_empty(self):
        results, total = server.search_schools("ZZZZNONEXISTENT999")
        self.assertEqual(results, [])
        self.assertEqual(total, 0)

    def test_search_respects_limit(self):
        results, total = server.search_schools("School", limit=5)
        self.assertLessEqual(len(results), 5)
        self.assertGreaterEqual(total, len(results))

    def test_search_is_case_insensitive(self):
        r1, t1 = server.search_schools("grammar")
        r2, t2 = server.search_schools("Grammar")
        self.assertEqual(t1, t2)


class TestFetchSchool(unittest.TestCase):
    """测试 fetch_school() 函数"""

    def test_fetch_existing_school(self):
        # 先搜索获取一个有效的 school_number
        results, _ = server.search_schools("Auckland Grammar")
        self.assertGreater(len(results), 0)
        num = results[0]["school_number"]

        school = server.fetch_school(num)
        self.assertIsNotNone(school)
        self.assertEqual(school["school_number"], num)
        self.assertIn("school_name", school)

    def test_fetch_nonexistent_school(self):
        school = server.fetch_school("999999")
        self.assertIsNone(school)

    def test_fetch_returns_all_49_fields(self):
        results, _ = server.search_schools("Auckland Grammar")
        num = results[0]["school_number"]
        school = server.fetch_school(num)
        # 49 数据列 + id 自增主键 = 至少 49 个字段
        self.assertGreaterEqual(len(school), 49)

    def test_fetch_school_has_category_fields(self):
        """验证 A-E 五大分类的关键字段都存在"""
        results, _ = server.search_schools("Auckland Grammar")
        num = results[0]["school_number"]
        school = server.fetch_school(num)

        # A 类: 学校身份
        for f in ["school_name", "school_number", "school_type", "authority",
                   "gender_of_students", "boarding_facilities", "school_website"]:
            self.assertIn(f, school, f"Missing A-category field: {f}")

        # B 类: 位置联系
        for f in ["street", "suburb", "town_city", "telephone", "email"]:
            self.assertIn(f, school, f"Missing B-category field: {f}")

        # C 类: 学生构成
        for f in ["total_school_roll", "european_pakeha", "maori", "pacific",
                   "asian", "melaa", "other", "international", "enrolment_scheme"]:
            self.assertIn(f, school, f"Missing C-category field: {f}")

        # D 类: 质量特色
        for f in ["equity_index_eqi", "isolation_index", "principal", "status"]:
            self.assertIn(f, school, f"Missing D-category field: {f}")

        # E 类: 行政归属
        for f in ["education_region", "territorial_authority", "general_electorate"]:
            self.assertIn(f, school, f"Missing E-category field: {f}")


# ══════════════════════════════════════════════════════
# 2. HTTP API 集成测试
# ══════════════════════════════════════════════════════

class TestSearchAPI(unittest.TestCase):
    """测试 /api/search 端点"""

    def test_search_success(self):
        status, data = api_get("/api/search?q=Grammar")
        self.assertEqual(status, 200)
        self.assertIn("results", data)
        self.assertIn("count", data)
        self.assertIn("total", data)
        self.assertGreater(data["total"], 0)

    def test_search_empty_query(self):
        status, data = api_get("/api/search?q=")
        self.assertEqual(status, 400)
        self.assertIn("error", data)

    def test_search_missing_query_param(self):
        status, data = api_get("/api/search")
        self.assertEqual(status, 400)
        self.assertIn("error", data)

    def test_search_no_results(self):
        status, data = api_get("/api/search?q=ZZZZNONEXISTENT999")
        self.assertEqual(status, 200)
        self.assertEqual(data["results"], [])
        self.assertEqual(data["total"], 0)

    def test_search_count_matches_results_length(self):
        status, data = api_get("/api/search?q=College")
        self.assertEqual(status, 200)
        self.assertEqual(data["count"], len(data["results"]))

    def test_search_total_gte_count(self):
        """total（真实总数）应 >= count（返回数量）"""
        status, data = api_get("/api/search?q=School")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(data["total"], data["count"])

    def test_search_response_content_type(self):
        conn = http.client.HTTPConnection("localhost", TEST_PORT, timeout=5)
        conn.request("GET", "/api/search?q=test")
        resp = conn.getresponse()
        resp.read()
        ct = resp.getheader("Content-Type")
        self.assertIn("application/json", ct)
        conn.close()

    def test_search_cors_header(self):
        conn = http.client.HTTPConnection("localhost", TEST_PORT, timeout=5)
        conn.request("GET", "/api/search?q=test")
        resp = conn.getresponse()
        resp.read()
        cors = resp.getheader("Access-Control-Allow-Origin")
        self.assertEqual(cors, "*")
        conn.close()


class TestSchoolDetailAPI(unittest.TestCase):
    """测试 /api/school/<number> 端点"""

    def test_fetch_existing_school(self):
        # 先搜索获取一个有效编号
        _, search_data = api_get("/api/search?q=Auckland%20Grammar")
        num = search_data["results"][0]["school_number"]

        status, data = api_get(f"/api/school/{num}")
        self.assertEqual(status, 200)
        self.assertIn("school_name", data)
        self.assertNotIn("error", data)

    def test_fetch_nonexistent_school(self):
        status, data = api_get("/api/school/999999")
        self.assertEqual(status, 404)
        self.assertIn("error", data)

    def test_fetch_returns_full_record(self):
        _, search_data = api_get("/api/search?q=Auckland%20Grammar")
        num = search_data["results"][0]["school_number"]
        status, data = api_get(f"/api/school/{num}")
        self.assertEqual(status, 200)
        # 应包含搜索结果中没有的字段（如 email, principal 等）
        self.assertIn("email", data)
        self.assertIn("principal", data)
        self.assertIn("equity_index_eqi", data)


class TestSchoolWebAPI(unittest.TestCase):
    """测试 /api/school/{num}/web 端点"""

    def test_web_data_for_ags(self):
        status, data = api_get("/api/school/54/web")
        self.assertEqual(status, 200)
        self.assertIn("subjects_count", data)
        self.assertIn("sports_count", data)
        self.assertIn("intl_tuition_annual", data)
        self.assertIn("subjects_url", data)

    def test_web_data_not_found(self):
        status, data = api_get("/api/school/99999/web")
        self.assertEqual(status, 404)


class TestStaticRoutes(unittest.TestCase):
    """测试静态路由和安全性"""

    def test_root_serves_index_html(self):
        conn = http.client.HTTPConnection("localhost", TEST_PORT, timeout=5)
        conn.request("GET", "/")
        resp = conn.getresponse()
        body = resp.read().decode("utf-8")
        self.assertEqual(resp.status, 200)
        self.assertIn("text/html", resp.getheader("Content-Type"))
        self.assertIn("NZ School Finder", body)
        conn.close()

    def test_index_html_serves(self):
        conn = http.client.HTTPConnection("localhost", TEST_PORT, timeout=5)
        conn.request("GET", "/index.html")
        resp = conn.getresponse()
        resp.read()
        self.assertEqual(resp.status, 200)
        conn.close()

    def test_unknown_route_returns_404(self):
        conn = http.client.HTTPConnection("localhost", TEST_PORT, timeout=5)
        conn.request("GET", "/some/random/path")
        resp = conn.getresponse()
        resp.read()
        self.assertEqual(resp.status, 404)
        conn.close()

    def test_db_file_not_exposed(self):
        """schools.db 不应通过 HTTP 访问"""
        conn = http.client.HTTPConnection("localhost", TEST_PORT, timeout=5)
        conn.request("GET", "/schools.db")
        resp = conn.getresponse()
        resp.read()
        self.assertEqual(resp.status, 404)
        conn.close()

    def test_server_py_not_exposed(self):
        """server.py 不应通过 HTTP 访问"""
        conn = http.client.HTTPConnection("localhost", TEST_PORT, timeout=5)
        conn.request("GET", "/server.py")
        resp = conn.getresponse()
        resp.read()
        self.assertEqual(resp.status, 404)
        conn.close()

    def test_directory_csv_not_exposed(self):
        """directory.csv 不应通过 HTTP 访问"""
        conn = http.client.HTTPConnection("localhost", TEST_PORT, timeout=5)
        conn.request("GET", "/directory.csv")
        resp = conn.getresponse()
        resp.read()
        self.assertEqual(resp.status, 404)
        conn.close()


# ══════════════════════════════════════════════════════
# 3. 前端 HTML 结构测试
# ══════════════════════════════════════════════════════

class TestHTMLStructure(unittest.TestCase):
    """测试 index.html 的关键结构"""

    @classmethod
    def setUpClass(cls):
        conn = http.client.HTTPConnection("localhost", TEST_PORT, timeout=5)
        conn.request("GET", "/")
        resp = conn.getresponse()
        cls.html = resp.read().decode("utf-8")
        conn.close()

    def test_has_search_input(self):
        self.assertIn('id="searchInput"', self.html)

    def test_has_search_input(self):
        self.assertIn('id="searchInput"', self.html)

    def test_has_search_results_container(self):
        self.assertIn('id="searchResults"', self.html)

    def test_has_eight_sections(self):
        """A-H 八个分区都存在"""
        for section_id in ["sectionA", "sectionB", "sectionC", "sectionD", "sectionE", "sectionF", "sectionG", "sectionH"]:
            self.assertIn(f'id="{section_id}"', self.html, f"Missing section: {section_id}")

    def test_has_eight_section_bodies(self):
        for body_id in ["bodyA", "bodyB", "bodyC", "bodyD", "bodyE", "bodyF", "bodyG", "bodyH"]:
            self.assertIn(f'id="{body_id}"', self.html, f"Missing body: {body_id}")

    def test_collapsible_sections_start_collapsed(self):
        """G 和 H 分区默认折叠"""
        self.assertIn('id="bodyG"', self.html)
        self.assertIn('id="bodyH"', self.html)
        import re
        body_g_match = re.search(r'class="section-body\s+collapsed"\s+id="bodyG"', self.html)
        body_h_match = re.search(r'class="section-body\s+collapsed"\s+id="bodyH"', self.html)
        self.assertIsNotNone(body_g_match, "Section G should start collapsed")
        self.assertIsNotNone(body_h_match, "Section H should start collapsed")

    def test_header_is_sticky(self):
        """Header 应为 sticky 定位"""
        self.assertIn("position: sticky", self.html)

    def test_has_current_school_tag(self):
        """当前学校名标签存在"""
        self.assertIn('id="currentSchoolTag"', self.html)

    def test_has_brand_text(self):
        """搜索栏中有 brand 文字"""
        self.assertIn('class="brand"', self.html)

    def test_no_back_button(self):
        """已移除返回搜索按钮"""
        self.assertNotIn('id="backBtn"', self.html)
        self.assertNotIn('back-btn', self.html)

    def test_no_scrollIntoView_smooth(self):
        """不应有 smooth scrollIntoView（会导致抖动）"""
        self.assertNotIn("scrollIntoView", self.html)

    def test_has_abort_controller(self):
        """应使用 AbortController 防止竞态"""
        self.assertIn("AbortController", self.html)

    def test_has_esc_function(self):
        """应有 XSS 转义函数"""
        self.assertIn("function esc(", self.html)

    def test_has_safe_url_function(self):
        """应有 URL 安全验证函数"""
        self.assertIn("function isSafeUrl(", self.html)


if __name__ == "__main__":
    unittest.main(verbosity=2)
