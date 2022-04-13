# Sanity checks and Statistical Data
## Cities
### Salzburg
[Salzburg OSM source](https://overpass-api.de/api/map?bbox=12.9968,47.7684,13.0940,47.8341)
| Sanity Check       |  Official  | Simulation | Source |
| :----------------- | ---------: | ---------: | :----- |
| Population         |    179 614 |    179 620 | (with sec. residence, 2021) [Stadt Salzburg](https://www.stadt-salzburg.at/statistik-bevoelkerung/)|
| Sqm per person     |       43.5 |       39.6 | (Salzburg state, 2021) [Statistik Austria](https://www.statistik.at/web_de/statistiken/menschen_und_gesellschaft/wohnen/wohnsituation/081235.html) |
| Avg household size |       2.05 |    ❌ 3.44 | [Similio](https://simil.io/politisch/salzburg-stadt/salzburg/haushaltsgroesse) |
| House sqm total    |          ? |  7 116 945 | |
| Families           |     87 616 |     52 178 | from population and avg houshold size |

### Graz
[Graz OSM source](https://overpass-api.de/api/map?bbox=15.3762,47.0232,15.5045,47.1240)
| Sanity Check       |  Official  | Simulation | Source |
| :----------------- | ---------: | ---------: | :----- |
| Population         |    333 049 |    333 049 | (with sec. residence, 2021) [Stadt Graz](https://www.graz.at/cms/beitrag/10034466/7772565/Zahlen_Fakten_Bevoelkerung_Bezirke_Wirtschaft.html) |
| Sqm per person     |       49.2 |    ❌ 54.1 | (Styria, 2021) [Statistik Austria](https://www.statistik.at/web_de/statistiken/menschen_und_gesellschaft/wohnen/wohnsituation/081235.html) |
| Avg household size |       2.03 |    ❌ 3.44 | [Similio](https://simil.io/politisch/graz-stadt/graz/haushaltsgroesse) |
| House sqm total    |          ? | 18 015 773 | |
| Families           |    164 063 |     96 748 | from population and avg houshold size |

### Vienna
[Vienna OSM source](https://overpass-api.de/api/map?bbox=16.2172,48.1304,16.5399,48.2846)
| Sanity Check       |  Official  | Simulation | Source |
| :----------------- | ---------: | ---------: | :----- |
| Population         |  1 935 000 |  1 934 926 | (2021) [Stadt Wien](https://www.wien.gv.at/statistik/bevoelkerung/bevoelkerungsstand/) |
| Sqm per person     |       36.8 |       40.3 | (Wien, 2021) [Statistik Austria](https://www.statistik.at/web_de/statistiken/menschen_und_gesellschaft/wohnen/wohnsituation/081235.html) |
| Avg household size |       2.04 |    ❌ 3.44 | [Statistik Austria](https://www.statistik.at/web_de/statistiken/menschen_und_gesellschaft/bevoelkerung/haushalte_familien_lebensformen/haushalte/index.html) |
| House sqm total    | 71 208 000 | 78 003 814 | from population and sqm per person |
| Families           |    948 529 |    562 064 | from population and avg houshold size (926 000 according to official)|

## Households
Source: (2021) [Statistik Austria](https://www.statistik.at/web_de/statistiken/menschen_und_gesellschaft/bevoelkerung/haushalte_familien_lebensformen/haushalte/index.html)
| Household Type    | Austria | Vienna |
| :---------------- | ------: | -----: |
| Single            |     38% |    45% |
| Pair w/o children |     25% |    21% |
| Pair w/ children  |     27% |    20% |
| Single parent     |      6% |     9% |
| Multiperson       |      3% |     4% |
| Other             |      1% |     1% |

| Household Size | Austria | Vienna |
| :------------- | ------: | -----: |
| 1              |     38% |    45% |
| 2              |     30% |    28% |
| 3              |     14% |    13% |
| 4              |     12% |     9% |
| 5 or more      |      6% |     5% |

| Household Size | Share of Population |
| :------------- | ------------------: |
| 1              |                 17% |
| 2              |                 28% |
| 3              |                 20% |
| 4              |                 21% |
| 5              |                 10% |
| 6 or more      |                  4% |

## Schooling
Source: (2021) [Statistik Austria](https://www.statistik.at/web_de/statistiken/menschen_und_gesellschaft/bildung/schulen/schulbesuch/index.html)
| Schooling  | Austria |
| :--------- | ------: |
| Pupil      |     13% |
| Not pupil  |     87% |

## Age
Source: (2019) [Statistik Austria](https://www.statistik.at/web_de/statistiken/menschen_und_gesellschaft/bevoelkerung/volkszaehlungen_registerzaehlungen_abgestimmte_erwerbsstatistik/bevoelkerung_nach_demographischen_merkmalen/index.html)
| Age     | Austria |
| :------ | ------: |
| < 6     |      5% |
| 6 to 20 |     15% |
| > 20    |     80% |

