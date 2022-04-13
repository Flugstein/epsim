import xml.etree.ElementTree as ET
from parse_osm import *
import numpy as np
import csv


def write_line(f, cat, tag, x, y, sqm):
    f.write(f"{cat},{tag},{x},{y},{sqm}\n")


def extract_houses(root, node_list, outpath):
    # https://wiki.openstreetmap.org/wiki/Key:building
    house_building_types = ['yes', 'apartments', 'detached', 'house', 'residential', 'semidetached_house', 'terrace', 'dormitory']
    with open(outpath, 'a') as f:
        for c1 in root:
            if c1.tag == 'way':
                tags = get_tags(c1)
                building_tag = tags.get('building')
                if building_tag in house_building_types:
                    if not (tags.get('man_made') or tags.get('amenity') or tags.get('layer')):  # filter out other structures
                        p = get_polygon_from_way(c1, node_list)
                        if p:
                            x, y, sqm = get_polygon_x_y_sqm(p)
                            if building_tag == 'yes':
                                if sqm > 50 and sqm < 400:  # filter out very small and large unspecified buildings
                                    write_line(f, 'house', building_tag, x, y, sqm)
                            else:
                                if 'building:levels' in tags and tags['building:levels'].isnumeric():
                                    levels = int(tags['building:levels'])
                                else:
                                    levels = 1
                                write_line(f, 'house', building_tag, x, y, sqm * levels)


def extract_shops(root, node_list, outpath):
    # https://wiki.openstreetmap.org/wiki/Key:shop
    # [1] https://de.statista.com/statistik/daten/studie/289775/umfrage/verkaufsflaeche-je-filiale-der-unternehmen-im-lebensmittelhandel-in-oesterreich/
    # [2] https://de.statista.com/statistik/daten/studie/297045/umfrage/verkaufsflaeche-der-groessten-lebensmittelhaendler-in-oesterreich/
    # [3] https://de.statista.com/statistik/daten/studie/895728/umfrage/verkaufsflaeche-im-stationaeren-einzelhandel-in-oesterreich/
    # [4] https://de.statista.com/statistik/daten/studie/283959/umfrage/unternehmen-im-einzelhandel-in-oesterreich/
    # [5] https://de.statista.com/statistik/daten/studie/1191398/umfrage/shopgroesse-in-ausgewaehlten-staedten-und-einkaufsstrassen-in-oesterreich/
    with open(outpath, 'a') as f:
        for c1 in root:
            tags = get_tags(c1)
            if tags.get('shop'):
                shop_tag = tags['shop']
                if c1.tag == 'way':
                    p = get_polygon_from_way(c1, node_list)
                    if not p:
                        continue
                    sqm = int(calc_geom_area(p))
                    x = p.centroid.x
                    y = p.centroid.y
                elif c1.tag == 'node':
                    x = c1.attrib['lon']
                    y = c1.attrib['lat']
                    if shop_tag == 'supermarket':
                        sqm = 525  # default sqm for supermarket: avg in Austria ~700sqm [1][2], but should be smaller for urban regions
                    else:
                        sqm = 114  # default sqm for shop: avg in Austria ~368sqm [3][4], in Salzburg 114sqm [5]
                else:
                    continue
                if shop_tag == 'supermarket':
                    write_line(f, 'supermarket', shop_tag, x, y, sqm)
                else:
                    write_line(f, 'shop', shop_tag, x, y, sqm)


def extract_leisure(root, node_list, outpath):
    # https://wiki.openstreetmap.org/wiki/Key:amenity
    # https://wiki.openstreetmap.org/wiki/Key:leisure
    restaurant_tags = ['biergarten', 'cafe', 'fast_food', 'food_court', 'ice_cream', 'restaurant']
    nightlife_tags = ['bar', 'pub', 'nightclub', 'stripclub', 'swingerclub', 'brothel']
    entertainment_tags = ['arts_centre', 'casino', 'cinema', 'community_centre', 'conference_centre', 'events_venue', 'gambling',
                          'social_centre', 'theatre']
    leisure_tags = ['adult_gaming_centre', 'amusement_arcade', 'bowling_alley', 'dance', 'escape_game', 'fitness_centre', 'hackerspace',
                    'sauna', 'sports_centre', 'sports_hall']
    with open(outpath, 'a') as f:
        for c1 in root:
            tags = get_tags(c1)
            amenity_tag = tags.get('amenity')
            leisure_tag = tags.get('leisure')
            if amenity_tag or leisure_tag:
                if c1.tag == 'way':
                    p = get_polygon_from_way(c1, node_list)
                    if not p:
                        continue
                    sqm = int(calc_geom_area(p))
                    x = p.centroid.x
                    y = p.centroid.y
                elif c1.tag == 'node':
                    x = c1.attrib['lon']
                    y = c1.attrib['lat']
                    sqm = 500  # default sqm
                else:
                    continue
                if amenity_tag in restaurant_tags:
                    write_line(f, 'restaurant', amenity_tag, x, y, sqm)
                elif amenity_tag in nightlife_tags:
                    write_line(f, 'nightlife', amenity_tag, x, y, sqm)
                elif leisure_tag in nightlife_tags:
                    write_line(f, 'nightlife', leisure_tag, x, y, sqm)
                elif amenity_tag in entertainment_tags and tags.get('access') != 'private':
                    write_line(f, 'leisure', amenity_tag, x, y, sqm)
                elif leisure_tag in leisure_tags and tags.get('access') != 'private':
                    write_line(f, 'leisure', leisure_tag, x, y, sqm)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python extract_buildings.py osm_file outfile")
        exit(0)

    tree = ET.parse(sys.argv[1])
    outpath = sys.argv[2]

    root = tree.getroot()
    node_list = build_node_list(root)

    with open(outpath, 'w') as f:
        f.write("building_type,tag,longitude,latitude,sqm\n")

    extract_houses(root, node_list, outpath)
    extract_shops(root, node_list, outpath)
    extract_leisure(root, node_list, outpath)
