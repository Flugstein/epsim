import xml.etree.ElementTree as ET
from parse_osm import *
import numpy as np
import csv


def extract_houses(root, node_list, outpath):
    num_houses = 0
    house_building_types = ['yes', 'apartments', 'detached', 'house', 'residential', 'semidetached_house', 'terrace', 'dormitory']
    with open(outpath, 'a') as f:
        for c1 in root:
            if c1.tag == 'way':
                tags = get_tags(c1)
                if tags.get('building') in house_building_types:  # https://wiki.openstreetmap.org/wiki/Key:building
                    if not (tags.get('man_made') or tags.get('amenity') or tags.get('layer')):  # filter out other structures
                        p = get_polygon_from_way(c1, node_list)
                        if p:
                            x, y, sqm = get_polygon_x_y_sqm(p)
                            if tags['building'] == 'yes':
                                if sqm > 50 and sqm < 400:  # filter out very small and large unspecified buildings
                                    f.write("house,{},{},{}\n".format(x, y, sqm))
                                    num_houses += 1
                            else:
                                levels = int(float(tags['building:levels'])) if 'building:levels' in tags else 1
                                f.write("house,{},{},{}\n".format(x, y, sqm * levels))
                                num_houses += 1

    print(f"Extracted {num_houses} house locations")


def extract_shops(root, node_list, outpath):
    num_supermarkets = 0
    num_shops = 0
    with open(outpath, 'a') as f:
        for c1 in root:
            tags = get_tags(c1)
            if tags.get('shop'):
                shop_tag = tags['shop']
                if c1.tag == 'way':
                    p = get_polygon_from_way(c1, node_list)
                    if not p:
                        continue
                    area = int(calc_geom_area(p))
                    x = p.centroid.x
                    y = p.centroid.y
                elif c1.tag == 'node':
                    x = c1.attrib['lon']
                    y = c1.attrib['lat']
                    if shop_tag == 'supermarket':
                        area = 1500  # default sqm for supermarket
                    else:
                        area = 500  # default sqm for shop
                else:
                    continue
                if shop_tag == 'supermarket':
                    f.write("supermarket,{},{},{}\n".format(x, y, area))
                    num_supermarkets += 1
                else:
                    f.write("shop,{},{},{}\n".format(x, y, area))
                    num_shops += 1

    print(f"Extracted {num_supermarkets} supermarket and {num_shops} shop locations")


def extract_leisure(root, node_list, outpath):
    num_restaurant = 0
    num_leisure = 0
    restaurant_tags = ['bar', 'biergarten', 'cafe', 'fast_food', 'food_court', 'ice_cream', 'pub', 'restaurant']
    entertainment_tags = ['arts_centre', 'brothel', 'casino', 'cinema', 'community_centre', 'conference_centre', 'events_venue', 'gambling', 'nightclub', 
                          'social_centre', 'stripclub', 'swingerclub', 'theatre', 'place_of_worship']
    leisure_tags = ['adult_gaming_centre', 'amusement_arcade', 'bowling_alley', 'dance', 'escape_game', 'fitness_centre', 'hackerspace', 'sauna', 
                    'sports_centre', 'sports_hall']
    with open(outpath, 'a') as f:
        for c1 in root:
            tags = get_tags(c1)
            if tags.get('amenity') or tags.get('leisure'):
                if c1.tag == 'way':
                    p = get_polygon_from_way(c1, node_list)
                    if not p:
                        continue
                    area = int(calc_geom_area(p))
                    x = p.centroid.x
                    y = p.centroid.y
                elif c1.tag == 'node':
                    x = c1.attrib['lon']
                    y = c1.attrib['lat']
                    area = 500  # default sqm
                else:
                    continue
                if tags.get('amenity') in restaurant_tags:
                    f.write("restaurant,{},{},{}\n".format(x, y, area))
                    num_restaurant += 1
                if (tags.get('amenity') in entertainment_tags) or (tags.get('leisure') in leisure_tags and tags.get('access') != 'private'):
                    f.write("leisure,{},{},{}\n".format(x, y, area))
                    num_leisure += 1

    print(f"Extracted {num_restaurant} restaurant and {num_leisure} leisure locations")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python extract_buildings.py osm_file outfile")
        exit(0)

    tree = ET.parse(sys.argv[1])
    outpath = sys.argv[2]

    root = tree.getroot()
    node_list = build_node_list(root)

    with open(outpath, 'w') as f:
        f.write("building_type,longitude,latitude,sqm\n")

    extract_houses(root, node_list, outpath)
    extract_shops(root, node_list, outpath)
    extract_leisure(root, node_list, outpath)
