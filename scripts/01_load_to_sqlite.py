# Read the PSID Data Center extract and save it as a small SQLite database.
# Run from the project folder: python scripts/01_load_to_sqlite.py

from pathlib import Path
import re
import sqlite3
import zipfile

import pandas as pd

RAW_DIR = Path("data/raw")
DB_FILE = Path("data/psid.db")


def read_psid_extract():
    # The Data Center gives a zip with a fixed-width text file (.txt) and a
    # Stata do-file (.do). The do-file says where each variable sits in a line,
    # for example "ER30001  2 - 5" means columns 2 to 5.
    # works with the zip file or with the unzipped folder
    zips = list(RAW_DIR.glob("*.zip"))
    if zips:
        z = zipfile.ZipFile(zips[0])
        do_name = [n for n in z.namelist() if n.endswith(".do") and "formats" not in n][0]
        txt_name = [n for n in z.namelist() if n.endswith(".txt")][0]
        do_text = z.read(do_name).decode("latin-1")
        txt_file = z.open(txt_name)
    else:
        do_file = [f for f in RAW_DIR.rglob("*.do") if "formats" not in f.name][0]
        txt_name = do_file.with_suffix(".txt")
        do_text = do_file.read_text(encoding="latin-1")
        txt_file = open(txt_name, "rb")
    print("Reading", txt_name)

    infix = do_text[do_text.lower().index("infix"):do_text.lower().index("using")]
    positions = re.findall(r"(\w+)\s+(\d+)\s*-\s*(\d+)", infix)

    # keep only the variables we need
    var_map = pd.read_csv("data/psid_variables.csv", dtype=str).fillna("")
    needed = {"ER30001", "ER30002", "ER32000"}
    for col in ["interview_no", "sequence_no", "relation_to_head", "age", "family_income"]:
        needed.update(v for v in var_map[col] if v)

    names, colspecs = [], []
    for name, first, last in positions:
        if name.upper() in needed:
            names.append(name.upper())
            colspecs.append((int(first) - 1, int(last)))
    missing = needed - set(names)
    if missing:
        raise ValueError(f"These variables are not in the download: {sorted(missing)}")

    data = pd.read_fwf(txt_file, colspecs=colspecs, names=names, header=None)
    txt_file.close()
    return data


wide = read_psid_extract().copy()
wide.columns = [c.upper() for c in wide.columns]
print("Raw extract:", wide.shape[0], "people,", wide.shape[1], "columns")

# variable names for each year (from the PSID cross-year index)
var_map = pd.read_csv("data/psid_variables.csv", dtype=str).fillna("")

# one row per person
# person id = 1968 interview number * 1000 + person number
wide["pid"] = wide["ER30001"] * 1000 + wide["ER30002"]
persons = pd.DataFrame({
    "pid": wide["pid"],
    "id1968": wide["ER30001"],
    "sex": wide["ER32000"],
})

# one row per person and year (wide -> long)
rows = []
for _, v in var_map.iterrows():
    year = int(v["year"])
    one = pd.DataFrame({
        "pid": wide["pid"],
        "year": year,
        "family_id": wide[v["interview_no"]],
        "relation": wide[v["relation_to_head"]],
        "age": wide[v["age"]],
        "family_income": wide[v["family_income"]],
    })
    # 1968 has no sequence number; a person was in a 1968 family
    # if their relation to head is not 0
    if v["sequence_no"] == "":
        one["seq"] = (one["relation"] > 0).astype(int)
    else:
        one["seq"] = wide[v["sequence_no"]]
    rows.append(one)

person_years = pd.concat(rows, ignore_index=True)

# keep people who actually lived in a PSID family that year (sequence 1-20)
person_years = person_years[
    (person_years["family_id"] > 0)
    & (person_years["seq"] >= 1)
    & (person_years["seq"] <= 20)
]

# the codes for relation to head changed in 1983 (1 -> 10, 2 -> 20, 3 -> 30)
person_years["role"] = "other"
person_years.loc[person_years["relation"].isin([1, 10]), "role"] = "head"
person_years.loc[person_years["relation"].isin([2, 20, 22]), "role"] = "spouse"
person_years.loc[person_years["relation"].isin([3, 30]), "role"] = "child"

# 9999999 is a missing value code for family income in 1994 and 1995
person_years.loc[person_years["family_income"] >= 9999999, "family_income"] = None

# age 0 or 999 means missing
person_years.loc[(person_years["age"] == 0) | (person_years["age"] >= 999), "age"] = None

print("Person-year rows:", len(person_years))

if DB_FILE.exists():
    DB_FILE.unlink()

conn = sqlite3.connect(DB_FILE)
persons.to_sql("persons", conn, index=False)
person_years.to_sql("person_years", conn, index=False)

# family table: one row per family and year
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

for t in ["persons", "person_years", "families"]:
    n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(t, n)

conn.close()
print("Saved", DB_FILE)
