# Strict "step down" pattern: two readings before the drop (both higher, rising normally) and one after (rising again
# from the lower level but still below the earlier reading). Excludes every recording-error pattern.
import duckdb, os
O = "out/clocking"; os.makedirs(O, exist_ok=True)
con = duckdb.connect("work/clocking.duckdb", read_only=True)
con.execute("PRAGMA threads=12; PRAGMA memory_limit='12GB'; PRAGMA temp_directory='work/tmp'")
con.execute("""CREATE TEMP VIEW t AS SELECT *, (m_prev2 IS NOT NULL AND m_next IS NOT NULL) ok,
  (cls = 'stayed' AND m_prev2 IS NOT NULL AND m < m_prev2 AND m_prev2 <= m_prev AND m_next >= m AND m_next < m_prev) step FROM tr""")
def out(name, sql, show=40):
    df = con.execute(sql).df(); df.to_csv(f"{O}/{name}.csv", index=False)
    print(f"--- {name} ({len(df)})"); print(df.head(show).to_string()); return df
W = "round(100 * ((s + 1.92) / (n + 3.84) - 1.96 * sqrt((s * (n - s) / n + 0.96) ) / (n + 3.84)) * 100, 2)"
def ci(lo):  # Wilson 95% bounds per 10,000
    sign = "-" if lo else "+"
    return f"round(10000 * ((s + 1.9208) / (n + 3.8416) {sign} 1.96 * sqrt(s * (n - s) / n + 0.9604) / (n + 3.8416)), 2)"
STAT = f"""n, s, round(10000.0 * s / n, 2) per_10k, {ci(True)} ci_lo, {ci(False)} ci_hi"""
out("00_headline", """SELECT count(*) FILTER (WHERE ok) tests_checkable, count(DISTINCT v) FILTER (WHERE ok) vehicles_checkable,
  count(*) FILTER (WHERE step) step_drops, count(DISTINCT v) FILTER (WHERE step) step_vehicles,
  round(10000.0 * count(*) FILTER (WHERE step) / count(*) FILTER (WHERE ok), 2) per_10k,
  median(m_prev - m) FILTER (WHERE step) median_drop, avg(m_prev - m) FILTER (WHERE step) mean_drop,
  sum(m_prev - m) FILTER (WHERE step) miles_removed,
  quantile_cont(m_prev - m, 0.25) FILTER (WHERE step) p25_drop, quantile_cont(m_prev - m, 0.75) FILTER (WHERE step) p75_drop,
  median(m_prev) FILTER (WHERE step) median_reading_before, median(m) FILTER (WHERE step) median_reading_after FROM t""")
out("01_by_year", f"SELECT yr, {STAT} FROM (SELECT yr, count(*) FILTER (WHERE ok) n, count(*) FILTER (WHERE step) s FROM t GROUP BY 1) WHERE n > 0 ORDER BY 1")
out("02_drop_size", """SELECT CASE WHEN m_prev - m < 5000 THEN '1,000-4,999' WHEN m_prev - m < 10000 THEN '5,000-9,999'
  WHEN m_prev - m < 20000 THEN '10,000-19,999' WHEN m_prev - m < 50000 THEN '20,000-49,999' WHEN m_prev - m < 100000 THEN '50,000-99,999' ELSE '100,000+' END band,
  count(*) drops, round(100.0 * count(*) / sum(count(*)) OVER (), 1) pct FROM t WHERE step GROUP BY 1 ORDER BY min(m_prev - m)""")
out("03_by_area", f"""SELECT x.area, a.name, {STAT} FROM (SELECT area, count(*) FILTER (WHERE ok) n, count(*) FILTER (WHERE step) s FROM t WHERE area <> 'XX' GROUP BY 1) x
  LEFT JOIN read_csv('data/clocking-2022-2025/postcode-areas.csv') a ON x.area = a.area WHERE n >= 50000 ORDER BY per_10k DESC""", 120)
out("04_by_make", f"SELECT make, {STAT} FROM (SELECT make, count(*) FILTER (WHERE ok) n, count(*) FILTER (WHERE step) s FROM t GROUP BY 1) WHERE n >= 50000 ORDER BY per_10k DESC", 60)
out("05_by_model", f"SELECT make, model, {STAT} FROM (SELECT make, model, count(*) FILTER (WHERE ok) n, count(*) FILTER (WHERE step) s FROM t GROUP BY 1, 2) WHERE n >= 15000 ORDER BY per_10k DESC", 50)
out("06_by_fuel", f"""SELECT fuel, {STAT} FROM (SELECT CASE WHEN fuel = 'PE' THEN 'Petrol' WHEN fuel = 'DI' THEN 'Diesel' WHEN fuel = 'EL' THEN 'Electric'
  WHEN fuel IN ('HY', 'ED') THEN 'Hybrid' ELSE 'Other' END fuel, count(*) FILTER (WHERE ok) n, count(*) FILTER (WHERE step) s FROM t GROUP BY 1) ORDER BY per_10k DESC""")
out("07_by_age", f"""SELECT age_band, {STAT} FROM (SELECT CASE WHEN age < 5 THEN '3-4' WHEN age < 8 THEN '5-7' WHEN age < 11 THEN '8-10' WHEN age < 15 THEN '11-14'
  WHEN age < 20 THEN '15-19' ELSE '20+' END age_band, min(age) a0, count(*) FILTER (WHERE ok) n, count(*) FILTER (WHERE step) s FROM t WHERE age >= 2.5 GROUP BY 1) ORDER BY a0""")
out("08_by_previous_mileage", f"""SELECT band, {STAT} FROM (SELECT CASE WHEN m_prev < 30000 THEN 'under 30,000' WHEN m_prev < 60000 THEN '30,000-59,999'
  WHEN m_prev < 100000 THEN '60,000-99,999' WHEN m_prev < 150000 THEN '100,000-149,999' ELSE '150,000+' END band, min(m_prev) m0,
  count(*) FILTER (WHERE ok) n, count(*) FILTER (WHERE step) s FROM t GROUP BY 1) ORDER BY m0""")
out("09_area_change", "SELECT step, count(*) n, round(100.0 * avg((area <> area_prev)::INT), 1) pct_different_area FROM t WHERE ok AND area <> 'XX' AND area_prev <> 'XX' GROUP BY 1")
out("10_all_drops_by_year", "SELECT yr, count(*) tests, count(*) FILTER (WHERE cls IS NOT NULL) drops, round(10000.0 * count(*) FILTER (WHERE cls IS NOT NULL) / count(*), 2) per_10k FROM t GROUP BY 1 ORDER BY 1")
out("11_ratio_hist", "SELECT round(floor(m::DOUBLE / m_prev * 20) / 20, 2) ratio_bin, count(*) n FROM t WHERE step GROUP BY 1 ORDER BY 1", 30)
out("12_class_counts", "SELECT cls, count(*) n FROM t WHERE cls IS NOT NULL GROUP BY 1 ORDER BY 2 DESC")
