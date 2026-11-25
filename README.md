# UK MOT failure rates, real car mileage and clocked cars (DVSA MOT data)

Free CSV tables built from DVSA's anonymised MOT test data for Great Britain: first-time MOT failure rates by make, model, age and fuel, how many miles cars really cover each year, and a four-year study of MOT mileage readings that go backwards (clocking).

- **33.2 million MOT tests** on 31.7 million vehicles in 2025 (class 4 cars and light vans, normal tests)
- **22.4 million cars** tested in both 2023 and 2025, matched to measure the miles actually driven
- **131.2 million MOT tests** on 37.9 million vehicles from 2022 to 2025 for the clocking study
- **95% confidence intervals** (Wilson) on every rate

Analysis by [Car Control](https://carcontrol.uk), a UK car history check. The full write-ups, with charts and caveats:

- [MOT failure rates 2025 by make, model, age and fuel](https://carcontrol.uk/research/mot-failure-rates-2025)
- [Average car mileage in the UK, by age and fuel](https://carcontrol.uk/average-mileage)
- [Clocked cars: what 131 million MOT mileage readings show](https://carcontrol.uk/research/clocked-cars-mot-data)

## Key findings

| Finding | Figure |
|---|---|
| Share of 2025 MOT tests that were an initial failure | 27.7% |
| Ten-year-old cars (first used 2015): Vauxhall Corsa vs VW Golf failing first time | 36.0% vs 17.9% |
| Initial failure at the first MOT, at 7 to 9 years, at 16 to 18 years | 11.6%, 22.3%, 42.4% |
| First MOT by fuel: diesel, electric, petrol, hybrid | 17.2%, 13.4%, 10.2%, 9.7% |
| First MOT by make: highest (Citroen, Isuzu, Tesla) and lowest (Honda, Lexus) | 16.7%, 16.4%, 15.8% / 6.1%, 4.9% |
| Median miles a year, all cars aged 5 to 20 (average 6,800) | 5,900 |
| Median miles a year, diesel vs petrol | 7,000 vs 5,000 |
| Cars whose 2025 reading was 1,000+ miles lower than their 2023 reading | 0.14% (31,010 of 21.8 million) |
| MOT tests in 2025 with a reading 1,000+ miles below the car's previous MOT | 61,506, about 1 in 500 |
| Share of all such drops (2022-2025) that match a recording error (typo, km/miles mix-up, missing digit) | 78% |
| Cars with the clearest sign of a changed odometer (step-down pattern, 2022-2025) | 3,888 cars, 1 in 7,300 tests checked |
| Step-down rate, previous reading 150,000+ vs under 30,000 miles | 13.7 vs 0.04 per 10,000 |
| Step-down rate, East London (E) vs national | 6.65 vs 1.36 per 10,000 |

## Files

### `data/mot-failure-rates-2025/`

| File | What it shows |
|---|---|
| `mot-2025-fail-by-age-band.csv` | Initial and final failure rate by age at test (cars aged 2.9 years or more) |
| `mot-2025-fail-by-fuel-and-age.csv` | The same, split by fuel (petrol, diesel, hybrid, electric) |
| `mot-2025-first-mot-fail-by-make.csv` | First MOT (cars first used in 2022, tested at 2.9 to 3.6 years), makes with 3,000+ tests |
| `mot-2025-first-mot-fail-by-model.csv` | First MOT by model, models with 1,500+ tests |
| `mot-2025-first-mot-fail-by-fuel.csv` | First MOT by fuel |
| `mot-2025-ten-year-old-fail-by-model.csv` | Cars first used in 2015, tested at 9.9 to 10.6 years, models with 2,500+ tests |
| `mot-2025-fail-by-model-and-year.csv` | 80 popular models, by year of first use (2000 to 2022), with the rate for all cars of the same year and the median mileage. Years with 500+ tests |

Columns: `tests`, `init_fail_n` (Fail or Pass with rectification at the station), `final_fail_n` (Fail only), `init_fail_pct`, `final_fail_pct`, `ci_lo` and `ci_hi` (95% Wilson interval for the initial failure rate, in %).

### `data/mileage/`

| File | What it shows |
|---|---|
| `mileage-2025-odometer-by-age.csv` | Odometer reading at the 2025 MOT by age: average, median, 25th and 75th percentile (25.9 million vehicles aged 3 to 20) |
| `mileage-2023-2025-miles-per-year-by-age.csv` | Miles a year between the 2023 and 2025 tests of the same car, by age (median and average) |
| `mileage-2023-2025-miles-per-year-by-fuel.csv` | Median miles a year by fuel |

### `data/clocking-2022-2025/`

| File | What it shows |
|---|---|
| `mot-mileage-drops-by-year.csv` | Tests with a reading 1,000+ miles below the car's previous MOT, by year |
| `mot-mileage-drops-by-pattern-2022-2025.csv` | All 192,644 drops sorted by what the readings either side show (typing error, km/miles mix-up, missing digit, rollover, reset, stayed lower, no later MOT) |
| `mot-mileage-step-down-by-postcode-area.csv` | Step-down rate per 10,000 tests checked, by postcode area of the test station, with 95% Wilson intervals |
| `mot-mileage-step-down-by-area-standardised.csv` | The same, against the number expected from each area's mix of previous mileage and fuel |
| `mot-mileage-step-down-by-model.csv`, `mot-mileage-step-down-by-make.csv` | By model (15,000+ tests checked) and make (50,000+) |
| `mot-mileage-step-down-by-previous-mileage.csv`, `mot-mileage-step-down-by-age.csv`, `mot-mileage-step-down-by-fuel.csv` | By the reading before the drop, age and fuel |
| `postcode-areas.csv` | Postcode area codes and names |

A **step-down** is a reading 1,000+ miles below the previous MOT where the car had two earlier readings (rising normally and both above the new one) and a later reading that rose again but stayed below the old figure, after excluding every recording-error pattern. It fits clocking or an instrument cluster swap, and it is a minimum: clocking that keeps the reading above the last MOT leaves no trace.

### `data/mileage-lower-readings/`

| File | What it shows |
|---|---|
| `mot-mileage-lower-readings-overall.csv` | Cars compared, and how many had a 2025 reading lower than their last 2023 reading (by 1+, 1,000+ and 10,000+ miles) |
| `mot-mileage-lower-readings-by-make.csv` | Share with a reading 1,000+ miles lower, by make (5,000+ cars) |
| `mot-mileage-lower-readings-by-model.csv` | The same by model (2,000+ cars) |
| `mot-mileage-lower-readings-by-fuel.csv` | The same by fuel |

`lower_n` is the number with a reading 1,000+ miles lower, `big_n` 10,000+ miles lower. A lower reading is not proof of clocking: it can be a typing error by the tester, a replaced instrument cluster or a transferred registration plate.

## Method

- **Source.** DVSA anonymised MOT tests and results: the 2025 results (all 12 monthly files) and the 2023 results.
- **Population.** Test class 4 (cars and light vehicles up to 8 seats, including small vans), normal first-attempt tests only, with a result of Pass, Fail or Pass with rectification at the station. Retests, partial retests, aborted and abandoned tests are excluded.
- **Initial failure** is Fail plus Pass with rectification at the station, as a share of all tests. **Final failure** is Fail only.
- **Age at test** is the test date minus the first use date.
- **Lower readings.** For each vehicle, the last 2023 reading above zero is compared with the first 2025 reading above zero. Cars first used in 2010 or later, readings below 400,000.
- **Miles per year.** Each vehicle's first test of the year, readings between 1 and 400,000. The 2023 and 2025 tests must be 600 to 860 days apart, the car aged 5 to 20 in 2025. Readings that went down or rose by more than 120,000 miles are left out.
- **Model names** are the text DVSA records, so trims can split into separate rows. In the model-by-year file, a model is matched on the first word of the DVSA model field (for example `FIESTA`).
- Data downloaded and analysed in October and November 2026; all four years read in full on 25 November 2026.

### Caveats

- An initial failure includes small items, such as a bulb or a wiper blade, fixed at the test station.
- The reasons for failure were not analysed.
- Makes and models differ in how many are fleet cars, taxis or vans and in how they are serviced. The figures describe the cars on the road in 2025, not how well they were built.
- The electric and hybrid groups are much smaller than petrol and diesel.

### Clocking study (2022 to 2025)

- All class 4 normal tests from the 2022, 2023, 2024 and 2025 files with a mileage above zero, linked by vehicle id; one reading per vehicle per day (the highest).
- Each reading at least 1,000 miles below the previous one is put in the first pattern it fits: a token reading under 1,000; the earlier reading out of line; the lower reading out of line; kilometres and miles mixed up (the new reading within about 6% of the old one divided by 1.609, plus the car's own driving rate); a five-digit rollover; a missing digit; a reset to under 10,000; otherwise stayed lower, or no later MOT.
- Rates are per 10,000 tests with two earlier readings and one later reading (28.7 million tests on 24.9 million vehicles). The area comparison applies national rates by previous-mileage band and fuel.

## Corrections

- **25 November 2026.** The first version of the 2025 tables read about 11% fewer 2025 tests (29.6 million instead of 33.2 million): the original pandas step lost rows near values with escaped quotes. Every file is now read in full and the row counts are checked against the line counts. The rates changed by 0.3 percentage points or less for the figures above, and the tables now include some makes and models that pass the minimum number of tests.

## Reproduce it

The scripts in `scripts/` are the ones used (Python, pandas, DuckDB). Put the DVSA downloads in `raw/`, unzip them into `work/`, then run the scripts in order from `work/`. Output file names from the scripts were renamed for publication.

1. `0_unzip_2023_deflate64.py`: extract the 2023 and 2022 files, which use Deflate64
2. `5a_prep_2023_2025.py` and `5b_prep_2022_2024.py`: read every row to parquet and check the row counts
3. `2_failure_rates_and_lower_readings.py`: failure rates and lower readings
4. `3_model_by_year.py`: models by year of first use
5. `4_mileage_by_age.py`: odometer and miles per year (writes to `out/`)
6. `6_clocking_classify_drops.py`, `7_clocking_step_down_tables.py`, `8_clocking_robustness.py`: the clocking study

## Licence and how to cite

The tables are free to reuse, including commercially, under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Please credit **Car Control (carcontrol.uk)** with a link to [carcontrol.uk/research/clocked-cars-mot-data](https://carcontrol.uk/research/clocked-cars-mot-data), [carcontrol.uk/research/mot-failure-rates-2025](https://carcontrol.uk/research/mot-failure-rates-2025) or [carcontrol.uk/average-mileage](https://carcontrol.uk/average-mileage).

Contains public sector information licensed under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). Source: Driver and Vehicle Standards Agency (DVSA), [Anonymised MOT tests and results](https://www.data.gov.uk/dataset/c63fca52-ae4c-4b75-bab5-8b4735e1a4c9/anonymised-mot-tests-and-results), 2022 to 2025.

This is an independent analysis. It is not produced or endorsed by DVSA.

Questions, or need a cut for a specific model, region or fuel? Email support@carcontrol.uk.
