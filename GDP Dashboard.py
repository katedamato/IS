import pandas as pd
import dash
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.colors as pc
import webbrowser

# -------------------------------------------------------------
# Load data
# -------------------------------------------------------------
df = pd.read_csv("/Users/katedamato/Downloads/WEO_data.csv", index_col=0, engine='python',
                 on_bad_lines='skip')

# Aggregate duplicates
df_agg = (df.groupby(
    ["REF_AREA_ID", "REF_AREA_NAME", "TIME_PERIOD", "INDICATOR_NAME", "UNIT_MEASURE_NAME"],
    as_index=False
).agg({"OBS_VALUE": "mean", "COMMENT_OBS": "first"}))

# Pivot to wide format
df_wide = df_agg.pivot(
    index=["REF_AREA_ID", "REF_AREA_NAME", "TIME_PERIOD"],
    columns="INDICATOR_NAME",
    values=["OBS_VALUE", "COMMENT_OBS"]
)

# Flatten multi-index column names
df_wide.columns = [f"{val}_{col}" for val, col in df_wide.columns]
df_wide = df_wide.reset_index()

# Dropdown options
country_options = [{"label": c, "value": c} for c in sorted(df_wide["REF_AREA_NAME"].unique())]

obs_columns = [col for col in df_wide.columns if col.startswith("OBS_VALUE_")]
clean_names = [col.replace("OBS_VALUE_", "") for col in obs_columns]
variable_options = [{"label": clean, "value": col} for clean, col in zip(clean_names, obs_columns)]

# Color scales
color_scale = pc.qualitative.Plotly
country_colors = {c: color_scale[i % len(color_scale)] for i, c in enumerate(df_wide["REF_AREA_NAME"].unique())}
indicator_colors = {v: color_scale[i % len(color_scale)] for i, v in enumerate(clean_names)}

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

        # Controls Row
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
                        html.Label("Correlation Type:", className="fw-bold", style={"marginTop": "10px"}),
                        html.Div(
                            dcc.RadioItems(
                                id="corr_type",
                                options=[
                                    {"label": "Level", "value": "level"},
                                    {"label": "First Differences", "value": "diff"}
                                ],
                                value="level",
                                inline=True
                            ),
                            style={"marginTop": "10px", "marginBottom": "10px"}
                        ),
                        dcc.Graph(id="corr_graph", style={"height": "80vh"})
                    ]),
                    className="shadow-sm"
                ),
                width=6
            )
        ])
    ]
)

# -------------------------------------------------------------
# Line Graph Callback
# -------------------------------------------------------------
@app.callback(
    Output("line_graph", "figure"),
    Output("tab_description", "children"),
    Input("country_selector", "value"),
    Input("variable_selector", "value"),
    Input("tabs", "value")
)
def update_graph(selected_countries, selected_variables, selected_tab):
    if not selected_countries or not selected_variables:
        return px.line(title="Please select at least one country and one indicator"), ""
    
    dff = df_wide[df_wide["REF_AREA_NAME"].isin(selected_countries)]
    
    dff_melt = dff.melt(
        id_vars=["REF_AREA_NAME", "TIME_PERIOD"],
        value_vars=selected_variables,
        var_name="Indicator",
        value_name="Value"
    )
    dff_melt["Indicator"] = dff_melt["Indicator"].str.replace("OBS_VALUE_", "", regex=False)
    
    if selected_tab == "tab1":
        fig = px.line(
            dff_melt,
            x="TIME_PERIOD",
            y="Value",
            color="REF_AREA_NAME",
            facet_row="Indicator",
            markers=True,
            title="Economic Indicators Over Time (By Variable)",
            color_discrete_map=country_colors,
            hover_data={"Indicator": True, "REF_AREA_NAME": True, "Value": True, "TIME_PERIOD": True}
        )
        description = "Each subplot shows a different economic indicator. Lines represent countries."
   #Tab 2 Line graph 
    else:
        fig = px.line(
            dff_melt,
            x="TIME_PERIOD",
            y="Value",
            color="Indicator",
            facet_row="REF_AREA_NAME",
            markers=True,
            title="Economic Indicators Over Time (By Country)",
            color_discrete_map=indicator_colors,
            hover_data={"Indicator": True, "REF_AREA_NAME": True, "Value": True, "TIME_PERIOD": True}
        )
        description = "Each subplot shows a different country. Lines represent variables."
    
    fig.update_yaxes(matches=None)
    fig.update_layout(
        height=400 + 300 * (len(selected_variables) if selected_tab=="tab1" else len(selected_countries)),
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40),
        legend_title_text="Country" if selected_tab=="tab1" else "Indicator"
    )
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    
    return fig, description

# -------------------------------------------------------------
# Correlation Plot Callback
# -------------------------------------------------------------
@app.callback(
    Output("corr_graph", "figure"),
    Output("corr_message", "children"),
    Input("country_selector", "value"),
    Input("variable_selector", "value"),
    Input("tabs", "value"),
    Input("corr_type", "value")
)
def update_corr_graph(selected_countries, selected_variables, selected_tab, corr_type):
    # Validate input
    if not selected_countries or len(selected_variables) != 2:
        return px.scatter(title="Please select one country and two variables"), "Select one country and exactly two indicators."

    var_x, var_y = selected_variables

    if selected_tab == "tab2":
        country = selected_countries[0]
       #data set for country, time and variables selected
        df_corr = df_wide[df_wide["REF_AREA_NAME"] == country][
            ["TIME_PERIOD", var_x, var_y]
        ].dropna().reset_index(drop=True)
        color_arg = None
        colors = ["#636EFA", "#00CC96"]  # just two colors for trendline consistency
    else:
        # tab1: multiple countries
        df_corr = df_wide[df_wide["REF_AREA_NAME"].isin(selected_countries)][
            ["TIME_PERIOD", "REF_AREA_NAME", var_x, var_y]
        ].dropna().reset_index(drop=True)
        color_arg = "REF_AREA_NAME"
        colors = px.colors.qualitative.Dark24

    # Apply first differences if needed
    if corr_type == "diff":
        df_corr[var_x] = df_corr[var_x].diff()
        df_corr[var_y] = df_corr[var_y].diff()
        df_corr = df_corr.dropna().reset_index(drop=True)

    # Build scatter plot
    fig = px.scatter(
        df_corr,
        x=var_x,
        y=var_y,
        color=color_arg,
        trendline="ols",
        color_discrete_sequence=colors,
        title=f"{'First Differences' if corr_type=='diff' else 'Level'} Correlation"
    )

    # Calculate and display correlation coefficient
    if not df_corr.empty:
        corr_coef = df_corr[var_x].corr(df_corr[var_y])
        fig.add_annotation(
            text=f"Correlation: r = {corr_coef:.2f}",
            xref="paper",
            yref="paper",
            x=0.95,
            y=0.05,
            showarrow=False,
            font=dict(size=12)
        )

    return fig, f"Correlation between {var_x} and {var_y}"


# -------------------------------------------------------------
# Run app
# -------------------------------------------------------------
if __name__ == "__main__":
    url = "http://127.0.0.1:9000/"
    print(f"Your Dash app is running at: {url}")
    webbrowser.open(url)
    app.run(debug=True, port=9000)
