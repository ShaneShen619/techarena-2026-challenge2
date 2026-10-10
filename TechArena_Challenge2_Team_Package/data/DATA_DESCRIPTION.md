# Challenge 2 data package

## Operating data - `operation/segment_NN_TTdegC.csv.gz`
One file per operating segment (13 segments, Jan-Sep 2025, 10-second sampling; segment 3 - 19 Feb to 11 Mar -
is not provided, the Ah counters continue through it):

| column | unit | meaning |
|---|---|---|
| timestamp | - | absolute time (YYYY-MM-DD HH:MM:SS) |
| elapsed_s | s | seconds since the first operating sample of the campaign |
| segment | - | segment number 1..14 |
| chamber_temperature_C | degC | climate chamber set point (25 or 45) |
| current_A | A | current through the series string (identical for all cells), + charge / - discharge |
| charge_Ah_cum | Ah | BMS-style cumulative charged Ah since campaign start (cycler accounting, never reset, monotonic) |
| discharge_Ah_cum | Ah | BMS-style cumulative discharged Ah since campaign start (never reset, monotonic) |
| cell1_V .. cell4_V | V | individual cell voltages |
| pack_voltage_V | V | string voltage (sum of the four cells) |
| temp_mean_C, temp_min_C, temp_max_C | degC | statistics over the cell temperature sensors |

The pack: 4 x 102 Ah LFP cells in series, operated with a simulated storage-application profile
(daily charge/discharge pattern; a full CCCV charge to 14.0 V followed by a 30-min 20 A discharge
pulse roughly every 5 days). Segments alternate between 25 degC (short) and 45 degC (long).
Gaps between months are the monthly checkups. The Ah counters come from the cycler's own integration, so they stay correct across
recording gaps inside a segment (use their jumps to estimate throughput where samples are missing). Checkup throughput is NOT counted.

## Checkups - `checkups/`
* `checkup_capacities_released.csv` - the beginning-of-life checkup CK0: C/20 capacity (5.1 A to
  11.2 V) = 100.41 Ah. SOH is defined against the NOMINAL capacity of 102 Ah throughout the
  challenge, so CK0 = 98.44 % SOH (not 100 %). This is the ONLY capacity value you receive.
* `evaluation_points.csv` - dates of ALL checkups CK0..CK7. Your model must output an SOH estimate
  (percent of 102 Ah) for every date; CK1..CK7 are hidden and scored:
  CK0 2025-01-14 (released), CK1 2025-02-08, CK2 2025-03-11, CK3 2025-04-14, CK4 2025-05-16,
  CK5 2025-06-16, CK6 2025-07-25, CK7 2025-08-28 (hidden).
* `CK0_reference_discharge.csv.gz` - the full C/20 discharge curve of CK0 (pack and cell voltages
  vs discharged Ah).
