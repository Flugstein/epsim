import csv
import os
import numpy as np
import random
import pickle
from epsim import Location

# Read csv file of buildings and compute nearest locations.
# The format is:
# building_type,longitude,latitude,sqm

def calc_dist(x1, y1, x2, y2):
        return (np.abs(x1-x2)**2 + np.abs(y1-y2)**2)**0.5


def calc_dist_cheap(x1, y1, x2, y2):
    return np.abs(x1-x2) + np.abs(y1-y2)


def read_building_csv(e, csvpath):
    if os.path.isfile(csvpath + ".p"):
        pickle_data = pickle.load(open(csvpath + ".p", "rb"))
        house_locs = pickle_data['house_locs']
        locations = pickle_data['locations']
        house_nearest_locs = pickle_data['house_nearest_locs']
    else:
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

                loc_type = row[0]

                x = float(row[1])
                y = float(row[2])
                xbound[0] = min(x, xbound[0])
                ybound[0] = min(y, ybound[0])
                xbound[1] = max(x, xbound[1])
                ybound[1] = max(y, ybound[1])

                sqm = int(row[3])

                if loc_type == 'house':
                    house_locs.append((x, y, sqm))
                else:
                    if loc_type not in locations:
                        locations[loc_type] = []
                    locations[loc_type].append((x, y, sqm))

                row_number += 1

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

    # distribute families to houses
    random.shuffle(house_locs)
    family_house = [0 for family in e.families]
    family_i = 0
    for house_i, house_loc in enumerate(house_locs):
        sqm = house_loc[2]
        if family_i > len(e.families) - 1:
            print(f"{len(house_locs) - house_i} houses remain empty")
            break
        while sqm > 0 and family_i < len(e.families):
            family_house[family_i] = house_i
            sqm -= 100  # 100 sqm per family for multifamily houses (https://www.statistik.at/web_de/statistiken/menschen_und_gesellschaft/wohnen/wohnsituation/081235.html)
            family_i += 1
    
    if family_i < len(e.families) - 1:
        print(f"{len(e.families) - 1 - family_i} families did not get a house, they are randomly distributed to occupied houses")
        while family_i < len(e.families) - 1:
            family_house[family_i] = random.randint(0, len(house_locs) - 1)
            family_i += 1

    e.nearest_locs = [{loc_type: locs[house_nearest_locs[family_house[f]][loc_type]] for loc_type, locs in e.locations.items()} for f, family in enumerate(e.families)]

    print(f"read in {len(house_locs)} houses and {sum(len(locs) for loc_type, locs in locations.items())} other locations")
