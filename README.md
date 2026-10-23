# Matching Parents and Children with SQL in Python

Code for: [Matching Parents and Children with SQL in Python](https://xushiori-svg.github.io/claraxu_6400project/blog/posts/post6/).

The project uses SQL inside Python (`sqlite3`) to match children to their parents in the Panel Study of Income Dynamics (PSID). It then builds parent and child income measures and estimates the intergenerational elasticity (IGE), comparing one year of income with income averaged over several years.

## Data

Panel Study of Income Dynamics (PSID), public use data, 1968–2023, from the [PSID Data Center](https://simba.isr.umich.edu/data/data.aspx). A free account is needed.

The extract has 216 variables for 85,536 people:

- `ER30001` and `ER30002`: 1968 interview number and person number. Together they give each person a fixed ID.
- `ER32000`: sex.
- For each year: interview number (the family ID for that year), sequence number, relation to head, and age.
- For each year: total family money income.

`data/psid_variables.csv` lists the PSID variable name of each item in each year.

The PSID conditions of use do not allow sharing the data, so `data/raw/` is empty in this repository.

## Getting the data

1. Log in to the PSID Data Center and open Variable Search.
2. Check *PSID Family-level* and *PSID Individual-level*, click *Check all years*, and search by *Variable name* with *Any words (OR)*.
3. Paste the names from `data/psid_variables.csv`, plus `ER30002 ER32000`, and add the results to the cart. About 40 names per search works best.
4. Check out with *ASCII Data With Stata Statements* and *All Individuals*.
5. Unzip the download into `data/raw/`. My download is `data/raw/J366557/` with `J366557.txt` and `J366557.do`. If your job number is different, change `RAW_TXT` and `RAW_DO` at the top of `scripts/01_load_to_sqlite.py`.

The Data Center adds some ID variables on its own, so the cart will have more than 216 variables. The script reads only the ones it needs and stops if any are missing.

## Folder structure

```
psid-parent-child-sql/
├── data/
│   ├── psid_variables.csv     PSID variable names by year
│   ├── raw/                   PSID download (not shared)
│   ├── psid.db                SQLite database, made by 01
│   └── clean/                 matched sample, made by 02
├── sql/
│   ├── 01_parent_child.sql    match children to parents
│   ├── 02_parent_income.sql   parent income: 1968 and 1968–1972 average
│   └── 03_child_income.sql    child income by age and ages 35–44 average
├── scripts/
│   ├── 01_load_to_sqlite.py   read the PSID file, reshape to one row per person-year, save to SQLite
│   ├── 02_match_with_sql.py   run the SQL files, save the matched sample
│   └── 03_estimate_ige.py     estimate the IGE and rank slope, make figures
└── results/                   tables and figures
```

## How to run

You need Python 3 with `pandas`, `numpy` and `matplotlib`. `sqlite3` comes with Python.

From the project folder in a terminal:

```
pip install pandas numpy matplotlib
python scripts/01_load_to_sqlite.py
python scripts/02_match_with_sql.py
python scripts/03_estimate_ige.py
```

Or in the RStudio console, with the project open:

```r
library(reticulate)
py_require(c("pandas", "numpy", "matplotlib"))
py_run_file("scripts/01_load_to_sqlite.py")
py_run_file("scripts/02_match_with_sql.py")
py_run_file("scripts/03_estimate_ige.py")
```

Step 1 reads a 180 MB text file and takes a minute or two.

## Output

| File | What it shows |
|:--|:--|
| `results/ige_table.csv` | Log IGE and rank slope with one-year and averaged income, same 1,352 children in every row |
| `results/lifecycle_estimates.csv` | Estimates when child income is measured at each age from 25 to 45 |
| `results/sample_description.csv` | Sample sizes and basic facts |
| `results/fig1_lifecycle.png` | Figure 1 in the post |
| `results/fig2_rank_rank.png` | Child rank by parent rank (not used in the post) |

Main result: one year of income for both generations gives a log IGE of 0.31. A 1968–1972 parent average and a child average at ages 35–44 give 0.48.

## Definitions

- **Child**: son or daughter of the household head in any year 1968–1972, born 1952–1968, from the original SRC sample (1968 interview number below 3000). Children who lived with more than one head in these years are dropped.
- **Parent**: the head of the child's family in 1968–1972.
- **Income**: total family money income divided by the average PSID family income in that year. Only positive incomes are used. The 1994–1995 code 9999999 is treated as missing.
- **Parent income**: the 1968 value, and the average over 1968–1972 (at least 3 years).
- **Child income**: family income when the child is head or spouse. One year at a given age (that age or one year older, since the PSID is every two years after 1997), and the average at ages 35–44 (at least 3 years).
- **Log IGE**: slope of log child income on log parent income.
- **Rank slope**: slope of child percentile rank on parent percentile rank, ranks computed within the sample.
- Robust (HC1) standard errors. No survey weights.
