import csv
import sys
import yaml
import os
import numpy as np
import random
import pickle
from epsim import Location

# File to read in CSV files of building definitions.
# The format is as follows:
# No,building,Longitude,Latitude,Occupancy

def apply_building_mapping(mapdict, label):
    """
    Applies a building map YAML to a given label, binning it
    into the appropriate category.
    """
    if label == 'house':
        return label
    for category in mapdict:
        if label in mapdict[category]['labels']:
            return category
    return None


def calc_dist(x1, y1, x2, y2):
        return (np.abs(x1-x2)**2 + np.abs(y1-y2)**2)**0.5


def calc_dist_cheap(x1, y1, x2, y2):
    return np.abs(x1-x2) + np.abs(y1-y2)


def read_building_csv(e, csvpath, building_type_map="input_data/building_types_map.yml"):
    if os.path.isfile(csvpath + ".p"):
        pickle_data = pickle.load(open(csvpath + ".p", "rb"))
        house_locs = pickle_data['house_locs']
        locations = pickle_data['locations']
        house_nearest_locs = pickle_data['house_nearest_locs']
    else:
        building_mapping = {}
        with open(building_type_map) as f:
            building_mapping = yaml.safe_load(f)

        house_locs = []
        locations = {}

        with open(csvpath) as f:
            building_reader = csv.reader(f)
            row_number = 0
            office_sqm = 0
            xbound = [99999.0, -99999.0]
            ybound = [99999.0, -99999.0]

            for row in building_reader:
                if row_number == 0:
                    row_number += 1
                    continue

                loc_type = apply_building_mapping(building_mapping, row[0])
                if loc_type == None:
                    continue

                x = float(row[1])
                y = float(row[2])
                xbound[0] = min(x, xbound[0])
                ybound[0] = min(y, ybound[0])
                xbound[1] = max(x, xbound[1])
                ybound[1] = max(y, ybound[1])

                sqm = int(row[3])

                if loc_type == 'house':
                    house_locs.append((x, y))
                else:
                    if loc_type not in locations:
                        locations[loc_type] = []
                    locations[loc_type].append((x, y, sqm))

                row_number += 1

            print(row_number, "read", file=sys.stderr)
            print("bounds:", xbound, ybound, file=sys.stderr)

        # find nearest location for every house
        house_nearest_locs = [{} for house in house_locs]
        for h, house_loc in enumerate(house_locs):
            for loc_type, locs in locations.items():
                min_dist = 99999.0
                for i, loc in enumerate(locs):
                    d = calc_dist(house_loc[0], house_loc[1], loc[0], loc[1])
                    if d < min_dist:
                        min_dist = d
                        house_nearest_locs[h][loc_type] = i

        pickle_data = {'house_locs': house_locs, 'locations': locations, 'house_nearest_locs': house_nearest_locs}
        pickle.dump(pickle_data, open(csvpath + ".p", "wb"))


    e.locations = {loc_type: [Location(loc_type, loc[0], loc[1], loc[2]) for loc in locs] for loc_type, locs in locations.items()}
    #family_house = [i % len(house_locs) for i, family in enumerate(e.families)]  # distribute families to houses
    family_house = [random.randint(0, len(house_locs) - 1) for i, family in enumerate(e.families)]  # distribute families to houses
    e.nearest_locs = [{loc_type: locs[house_nearest_locs[family_house[f]][loc_type]] for loc_type, locs in e.locations.items()} for f, family in enumerate(e.families)]

    print(f"read in {len(house_locs)} houses and {sum(len(locs) for loc_type, locs in locations.items())} other locations")
