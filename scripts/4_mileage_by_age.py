"""Mileage by age from DVSA MOT tests (class 4 cars, normal tests).
- odometer by age: one test per vehicle in 2025 (its first test of the year)
- real miles per year: the same vehicle tested in 2023 and 2025 (difference / years between the tests)
Output: CSV files in ./out and printed tables."""
import duckdb, pathlib
W = "work"
con = duckdb.connect()
con.execute("PRAGMA threads=8; PRAGMA memory_limit='8GB'")
con.execute(f"""
CREATE TEMP TABLE t25 AS
SELECT vehicle_id, test_date, test_mileage AS m, fuel_type AS fuel, first_use_date,
       date_diff('day', first_use_date, test_date)/365.25 AS age
FROM (SELECT *, row_number() OVER (PARTITION BY vehicle_id ORDER BY test_date) rn FROM read_parquet('{W}/nt4_2025.parquet'))
WHERE rn=1 AND test_mileage BETWEEN 1 AND 400000 AND first_use_date IS NOT NULL
""")
con.execute(f"""
CREATE TEMP TABLE t23 AS
SELECT vehicle_id, test_date AS d23, test_mileage AS m23
FROM (SELECT *, row_number() OVER (PARTITION BY vehicle_id ORDER BY test_date) rn FROM read_parquet('{W}/nt4_2023.parquet'))
WHERE rn=1 AND test_mileage BETWEEN 1 AND 400000
""")
odo = con.execute("""
SELECT floor(age)::INT AS age_years, count(*) n,
       round(avg(m)) avg_odometer, round(median(m)) median_odometer,
       round(quantile_cont(m,0.25)) p25, round(quantile_cont(m,0.75)) p75
FROM t25 WHERE age >= 3 AND age < 21 GROUP BY 1 ORDER BY 1""").df()
pair = con.execute("""
SELECT floor(a.age)::INT AS age_years, count(*) n,
       round(median((a.m - b.m23) / (date_diff('day', b.d23, a.test_date)/365.25))) median_miles_per_year,
       round(avg((a.m - b.m23) / (date_diff('day', b.d23, a.test_date)/365.25))) avg_miles_per_year
FROM t25 a JOIN t23 b USING (vehicle_id)
WHERE date_diff('day', b.d23, a.test_date) BETWEEN 600 AND 860 AND a.m >= b.m23 AND a.m - b.m23 < 120000
  AND a.age >= 5 AND a.age < 21
GROUP BY 1 ORDER BY 1""").df()
fuel = con.execute("""
SELECT CASE WHEN fuel IN ('PE','PETROL') THEN 'Petrol' WHEN fuel IN ('DI','DIESEL') THEN 'Diesel' WHEN fuel IN ('EL','ELECTRIC') THEN 'Electric'
            WHEN fuel IN ('HY','ED','GB','HYBRID ELECTRIC (CLEAN)') THEN 'Hybrid' ELSE 'Other' END AS fuel_group,
       count(*) n, round(median((a.m - b.m23) / (date_diff('day', b.d23, a.test_date)/365.25))) median_miles_per_year
FROM t25 a JOIN t23 b USING (vehicle_id)
WHERE date_diff('day', b.d23, a.test_date) BETWEEN 600 AND 860 AND a.m >= b.m23 AND a.m - b.m23 < 120000 AND a.age>=5 AND a.age<21
GROUP BY 1 ORDER BY n DESC""").df()
allpair = con.execute("""
SELECT count(*) n, round(median((a.m - b.m23) / (date_diff('day', b.d23, a.test_date)/365.25))) med,
       round(avg((a.m - b.m23) / (date_diff('day', b.d23, a.test_date)/365.25))) avg
FROM t25 a JOIN t23 b USING (vehicle_id)
WHERE date_diff('day', b.d23, a.test_date) BETWEEN 600 AND 860 AND a.m >= b.m23 AND a.m - b.m23 < 120000 AND a.age>=5 AND a.age<21""").df()
fuels = con.execute("SELECT fuel, count(*) FROM t25 GROUP BY 1 ORDER BY 2 DESC LIMIT 10").df()
odo.to_csv(pathlib.Path('out')/'odometer_by_age_2025.csv', index=False)
pair.to_csv(pathlib.Path('out')/'miles_per_year_by_age_2023_2025.csv', index=False)
fuel.to_csv(pathlib.Path('out')/'miles_per_year_by_fuel_2023_2025.csv', index=False)
print(odo.to_string()); print(pair.to_string()); print(fuel.to_string()); print(allpair.to_string()); print(fuels.to_string())
