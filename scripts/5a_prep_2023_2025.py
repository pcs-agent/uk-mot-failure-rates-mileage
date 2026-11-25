# Step 1 (replaces an older pandas step that dropped about 11% of the 2025 rows, those near values with escaped quotes):
# read every class 4 normal test (Pass, Fail, PRS) for 2023 and 2025 into parquet, checking that every line is read.
# Run from the folder that holds test_result_2023.csv (see 0_unzip_2023_deflate64.py) and 2025csv/ (the unzipped 2025 extracts).
import duckdb, glob

con = duckdb.connect()
con.execute("PRAGMA threads=12; PRAGMA memory_limit='8GB'")
COLS = ("vehicle_id, CAST(test_date AS DATE) test_date, test_result, TRY_CAST(test_mileage AS BIGINT) test_mileage, postcode_area, "
        "upper(trim(make)) make, upper(trim(model)) model, colour, fuel_type, TRY_CAST(cylinder_capacity AS INT) cc, "
        "TRY_CAST(first_use_date AS DATE) first_use_date")
FLT = "test_class_id='4' AND test_type='NT' AND test_result IN ('P','F','PRS')"


def lines(path):
    n = 0
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            n += b.count(b"\n")
    return n


SOURCES = {
    2023: (["test_result_2023.csv"], "|"),
    2025: (sorted(f.replace("\\", "/") for f in glob.glob("2025csv/**/dft_test_result_extract_2025*.csv", recursive=True)), ","),
}
for year, (files, delim) in SOURCES.items():
    flist = "[" + ",".join("'" + f + "'" for f in files) + "]"
    src = ("read_csv(" + flist + ", delim='" + delim + "', quote='\"', escape='\\', header=true, all_varchar=true, strict_mode=false)")
    read = con.execute("SELECT count(*) FROM " + src).fetchone()[0]
    want = sum(lines(f) - 1 for f in files)
    print(year, "rows read", read, "lines in files", want, "OK" if read == want else "MISMATCH")
    con.execute("COPY (SELECT " + COLS + " FROM " + src + " WHERE " + FLT + ") TO 'full_" + str(year) + ".parquet' (FORMAT parquet)")

# slim copies used by steps 2 to 4
for year, name in ((2023, "nt4_2023.parquet"), (2025, "nt4full_2025.parquet")):
    con.execute("COPY (SELECT CAST(vehicle_id AS BIGINT) vehicle_id, CAST(test_date AS TIMESTAMP) test_date, test_result, "
                "CAST(test_mileage AS DOUBLE) test_mileage, make, model, fuel_type, CAST(first_use_date AS TIMESTAMP) first_use_date, "
                + str(year) + " AS src FROM 'full_" + str(year) + ".parquet') TO '" + name + "' (FORMAT parquet)")
    print(name, con.execute("SELECT count(*) FROM '" + name + "'").fetchone()[0])
