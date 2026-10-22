-- Match each child to the head of the family the child lived in, 1968-1972.
-- A child and a parent are in the same family when they share the same
-- year and the same family interview number.

DROP TABLE IF EXISTS parent_child;

CREATE TABLE parent_child AS
WITH pairs AS (
    SELECT
        c.pid AS child_id,
        p.pid AS parent_id,
        MIN(c.year - c.age) AS child_birth_year,
        COUNT(*) AS years_together
    FROM person_years AS c
    INNER JOIN person_years AS p
        ON c.year = p.year
        AND c.family_id = p.family_id
    WHERE c.role = 'child'
        AND p.role = 'head'
        AND c.year BETWEEN 1968 AND 1972
    GROUP BY c.pid, p.pid
),
one_parent AS (
    -- drop children who lived with more than one head in these years
    SELECT child_id
    FROM pairs
    GROUP BY child_id
    HAVING COUNT(*) = 1
)
SELECT pairs.*
FROM pairs
INNER JOIN one_parent
    ON pairs.child_id = one_parent.child_id
INNER JOIN persons AS s
    ON pairs.child_id = s.pid
WHERE s.id1968 < 3000                      -- core SRC sample
    AND pairs.child_birth_year BETWEEN 1952 AND 1968;
