import duckdb
O = "out/clocking"
con = duckdb.connect("work/clocking.duckdb", read_only=True)
con.execute("PRAGMA threads=12; PRAGMA memory_limit='12GB'; PRAGMA temp_directory='work/tmp'")
con.execute("""CREATE TEMP TABLE t AS SELECT area, make, model, fuel, m_prev, (m_prev2 IS NOT NULL AND m_next IS NOT NULL) ok,
  (cls = 'stayed' AND m_prev2 IS NOT NULL AND m < m_prev2 AND m_prev2 <= m_prev AND m_next >= m AND m_next < m_prev) step,
  CASE WHEN m_prev < 30000 THEN 1 WHEN m_prev < 60000 THEN 2 WHEN m_prev < 100000 THEN 3 WHEN m_prev < 150000 THEN 4 WHEN m_prev < 200000 THEN 5 ELSE 6 END mb,
  (model IN ('PRIUS', 'PRIUS +', 'TX4', 'TX', 'TXII', 'TX1') OR make LIKE 'LONDON TAXI%' OR make = 'LEVC') taxi
  FROM tr WHERE m_prev2 IS NOT NULL AND m_next IS NOT NULL AND area <> 'XX'""")
# expected events per area if each mileage band and fuel had the national rate
con.execute("""CREATE TEMP TABLE nat AS SELECT mb, fuel, count(*) n, sum(step::INT) s FROM t GROUP BY 1, 2""")
df = con.execute("""WITH a AS (SELECT area, mb, fuel, count(*) n, sum(step::INT) s FROM t GROUP BY 1, 2, 3)
  SELECT a.area, p.name, sum(a.n) n, sum(a.s) s, round(sum(a.n * nat.s / nat.n), 1) expected, round(sum(a.s) / sum(a.n * nat.s / nat.n), 2) ratio
  FROM a JOIN nat USING (mb, fuel) LEFT JOIN read_csv('data/clocking-2022-2025/postcode-areas.csv') p ON a.area = p.area
  GROUP BY 1, 2 HAVING sum(a.n) >= 50000 ORDER BY ratio DESC""").df()
df.to_csv(f"{O}/13_area_standardised.csv", index=False)
print("--- area, standardised for previous mileage and fuel (ratio 1 = national)"); print(df.head(15).to_string()); print(df.tail(8).to_string())
df2 = con.execute("""SELECT area, count(*) n, sum(step::INT) s, round(10000.0 * sum(step::INT) / count(*), 2) per_10k FROM t WHERE NOT taxi
  GROUP BY 1 HAVING count(*) >= 50000 ORDER BY per_10k DESC LIMIT 12""").df()
df2.to_csv(f"{O}/14_area_excluding_taxis.csv", index=False)
print("--- area excluding Prius and London taxis"); print(df2.to_string())
print("--- national excl taxis", con.execute("SELECT count(*), sum(step::INT), round(10000.0*sum(step::INT)/count(*),2) FROM t WHERE NOT taxi").fetchone())
print("--- E area: share of step events that are taxis", con.execute("SELECT sum((step AND taxi)::INT), sum(step::INT) FROM t WHERE area='E'").fetchone())
print("--- E area mileage mix: share of tests with previous reading 150k+", con.execute("SELECT round(100*avg((m_prev>=150000)::INT),1) FROM t WHERE area='E'").fetchone(), "national", con.execute("SELECT round(100*avg((m_prev>=150000)::INT),1) FROM t").fetchone())
df3 = con.execute("""SELECT mb, count(*) n, sum(step::INT) s, round(10000.0*sum(step::INT)/count(*),2) per_10k FROM t WHERE NOT taxi GROUP BY 1 ORDER BY 1""").df()
print("--- mileage bands excluding taxis"); print(df3.to_string())
df4 = con.execute("""SELECT make, model, count(*) n, sum(step::INT) s, round(10000.0*sum(step::INT)/count(*),2) per_10k FROM t
  GROUP BY 1, 2 HAVING count(*) >= 150000 ORDER BY per_10k DESC""").df()
df4.to_csv(f"{O}/15_popular_models.csv", index=False)
print("--- popular models (150k+ checkable tests)"); print(df4.head(12).to_string()); print(df4.tail(8).to_string())
