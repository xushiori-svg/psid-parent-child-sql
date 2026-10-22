# Matching Parents and Children with SQL in Python (PSID)

Question: How strongly is a child's income as an adult linked to their parents' income, and how does the answer change when income is measured in one year or averaged over several years?

This repository has the code for Blog Post 6. It uses SQL inside Python (`sqlite3`) to match children to their parents in the Panel Study of Income Dynamics (PSID), builds parent and child income measures, and estimates the intergenerational elasticity (IGE) and the rank-rank slope.

## Data

- **Panel Study of Income Dynamics (PSID)**, public use data, 1968-2023, from the PSID Data Center (https://simba.isr.umich.edu/data/data.aspx). A free account is required.
- Variables (216 in total, listed by year in `data/psid_variables.csv`):
  - `ER30001` 1968 interview number and `ER30002` person number (together they identify a person)
  - `ER32000` sex
  - for each year: interview number (family ID), sequence number, relation to head, age
  - for each year: total family money income (from the family files)

The PSID conditions of use do not allow sharing the data, so `data/raw/` is empty in this repository. Follow the steps below to download your own copy.

## How to download the data

1. Register and log in at the PSID Data Center.
2. Go to Variable Search. Check *PSID Family-level* and *PSID Individual-level*, click *Check all years*, choose *Variable name* and *Any words (OR)*.
3. Paste the variable names from `data/psid_variables.csv` (plus `ER30002 ER32000`) and add all results to the cart. Searching about 40 names at a time works better than all at once.
4. Check out with these options: *ASCII Data With Stata Statements*, *All Individuals*, zip file.
5. Put the zip file (or the unzipped folder, e.g. `J366557/`) in `data/raw/`.

The Data Center adds some ID variables on its own, so the cart may have more than 216 variables. The script only reads the ones it needs and stops with a message if any are missing.

## Folder structure

```
psid-parent-child-sql/
├── data/
│   ├── psid_variables.csv   PSID variable names for each year
│   ├── raw/                 PSID download goes here (not shared)
│   ├── psid.db              SQLite database, created by 01
│   └── clean/               matched sample, created by 02
├── sql/
│   ├── 01_parent_child.sql  match children to parents
│   ├── 02_parent_income.sql parent income, one year and 5-year average
│   └── 03_child_income.sql  child income by age and ages 35-44 average
├── scripts/
│   ├── 01_load_to_sqlite.py read the PSID file, reshape to long, save to SQLite
│   ├── 02_match_with_sql.py run the SQL files, save the matched sample
│   └── 03_estimate_ige.py   IGE and rank-rank estimates, figures
└── results/                 tables and figures
```

## How to reproduce

1. Python 3 with `pandas`, `numpy` and `matplotlib` (`sqlite3` comes with Python):

   ```
   pip install pandas numpy matplotlib
   ```

2. Download the data as described above.

3. From the project folder, run the scripts in order:

   ```
   python scripts/01_load_to_sqlite.py
   python scripts/02_match_with_sql.py
   python scripts/03_estimate_ige.py
   ```

All tables and figures in `results/` are written by the code.

## Definitions

- **Child**: a person listed as son or daughter of the household head in any year from 1968 to 1972, born 1952-1968, from the core SRC sample (1968 interview number below 3000). Children who lived with more than one head in these years are dropped.
- **Parent**: the head of the child's family in 1968-1972.
- **Income**: total family money income. Each year's income is divided by the average family income in the PSID that year, so different years are on the same scale. Only positive incomes are used.
- **Parent income**: income in the 1968 survey (one year), and the average over the 1968-1972 surveys (at least 3 years).
- **Child income**: family income when the child is head or spouse of their own family. One year at a given age (that age or one year older, because the PSID is every two years after 1997), and the average over ages 35-44 (at least 3 years).
- **Log-log IGE**: slope of log(child income) on log(parent income).
- **Rank-rank slope**: slope of the child's percentile rank on the parent's percentile rank, with ranks computed inside the sample.
- The main table uses one common sample (1,352 children) with income at age 27, at age 40, and at least 3 years at ages 35-44. Standard errors are robust (HC1). No survey weights are used.
