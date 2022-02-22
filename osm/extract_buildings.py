import xml.etree.ElementTree as ET
from parse_osm import *
import numpy as np
import csv


def extract_houses(root, node_list, outpath, population, avg_household_size):
    """
    Extract houses from open street map file.
    Since information on individual houses is not always available, houses are generated randomly across residential areas.
    """
    num_houses = int(population / avg_household_size)

    residential_areas = []
    total_area = 0
    for c1 in root:
        if c1.tag == 'way':
            for c2 in c1:
                if get_tag(c2, 'landuse') == 'residential':
                    p = get_polygon_from_way(c1, node_list)
                    if p:
                        area = int(calc_geom_area(p))
                        residential_areas.append((p, p.centroid.x, p.centroid.y, area))
                        total_area += area

    num_actual_houses = 0
    with open(outpath, 'a') as f:
        for ra in residential_areas:
            num_houses_ra = int(num_houses * ra[3] / total_area)
            num_actual_houses += num_houses_ra
            points = random_points_within(ra[0], num_houses_ra)
            for h in points:
                f.write("house,{},{},{}\n".format(h.x, h.y, 0))
    
    print(f"Extracted {num_actual_houses} house locations")


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
    if len(sys.argv) != 5:
        print("usage: python extract_buildings.py osm_file outfile population avg_household_size")
        exit(0)

    tree = ET.parse(sys.argv[1])
    outpath = sys.argv[2]
    population = int(sys.argv[3])
    avg_household_size = float(sys.argv[4])

    root = tree.getroot()
    node_list = build_node_list(root)

    with open(outpath, 'w') as f:
        f.write("building_type,longitude,latitude,sqm\n")

    extract_houses(root, node_list, outpath, population, avg_household_size)
    extract_leisure(root, node_list, outpath)
    extract_shops(root, node_list, outpath)
