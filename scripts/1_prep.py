# Step 1: keep class 4 normal tests (Pass, Fail, PRS) from the DVSA 2023 and 2025 files and save them as parquet.
WORK, RAW = "work", "raw"  # folders: raw = DVSA downloads, work = intermediate files
import pandas as pd, zipfile, glob
cols=['test_id','vehicle_id','test_date','test_class_id','test_type','test_result','test_mileage','make','model','fuel_type','first_use_date']
dt={'test_id':'int64','vehicle_id':'int64','test_class_id':'string','test_type':'string','test_result':'string','test_mileage':'float64','make':'string','model':'string','fuel_type':'string'}
out=[]
def proc(chunk,year):
    chunk=chunk[(chunk.test_class_id=='4')&(chunk.test_type=='NT')&chunk.test_result.isin(['P','F','PRS'])].copy()
    chunk['test_date']=pd.to_datetime(chunk.test_date,errors='coerce')
    chunk['first_use_date']=pd.to_datetime(chunk.first_use_date,errors='coerce')
    return chunk.drop(columns=['test_class_id','test_type'])
tot={}
parts=[]
for ch in pd.read_csv(WORK + '/test_result_2023.csv',sep='|',usecols=cols,dtype=dt,chunksize=2_000_000):
    parts.append(proc(ch,2023))
a=pd.concat(parts); a['src']=2023; a.to_parquet(WORK + '/nt4_2023.parquet'); print('2023',len(a)); del parts,a
z=zipfile.ZipFile(RAW + '/dft_test_result_extracts_2025.zip')
parts=[]
for i in z.infolist():
    with z.open(i) as f:
        for ch in pd.read_csv(f,usecols=cols,dtype=dt,chunksize=2_000_000):
            parts.append(proc(ch,2025))
a=pd.concat(parts); a['src']=2025; a.to_parquet(WORK + '/nt4_2025.parquet'); print('2025',len(a))
