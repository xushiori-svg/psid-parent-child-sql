-- Average family income in each year, used to put all years on the same scale
DROP TABLE IF EXISTS year_means;

CREATE TABLE year_means AS
SELECT
    year,
    AVG(family_income) AS mean_income
FROM families
WHERE family_income > 0
GROUP BY year;

-- Parent family income in each year from 1968 to 1972
-- (income is for the year before the interview, so 1967-1971)
DROP TABLE IF EXISTS parent_income_years;

CREATE TABLE parent_income_years AS
SELECT
    pc.child_id,
    py.year,
    py.age AS parent_age,
    f.family_income,
    f.family_income / ym.mean_income AS rel_income
FROM parent_child AS pc
INNER JOIN person_years AS py
    ON pc.parent_id = py.pid
INNER JOIN families AS f
    ON py.year = f.year
    AND py.family_id = f.family_id
INNER JOIN year_means AS ym
    ON py.year = ym.year
WHERE py.year BETWEEN 1968 AND 1972
    AND py.role = 'head'
    AND f.family_income > 0;

-- One row per child: parent income in one year and the 5-year average
DROP TABLE IF EXISTS parent_income;

CREATE TABLE parent_income AS
SELECT
    child_id,
    MAX(CASE WHEN year = 1968 THEN rel_income END) AS p_inc_1968,
    AVG(rel_income) AS p_inc_avg,
    COUNT(*) AS p_years,
    MAX(CASE WHEN year = 1968 THEN parent_age END) AS parent_age_1968
FROM parent_income_years
GROUP BY child_id;
