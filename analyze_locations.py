import plotly.express as px
import plotly.graph_objects as go
import  plotly as py
import pandas as pd
import sys

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python analyze_locations.py buildings.csv out.html")
        exit(0)

    buildings_csv_path = sys.argv[1]
    outpath = sys.argv[2]

    df = pd.read_csv(buildings_csv_path, delimiter=',')
    df.columns = ['type', 'x', 'y', 'area']
    groups = df.groupby('type').count()
    type = ['house', 'shop', 'supermarket', 'restaurant', 'leisure']
    df['color'] = 0
    for index, row in df.iterrows():
        df['color'][index] = type.index(row['type'])

    fig = px.scatter_mapbox(df, lat="y", lon="x",
                            hover_name="type",
                            color = 'color',
                            color_continuous_scale=["crimson", "darkgreen", "gold", "purple", "blue"],
                            zoom=8,  height=800)
    fig.update_layout(mapbox_style="open-street-map")
    py.offline.plot(fig, filename=outpath)
