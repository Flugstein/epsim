# Epidemic Simulation
COVID-19 epidemic simulation modeling family, schools, offices and leisure activities based on open street map data.

## Prepare OSM data
- Obtain an OSM XML file containing the region you want to simulate. This can be done by using the OSM export feature on [openstreetmap.org](https://openstreetmap.org).
- Find the population and average household size of your region. This is necessary, because currently houses are not extracted, but generated randomly in residential areas.
- Run `python osm/extract_buildings.py osm_file.xml outfile.csv population avg_household_size` to extract buildings and save them in a CSV file.

## Run
- For examples on how to use the API see `epsim_plot.ipynb`
- If you do not call `read_building_csv()` while setting up the Epsim object, the simulation runs without leisure activites.
