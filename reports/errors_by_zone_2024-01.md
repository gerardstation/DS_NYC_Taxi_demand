# Errors by zone (2024-01)

This report ranks zones by error on the test predictions.

**Overall metrics**

- MAE: 6.179
- RMSE: 13.431

## Top 15 zones by MAE

|   zone_id | borough   | zone_name                    |   n |    mae |   rmse |   avg_pickups |   p95_pickups |
|----------:|:----------|:-----------------------------|----:|-------:|-------:|--------------:|--------------:|
|       132 | Queens    | JFK Airport                  | 168 | 26.982 | 35.003 |        166.22 |        331.5  |
|       138 | Queens    | LaGuardia Airport            | 148 | 26.091 | 32.961 |        131.69 |        255.65 |
|       186 | Manhattan | Penn Station/Madison Sq West | 169 | 24.275 | 35.408 |        144.96 |        276.4  |
|       142 | Manhattan | Lincoln Square East          | 166 | 23.839 | 44.055 |        140.53 |        294    |
|       237 | Manhattan | Upper East Side South        | 167 | 21.464 | 30.272 |        211.37 |        429.7  |
|       236 | Manhattan | Upper East Side North        | 164 | 21.063 | 29.474 |        203.53 |        407.95 |
|       161 | Manhattan | Midtown Center               | 167 | 19.841 | 31.69  |        208.56 |        543.4  |
|       230 | Manhattan | Times Sq/Theatre District    | 168 | 18.901 | 27.216 |        141.99 |        312.2  |
|       162 | Manhattan | Midtown East                 | 168 | 16.532 | 22.316 |        152.91 |        344.3  |
|        68 | Manhattan | East Chelsea                 | 168 | 15.304 | 21.434 |        111.79 |        209    |
|       163 | Manhattan | Midtown North                | 168 | 14.923 | 21.911 |        125.17 |        274.75 |
|       170 | Manhattan | Murray Hill                  | 168 | 14.061 | 18.805 |        118.22 |        248.3  |
|       164 | Manhattan | Midtown South                | 168 | 14.041 | 20.487 |         91.64 |        192    |
|        79 | Manhattan | East Village                 | 168 | 13.895 | 24.008 |         98.6  |        337.35 |
|       246 | Manhattan | West Chelsea/Hudson Yards    | 166 | 13.801 | 19.997 |         75.43 |        237.25 |

## Zones with highest relative error (MAE / avg_pickups)

Useful to spot low-demand zones where a small absolute error is still big vs typical demand.

|   zone_id | borough   | zone_name                 |   n |   mae |   avg_pickups |   mae_perc_of_avg |
|----------:|:----------|:--------------------------|----:|------:|--------------:|------------------:|
|       101 | Queens    | Glen Oaks                 |   5 | 0.583 |          1    |              0.58 |
|        54 | Brooklyn  | Columbia Street           |  14 | 0.624 |          1.07 |              0.58 |
|       153 | Manhattan | Marble Hill               |   7 | 0.57  |          1    |              0.57 |
|       255 | Brooklyn  | Williamsburg (North Side) |  75 | 1.988 |          3.52 |              0.56 |
|       265 | nan       | Outside of NYC            |  76 | 0.787 |          1.42 |              0.55 |
|        61 | Brooklyn  | Crown Heights North       | 100 | 1.213 |          2.26 |              0.54 |
|       181 | Brooklyn  | Park Slope                |  99 | 1.168 |          2.2  |              0.53 |
|       195 | Brooklyn  | Red Hook                  |  27 | 1.145 |          2.19 |              0.52 |
|         4 | Manhattan | Alphabet City             | 132 | 3.963 |          7.6  |              0.52 |
|       197 | Queens    | Richmond Hill             |  63 | 0.863 |          1.67 |              0.52 |

## Worst (day_of_week, hour) segments by MAE

day_of_week: 0=Mon ... 6=Sun

|   day_of_week |   hour |   n |     mae |    rmse |
|--------------:|-------:|----:|--------:|--------:|
|             5 |     21 | 101 | 15.1357 | 30.8868 |
|             4 |     22 |  89 | 13.3665 | 33.3636 |
|             2 |     21 |  82 | 13.1012 | 27.7577 |
|             6 |      0 | 108 | 12.552  | 22.2403 |
|             1 |     19 |  83 | 12.3223 | 22.7377 |
|             3 |     21 |  84 | 12.1247 | 22.0387 |
|             6 |      1 |  96 | 11.7518 | 25.6574 |
|             5 |      1 |  78 | 11.7423 | 24.0315 |
|             1 |     21 |  79 | 11.6992 | 23.7273 |
|             1 |     22 |  84 | 11.2791 | 22.161  |
|             3 |     23 |  84 | 11.2644 | 24.2843 |
|             1 |      0 |  70 | 11.1355 | 28.7245 |
|             6 |     16 |  94 | 11.1017 | 21.0266 |
|             3 |     22 |  83 | 10.6355 | 17.1565 |
|             3 |     18 | 103 | 10.5652 | 20.3066 |

## Notes (how to explain it)

- High-MAE zones are often **high-volume and volatile** (airports, Midtown, Times Sq): spikes are harder.
- Relative error highlights **low-demand zones** where small absolute misses look fine but are large proportionally.
- Hour/day patterns can indicate **rush hours / weekend nightlife / weather sensitivity**.
