"""
init_db.py — 读取 directory.csv，创建 SQLite 数据库 schools.db，导入全部学校数据。

CSV 共 49 列，按家长选校决策流程分为 A-E 五大类：
  A. 学校身份概览（7列）
  B. 位置与联系方式（10列）
  C. 学生规模与构成（9列）
  D. 学校质量与特色（11列）
  E. 行政与区域归属（12列）
"""

import csv
import sqlite3
import os

# ============================================================
# 列名映射：CSV 原始列名 → SQLite 下划线命名
# 每个映射标注所属分类（A-E）
# ============================================================
COLUMN_MAPPING = [
    # ----- A. 学校身份概览（7列）-----
    ("School Number",           "school_number"),           # A2 学校编号
    ("School Name",             "school_name"),             # A1 学校名称
    ("School Type",             "school_type"),             # A3 学校类型
    ("Authority",               "authority"),               # A4 管理性质
    ("Gender of Students",      "gender_of_students"),      # A5 学生性别
    ("Boarding Facilities",     "boarding_facilities"),     # A6 寄宿设施
    ("School Website",          "school_website"),          # A7 学校官网

    # ----- B. 位置与联系方式（10列）-----
    ("Street",                  "street"),                  # B1 街道地址
    ("Suburb",                  "suburb"),                  # B2 区/街区
    ("Town / City",             "town_city"),               # B3 城市
    ("Postal Address",          "postal_address"),          # B4 邮政地址
    ("Postal Address Suburb",   "postal_address_suburb"),   # B5 邮政区
    ("Postal Address City",     "postal_address_city"),     # B6 邮政城市
    ("Postal Code",             "postal_code"),             # B7 邮编
    ("Urban/Rural",             "urban_rural"),             # B8 城乡属性
    ("Telephone",               "telephone"),               # B9 电话
    ("Email^",                  "email"),                   # B10 邮箱（去掉 ^ 符号）

    # ----- C. 学生规模与构成（9列）-----
    ("Total School Roll",       "total_school_roll"),       # C1 学校总人数
    ("European / Pākehā",       "european_pakeha"),         # C2 欧洲裔/白人
    ("Māori",                   "maori"),                   # C3 毛利裔
    ("Pacific",                 "pacific"),                 # C4 太平洋岛裔
    ("Asian",                   "asian"),                   # C5 亚裔
    ("MELAA",                   "melaa"),                   # C6 中东/拉丁/非洲裔
    ("Other",                   "other"),                   # C7 其他族裔
    ("International",           "international"),           # C8 国际学生
    ("Enrolment Scheme",        "enrolment_scheme"),        # C9 招生计划

    # ----- D. 学校质量与特色（11列）-----
    ("Equity Index (EQI)",      "equity_index_eqi"),        # D1 公平指数
    ("Isolation Index",         "isolation_index"),         # D2 偏远指数
    ("Language of Instruction", "language_of_instruction"), # D3 教学语言
    ("Donations",               "donations"),               # D4 捐赠政策
    ("KME Peak Body",           "kme_peak_body"),           # D5 毛利教育机构
    ("Latitude",                "latitude"),                # D6 纬度
    ("Longitude",               "longitude"),               # D7 经度
    ("Principal*",              "principal"),               # D8 校长（去掉 * 符号）
    ("Definition",              "definition"),              # D9 办学定义
    ("Status",                  "status"),                  # D10 运营状态
    ("Cohort Entry",            "cohort_entry"),            # D11 群体入学

    # ----- E. 行政与区域归属（12列）-----
    ("Education Region",        "education_region"),        # E1 教育大区
    ("Takiwā",                  "takiwa"),                  # E2 毛利语区域
    ("Territorial Authority",   "territorial_authority"),   # E3 领土管理局
    ("Regional Council",        "regional_council"),        # E4 区域议会
    ("Local Office",            "local_office"),            # E5 地方办事处
    ("General Electorate",      "general_electorate"),      # E6 普通选区
    ("Māori Electorate",        "maori_electorate"),        # E7 毛利选区
    ("Neighbourhood (SA2 code)","neighbourhood_sa2_code"),  # E8 社区编码
    ("Neighbourhood (SA2)",     "neighbourhood_sa2"),       # E9 社区名称
    ("Ward",                    "ward"),                    # E10 地方选区
    ("Community of Learning ID","community_of_learning_id"),# E11 学习社区ID
    ("Community of Learning Name","community_of_learning_name"), # E12 学习社区名称
]

# 从映射表中提取原始列名和数据库列名
CSV_COLUMNS = [pair[0] for pair in COLUMN_MAPPING]
DB_COLUMNS  = [pair[1] for pair in COLUMN_MAPPING]


def create_table(cursor):
    """重建 schools 表，全部列使用 TEXT 类型以保留原始数据。"""
    col_defs = ",\n    ".join(f"{col} TEXT" for col in DB_COLUMNS)
    sql = f"""
    CREATE TABLE schools (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        {col_defs}
    )
    """
    cursor.execute("DROP TABLE IF EXISTS schools")
    cursor.execute(sql)


def import_data(csv_path, db_path):
    """读取 CSV 并导入 SQLite 数据库。"""

    if not os.path.exists(csv_path):
        print(f"错误：CSV 文件不存在 → {csv_path}")
        return

    # 先验证 CSV 表头，再操作数据库（避免破坏现有数据）
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            print("错误：CSV 表头为空或无法解析。请确认文件格式为标准 CSV。")
            return

        # 规范化表头（去除首尾空白）
        reader.fieldnames = [h.strip() if isinstance(h, str) else h for h in reader.fieldnames]
        csv_headers = reader.fieldnames

        # 检查 CSV 列名是否都能匹配（49 列）— 验证在建表之前
        missing = [col for col in CSV_COLUMNS if col not in csv_headers]
        if missing:
            print(f"错误：CSV 中缺少以下必需列，无法继续导入：{missing}")
            return

    inserted = 0
    skipped = 0
    errors = []
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 表头验证通过后才重建表
        create_table(cursor)

        # 重新读取 CSV 导入数据
        with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            reader.fieldnames = [h.strip() if isinstance(h, str) else h for h in reader.fieldnames]
            csv_headers = reader.fieldnames

            extra = [col for col in csv_headers if col and col not in CSV_COLUMNS]
            if extra:
                print(f"提示：CSV 中有未映射的列（将忽略）：{extra}")

            # 准备 INSERT 语句
            placeholders = ", ".join(["?"] * len(DB_COLUMNS))
            col_names = ", ".join(DB_COLUMNS)
            insert_sql = f"INSERT INTO schools ({col_names}) VALUES ({placeholders})"

            for row_num, row in enumerate(reader, start=2):  # 第2行开始（第1行是表头）
                try:
                    # 按映射顺序提取每列的值，空字符串保留为空字符串，None 保留为 None
                    values = [row.get(csv_col) for csv_col in CSV_COLUMNS]
                    cursor.execute(insert_sql, values)
                    inserted += 1
                except Exception as e:
                    skipped += 1
                    errors.append(f"  第 {row_num} 行：{e}")

        conn.commit()
    finally:
        if conn is not None:
            conn.close()

    # ---- 打印导入统计信息 ----
    print("=" * 50)
    print("  学校数据库导入完成")
    print("=" * 50)
    print(f"  CSV 文件：{csv_path}")
    print(f"  数据库  ：{db_path}")
    print(f"  表名    ：schools")
    print(f"  列数    ：{len(DB_COLUMNS)} 列（+ 1 自增主键）")
    print("-" * 50)
    print(f"  成功导入：{inserted} 条记录")
    if skipped > 0:
        print(f"  跳过    ：{skipped} 条记录")
        for err in errors[:10]:  # 最多显示10条错误
            print(err)
    print("-" * 50)

    # 验证查询
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM schools")
    count = cursor.fetchone()[0]
    print(f"  数据库验证：schools 表共 {count} 条记录")

    # 验证列数/字段覆盖（49 列）
    cursor.execute("PRAGMA table_info(schools)")
    cols = [r[1] for r in cursor.fetchall()]  # r[1] 为列名
    # 排除自增主键 id
    data_cols = [c for c in cols if c != "id"]
    if len(data_cols) != len(DB_COLUMNS) or any(c not in data_cols for c in DB_COLUMNS):
        missing_db = [c for c in DB_COLUMNS if c not in data_cols]
        extra_db = [c for c in data_cols if c not in DB_COLUMNS]
        print("  [警告] 数据表列结构与预期不一致，可能影响查询脚本：")
        print(f"    预期数据列：{len(DB_COLUMNS)}，实际数据列：{len(data_cols)}")
        if missing_db:
            print(f"    缺失列：{missing_db}")
        if extra_db:
            print(f"    额外列：{extra_db}")

    # 抽样展示
    cursor.execute("SELECT school_number, school_name, school_type, town_city FROM schools LIMIT 3")
    rows = cursor.fetchall()
    print("\n  前 3 条数据预览：")
    print(f"  {'编号':<8} {'学校名称':<35} {'类型':<25} {'城市'}")
    print(f"  {'-'*8} {'-'*35} {'-'*25} {'-'*15}")
    for r in rows:
        print(f"  {r[0] or '':<8} {r[1] or '':<35} {r[2] or '':<25} {r[3] or ''}")

    print("=" * 50)
    conn.close()


def ensure_school_fees_table(db_path):
    """Create school_fees table if it doesn't exist, and migrate existing data from school_web_data."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table (idempotent)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS school_fees (
            school_number  INTEGER NOT NULL,
            year           INTEGER NOT NULL,
            tuition_annual REAL,
            homestay_weekly REAL,
            fees_url       TEXT,
            crawled_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (school_number, year)
        )
    """)

    # Migrate existing fee data from school_web_data (skip if already migrated)
    cursor.execute("""
        SELECT school_number, intl_tuition_annual, intl_homestay_weekly,
               intl_fees_url, intl_fees_year, crawled_at
        FROM school_web_data
        WHERE intl_tuition_annual IS NOT NULL
    """)
    rows = cursor.fetchall()
    migrated = 0
    for row in rows:
        school_num, tuition, homestay, url, year, crawled = row
        if not year:
            continue  # skip records without a year (e.g. school 54)
        # Only insert if not already present
        cursor.execute(
            "SELECT 1 FROM school_fees WHERE school_number = ? AND year = ?",
            (school_num, year),
        )
        if not cursor.fetchone():
            cursor.execute(
                """INSERT INTO school_fees (school_number, year, tuition_annual,
                   homestay_weekly, fees_url, crawled_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (school_num, year, tuition, homestay, url, crawled),
            )
            migrated += 1

    conn.commit()
    conn.close()

    print("=" * 50)
    print("  school_fees 表初始化完成")
    print(f"  从 school_web_data 迁移了 {migrated} 条费用记录")
    print("=" * 50)


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "directory.csv")
    db_path  = os.environ.get(
        "SCHOOLS_DB",
        os.path.join(base_dir, "schools.db")
    )

    import_data(csv_path, db_path)
    ensure_school_fees_table(db_path)
