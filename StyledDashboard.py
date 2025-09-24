#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thurs Sept 25 1:04:37 2025

@author: katedamato
"""
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

# Load dataset
df = pd.read_csv("https://vincentarelbundock.github.io/Rdatasets/csv/sampleSelection/Mroz87.csv", index_col=0)

# Clean numeric columns
df["kids5"] = pd.to_numeric(df["kids5"], errors="coerce")
df["kids618"] = pd.to_numeric(df["kids618"], errors="coerce")

kids5_values = sorted(df["kids5"].dropna().astype(int).unique())
kids618_values = sorted(df["kids618"].dropna().astype(int).unique())

# Create Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H2("Kids & Women's LFP Dashboard", 
                        className="text-center mb-4"), width=12)
    ]),

    # Sliders inside cards
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("Children under 5"),
            dbc.CardBody([
                dcc.RangeSlider(
                    id="kids5-slider",
                    min=min(kids5_values),
                    max=max(kids5_values),
                    step=1,
                    value=[min(kids5_values), max(kids5_values)],
                    marks={int(k): str(int(k)) for k in kids5_values},
                    allowCross=False
                )
            ])
        ]), width=6),

        dbc.Col(dbc.Card([
            dbc.CardHeader("Children aged 6–18"),
            dbc.CardBody([
                dcc.RangeSlider(
                    id="kids618-slider",
                    min=min(kids618_values),
                    max=max(kids618_values),
                    step=1,
                    value=[min(kids618_values), max(kids618_values)],
                    marks={int(k): str(int(k)) for k in kids618_values},
                    allowCross=False
                )
            ])
        ]), width=6),
    ], className="mb-4"),

    # Charts row
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("Work Status"),
            dbc.CardBody(dcc.Graph(id="pie-chart"))
        ]), width=6),

        dbc.Col(dbc.Card([
            dbc.CardHeader("Hours Distribution"),
            dbc.CardBody([
                dcc.Graph(id="hours-histogram"),
                html.Div(id="hours-summary", 
                         className="mt-2 fw-bold text-center")
            ])
        ]), width=6),
    ])
], fluid=True)


# Callback with three outputs 
@app.callback(
    Output("pie-chart", "figure"),
    Output("hours-histogram", "figure"),
    Output("hours-summary", "children"),  # new output for summary stats
    Input("kids5-slider", "value"),
    Input("kids618-slider", "value")
)
def update_charts(kids5_range, kids618_range):
  
   # NUnpacking range into high and low values 
    k5_lo, k5_hi = int(kids5_range[0]), int(kids5_range[1])
    k618_lo, k618_hi = int(kids618_range[0]), int(kids618_range[1])

    # Filter dataset
    filtered_df = df[
        df["kids5"].between(k5_lo, k5_hi) &
        df["kids618"].between(k618_lo, k618_hi)
    ]

    title_suffix = f"(kids under 5 = {k5_lo}–{k5_hi}, kids 6–18 = {k618_lo}–{k618_hi})"

    
  # Pie chart
    pie_data = filtered_df["lfp"].value_counts().rename_axis("lfp").reset_index(name="count")
    pie_data["lfp"] = pie_data["lfp"].map({1: "Working", 0: "Not Working"}).fillna(pie_data["lfp"].astype(str))

    pie_chart = px.pie(pie_data, names="lfp", values="count",
                       title=f"Work Status {title_suffix}", hole=0.3)

    # Histogram (exclude zeros)
    hist_df = filtered_df[filtered_df["hours"] > 0]
    hist_chart = px.histogram(hist_df, x="hours", nbins=20,
                              title=f"Distribution of Hours {title_suffix}")

    # Summary stats
    if not hist_df.empty:
        mean_hours = hist_df["hours"].mean()
        std_hours = hist_df["hours"].std()
        summary_text = f"📊 Average hours: {mean_hours:.2f}, Std Dev: {std_hours:.2f}"
    else:
        summary_text = "No positive hours for selected range"

    return pie_chart, hist_chart, summary_text


if __name__ == "__main__":
    url = "http://127.0.0.1:9000/"
    print(f"Your Dash app is running at: {url}")

    import webbrowser
    webbrowser.open(url)
    app.run(debug=True, port=9000)