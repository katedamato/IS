#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 11 12:24:12 2025
@author: katedamato
"""

import pandas as pd
import dash
from dash import Dash, dcc, html, Input, Output, State
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
obs_columns = [col for col in df_wide.columns if col.startswith("OBS_VALUE_")]
clean_names = [col.replace("OBS_VALUE_", "") for col in obs_columns]
variable_options = [{"label": clean, "value": col} for clean, col in zip(clean_names, obs_columns)]

calculated_columns = ["Net_Exports_Goods_Services", "Capital_Account_Balance"]
variable_options += [{"label": col.replace("_", " "), "value": col} for col in calculated_columns]

year_options = sorted(df_wide["TIME_PERIOD"].dropna().astype(int).unique())
year_list = [int(x) for x in year_options]

# -------------------------------------------------------------
# App Layout
# -------------------------------------------------------------
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

app.layout = dbc.Container(
    fluid=True,
    children=[

        html.H2("World Bank Choropleth Dashboard", className="text-center my-4"),

        # -------------------------------------------------------------
        # Row 1: Dropdown + instruction text
        # -------------------------------------------------------------
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
                    html.Div(
                        "Click a country on the map to explore its trends. "
                        "Scroll down below the map to view the detailed time series.",
                        style={"fontSize": "16px", "fontWeight": "500", "color": "#333"}
                    )
                ]), style={"height": "100%"})
            )
        ], className="mb-4"),

        # -------------------------------------------------------------
        # Row 2: Slider + Play Button
        # -------------------------------------------------------------
        dbc.Row([
            dbc.Col(
                html.Div([
                    dcc.Slider(
                        id="year_slider",
                        min=min(year_list),
                        max=max(year_list),
                        step=1,
                        value=min(year_list),
                        marks={int(y): str(int(y)) for y in year_list[::5]},
                        tooltip={"placement": "bottom"}
                    ),
                    html.Button("▶ Play", id="play_button", n_clicks=0,
                                style={"marginTop": "15px", "fontWeight": "bold"})
                ], style={"paddingBottom": "20px"})
            )
        ]),

        # Interval timer (disabled by default)
        dcc.Interval(id="play_interval", interval=400, n_intervals=0, disabled=True),

        # -------------------------------------------------------------
        # Row 3: Choropleth Map
        # -------------------------------------------------------------
        dbc.Row([
            dbc.Col(
                dbc.Card(dbc.CardBody([
                    dcc.Graph(id="choropleth_map", style={"height": "78vh"})
                ])), width=12
            )
        ]),

        # -------------------------------------------------------------
        # Row 4: Collapsible Country Time Series
        # -------------------------------------------------------------
        dbc.Row([
            dbc.Col(
                dbc.Collapse(
                    dbc.Card(dbc.CardBody([
                        dcc.Graph(id="country_time_series", style={"height": "40vh"})
                    ])),
                    id="country_panel",
                    is_open=False
                ), width=12
            )
        ])
    ]
)

# -------------------------------------------------------------
# Map Generator
# -------------------------------------------------------------
def generate_map(selected_variable, selected_year):
    dff = df_wide[df_wide["TIME_PERIOD"].astype(int) == int(selected_year)].copy()
    dff[selected_variable] = pd.to_numeric(dff[selected_variable], errors="coerce")
    dff = dff.dropna(subset=[selected_variable])

    # Trim outliers for stronger visible contrast
    lower_bound = dff[selected_variable].quantile(0.05)
    upper_bound = dff[selected_variable].quantile(0.95)

    fig = px.choropleth(
        dff,
        locations="REF_AREA_ID",
        color=selected_variable,
        hover_name="REF_AREA_NAME",
        color_continuous_scale=px.colors.sequential.Blues,
        range_color=(lower_bound, upper_bound),
        labels={selected_variable: selected_variable.replace("_", " ")}
    )

    fig.update_layout(template="plotly_white")
    return fig

# -------------------------------------------------------------
# Update map
# -------------------------------------------------------------
@app.callback(
    Output("choropleth_map", "figure"),
    Input("variable_selector", "value"),
    Input("year_slider", "value")
)
def update_map(selected_variable, selected_year):
    return generate_map(selected_variable, selected_year)

# -------------------------------------------------------------
# Toggle play / pause
# -------------------------------------------------------------
@app.callback(
    Output("play_interval", "disabled"),
    Output("play_button", "children"),
    Input("play_button", "n_clicks"),
    State("play_interval", "disabled")
)
def toggle_play(n_clicks, interval_disabled):
    if n_clicks == 0:
        return True, "▶ Play"
    if interval_disabled:
        return False, "⏸ Pause"
    else:
        return True, "▶ Play"

# -------------------------------------------------------------
# Advance year on interval
# -------------------------------------------------------------
@app.callback(
    Output("year_slider", "value"),
    Input("play_interval", "n_intervals"),
    State("year_slider", "value")
)
def animate(n, current_year):
    if current_year < max(year_list):
        return current_year + 1
    return max(year_list)

# -------------------------------------------------------------
# Country time series
# -------------------------------------------------------------
@app.callback(
    Output("country_time_series", "figure"),
    Output("country_panel", "is_open"),
    Input("choropleth_map", "clickData"),
    State("country_panel", "is_open"),
    Input("variable_selector", "value")
)
def update_line_chart(clickData, is_open, selected_variable):
    if clickData is None:
        return px.line(title="Click a country to see its time series"), is_open
    
    country_id = clickData['points'][0]['location']
    dff_country = df_wide[df_wide["REF_AREA_ID"] == country_id].copy()
    dff_country[selected_variable] = pd.to_numeric(dff_country[selected_variable], errors="coerce")
    dff_country = dff_country.dropna(subset=[selected_variable])
    dff_country = dff_country.sort_values("TIME_PERIOD")

    fig = px.line(
        dff_country,
        x="TIME_PERIOD",
        y=selected_variable,
        title=f"{dff_country['REF_AREA_NAME'].iloc[0]}: {selected_variable.replace('_', ' ')}",
        labels={"TIME_PERIOD": "Year", selected_variable: selected_variable.replace("_", " ")}
    )
    fig.update_layout(template="plotly_white")
    
    return fig, True  # open panel automatically when a country is clicked

# -------------------------------------------------------------
if __name__ == "__main__":
    url = "http://127.0.0.1:8050/"
    print(f"Your Dash app is running at: {url}")
    webbrowser.open(url)
    app.run(debug=True, port=8050)
