import pandas as pd
import dash
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import webbrowser


#Load data with low RAM issue 
df = pd.read_csv("/Users/katedamato/Downloads/WEO_data.csv", index_col=0, engine='python',        # slower but handles irregular CSVs better
    on_bad_lines='skip')

df.isna().sum() # Check for missing values
df.dtypes # Check data types

df.value_counts("INDICATOR_NAME").reset_index()
df.value_counts(["REF_AREA_ID", "TIME_PERIOD", "INDICATOR_NAME"]).reset_index()

# Counting how many rows exist for each combination of REF_AREA_ID, TIME_PERIOD, and INDICATOR_NAME.
#df.groupby(["REF_AREA_ID", "TIME_PERIOD", "INDICATOR_NAME"]).agg(
    #nrow = ("OBS_VALUE", 'size')
#).reset_index()

# Which columns have real data?
df.nunique().reset_index(name = 'nunique')


df.value_counts('UNIT_MEASURE_ID')
df.value_counts('UNIT_MEASURE_NAME')
df.value_counts('Unnamed: 47')




#Checking for measure 
#df.groupby(["REF_AREA_ID", "TIME_PERIOD", "INDICATOR_NAME", "UNIT_MEASURE_NAME"]).agg(nrow=("OBS_VALUE", "size")).query("nrow > 1")



# --- Aggregate duplicates  ---
#duplicates = df[df.duplicated(keep=False)]

df_agg = (df.groupby(["REF_AREA_ID", "REF_AREA_NAME", "TIME_PERIOD", "INDICATOR_NAME", "UNIT_MEASURE_NAME"], as_index=False).agg({"OBS_VALUE": "mean", "COMMENT_OBS": "first"}))

# --- Now pivot  ---
df_wide = df_agg.pivot(index=["REF_AREA_ID", "REF_AREA_NAME", "TIME_PERIOD"], columns="INDICATOR_NAME", values=["OBS_VALUE", "COMMENT_OBS"])

# --- Flatten multi-index column names --- loops through each tupule and creates a single string for column name for dropdown
df_wide.columns = [f"{val}_{col}" for val, col in df_wide.columns]
df_wide = df_wide.reset_index()


# Country dropdown (unique + sorted)
country_options = [{"label": c, "value": c} for c in sorted(df_wide["REF_AREA_NAME"].unique())]

# Keep only columns with "OBS_VALUE_" prefix - dont want COMMENT_ObS in dropdwon
obs_columns = [col for col in df_wide.columns if col.startswith("OBS_VALUE_")]

# Clean variable names for display (remove prefix) - get rid of OBS_VAl
clean_names = [col.replace("OBS_VALUE_", "") for col in obs_columns]

# Build dropdown options with readable labels
# zip is a built in function that pairs elements from two or more iterables (like lists or tuples) together.
#Creating dictionary of old column names with new 
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

        # Controls Row
        dbc.Row([
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.Label("Select Countries:", className="fw-bold"),
                        #Search functionality default in dcc.Dropdown
                        dcc.Dropdown(
                            id="country_selector",
                            options=country_options,
                            multi=True,
                            placeholder="Search or select countries..."
                        )
                    ]),
                    #different classes that i can assign to apply different CSS stylings
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
                            value=[obs_columns[0]],
                            placeholder="Search or select indicators..."
                        )
                    ]),
                    className="shadow-sm mb-3"
                ),
                width=6
            )
        ]),

        # Graph Row
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        dcc.Graph(id="line_graph", style={"height": "80vh"})
                    ]),
                    className="shadow-sm"
                ),
                width=12
            )
        )
    ]
)

# -------------------------------------------------------------
# 4️ Callback
# -------------------------------------------------------------
@app.callback(
    Output("line_graph", "figure"),
    Input("country_selector", "value"),
    Input("variable_selector", "value")
)
def update_graph(selected_countries, selected_variables):
    if not selected_countries or not selected_variables:
        return px.line(title="Please select at least one country and one indicator")

#Filter by selected country (isin changes to boolean and extra df_wide filters)
    dff = df_wide[df_wide["REF_AREA_NAME"].isin(selected_countries)]

#unpacking the selected variable from wide to long format for easier plotting
    dff_melt = dff.melt(
        id_vars=["REF_AREA_NAME", "TIME_PERIOD"], #these stay the same
        value_vars=selected_variables, #these change 
        var_name="Indicator", #creates a new column with just the name of the variable/indicator
        value_name="Value"
    )
#Cleans indicator names for graphing 
    dff_melt["Indicator"] = dff_melt["Indicator"].str.replace("OBS_VALUE_", "", regex=False)

    fig = px.line(
        dff_melt,
        x="TIME_PERIOD",
        y="Value",
        color="REF_AREA_NAME",
        facet_row="Indicator", #how to split plot into subplots 
        markers=True,
        title="Economic Indicators Over Time"
    )

    fig.update_layout(
        height=400 + 300 * len(selected_variables),
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40),
        legend_title_text="Country"
    )
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    return fig

# -------------------------------------------------------------
#  Run app
# -------------------------------------------------------------
if __name__ == "__main__":
    url = "http://127.0.0.1:9000/"
    print(f"Your Dash app is running at: {url}")
    webbrowser.open(url)
    app.run(debug=True, port=9000)