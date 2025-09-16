#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 16 13:09:29 2025

@author: katedamato
"""

import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px

# Load the dataset
df = pd.read_csv("https://vincentarelbundock.github.io/Rdatasets/csv/sampleSelection/Mroz87.csv", index_col=0)

# Get unique values for dropdowns
kids5_values = sorted(df['kids5'].unique())
kids618_values = sorted(df['kids618'].unique())

# Create the Dash app
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H2("Kids & Women's LFP Dashboard"),

    # Dropdown for kids5
    html.Label("Select the number of children under 5 years old:"),
    dcc.Dropdown(
        id="kids5-dropdown",
        options=[{"label": str(k), "value": k} for k in kids5_values],
        value=kids5_values[0],
        clearable=False
    ),

    # Dropdown for kids618
    html.Label("Select the number of children between 6 and 18 years old:"),
    dcc.Dropdown(
        id="kids618-dropdown",
        options=[{"label": str(k), "value": k} for k in kids618_values],
        value=kids618_values[0],
        clearable=False
    ),

    html.Br(),

    # Output 1: Pie chart
    dcc.Graph(id="pie-chart"),

    # Output 2: Histogram
    dcc.Graph(id="hours-histogram")
])

# Callback with two outputs
@app.callback(
    Output("pie-chart", "figure"),
    Output("hours-histogram", "figure"),
    Input("kids5-dropdown", "value"),
    Input("kids618-dropdown", "value")
)
def update_charts(selected_kids5, selected_kids618):
    # Filter data for selected
    filtered_df = df[
        (df["kids5"] == selected_kids5) &
        (df["kids618"] == selected_kids618)
    ]

    # --- Pie chart: working vs not working (lfp column) ---
   #Counts how many lfp=1 in the lfp column after filtering 
    pie_data = filtered_df["lfp"].value_counts().reset_index()
    #Creates a table with index, lfp, and count columns. 0 index for not working and 1 for working. 
    pie_data.columns = ["lfp", "count"]
    pie_data["lfp"] = pie_data["lfp"].map({1: "Working", 0: "Not Working"})
    
    #slice names pulled from lfp mapping above 
    pie_chart = px.pie(
        pie_data,
        names="lfp",
        values="count",
        title=f"Work Status (kids under 5={selected_kids5}, kids 6-18 = {selected_kids618})",
        hole=0.3
    )

    # --- Histogram: distribution of hours ---
    
    hist_chart = px.histogram(
        filtered_df,
        x="hours",
        nbins=20,
        title=f"Distribution of Hours (kids under 5={selected_kids5}, kids 6-18 = {selected_kids618})"
    )

    return pie_chart, hist_chart


if __name__ == "__main__":
    url = "http://127.0.0.1:9000/"
    print(f"Your Dash app is running at: {url}")

    import webbrowser
    webbrowser.open(url)
    app.run(debug=True, port=9000)
