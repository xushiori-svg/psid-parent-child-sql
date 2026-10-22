from pathlib import Path
import re
import sqlite3

import pandas as pd

RAW_TXT = Path("data/raw/J366557/J366557.txt")
RAW_DO = Path("data/raw/J366557/J366557.do")
DB_FILE = Path("data/psid.db")

var_map = pd.read_csv("data/psid_variables.csv", dtype=str).fillna("")

needed = {"ER30001", "ER30002", "ER32000"}
for col in ["interview_no", "sequence_no", "relation_to_head", "age", "family_income"]:
    needed.update(v for v in var_map[col] if v)

do_text = RAW_DO.read_text(encoding="latin-1")
infix = do_text[do_text.index("infix"):do_text.index("using")]
positions = re.findall(r"(\w+)\s+(\d+)\s*-\s*(\d+)", infix)

names = []
colspecs = []
for name, first, last in positions:
    if name in needed:
        names.append(name)
        colspecs.append((int(first) - 1, int(last)))

missing = needed - set(names)
if missing:
    raise ValueError(f"Missing variables: {sorted(missing)}")

wide = pd.read_fwf(RAW_TXT, colspecs=colspecs, names=names, header=None)
print("People:", len(wide), "Variables:", len(names))

wide["pid"] = wide["ER30001"] * 1000 + wide["ER30002"]

persons = pd.DataFrame({
    "pid": wide["pid"],
    "id1968": wide["ER30001"],
    "sex": wide["ER32000"],
})

rows = []
for _, v in var_map.iterrows():
    one = pd.DataFrame({
        "pid": wide["pid"],
        "year": int(v["year"]),
        "family_id": wide[v["interview_no"]],
        "relation": wide[v["relation_to_head"]],
        "age": wide[v["age"]],
        "family_income": wide[v["family_income"]],
    })
    if v["sequence_no"] == "":
        one["seq"] = (one["relation"] > 0).astype(int)
    else:
        one["seq"] = wide[v["sequence_no"]]
    rows.append(one)

person_years = pd.concat(rows, ignore_index=True)

person_years = person_years[
    (person_years["family_id"] > 0)
    & (person_years["seq"].between(1, 20))
].copy()

person_years["role"] = "other"
person_years.loc[person_years["relation"].isin([1, 10]), "role"] = "head"
person_years.loc[person_years["relation"].isin([2, 20, 22]), "role"] = "spouse"
person_years.loc[person_years["relation"].isin([3, 30]), "role"] = "child"

person_years.loc[person_years["family_income"] >= 9999999, "family_income"] = None
person_years.loc[(person_years["age"] == 0) | (person_years["age"] >= 999), "age"] = None

print("Person-years:", len(person_years))

if DB_FILE.exists():
    DB_FILE.unlink()

conn = sqlite3.connect(DB_FILE)
persons.to_sql("persons", conn, index=False)
person_years.to_sql("person_years", conn, index=False)

conn.execute("""
CREATE TABLE families AS
SELECT
    year,
    family_id,
    MAX(family_income) AS family_income,
    COUNT(*) AS family_size
FROM person_years
GROUP BY year, family_id;
""")

conn.execute("CREATE INDEX idx_py ON person_years (year, family_id);")
conn.execute("CREATE INDEX idx_py_pid ON person_years (pid);")
conn.execute("CREATE INDEX idx_fam ON families (year, family_id);")
conn.commit()

for table in ["persons", "person_years", "families"]:
    n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(table, n)

conn.close()
print("Saved", DB_FILE)
