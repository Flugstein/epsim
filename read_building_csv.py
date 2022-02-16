import csv
import sys
import yaml

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

def read_building_csv(e, csvfile, building_type_map="input_data/building_types_map.yml"):
  building_mapping = {}
  with open(building_type_map) as f:
    building_mapping = yaml.safe_load(f)

  house_locs = []
  num_locs = 0

  with open(csvfile) as csvfile:
    building_reader = csv.reader(csvfile)
    row_number = 0
    office_sqm = 0
    xbound = [99999.0,-99999.0]
    ybound = [99999.0,-99999.0]

    for row in building_reader:
      if row_number == 0:
        row_number += 1
        continue

      location_type = apply_building_mapping(building_mapping, row[0])
      if location_type == None:
        continue

      x = float(row[1])
      y = float(row[2])
      xbound[0] = min(x,xbound[0])
      ybound[0] = min(y,ybound[0])
      xbound[1] = max(x,xbound[1])
      ybound[1] = max(y,ybound[1])

      sqm = int(row[3])

      if location_type == 'house':
        house_locs.append((x, y))
      else:
        e.add_location(num_locs, location_type, x, y, sqm)
        num_locs += 1

      row_number += 1

    print(row_number, "read", file=sys.stderr)
    print("bounds:", xbound, ybound, file=sys.stderr)

  for i, family in enumerate(e.families):
    e.family_locs.append(house_locs[i % len(house_locs)])

  e.update_nearest_locs()

  print(f"read in {len(house_locs)} houses and {num_locs} other locations")
