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
import plotly.colors as pc
import webbrowser
import random 


# -------------------------------------------------------------
# Load data
# -------------------------------------------------------------
df = pd.read_csv(
    "/Users/katedamato/Downloads/WEO_data-2.csv",
    index_col=0,
    engine='python',
    on_bad_lines='skip'
)

#subset of countries - separate based on what you need it for 
#faster way to read file? multithreaded function 


# Check how many duplicate rows there are based on your supposed unique identifiers
if False:
    dupes = df[df.duplicated(subset=["REF_AREA_ID", "REF_AREA_NAME", "TIME_PERIOD", "INDICATOR_NAME"], keep=False)]
    print(f"Total duplicates: {len(dupes)}")
    dupes.head(10)

## Keep only rows where OBS_VALUE is numeric
df = df[pd.to_numeric(df["OBS_VALUE"], errors="coerce").notna()]
##Get rid of headers and start/end statments 
df = df[~df["STRUCTURE_ID"].str.contains("Start/end months", na=False)]


# Aggregate duplicates
df_agg = (
    df.groupby(
        ["REF_AREA_ID", "REF_AREA_NAME", "TIME_PERIOD", "INDICATOR_NAME", "UNIT_MEASURE_NAME"],
        as_index=False
    )
    .agg({"OBS_VALUE": "mean", "COMMENT_OBS": "first"})
)

# Pivot to wide format
df_wide = df_agg.pivot(
    index=["REF_AREA_ID", "REF_AREA_NAME", "TIME_PERIOD"],
    columns="INDICATOR_NAME",
    values=["OBS_VALUE", "COMMENT_OBS"]
)

# Flatten multi-index column names
df_wide.columns = [f"{val}_{col}" for val, col in df_wide.columns]
df_wide = df_wide.reset_index()


#OBS columns to numbers 
obs_columns = [col for col in df_wide.columns if col.startswith("OBS_VALUE_")]

# Dropdown options
country_options = [{"label": c, "value": c} for c in sorted(df_wide["REF_AREA_NAME"].unique())]
obs_columns = [col for col in df_wide.columns if col.startswith("OBS_VALUE_")]
clean_names = [col.replace("OBS_VALUE_", "") for col in obs_columns]
variable_options = [{"label": clean, "value": col} for clean, col in zip(clean_names, obs_columns)]


# -------------------------------------------------------------
# Initialize Dash app
# -------------------------------------------------------------
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.layout = dbc.Container(
    fluid=True,
    children=[
        # Header
        dbc.Row(
            dbc.Col(
                html.H2("Economic Indicators Dashboard", className="text-center text-primary my-4"),
                width=12
            )
        ),

        # Global Controls Row
        dbc.Row([
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.Label("Select Countries:", className="fw-bold"),
                        dcc.Dropdown(
                            id="country_selector",
                            options=country_options,
                            multi=True,
                            placeholder="Search or select countries..."
                        )
                    ]),
                    className="shadow-sm mb-3"
                ),
                width=6
            ),
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.Label("Select Indicators:", className="fw-bold"),
                        dcc.Dropdown(
                            id="variable_selector",
                            options=variable_options,
                            multi=True,
                            value=[obs_columns[0]] if obs_columns else None,
                            placeholder="Search or select indicators..."
                        )
                    ]),
                    className="shadow-sm mb-3"
                ),
                width=6
            )
        ]),

        # Global Data Type Selector
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.Label("Data Type:", className="fw-bold"),
                        dcc.RadioItems(
                            id="data_type_selector",
                            options=[
                                {"label": "Level", "value": "level"},
                                {"label": "First Differences", "value": "diff"}
                            ],
                            value="level",
                            inline=True
                        )
                    ]),
                    className="shadow-sm mb-3"
                ),
                width=6
            )
        ),

        # Graph Row with 50/50 layout
        dbc.Row([
            # Left: Line Graph with Tabs
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        dcc.Tabs(id="tabs", value="tab1", children=[
                            dcc.Tab(label="By Variable", value="tab1"),
                            dcc.Tab(label="By Country", value="tab2"),
                        ]),
                        html.Div(id="tab_description", className="mb-3", style={"fontStyle": "italic", "color": "#555"}),
                        dcc.Graph(id="line_graph", style={"height": "80vh"})
                    ]),
                    className="shadow-sm"
                ),
                width=6
            ),
            # Right: Correlation Graph
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.Label("Correlation Graph", className="fw-bold"),
                        html.Div(id="corr_message", style={"marginBottom": "10px", "color": "#555"}),
                        dcc.Graph(id="corr_graph", style={"height": "80vh"})
                    ]),
                    className="shadow-sm"
                ),
                width=6
            )
        ])
    ]
)


# Function to generate all plots - replace exactly with at least
# -------------------------------------------------------------
def generate_all_plots(selected_countries, selected_variables, data_type="level"):
    
    plots = {}

    # Return empty figures if nothing selected
    if not selected_countries or not selected_variables:
        empty_fig = px.line(title="Please select at least one country and one indicator")
        empty_scatter = px.scatter(title="Please select exactly two indicators")
        plots['by_country'] = {"plot": empty_fig, "descr": ""}
        plots['by_variable'] = {"plot": empty_fig, "descr": ""}
        plots['scatterplot'] = {"plot": empty_scatter, "descr": ""}
        return plots

    # Subset and sort
    dff = df_wide[df_wide["REF_AREA_NAME"].isin(selected_countries)].copy()
    dff["TIME_PERIOD"] = pd.to_numeric(dff["TIME_PERIOD"], errors="coerce")
    dff = dff.sort_values(["REF_AREA_NAME", "TIME_PERIOD"])

    # Apply first differences per country if selected
    if data_type == "diff":
        dff[selected_variables] = dff[selected_variables].apply(pd.to_numeric, errors="coerce")
        dff[selected_variables] = dff.groupby("REF_AREA_NAME")[selected_variables].transform('diff')
        dff[selected_variables] = dff[selected_variables].fillna(0)

    # Melt for plotting
    dff_melt = dff.melt(
        id_vars=["REF_AREA_NAME", "TIME_PERIOD"],
        value_vars=selected_variables,
        var_name="Indicator",
        value_name="Value"
    )
    dff_melt["Indicator"] = dff_melt["Indicator"].str.replace("OBS_VALUE_", "", regex=False)
    dff_melt["REF_AREA_NAME"] = pd.Categorical(
        dff_melt["REF_AREA_NAME"], categories=selected_countries, ordered=True
    )

    # -------------------------
    # Dynamic high-contrast color assignment
    # -------------------------
    base_colors = px.colors.qualitative.Dark24  # 24 distinct colors

    def get_distinct_color(index):
        if index < len(base_colors):
            return base_colors[index]
        # generate a random bright color for extra entries
        return f"rgb({random.randint(50,255)}, {random.randint(50,255)}, {random.randint(50,255)})"

    # Assign distinct colors to countries and indicators
    country_colors = {c: get_distinct_color(i) for i, c in enumerate(selected_countries)}
    selected_clean_names = [col.replace("OBS_VALUE_", "") for col in selected_variables]
    indicator_colors = {v: get_distinct_color(i) for i, v in enumerate(selected_clean_names)}

    # -------------------------
    # By Variable Graph
    # -------------------------
    fig_var = px.line(
        dff_melt,
        x="TIME_PERIOD",
        y="Value",
        color="REF_AREA_NAME",
        facet_row="Indicator",
        markers=True,
        title="Economic Indicators Over Time (By Variable)",
        color_discrete_map=country_colors,
        hover_data={"Indicator": True, "REF_AREA_NAME": True, "Value": True, "TIME_PERIOD": True},
        category_orders={"REF_AREA_NAME": selected_countries}
    )
    fig_var.update_yaxes(matches=None)
    fig_var.update_layout(
        height=400 + 300 * len(selected_variables),
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40),
        legend_title_text="Country"
    )
    fig_var.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    plots["by_variable"] = {
        "plot": fig_var,
        "descr": "Each subplot shows a different economic indicator. Lines represent countries."
    }

    # -------------------------
    # By Country Graph
    # -------------------------
    fig_country = px.line(
        dff_melt,
        x="TIME_PERIOD",
        y="Value",
        color="Indicator",
        facet_row="REF_AREA_NAME",
        markers=True,
        title="Economic Indicators Over Time (By Country)",
        color_discrete_map=indicator_colors,
        hover_data={"Indicator": True, "REF_AREA_NAME": True, "Value": True, "TIME_PERIOD": True},
        category_orders={"REF_AREA_NAME": selected_countries}
    )
    fig_country.update_yaxes(matches=None)
    fig_country.update_layout(
        height=400 + 300 * len(selected_countries),
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40),
        legend_title_text="Indicator"
    )
    fig_country.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    plots["by_country"] = {
        "plot": fig_country,
        "descr": "Each subplot shows a different country. Lines represent variables."
    }

    # -------------------------
    # Scatterplot (Correlation)
    # -------------------------
    if len(selected_variables) == 2:
        var_x, var_y = selected_variables
        df_scatter = dff[["REF_AREA_NAME", var_x, var_y]].dropna().reset_index(drop=True)
        fig_scatter = px.scatter(
            df_scatter,
            x=var_x,
            y=var_y,
            color="REF_AREA_NAME",
            trendline="ols",
            color_discrete_map=country_colors,
            title=f"{'First Differences' if data_type=='diff' else 'Level'} Correlation"
        )

        # Add per-country correlation annotations
        for idx, country in enumerate(selected_countries):
            temp = df_scatter[df_scatter["REF_AREA_NAME"] == country]
            if not temp.empty:
                r = temp[var_x].corr(temp[var_y])
                fig_scatter.add_annotation(
                    text=f"{country} r={r:.2f}",
                    xref="paper",
                    yref="paper",
                    x=0.95,
                    y=0.05 - 0.05 * idx,
                    showarrow=False,
                    font=dict(size=12)
                )

        plots["scatterplot"] = {"plot": fig_scatter, "descr": f"Correlation between {var_x} and {var_y}"}
    else:
        fig_scatter = px.scatter(title="Select exactly two indicators")
        plots["scatterplot"] = {
            "plot": fig_scatter,
            "descr": "Select at least one country and exactly two indicators."
        }

    return plots




#-------Callback ---------------------------
@app.callback(

    Output("corr_graph", "figure"),
    Output("corr_message", "children"),
    Input("country_selector", "value"),
    Input("variable_selector", "value"),
    Input("tabs", "value"),
    Input("data_type_selector", "value")
)

def update_all(selected_countries, selected_variables, selected_tab, data_type):
    # Generate all relevant plots once
    plots = generate_all_plots(selected_countries, selected_variables, data_type)

    # Handle line graph + description depending on tab
    if selected_tab == "tab1":
        line_plot = plots['by_variable']['plot']
        line_descr = plots['by_variable']['descr']
    else:
        line_plot = plots['by_country']['plot']
        line_descr = plots['by_country']['descr']

    # Handle correlation graph + message
    corr_plot = plots['scatterplot']['plot']
    corr_descr = plots['scatterplot']['descr']

    return line_plot, line_descr, corr_plot, corr_descr


# -------------------------------------------------------------
# Run app
# -------------------------------------------------------------
if __name__ == "__main__":
    url = "http://127.0.0.1:9000/"
    print(f"Your Dash app is running at: {url}")
    webbrowser.open(url)
    app.run(debug=True, port=9000)


    
    #Test if correlation is different for small vs big countries : 
    #Appears to have no relation @levels between size and twin deficits hypothesis
    ##Bulgaria (positive),US (positive), Canada (negative), Mexico (positive), Brazil (posiitve), Belgium (positive), Germany (negative)
    
    
    #We could run some random forests or ann's to investigate these countries and factors contirbuting to twin deficits hypothesis 
    #Add which correlations are statistically significant 
    #Create new dashboard focused on twin deficits hypothesis and allow filtering based on outcome (positive/negative relationship_)

