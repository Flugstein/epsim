# Sanity checks and Statistical Data
## Cities
### Salzburg
[Salzburg OSM source](https://overpass-api.de/api/map?bbox=12.9968,47.7684,13.0940,47.8341)
| Sanity Check       |  Official  | Simulation | Source |
| :----------------- | ---------: | ---------: | :----- |
| Population         |    179 614 |    179 619 | (with sec. residence, 2021) [Stadt Salzburg](https://www.stadt-salzburg.at/statistik-bevoelkerung/)|
| Sqm per person     |       43.5 |       39.6 | (Salzburg state, 2021) [Statistik Austria](https://www.statistik.at/web_de/statistiken/menschen_und_gesellschaft/wohnen/wohnsituation/081235.html) |
| Avg household size |       2.05 |       2.13 | [Similio](https://simil.io/politisch/salzburg-stadt/salzburg/haushaltsgroesse) |
| House sqm total    |          ? |  7 116 945 | |
| Households         |     87 616 |     84 378 | from population and avg houshold size |
| Sqm per household  |         97 |         84 | (Salzburg state, 2021) [Statistik Austria](https://www.statistik.at/web_de/statistiken/menschen_und_gesellschaft/wohnen/wohnsituation/081235.html) |

### Graz
[Graz OSM source](https://overpass-api.de/api/map?bbox=15.3762,47.0232,15.5045,47.1240)
| Sanity Check       |  Official  | Simulation | Source |
| :----------------- | ---------: | ---------: | :----- |
| Population         |    333 049 |    333 057 | (with sec. residence, 2021) [Stadt Graz](https://www.graz.at/cms/beitrag/10034466/7772565/Zahlen_Fakten_Bevoelkerung_Bezirke_Wirtschaft.html) |
| Sqm per person     |       49.2 |       51.6 | (Styria, 2021) [Statistik Austria](https://www.statistik.at/web_de/statistiken/menschen_und_gesellschaft/wohnen/wohnsituation/081235.html) |
| Avg household size |       2.03 |       2.13 | [Similio](https://simil.io/politisch/graz-stadt/graz/haushaltsgroesse) |
| House sqm total    |          ? | 17 169 552 | |
| Households         |    164 063 |    156 457 | from population and avg houshold size |
| Sqm per household  |        108 |        110 | (Styria, 2021) [Statistik Austria](https://www.statistik.at/web_de/statistiken/menschen_und_gesellschaft/wohnen/wohnsituation/081235.html) |

### Vienna
[Vienna OSM source](https://overpass-api.de/api/map?bbox=16.2172,48.1304,16.5399,48.2846)
| Sanity Check       |  Official  | Simulation | Source |
| :----------------- | ---------: | ---------: | :----- |
| Population         |  1 935 000 |  1 935 012 | (2021) [Stadt Wien](https://www.wien.gv.at/statistik/bevoelkerung/bevoelkerungsstand/) |
| Sqm per person     |       36.8 |       40.3 | (Wien, 2021) [Statistik Austria](https://www.statistik.at/web_de/statistiken/menschen_und_gesellschaft/wohnen/wohnsituation/081235.html) |
| Avg household size |       2.04 |       2.13 | [Statistik Austria](https://www.statistik.at/web_de/statistiken/menschen_und_gesellschaft/bevoelkerung/haushalte_familien_lebensformen/haushalte/index.html) |
| House sqm total    | 71 208 000 | 78 003 814 | from population and sqm per person |
| Households         |    948 529 |    908 989 | from population and avg houshold size (926 000 according to official) |
| Sqm per household  |         75 |         86 | (Vienna, 2021) [Statistik Austria](https://www.statistik.at/web_de/statistiken/menschen_und_gesellschaft/wohnen/wohnsituation/081235.html) |

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

