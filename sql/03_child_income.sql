-- Child family income as an adult, when the child is head or spouse
-- of their own family, ages 25 to 50
DROP TABLE IF EXISTS child_income_years;

CREATE TABLE child_income_years AS
SELECT
    pc.child_id,
    py.year,
    py.age,
    f.family_income,
    f.family_income / ym.mean_income AS rel_income
FROM parent_child AS pc
INNER JOIN person_years AS py
    ON pc.child_id = py.pid
INNER JOIN families AS f
    ON py.year = f.year
    AND py.family_id = f.family_id
INNER JOIN year_means AS ym
    ON py.year = ym.year
WHERE py.role IN ('head', 'spouse')
    AND py.age BETWEEN 25 AND 50
    AND f.family_income > 0;

-- One row per child: average income at ages 35-44
DROP TABLE IF EXISTS child_income;

CREATE TABLE child_income AS
SELECT
    child_id,
    AVG(CASE WHEN age BETWEEN 35 AND 44 THEN rel_income END) AS c_inc_avg,
    COUNT(CASE WHEN age BETWEEN 35 AND 44 THEN 1 END) AS c_years
FROM child_income_years
GROUP BY child_id;
