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

# Ensure kids columns are numeric and drop NA for the slider marks
df["kids5"] = pd.to_numeric(df["kids5"], errors="coerce")
df["kids618"] = pd.to_numeric(df["kids618"], errors="coerce")

kids5_values = sorted(df["kids5"].dropna().astype(int).unique())
kids618_values = sorted(df["kids618"].dropna().astype(int).unique())

# Create the Dash app
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H2("Kids & Women's LFP Dashboard"),
    
    # Sliders
    html.Label("Select the number of children under 5 years old:"),
    dcc.RangeSlider(
        id="kids5-slider",
        min=min(kids5_values),
        max=max(kids5_values),
        step=1,
        value=[min(kids5_values), max(kids5_values)],
        marks={int(k): str(int(k)) for k in kids5_values},
        allowCross=False
    ),

    html.Label("Select the number of children between 6 and 18 years old:"),
    dcc.RangeSlider(
        id="kids618-slider",
        min=min(kids618_values),
        max=max(kids618_values),
        step=1,
        value=[min(kids618_values), max(kids618_values)],
        marks={int(k): str(int(k)) for k in kids618_values},
        allowCross=False
    ),

    html.Br(),

    # Container for side-by-side charts
    html.Div([
        # Left: Pie chart
        html.Div(dcc.Graph(id="pie-chart"), style={"flex": "1", "marginRight": "20px"}),

        # Right: Histogram + summary
        html.Div([
            dcc.Graph(id="hours-histogram"),
            html.Div(id="hours-summary", style={"marginTop": "10px", "fontWeight": "bold"})
        ], style={"flex": "1"})
    ], style={"display": "flex", "alignItems": "flex-start"})
])

# Callback with three outputs 
@app.callback(
    Output("pie-chart", "figure"),
    Output("hours-histogram", "figure"),
    Output("hours-summary", "children"),  # new output for summary stats
    Input("kids5-slider", "value"),
    Input("kids618-slider", "value")
)
def update_charts(kids5_range, kids618_range):
    # normalize slider input to (low, high) ints
    #all_values is full set of possible values for the slider
    def norm_range(rng, all_values):
        """Convert slider input into a (low, high) integer range."""
        # If slider is None, use the full range
        if rng is None:
            return min(all_values), max(all_values)

        # If slider returns a single number
        if isinstance(rng, (int, float)):
            return int(rng), int(rng)

        # If slider returns a list or tuple [low, high]
        if isinstance(rng, (list, tuple)) and len(rng) == 2:
            return int(rng[0]), int(rng[1])

        # Fallback to full range just in case
        return min(all_values), max(all_values)

    # Now call the helper function
    k5_lo, k5_hi = norm_range(kids5_range, kids5_values)
    k618_lo, k618_hi = norm_range(kids618_range, kids618_values)


    # Filter data for selected ranges
    filtered_df = df[
        df["kids5"].between(k5_lo, k5_hi, inclusive="both") &
        df["kids618"].between(k618_lo, k618_hi, inclusive="both")
    ]

    title_suffix = f"(kids under 5 = {k5_lo}–{k5_hi}, kids 6–18 = {k618_lo}–{k618_hi})"

    
    # --- Pie chart: working vs not working (lfp column) ---
    pie_data = filtered_df["lfp"].value_counts().rename_axis("lfp").reset_index(name="count")
    pie_data["lfp"] = pie_data["lfp"].map({1: "Working", 0: "Not Working"}).fillna(pie_data["lfp"].astype(str))

    pie_chart = px.pie(
        pie_data,
        names="lfp",
        values="count",
        title=f"Work Status {title_suffix}",
        hole=0.3
    )

    # --- Histogram: distribution of hours (exclude zeros) ---
    hist_df = filtered_df[filtered_df["hours"] > 0]

    hist_chart = px.histogram(
        hist_df,
        x="hours",
        nbins=20,
        title=f"Distribution of Hours {title_suffix}"
    )

    # --- Summary statistics ---
    if not hist_df.empty:
        mean_hours = hist_df["hours"].mean()
        std_hours = hist_df["hours"].std()
        summary_text = f"Average hours: {mean_hours:.2f}, Std Dev: {std_hours:.2f}"
    else:
        summary_text = "No positive hours for selected range"

    return pie_chart, hist_chart, summary_text



if __name__ == "__main__":
    url = "http://127.0.0.1:9000/"
    print(f"Your Dash app is running at: {url}")

    import webbrowser
    webbrowser.open(url)
    app.run(debug=True, port=9000)
