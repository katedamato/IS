#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 11 12:24:12 2025

@author: katedamato
"""

import pandas as pd
import dash
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import webbrowser
import plotly.io as pio

pio.renderers.default = "browser"

# -------------------------------------------------------------
# Load and preprocess data
# -------------------------------------------------------------
df = pd.read_csv(
    "/Users/katedamato/Downloads/WEO_data-2.csv",
    index_col=0,
    engine='python',
    on_bad_lines='skip'
)

# Ensure numeric values
df = df[pd.to_numeric(df["OBS_VALUE"], errors="coerce").notna()]
df = df[~df["STRUCTURE_ID"].str.contains("Start/end months", na=False)]

# Pivot to wide format
df_wide = df.pivot(
    index=["REF_AREA_ID", "REF_AREA_NAME", "TIME_PERIOD"],
    columns="INDICATOR_NAME",
    values=["OBS_VALUE", "COMMENT_OBS"]
)

# Flatten multiindex columns
df_wide.columns = [f"{val}_{col}" for val, col in df_wide.columns]
df_wide = df_wide.reset_index()

# Optional calculated columns
df_wide['Net_Exports_Goods_Services'] = (
    df_wide.get('OBS_VALUE_Volume of exports of goods and services, Percent change', 0) -
    df_wide.get('OBS_VALUE_Volume of imports of goods and services, Percent change', 0)
)
df_wide['Capital_Account_Balance'] = (
    df_wide.get('OBS_VALUE_Current account balance, Percent of GDP', 0) -
    df_wide['Net_Exports_Goods_Services']
)

# -------------------------------------------------------------
# Dropdown options
# -------------------------------------------------------------
# Variables
obs_columns = [col for col in df_wide.columns if col.startswith("OBS_VALUE_")]
clean_names = [col.replace("OBS_VALUE_", "") for col in obs_columns]
variable_options = [{"label": clean, "value": col} for clean, col in zip(clean_names, obs_columns)]

# Add calculated columns
calculated_columns = ["Net_Exports_Goods_Services", "Capital_Account_Balance"]
variable_options += [{"label": col.replace("_", " "), "value": col} for col in calculated_columns]

# Years as integers
year_options = sorted(df_wide["TIME_PERIOD"].dropna().astype(int).unique())

# -------------------------------------------------------------
# Initialize Dash app
# -------------------------------------------------------------
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.layout = dbc.Container(
    fluid=True,
    children=[
        html.H2("World Bank Choropleth Dashboard", className="text-center my-4"),

        dbc.Row([
            dbc.Col(
                dbc.Card(dbc.CardBody([
                    html.Label("Select Indicator:", className="fw-bold"),
                    dcc.Dropdown(
                        id="variable_selector",
                        options=variable_options,
                        value=variable_options[0]['value'],
                        clearable=False
                    )
                ])), width=6
            ),
            dbc.Col(
                dbc.Card(dbc.CardBody([
                    html.Label("Select Year:", className="fw-bold"),
                    dcc.Dropdown(
                        id="year_selector",
                        options=[{"label": str(year), "value": year} for year in year_options],
                        value=max(year_options),  # default is most recent year
                        clearable=False
                    )
                ])), width=6
            )
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(
                dbc.Card(dbc.CardBody([
                    dcc.Graph(id="choropleth_map", style={"height": "80vh"})
                ])), width=12
            )
        ])
    ]
)

# -------------------------------------------------------------
# Map plotting function
# -------------------------------------------------------------
def generate_map(selected_variable, selected_year):
    dff = df_wide[df_wide['TIME_PERIOD'].astype(int) == selected_year].copy()

    fig = px.choropleth(
        dff,
        locations='REF_AREA_ID',      # ISO-3 country codes
        color=selected_variable,
        hover_name='REF_AREA_NAME',
        color_continuous_scale='Viridis',
        labels={selected_variable: selected_variable.replace("_", " ")}
    )
    fig.update_layout(template='plotly_white')
    return fig

# -------------------------------------------------------------
# Callback to update map
# -------------------------------------------------------------
@app.callback(
    Output('choropleth_map', 'figure'),
    Input('variable_selector', 'value'),
    Input('year_selector', 'value')
)
def update_map(selected_variable, selected_year):
    return generate_map(selected_variable, selected_year)

# -------------------------------------------------------------
if __name__ == "__main__":
    url = "http://127.0.0.1:8050/"
    print(f"Your Dash app is running at: {url}")
    webbrowser.open(url)
    app.run(debug=True, port=8050)
