# Step 2: failure rates (first MOT, age bands, fuel, ten-year-old models) and lower mileage readings, with 95% Wilson intervals.
WORK = "work"
import pandas as pd, numpy as np, os
OUT='out'; os.makedirs(OUT,exist_ok=True)
a=pd.read_parquet(WORK + '/nt4_2023.parquet'); b=pd.read_parquet(WORK + '/nt4_2025.parquet')
FM={'PE':'Petrol','DI':'Diesel','HY':'Hybrid','HYBRID ELECTRIC (CLEAN)':'Hybrid','EL':'Electric','ELECTRIC':'Electric','ED':'Other','ELECTRIC DIESEL':'Other'}
for d in (a,b):
    d['make']=d.make.astype(str).str.strip().str.upper(); d['model']=d.model.astype(str).str.strip().str.upper()
    d['fuel']=d.fuel_type.astype(str).str.upper().map(FM).fillna('Other')
    d.drop(columns=['fuel_type'],inplace=True)
def wil(k,n):
    z=1.96; p=k/n; d=1+z*z/n; c=p+z*z/(2*n); s=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n)); return (c-s)/d,(c+s)/d
# ---- Angle A: lower mileage than 2 yrs earlier
a1=a[(a.test_mileage>0)].sort_values('test_date').groupby('vehicle_id').tail(1)[['vehicle_id','test_mileage','test_date']].rename(columns={'test_mileage':'m23','test_date':'d23'})
b1=b[(b.test_mileage>0)].sort_values('test_date').groupby('vehicle_id').head(1)
p=b1.merge(a1,on='vehicle_id')
n0=len(p)
p=p[(p.first_use_date>='2010-01-01')&(p.m23<400000)&(p.test_mileage<400000)&(p.d23<p.test_date)]
p['drop']=p.m23-p.test_mileage
p['lower']=p['drop']>=1000
p['lower_any']=p['drop']>0
p['big']=p['drop']>=10000
p['gap_y']=(p.test_date-p.d23).dt.days/365.25
print('pairs raw',n0,'kept',len(p),'lower>=1000',p.lower.mean(),'any lower',p.lower_any.mean(),'>=10k',p.big.mean(),'gap',p.gap_y.median())
summ=pd.DataFrame([{'vehicles_compared':len(p),'lower_ge1000_n':int(p.lower.sum()),'lower_ge1000_pct':100*p.lower.mean(),'lower_any_n':int(p.lower_any.sum()),'lower_ge10000_n':int(p.big.sum()),'median_gap_years':p.gap_y.median()}])
summ.to_csv(f'{OUT}/A0_mileage_overall.csv',index=False)
def rank(g,keys,minn,name):
    r=g.groupby(keys).agg(vehicles=('lower','size'),lower_n=('lower','sum'),big_n=('big','sum')).reset_index()
    r=r[r.vehicles>=minn]; r['lower_pct']=100*r.lower_n/r.vehicles; r['big_pct']=100*r.big_n/r.vehicles
    r['ci_lo']=[100*wil(k,n)[0] for k,n in zip(r.lower_n,r.vehicles)]; r['ci_hi']=[100*wil(k,n)[1] for k,n in zip(r.lower_n,r.vehicles)]
    r=r.sort_values('lower_pct',ascending=False); r.round(2).to_csv(f'{OUT}/{name}.csv',index=False); return r
rm=rank(p,['make'],5000,'A1_mileage_lower_by_make'); rmo=rank(p,['make','model'],2000,'A2_mileage_lower_by_model')
print(rm.head(10).round(2).to_string()); print(rm.tail(5).round(2).to_string()); print(rmo.head(15).round(2).to_string()); print(rmo.tail(5).round(2).to_string())
fu=rank(p,['fuel'],1000,'A3_mileage_lower_by_fuel'); print(fu.round(2).to_string())
# ---- Angle B: first MOT (age ~3) initial failure, first use 2022
b['age']=(b.test_date-b.first_use_date).dt.days/365.25
b['init_fail']=b.test_result.isin(['F','PRS']); b['final_fail']=b.test_result.eq('F')
f=b[(b.first_use_date.dt.year==2022)&(b.age>=2.9)&(b.age<=3.6)]
print('first MOT n',len(f),f.init_fail.mean(),f.final_fail.mean())
def frate(g,keys,minn,name):
    r=g.groupby(keys).agg(tests=('init_fail','size'),init_fail_n=('init_fail','sum'),final_fail_n=('final_fail','sum')).reset_index()
    r=r[r.tests>=minn]; r['init_fail_pct']=100*r.init_fail_n/r.tests; r['final_fail_pct']=100*r.final_fail_n/r.tests
    r['ci_lo']=[100*wil(k,n)[0] for k,n in zip(r.init_fail_n,r.tests)]; r['ci_hi']=[100*wil(k,n)[1] for k,n in zip(r.init_fail_n,r.tests)]
    r=r.sort_values('init_fail_pct',ascending=False); r.round(2).to_csv(f'{OUT}/{name}.csv',index=False); return r
fm=frate(f,['make'],3000,'B1_first_mot_fail_by_make'); fmo=frate(f,['make','model'],1500,'B2_first_mot_fail_by_model'); ff=frate(f,['fuel'],1000,'B3_first_mot_fail_by_fuel')
print(fm.head(8).round(1).to_string()); print(fm.tail(8).round(1).to_string()); print(fmo.head(10).round(1).to_string()); print(fmo.tail(10).round(1).to_string()); print(ff.round(1).to_string())
# ---- Angle C: by age band and fuel; models at age ~10
b['band']=pd.cut(b.age,[0,3.6,6.6,9.6,12.6,15.6,18.6,100],labels=['3 (first MOT)','4-6','7-9','10-12','13-15','16-18','19+'],include_lowest=True)
c=b[b.age>=2.9]; 
cb=frate(c,['band'],1000,'C1_fail_by_age_band').sort_index(); print(cb.round(1).to_string())
cf=frate(c[c.fuel.isin(['Petrol','Diesel','Hybrid','Electric'])],['fuel','band'],1000,'C2_fail_by_fuel_and_age'); print(cf.sort_values(['band','fuel']).round(1).to_string())
t=b[(b.first_use_date.dt.year==2015)&(b.age>=9.9)&(b.age<=10.6)]
tm=frate(t,['make','model'],2500,'C3_ten_year_old_fail_by_model'); print(len(t),t.init_fail.mean()); print(tm.head(8).round(1).to_string()); print(tm.tail(8).round(1).to_string())
print('overall 2025 init fail',b.init_fail.mean(),len(b),b.vehicle_id.nunique())
