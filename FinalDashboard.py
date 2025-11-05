#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 29 12:57:07 2025

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
# Load data
# -------------------------------------------------------------
debug = True
if debug: 
    df = pd.read_csv(
        "/Users/katedamato/Downloads/WEO_data_small.csv",
        index_col=0,
        engine='python',
        on_bad_lines='skip'
    )
else:
    df = pd.read_csv(
        "/Users/katedamato/Downloads/WEO_data-2.csv",
        index_col=0,
        engine='python',
        on_bad_lines='skip'
    )

df = df[pd.to_numeric(df["OBS_VALUE"], errors="coerce").notna()]
df = df[~df["STRUCTURE_ID"].str.contains("Start/end months", na=False)]

df_wide = df.pivot(
    index=["REF_AREA_ID", "REF_AREA_NAME", "TIME_PERIOD"],
    columns="INDICATOR_NAME",
    values=["OBS_VALUE", "COMMENT_OBS"]
)

df_wide.columns = [f"{val}_{col}" for val, col in df_wide.columns]
df_wide = df_wide.reset_index()

# -------------------------------------------------------------
# Create Twin Deficits Variables
# -------------------------------------------------------------
df_wide['Net_Exports_Goods_Services'] = (
    df_wide.get('OBS_VALUE_Volume of exports of goods and services, Percent change', 0) -
    df_wide.get('OBS_VALUE_Volume of imports of goods and services, Percent change', 0)
)

df_wide['Capital_Account_Balance'] = (
    df_wide.get('OBS_VALUE_Current account balance, Percent of GDP', 0) -
    df_wide['Net_Exports_Goods_Services']
)

# -------------------------------------------------------------
# Dropdown Options
# -------------------------------------------------------------
obs_columns = [col for col in df_wide.columns if col.startswith("OBS_VALUE_")]
clean_names = [col.replace("OBS_VALUE_", "") for col in obs_columns]

# Regular indicators
variable_options = [
    {"label": clean, "value": col}
    for clean, col in zip(clean_names, obs_columns)
]

# Add calculated columns
calculated_columns = ["Net_Exports_Goods_Services", "Capital_Account_Balance"]
variable_options += [
    {"label": col.replace("_", " "), "value": col} for col in calculated_columns
]

# Country options
country_options = [{"label": c, "value": c} for c in sorted(df_wide["REF_AREA_NAME"].unique())]

# -------------------------------------------------------------
# Initialize Dash app
# -------------------------------------------------------------
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.layout = dbc.Container(
    fluid=True,
    children=[
        dbc.Row(dbc.Col(html.H2("Economic Indicators Dashboard", className="text-center text-primary my-4"), width=12)),

        dbc.Row([
            dbc.Col(
                dbc.Card(dbc.CardBody([
                    html.Label("Select Countries:", className="fw-bold"),
                    dcc.Dropdown(id="country_selector", options=country_options, multi=True)
                ])), width=6
            ),
            dbc.Col(
                dbc.Card(dbc.CardBody([
                    html.Label("Select Indicators:", className="fw-bold"),
                    dcc.Dropdown(id="variable_selector", options=variable_options, multi=True, value=[obs_columns[0]])
                ])), width=6
            )
        ]),

        dbc.Row(
            dbc.Col(
                dbc.Card(dbc.CardBody([
                    html.Label("Data Type:", className="fw-bold"),
                    dcc.RadioItems(
                        id="data_type_selector",
                        options=[{"label": "Level", "value": "level"}, {"label": "First Differences", "value": "diff"}],
                        value="level",
                        inline=True
                    )
                ])), width=6
            )
        ),

        dbc.Row([
            dbc.Col(
                dbc.Card(dbc.CardBody([
                    dcc.Tabs(id="tabs", value="tab1", children=[
                        dcc.Tab(label="By Variable", value="tab1"),
                        dcc.Tab(label="By Country", value="tab2"),
                    ]),
                    html.Div(id="tab_description", className="mb-3", style={"fontStyle": "italic", "color": "#555"}),
                    dcc.Graph(id="line_graph", style={"height": "80vh"})
                ])), width=6
            ),
            dbc.Col(
                dbc.Card(dbc.CardBody([
                    html.Label("Correlation Graph", className="fw-bold"),
                    html.Div(id="corr_message", style={"marginBottom": "10px", "color": "#555"}),
                    dcc.Graph(id="corr_graph", style={"height": "80vh"})
                ])), width=6
            )
        ])
    ]
)

# -------------------------------------------------------------
# Plot Generator
# -------------------------------------------------------------
def generate_all_plots(selected_countries, selected_variables, data_type="level"):
    plots = {}

    if not selected_countries or not selected_variables:
        empty_fig = px.line(title="Please select at least one country and one indicator")
        empty_scatter = px.scatter(title="Select exactly two indicators")
        plots['by_country'] = {"plot": empty_fig, "descr": ""}
        plots['by_variable'] = {"plot": empty_fig, "descr": ""}
        plots['scatterplot'] = {"plot": empty_scatter, "descr": ""}
        return plots

    dff = df_wide[df_wide["REF_AREA_NAME"].isin(selected_countries)].copy()
    dff["TIME_PERIOD"] = pd.to_numeric(dff["TIME_PERIOD"], errors="coerce")
    dff = dff.sort_values(["REF_AREA_NAME", "TIME_PERIOD"])

    # Ensure all selected variables exist and numeric
    for col in selected_variables:
        if col not in dff.columns:
            dff[col] = pd.to_numeric(dff[col], errors="coerce")

    if data_type == "diff":
        dff[selected_variables] = dff[selected_variables].apply(pd.to_numeric, errors="coerce")
        dff[selected_variables] = dff.groupby("REF_AREA_NAME")[selected_variables].transform('diff')

    dff_melt = dff.melt(
        id_vars=["REF_AREA_NAME", "TIME_PERIOD"],
        value_vars=selected_variables,
        var_name="Indicator",
        value_name="Value"
    )

    # Clean indicator names
    dff_melt["Indicator"] = dff_melt["Indicator"].str.replace("OBS_VALUE_", "", regex=False)
    dff_melt["Indicator"] = dff_melt["Indicator"].str.replace("_", " ")

    base_colors = px.colors.qualitative.Dark24
    def get_color(i): return base_colors[i % len(base_colors)]

    country_colors = {c: get_color(i) for i, c in enumerate(selected_countries)}
    indicator_names = dff_melt["Indicator"].unique()
    indicator_colors = {v: get_color(i) for i, v in enumerate(indicator_names)}

    # By Variable
    fig_var = px.line(
        dff_melt, x="TIME_PERIOD", y="Value", color="REF_AREA_NAME", facet_row="Indicator",
        markers=True, title="Economic Indicators Over Time (By Variable)", color_discrete_map=country_colors
    )
    fig_var.update_yaxes(matches=None)
    fig_var.update_layout(height=400 + 300 * len(selected_variables), template="plotly_white", legend_title_text="Country")
    fig_var.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    plots["by_variable"] = {"plot": fig_var, "descr": "Each subplot shows one indicator."}

    # By Country
    fig_country = px.line(
        dff_melt, x="TIME_PERIOD", y="Value", color="Indicator", facet_row="REF_AREA_NAME",
        markers=True, title="Economic Indicators Over Time (By Country)", color_discrete_map=indicator_colors
    )
    fig_country.update_yaxes(matches=None)
    fig_country.update_layout(
        height=400 + 300 * len(selected_countries),
        template="plotly_white",
        legend_title_text="Indicator",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.12,
            xanchor="center",
            x=0.5,
            title=None
        )
    )
    fig_country.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    plots["by_country"] = {"plot": fig_country, "descr": "Each subplot shows one country."}

    # Scatter Correlation
    if len(selected_variables) == 2:
        var_x, var_y = selected_variables
        df_scatter = dff[["REF_AREA_NAME", var_x, var_y]].dropna()
        fig_scatter = px.scatter(df_scatter, x=var_x, y=var_y, color="REF_AREA_NAME",
                                 trendline="ols", color_discrete_map=country_colors,
                                 title="Correlation Between Selected Indicators")

        start_y = 0.80
        spacing = 0.07

        for idx, country in enumerate(selected_countries):
            temp = df_scatter[df_scatter["REF_AREA_NAME"] == country]
            if not temp.empty:
                r = temp[var_x].corr(temp[var_y])
                fig_scatter.add_annotation(
                    text=f"{country}: r = {r:.2f}",
                    xref="paper", yref="paper",
                    x=1.25, y=start_y - idx * spacing,
                    showarrow=False,
                    font=dict(size=14, color="black"),
                    align="left",
                    bgcolor="white",
                    bordercolor="black",
                    borderpad=4
                )

        plots["scatterplot"] = {"plot": fig_scatter, "descr": ""}
    else:
        plots["scatterplot"] = {"plot": px.scatter(title="Select exactly two indicators"), "descr": ""}

    return plots

# -------------------------------------------------------------
@app.callback(
    Output("line_graph", "figure"),
    Output("tab_description", "children"),
    Output("corr_graph", "figure"),
    Output("corr_message", "children"),
    Input("country_selector", "value"),
    Input("variable_selector", "value"),
    Input("tabs", "value"),
    Input("data_type_selector", "value")
)
def update_all(selected_countries, selected_variables, selected_tab, data_type):
    plots = generate_all_plots(selected_countries, selected_variables, data_type)

    if selected_tab == "tab1":
        return plots['by_variable']['plot'], plots['by_variable']['descr'], plots['scatterplot']['plot'], plots['scatterplot']['descr']
    else:
        return plots['by_country']['plot'], plots['by_country']['descr'], plots['scatterplot']['plot'], plots['scatterplot']['descr']

# -------------------------------------------------------------
if __name__ == "__main__":
    url = "http://127.0.0.1:9000/"
    print(f"Your Dash app is running at: {url}")
    webbrowser.open(url)
    app.run(debug=True, port=9000)
