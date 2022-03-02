import sys
import xml.etree.ElementTree as ET
import pyproj
from shapely import ops
from functools import partial
from shapely.geometry import Polygon, Point
import random


def build_node_list(root):
    return {int(c1.attrib['id']):(float(c1.attrib['lon']), float(c1.attrib['lat'])) for c1 in root if c1.tag == 'node'}


def get_nodes(way):
    return [int(c2.attrib['ref']) for c2 in way if c2.tag == 'nd']


def get_polygon_from_way(way, node_list):
    node_ids = get_nodes(way)
    poly_nodes = []
    for node_id in node_ids:
        try:
            poly_nodes.append(node_list[node_id])
        except KeyError:
            print(f"Warning: node with key {i} is not found, ignoring it...", file=sys.stderr)
    if len(poly_nodes) > 3:
        return Polygon(poly_nodes)
    else:
        print("Warning: location has fewer than 3 valid nodes. Omitting it.", file=sys.stderr)
        return None


# Credit to jczaplew: https://gis.stackexchange.com/questions/127607/area-in-km-from-polygon-of-coordinates
def calc_geom_area(poly):
    bounds = poly.bounds
    p = ops.transform(
        partial(
            pyproj.transform,
            pyproj.Proj('EPSG:4326'),
            pyproj.Proj(
                proj='aea',
                lat_1=bounds[1],
                lat_2=bounds[3])),
        poly)
    return p.area


def get_polygon_x_y_sqm(poly):
    return poly.centroid.x, poly.centroid.y, int(calc_geom_area(poly))


def random_points_within(poly, num_points):
    min_x, min_y, max_x, max_y = poly.bounds
    points = []
    while len(points) < num_points:
        random_point = Point(
            [random.uniform(min_x, max_x), random.uniform(min_y, max_y)])
        if (random_point.within(poly)):
            points.append(random_point)

    return points


def get_tags(c1):
    return {c2.attrib['k']: c2.attrib['v'] for c2 in c1 if c2.tag == 'tag'}


def get_tag(c2, tag_type):
    if c2.tag == 'tag':
        if c2.attrib['k'] == tag_type:
            return c2.attrib['v']
    return None
