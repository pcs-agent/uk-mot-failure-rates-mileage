# Mileage going backwards at the MOT, Great Britain 2022-2025.
# Data: DVSA anonymised MOT tests and results 2022, 2023, 2024, 2025. Class 4 normal tests with a result of Pass,
# Fail or Pass with rectification at the station, mileage above zero, linked by vehicle id.
# A "drop" is a reading at least 1,000 miles lower than the vehicle's previous MOT reading. Each drop is classified
# using the readings either side of it, in this order:
#   tiny      the new reading is under 1,000 (usually an unreadable odometer typed as a token number)
#   spike     the earlier reading was the odd one out: the reading before it is no higher than the new one
#   dip       the new reading was the odd one out: the next reading is back at or above the earlier one
#   unit      the new reading is the earlier one divided by 1.609 plus normal driving (km and miles mixed up)
#   rollover  a 5-digit odometer that passed 99,999 and started again
#   unit also when the new reading matches the earlier one converted from km to miles plus the car's own driving rate
#   digit     the new reading is about a tenth of the earlier one plus normal driving (a digit missing)
#   reset     the new reading is under 10,000 and under a tenth of the earlier one (often a new or replacement instrument cluster)
#   stayed    the reading went down and the next MOT reading was still below the earlier one
#   open      no later reading yet to tell (mostly drops at the vehicle's last test in the data)
# "stayed" is the measure used for the headline figures: the mileage went backwards and did not catch up.
import duckdb, time, os
t0 = time.time()
W = "work"
O = "out/clocking_classes"
os.makedirs(O, exist_ok=True)
con = duckdb.connect(f"{W}/clocking.duckdb")
con.execute("PRAGMA threads=12; PRAGMA memory_limit='9GB'; PRAGMA temp_directory='work/tmp'; PRAGMA preserve_insertion_order=false")
def log(*a): print(*a, round(time.time() - t0), "s", flush=True)

con.execute("CREATE OR REPLACE TABLE r AS " + " UNION ALL ".join(
    f"""SELECT CAST(vehicle_id AS BIGINT) v, CAST(test_date AS DATE) d, CAST(test_mileage AS BIGINT) m,
        postcode_area area, make, model, fuel_type fuel, CAST(first_use_date AS DATE) fu
        FROM '{W}/full_{y}.parquet' WHERE test_mileage > 0""" for y in (2022, 2023, 2024, 2025)))
log("readings", con.execute("SELECT count(*), count(DISTINCT v) FROM r").fetchone())
# one reading per vehicle per day (the highest, so two entries on the same day never count as a drop)
con.execute("""CREATE OR REPLACE TABLE s AS
SELECT v, d, max(m) m, any_value(area) area, any_value(make) make, any_value(model) model, any_value(fuel) fuel, any_value(fu) fu
FROM r GROUP BY v, d""")
con.execute("DROP TABLE r")
con.execute("""CREATE OR REPLACE TABLE q AS
SELECT *, lag(m) OVER w m_prev, lag(d) OVER w d_prev, lag(area) OVER w area_prev, lag(m, 2) OVER w m_prev2, lag(d, 2) OVER w d_prev2,
       lead(m) OVER w m_next, lead(d) OVER w d_next, row_number() OVER w k, count(*) OVER (PARTITION BY v) n
FROM s WINDOW w AS (PARTITION BY v ORDER BY d)""")
con.execute("DROP TABLE s")
log("tests", con.execute("SELECT count(*), count(DISTINCT v) FROM q").fetchone())
log("vehicles by readings", con.execute("SELECT n, count(*) FROM (SELECT v, any_value(n) n FROM q GROUP BY v) GROUP BY n ORDER BY n").fetchall())

# transitions: every test with a previous reading. confirmable = there is also a later reading.
con.execute(r"""CREATE OR REPLACE TABLE tr AS
SELECT v, d, m, m_prev, m_prev2, m_next, d_prev, d_prev2, d_next, area, area_prev, make, model, fuel, fu,
  year(d) yr, date_diff('day', d_prev, d) gap, (date_diff('day', fu, d) / 365.25) age, m_next IS NOT NULL conf,
  CASE WHEN m > m_prev - 1000 THEN NULL
    WHEN m < 1000 THEN 'tiny'
    WHEN m_prev2 IS NOT NULL AND m_prev2 <= m AND (m_next IS NULL OR m_next >= m) THEN 'spike'
    WHEN m_next IS NOT NULL AND m_next >= m_prev THEN 'dip'
    WHEN m >= m_prev / 1.609344 * 0.995 AND m <= m_prev / 1.609344 + 20 * date_diff('day', d_prev, d) + 500 THEN 'unit'
    WHEN m_next IS NOT NULL AND abs(m - (m_prev / 1.609344 + (m_next - m) / greatest(date_diff('day', d, d_next), 1) * date_diff('day', d_prev, d)))
         <= greatest(1500, 0.06 * m) THEN 'unit'
    WHEN m_prev2 IS NOT NULL AND m_prev2 <= m_prev AND abs(m - (m_prev / 1.609344 + (m_prev - m_prev2) / 1.609344 / greatest(date_diff('day', d_prev2, d_prev), 1) * date_diff('day', d_prev, d)))
         <= greatest(1500, 0.06 * m) THEN 'unit'
    WHEN m_prev BETWEEN 90000 AND 99999 AND m + 100000 - m_prev BETWEEN 0 AND 40 * date_diff('day', d_prev, d) THEN 'rollover'
    WHEN m >= m_prev / 10 * 0.95 AND m <= m_prev / 10 + 20 * date_diff('day', d_prev, d) + 500 THEN 'digit'
    WHEN m < 10000 AND m < 0.1 * m_prev THEN 'reset'
    WHEN m_next IS NOT NULL THEN 'stayed'
    ELSE 'open' END cls
FROM q WHERE m_prev IS NOT NULL""")
con.execute("DROP TABLE q")
log("transitions", con.execute("SELECT count(*), sum(conf::INT) FROM tr").fetchone())

def out(name, sql):
    df = con.execute(sql).df()
    df.to_csv(f"{O}/{name}.csv", index=False)
    print(f"--- {name} ({len(df)} rows)")
    print(df.head(40).to_string())
    return df

out("00_drops_by_class", """SELECT cls, count(*) drops, count(DISTINCT v) vehicles, round(median(m_prev - m)) median_drop,
  round(100.0 * count(*) / sum(count(*)) OVER (), 2) pct FROM tr WHERE cls IS NOT NULL GROUP BY 1 ORDER BY 2 DESC""")
out("01_headline", """SELECT
  (SELECT count(DISTINCT v) FROM tr) vehicles_with_2plus_tests,
  (SELECT count(DISTINCT v) FROM tr WHERE conf) vehicles_with_3plus_tests,
  (SELECT count(*) FROM tr WHERE conf) confirmable_tests,
  (SELECT count(*) FROM tr WHERE cls IS NOT NULL) all_drops,
  (SELECT count(*) FROM tr WHERE cls = 'stayed') stayed_drops,
  (SELECT count(DISTINCT v) FROM tr WHERE cls = 'stayed') stayed_vehicles,
  (SELECT sum(m_prev - m) FROM tr WHERE cls = 'stayed') stayed_miles_removed,
  (SELECT median(m_prev - m) FROM tr WHERE cls = 'stayed') stayed_median_drop,
  (SELECT avg(m_prev - m) FROM tr WHERE cls = 'stayed') stayed_mean_drop""")
out("02_stayed_drop_size", """SELECT CASE WHEN m_prev - m < 5000 THEN '1,000-4,999' WHEN m_prev - m < 10000 THEN '5,000-9,999'
  WHEN m_prev - m < 20000 THEN '10,000-19,999' WHEN m_prev - m < 50000 THEN '20,000-49,999' ELSE '50,000+' END band,
  count(*) drops, round(100.0 * count(*) / sum(count(*)) OVER (), 1) pct FROM tr WHERE cls = 'stayed' GROUP BY 1 ORDER BY min(m_prev - m)""")
out("03_by_year", """SELECT yr, count(*) tests, sum((cls IS NOT NULL)::INT) all_drops,
  round(10000.0 * sum((cls IS NOT NULL)::INT) / count(*), 2) all_drops_per_10k,
  sum(conf::INT) confirmable, sum((cls = 'stayed')::INT) stayed, round(10000.0 * sum((cls = 'stayed')::INT) / nullif(sum(conf::INT), 0), 2) stayed_per_10k
  FROM tr GROUP BY 1 ORDER BY 1""")
STAY = """count(*) FILTER (WHERE conf) tests, count(*) FILTER (WHERE cls = 'stayed') stayed,
  round(10000.0 * count(*) FILTER (WHERE cls = 'stayed') / count(*) FILTER (WHERE conf), 2) per_10k"""
out("04_by_area", f"""SELECT t.area, a.name, {STAY} FROM tr t LEFT JOIN read_csv('data/clocking-2022-2025/postcode-areas.csv') a ON t.area = a.area
  WHERE t.area <> 'XX' GROUP BY 1, 2 HAVING count(*) FILTER (WHERE conf) >= 20000 ORDER BY per_10k DESC""")
out("05_by_make", f"""SELECT make, {STAY} FROM tr GROUP BY 1 HAVING count(*) FILTER (WHERE conf) >= 50000 ORDER BY per_10k DESC""")
out("06_by_model", f"""SELECT make, model, {STAY} FROM tr GROUP BY 1, 2 HAVING count(*) FILTER (WHERE conf) >= 20000 ORDER BY per_10k DESC""")
out("07_by_fuel", f"""SELECT CASE WHEN fuel IN ('PE') THEN 'Petrol' WHEN fuel IN ('DI') THEN 'Diesel' WHEN fuel IN ('EL') THEN 'Electric'
  WHEN fuel IN ('HY', 'ED') THEN 'Hybrid' ELSE 'Other' END fuel, {STAY} FROM tr GROUP BY 1 ORDER BY per_10k DESC""")
out("08_by_age", f"""SELECT CASE WHEN age < 5 THEN '3-4' WHEN age < 8 THEN '5-7' WHEN age < 11 THEN '8-10' WHEN age < 15 THEN '11-14'
  WHEN age < 20 THEN '15-19' ELSE '20+' END age_band, {STAY} FROM tr WHERE age >= 2.5 GROUP BY 1 ORDER BY min(age)""")
out("09_by_previous_mileage", f"""SELECT CASE WHEN m_prev < 30000 THEN 'under 30,000' WHEN m_prev < 60000 THEN '30,000-59,999'
  WHEN m_prev < 100000 THEN '60,000-99,999' WHEN m_prev < 150000 THEN '100,000-149,999' ELSE '150,000+' END previous_reading, {STAY}
  FROM tr GROUP BY 1 ORDER BY min(m_prev)""")
out("10_area_change", """SELECT cls IS NOT DISTINCT FROM 'stayed' stayed, count(*) tests,
  round(100.0 * avg((area <> area_prev)::INT), 1) pct_tested_in_different_area FROM tr WHERE conf AND area <> 'XX' AND area_prev <> 'XX' GROUP BY 1""")
out("11_errors_vs_stayed", """SELECT CASE WHEN cls IN ('spike', 'dip', 'tiny', 'unit', 'digit', 'rollover') THEN 'recording error pattern' WHEN cls = 'reset' THEN 'reset near zero'
  WHEN cls = 'stayed' THEN 'stayed lower' ELSE 'not yet known' END grp, count(*) drops, round(100.0 * count(*) / sum(count(*)) OVER (), 1) pct
  FROM tr WHERE cls IS NOT NULL GROUP BY 1 ORDER BY 2 DESC""")
log("done")
con.close()
