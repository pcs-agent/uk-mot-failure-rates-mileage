# Step 3: first-time failure rate by model and year of first use (2025 tests), against all cars of the same year,
# with median mileage. Output: work/model_stats_2025.json, flattened to mot-2025-fail-by-model-and-year.csv.
import json
import pandas as pd
WORK = "work"

MODELS = [  # (make, display name, first words of the DVSA model field that count as this model)
 ("FORD","Fiesta",["FIESTA"]),("FORD","Focus",["FOCUS"]),("FORD","Kuga",["KUGA"]),("FORD","Ka",["KA","KA+"]),("FORD","Mondeo",["MONDEO"]),
 ("FORD","EcoSport",["ECOSPORT"]),("FORD","C-Max",["C-MAX"]),("FORD","B-Max",["B-MAX"]),
 ("VAUXHALL","Corsa",["CORSA"]),("VAUXHALL","Astra",["ASTRA"]),("VAUXHALL","Mokka",["MOKKA"]),("VAUXHALL","Insignia",["INSIGNIA"]),
 ("VAUXHALL","Zafira",["ZAFIRA"]),("VAUXHALL","Meriva",["MERIVA"]),("VAUXHALL","Adam",["ADAM"]),("VAUXHALL","Crossland",["CROSSLAND"]),("VAUXHALL","Grandland",["GRANDLAND"]),
 ("VOLKSWAGEN","Golf",["GOLF"]),("VOLKSWAGEN","Polo",["POLO"]),("VOLKSWAGEN","Tiguan",["TIGUAN"]),("VOLKSWAGEN","Passat",["PASSAT"]),("VOLKSWAGEN","Up",["UP","UP!"]),("VOLKSWAGEN","T-Roc",["T-ROC"]),
 ("NISSAN","Qashqai",["QASHQAI"]),("NISSAN","Juke",["JUKE"]),("NISSAN","Micra",["MICRA"]),("NISSAN","Note",["NOTE"]),("NISSAN","Leaf",["LEAF"]),
 ("TOYOTA","Yaris",["YARIS"]),("TOYOTA","Aygo",["AYGO"]),("TOYOTA","Prius",["PRIUS"]),("TOYOTA","Auris",["AURIS"]),("TOYOTA","Corolla",["COROLLA"]),("TOYOTA","C-HR",["C-HR"]),("TOYOTA","RAV4",["RAV4","RAV-4"]),
 ("AUDI","A3",["A3"]),("AUDI","A4",["A4"]),("AUDI","A1",["A1"]),("AUDI","Q3",["Q3"]),("AUDI","A5",["A5"]),("AUDI","Q5",["Q5"]),("AUDI","A6",["A6"]),
 ("MERCEDES-BENZ","C-Class",["C","C-CLASS"]),("MERCEDES-BENZ","A-Class",["A","A-CLASS"]),("MERCEDES-BENZ","E-Class",["E","E-CLASS"]),
 ("BMW","3 Series",["3"]),
 ("HONDA","Jazz",["JAZZ"]),("HONDA","Civic",["CIVIC"]),("HONDA","CR-V",["CR-V"]),
 ("FIAT","500",["500"]),("FIAT","Panda",["PANDA"]),("FIAT","Punto",["PUNTO","GRANDE"]),
 ("RENAULT","Clio",["CLIO"]),("RENAULT","Captur",["CAPTUR"]),("RENAULT","Megane",["MEGANE"]),
 ("KIA","Sportage",["SPORTAGE"]),("KIA","Picanto",["PICANTO"]),("KIA","Ceed",["CEED","CEE'D"]),("KIA","Rio",["RIO"]),("KIA","Niro",["NIRO"]),
 ("HYUNDAI","i10",["I10"]),("HYUNDAI","Tucson",["TUCSON"]),("HYUNDAI","i20",["I20"]),("HYUNDAI","i30",["I30"]),
 ("CITROEN","C3",["C3"]),("CITROEN","C4",["C4"]),("CITROEN","C1",["C1"]),
 ("SKODA","Fabia",["FABIA"]),("SKODA","Octavia",["OCTAVIA"]),("SKODA","Superb",["SUPERB"]),
 ("SEAT","Ibiza",["IBIZA"]),("SEAT","Leon",["LEON"]),
 ("PEUGEOT","208",["208"]),("PEUGEOT","2008",["2008"]),("PEUGEOT","3008",["3008"]),("PEUGEOT","308",["308"]),("PEUGEOT","107",["107"]),
 ("SUZUKI","Swift",["SWIFT"]),("DACIA","Sandero",["SANDERO"]),("DACIA","Duster",["DUSTER"]),
]
b = pd.read_parquet(WORK + '/nt4full_2025.parquet', columns=['make','model','test_result','test_mileage','first_use_date','fuel_type'])
b['make'] = b.make.astype(str).str.strip().str.upper()
b['base'] = b.model.astype(str).str.strip().str.upper().str.split().str[0]
b['fail'] = b.test_result.isin(['F','PRS'])
b['year'] = b.first_use_date.dt.year
b = b[(b.year >= 2000) & (b.year <= 2022)]
nat = b.groupby('year').agg(n=('fail','size'), f=('fail','mean'))
nat_all = float(b.fail.mean())
FM = {'PE':'Petrol','DI':'Diesel','HY':'Hybrid','EL':'Electric'}
out = {"national_fail_pct": round(100*nat_all,1), "national_tests": int(len(b)),
       "national_by_year": {int(y): round(100*r.f,1) for y, r in nat.iterrows() if r.n >= 1000}, "models": []}
for make, name, bases in MODELS:
    m = b[(b.make == make) & (b.base.isin(bases))]
    if len(m) < 20000:
        print('too few', make, name, len(m)); continue
    rows = []
    for y, g in m.groupby('year'):
        if len(g) < 500: continue
        mil = g.test_mileage[(g.test_mileage > 0) & (g.test_mileage < 400000)]
        rows.append({"year": int(y), "tests": int(len(g)), "fail_pct": round(100*g.fail.mean(),1),
                     "all_cars_pct": out["national_by_year"].get(int(y)), "median_miles": int(round(mil.median(), -2)) if len(mil) else None})
    fuel = m.fuel_type.astype(str).str.upper().map(FM).fillna('Other').value_counts(normalize=True)
    out["models"].append({"make": make, "name": name, "tests": int(len(m)), "fail_pct": round(100*m.fail.mean(),1),
                          "fuel": {k: round(100*v) for k, v in fuel.items() if v >= 0.05}, "years": rows})
    print(make, name, len(m), round(100*m.fail.mean(),1), len(rows))
json.dump(out, open(WORK + '/model_stats_2025.json','w'), indent=1)
print('national', out["national_fail_pct"], out["national_tests"])
