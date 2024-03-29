# Epidemic Simulation
COVID-19 epidemic simulation modeling households, schools, offices, shopping and leisure activities based on open street map data.
Shopping and leisure activity simulation based on [FACS](https://github.com/djgroen/facs).

## Prepare OSM data
- Obtain an OSM XML file containing the region you want to simulate. This can be done by using the export feature on [openstreetmap.org](https://openstreetmap.org). For example [Salzburg](https://overpass-api.de/api/map?bbox=12.9968,47.7684,13.0940,47.8341).
- Use `osm/extract_buildings.py` to extract buildings and save them in a CSV file.

## Run
- For examples on how to use the API see `epsim_plot.ipynb`
- If you do not call `read_building_csv()` while setting up the Epsim object, only households, schools and offices are simulated.
