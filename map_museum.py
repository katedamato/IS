#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 11 11:44:39 2025

@author: katedamato
"""
import geopandas as gpd
import matplotlib.pyplot as plt
import plotly.express as px
import folium
import plotly.io as pio
import os
import webbrowser

pio.renderers.default = "browser"

url = "https://www2.census.gov/geo/tiger/GENZ2022/shp/cb_2022_us_state_20m.zip"
states = gpd.read_file(url)
states.head()


#==========Built in .plot() function==========
states.plot(edgecolor="black")

#Easy but static, viewable in plots tab 

#==========Matplotlib==========
fig, ax = plt.subplots(figsize=(12, 8))
states.plot(ax=ax, edgecolor="black", facecolor="lightgray")
ax.set_title("US States Boundary Map")
plt.show()

#Still static but more control over styling 

#==========Plotly ==========
fig = px.choropleth(
    states,
    geojson=states.__geo_interface__,
    locations=states.index,
    color="ALAND",  # land area
    color_continuous_scale="Viridis"
)
fig.update_geos(fitbounds="locations", visible=False)
fig.show()
#Interactive, easy to integrate with dashboard **** probably use this one 

#========== Folium ==========
# Create the map
m = folium.Map(location=[37.8, -96], zoom_start=4)
folium.GeoJson(states).add_to(m)

# Save HTML file
html_file = "us_states_map.html"
m.save(html_file)

# Get the absolute path
file_path = os.path.abspath(html_file)

# Open in new browser tab
webbrowser.open_new_tab(f"file://{file_path}")

#map overlay, good for web browswer map but less integrated with dashboard 


