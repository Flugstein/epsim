import pandas as pd
import csv
import sys

df = pd.read_csv(sys.argv[1])

for building_type in df.building_type.unique():
    df_s = df.loc[df.building_type == building_type]
    tags = {tag: len(df_s[df_s['tag'] == tag]) for tag in df_s.tag.unique()}
    print(f"{building_type}: {sum(tags.values())}")
    for tag, num in sorted(tags.items(), key=lambda x: x[1], reverse=True):
        print(f"{tag:<28} {len(df_s[df_s['tag'] == tag]):>6}")
    print()

print(f"sqm of all buildings: {df['sqm'].sum()}")
print(f"house sqm: {df[df['building_type'] == 'house']['sqm'].sum()}")
print(f"bbox: {df['longitude'].min()},{df['latitude'].min()},{df['longitude'].max()},{df['latitude'].min()}")
print(f"max sqm building: {df[df['building_type'] == 'house']['sqm'].max()}")
