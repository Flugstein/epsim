import csv
import os
import numpy as np
import random
import pickle
import heapq
import itertools
from collections import Counter
from epsim import Location

# Read csv file of buildings and compute nearest locations.
# The format is:
# building_type,longitude,latitude,sqm


def calc_dist(x1, y1, x2, y2):
    return (np.abs(x1-x2)**2 + np.abs(y1-y2)**2)**0.5


def calc_dist_cheap(x1, y1, x2, y2):
    return np.abs(x1-x2) + np.abs(y1-y2)


def calc_dist_house(loc, house_loc):
    return calc_dist(house_loc.x, house_loc.y, loc.x, loc.y)


class HouseLocation:
    def __init__(self, x, y, sqm):
        self.x = x
        self.y = y
        self.sqm = sqm


class PreprocLocation:
    def __init__(self, tag, x, y, sqm, idx):
        self.tag = tag
        self.x = x
        self.y = y
        self.sqm = sqm
        self.idx = idx


def get_visit_locs_supermarket(house_loc, locs):
    # choose 3 nearest locations
    return heapq.nsmallest(3, locs, key=lambda loc: calc_dist_house(loc, house_loc))

def get_visit_locs_shop(house_loc, locs):
    # choose 5 tags at random with tags weighted by occurances, pick neastest location per chosen tag
    tag_counts = Counter([loc.tag for loc in locs])
    chosen_tags = random.choices(list(tag_counts.keys()), weights=list(tag_counts.values()), k=5)
    return [min({loc: calc_dist_house(loc, house_loc) for loc in [loc for loc in locs if loc.tag == tag]}.items(), key=lambda x: x[1])[0]
            for tag in chosen_tags]

def get_visit_locs_restaurant(house_loc, locs):
    # choose 5 locations uniformly at random
    return random.choices(locs, k=5)

def get_visit_locs_leisure(house_loc, locs):
    return get_visit_locs_shop(house_loc, locs)

def get_visit_locs_nightlife(house_loc, locs):
    return get_visit_locs_restaurant(house_loc, locs)

get_visit_locs = {
    'supermarket': get_visit_locs_supermarket,
    'shop': get_visit_locs_shop,
    'restaurant': get_visit_locs_restaurant,
    'leisure': get_visit_locs_leisure,
    'nightlife': get_visit_locs_nightlife
}


def read_building_csv(e, csvpath):
    if os.path.isfile(csvpath + ".p"):
        pickle_data = pickle.load(open(csvpath + ".p", "rb"))
        house_locs = pickle_data['house_locs']
        locations = pickle_data['locations']
    else:
        house_locs = []
        locations = {}
        loc_idx = 0
        with open(csvpath) as f:
            csvreader = csv.reader(f)
            fields = next(csvreader)
            assert(fields == ['building_type', 'tag', 'longitude', 'latitude', 'sqm'])
            for row in csvreader:
                loc_type = row[0]
                tag = row[1]
                x = float(row[2])
                y = float(row[3])
                sqm = int(row[4])
                if loc_type == 'house':
                    house_locs.append(HouseLocation(x, y, sqm))
                else:
                    if loc_type not in locations:
                        locations[loc_type] = []
                    locations[loc_type].append(PreprocLocation(tag, x, y, sqm, loc_idx))
                    loc_idx += 1

        pickle_data = {'house_locs': house_locs, 'locations': locations}
        pickle.dump(pickle_data, open(csvpath + ".p", "wb"))

    e.locations = {loc_type: [Location(loc_type, loc.tag, loc.x, loc.y, loc.sqm) for loc in locs]
                   for loc_type, locs in locations.items()}

    # distribute families to houses
    # [1] https://www.statistik.at/web_de/statistiken/menschen_und_gesellschaft/wohnen/wohnsituation/081235.html
    random.shuffle(house_locs)
    house_families = []
    family_i = 0
    for house_i, house_loc in enumerate(house_locs):
        families = []
        sqm = house_loc.sqm
        if family_i > len(e.families) - 1:
            print(f"{len(house_locs) - house_i} houses remain empty")
            break
        while sqm > 0 and family_i < len(e.families):
            # family_houses[family_i] = house_i
            families.append(family_i)
            sqm -= 100  # 100 sqm per family for multifamily houses [1]
            family_i += 1
        house_families.append(families)
    
    if family_i < len(e.families) - 1:
        print(f"{len(e.families) - 1 - family_i} families did not get a house, they are randomly distributed to occupied houses")
        while family_i < len(e.families) - 1:
            random.choice(house_families).append(family_i)
            #family_houses[family_i] = random.randint(0, len(house_locs) - 1)
            family_i += 1
    
    e.house_families = house_families

    # get visit locations for every house
    e.house_visit_locs = [{loc_type: get_visit_locs[loc_type](house_loc, locs)
                           for loc_type, locs in e.locations.items()}
                          for house_loc in house_locs]

    print(f"read in {len(house_locs)} houses and {sum(len(locs) for loc_type, locs in locations.items())} other locations")
