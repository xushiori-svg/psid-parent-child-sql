from pathlib import Path
import sqlite3

import pandas as pd

DB_FILE = Path("data/psid.db")
CLEAN_DIR = Path("data/clean")
CLEAN_DIR.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DB_FILE)

for sql_file in ["sql/01_parent_child.sql",
                 "sql/02_parent_income.sql",
                 "sql/03_child_income.sql"]:
    print("Running", sql_file)
    conn.executescript(Path(sql_file).read_text())

summary = pd.read_sql("""
SELECT
    COUNT(*) AS children,
    COUNT(DISTINCT parent_id) AS parents,
    AVG(years_together) AS avg_years_together
FROM parent_child;
""", conn)
print(summary)

matched = pd.read_sql("""
SELECT
    pc.child_id,
    pc.parent_id,
    pc.child_birth_year,
    s.sex AS child_sex,
    p.p_inc_1968,
    p.p_inc_avg,
    p.p_years,
    p.parent_age_1968,
    c.c_inc_avg,
    c.c_years
FROM parent_child AS pc
LEFT JOIN persons AS s
    ON pc.child_id = s.pid
LEFT JOIN parent_income AS p
    ON pc.child_id = p.child_id
LEFT JOIN child_income AS c
    ON pc.child_id = c.child_id;
""", conn)

child_years = pd.read_sql("SELECT * FROM child_income_years;", conn)

conn.close()

matched.to_csv(CLEAN_DIR / "matched_sample.csv", index=False)
child_years.to_csv(CLEAN_DIR / "child_income_years.csv", index=False)
print("Matched children:", len(matched))
