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
                if 'building' in tags and tags['building'] in house_building_types:  # https://wiki.openstreetmap.org/wiki/Key:building
                    if not ('man_made' in tags or 'amenity' in tags or 'layer' in tags):  # filter out other structures
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


def extract_leisure(root, node_list, outpath):
    """
    Extract leisure locations from open street map file.
    """
    num_leisure = 0
    num_parks = 0
    with open(outpath, 'a') as f:
        for c1 in root:
            if c1.tag == 'way':
                for c2 in c1:
                    leisure_tag = get_tag(c2, 'leisure')
                    if leisure_tag:
                        p = get_polygon_from_way(c1, node_list)
                        if p:
                            if leisure_tag in ['park', 'garden', 'nature_reserve']:
                                f.write("park,{},{},{}\n".format(p.centroid.x, p.centroid.y, int(calc_geom_area(p))))
                                num_parks += 1
                            else:
                                f.write("leisure,{},{},{}\n".format(p.centroid.x, p.centroid.y, int(calc_geom_area(p))))
                                num_leisure += 1

    print(f"Extracted {num_leisure} leisure and {num_parks} park locations")


def extract_shops(root, node_list, outpath):
    num_supermarket = 0
    num_shopping = 0
    with open(outpath, 'a') as f:
        for c1 in root:
            if c1.tag == 'way':
                for c2 in c1:
                    if get_tag(c2, 'shop') == 'supermarket' or get_tag(c2, 'building') == 'supermarket':
                        p = get_polygon_from_way(c1, node_list)
                        if p:
                            f.write("supermarket,{},{},{}\n".format(p.centroid.x, p.centroid.y, int(calc_geom_area(p))))
                            num_supermarket += 1
                    elif get_tag(c2, 'shop'):
                        p = get_polygon_from_way(c1, node_list)
                        if p:
                            f.write("shopping,{},{},{}\n".format(p.centroid.x, p.centroid.y, int(calc_geom_area(p))))
                            num_shopping += 1

    print(f"Extracted {num_supermarket} supermarket and {num_shopping} shopping locations")


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
    extract_leisure(root, node_list, outpath)
    extract_shops(root, node_list, outpath)
