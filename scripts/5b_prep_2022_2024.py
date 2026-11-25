# Read the DVSA 2022 and 2024 result files into the same parquet layout as full_2023 / full_2025.
import duckdb, glob, os, subprocess, sys, time, zipfile
W = "work"
R = "raw"
t = time.time()
con = duckdb.connect()
con.execute("PRAGMA threads=12; PRAGMA memory_limit='5GB'")
cols = ("vehicle_id, CAST(test_date AS DATE) test_date, test_result, TRY_CAST(test_mileage AS BIGINT) test_mileage, postcode_area, "
        "upper(trim(make)) make, upper(trim(model)) model, colour, fuel_type, TRY_CAST(cylinder_capacity AS INT) cc, "
        "TRY_CAST(first_use_date AS DATE) first_use_date")
flt = "test_class_id='4' AND test_type='NT' AND test_result IN ('P','F','PRS')"

def lines(path):
    n = 0
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            n += b.count(b"\n")
    return n

def sniff(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.readline()

for y in [int(a) for a in sys.argv[1:]]:
    if y == 2022:
        z = zipfile.ZipFile(f"{R}/dft_test_result_2022.zip")
        info = z.infolist()
        print(2022, [(i.filename, i.compress_type, i.file_size) for i in info])
        out = f"{W}/test_result_2022.csv"
        if not os.path.exists(out):
            if info[0].compress_type == 9:  # Deflate64, same as 2023
                subprocess.run([sys.executable, "scripts/0_unzip_2023_deflate64.py", f"{R}/dft_test_result_2022.zip", out], check=True)
            else:
                with z.open(info[0]) as src, open(out, "wb") as dst:
                    for b in iter(lambda: src.read(1 << 24), b""):
                        dst.write(b)
        files = [out]
    else:
        d = f"{W}/2024csv"
        if not os.path.isdir(d):
            zipfile.ZipFile(f"{R}/dft_test_result_extracts_2024.zip").extractall(d)
        files = sorted(f.replace("\\", "/") for f in glob.glob(f"{d}/**/*.csv", recursive=True))
    head = sniff(files[0])
    delim = "|" if head.count("|") > head.count(",") else ","
    print(y, "files", len(files), "delim", repr(delim), "header", head.strip()[:160])
    flist = "[" + ",".join(f"'{f}'" for f in files) + "]"
    src = (f"read_csv({flist}, delim='{delim}', quote='\"', escape='\\', header=true, all_varchar=true, strict_mode=false"
           + (", filename=true" if len(files) > 1 else "") + ")")
    read = con.execute(f"SELECT count(*) FROM {src}").fetchone()[0]
    want = sum(lines(f) - 1 for f in files)
    print(y, "rows read", read, "lines in files", want, "OK" if read == want else "MISMATCH")
    con.execute(f"COPY (SELECT {cols} FROM {src} WHERE {flt}) TO '{W}/full_{y}.parquet' (FORMAT parquet)")
    print(y, con.execute(f"SELECT count(*), count(DISTINCT vehicle_id), min(test_date), max(test_date) FROM '{W}/full_{y}.parquet'").fetchone(), round(time.time() - t))
