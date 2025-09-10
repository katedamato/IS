#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 10 11:09:46 2025

@author: katedamato
"""
import dash
from dash import dcc, html
import plotly.express as px

# Example graph using Plotly Express
fig = px.scatter(
    x=[1, 2, 3, 4, 5],
    y=[10, 11, 12, 13, 14],
    title="Example Scatter Plot"
)


##START OF APP
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Dash Components Showcase"),
    html.Hr(),

    html.H2("Input Components"),
#Dropdown using dcc.Dropdown 
    html.Div([
        html.Label("Dropdown Example:"),
        dcc.Dropdown(
            options=[
                {"label": "Option A", "value": "A"},
                {"label": "Option B", "value": "B"},
                {"label": "Option C", "value": "C"}
            ],
            value="A"
        ),
    ], style={"margin": "10px 0"}),

#Checklist using dcc.Checklist *value is default
    html.Div([
        html.Label("Checklist Example:"),
        dcc.Checklist(
            options=["Apple", "Banana", "Cherry"],
            value=["Apple"]
        )
    ], style={"margin": "10px 0"}),

#Radio Button using dcc.RadioItems
    html.Div([
        html.Label("RadioItems Example:"),
        dcc.RadioItems(
            options=["Yes", "No", "Maybe"],
            value="Yes"
        )
    ], style={"margin": "10px 0"}),
#Slider  using dcc.Slider (0 - 10) 
    html.Div([
        html.Label("Slider Example:"),
        dcc.Slider(min=0, max=10, step=1, value=5)
    ], style={"margin": "10px 0"}),

#Range slider (0-20) 
    html.Div([
        html.Label("RangeSlider Example:"),
        dcc.RangeSlider(min=0, max=20, step=2, value=[4, 12])
    ], style={"margin": "10px 0"}),
#Text Input (one-line) using dcc.Input
    html.Div([
        html.Label("Text Input Example:"),
        dcc.Input(type="text", value="Hello Dash")
    ], style={"margin": "10px 0"}),
#Long text input using dcc.Textarea
    html.Div([
        html.Label("Textarea Example:"),
        dcc.Textarea(value="Multi-line text here", style={"width": "100%"})
    ], style={"margin": "10px 0"}),

#Pick date using dcc. DatePickerSingle
    html.Div([
        html.Label("DatePickerSingle Example:"),
        dcc.DatePickerSingle(date="2025-09-09")
    ], style={"margin": "10px 0"}),

#Pick multiple dates using dcc.DatePickerRange
    html.Div([
        html.Label("DatePickerRange Example:"),
        dcc.DatePickerRange(start_date="2025-09-01", end_date="2025-09-09")
    ], style={"margin": "10px 0"}),

###Start of static outputs
    html.H2("Output Components"),

#html.H3 and html.p create static text
    html.Div([
        html.H3("Static Text"),
        html.P("This is an example of static text inside a Dash app."),
    ]),
#formatting, - for bullet points, * italics, ** bold
    html.Div([
        html.H3("Markdown Example"),
        dcc.Markdown("""
        **Markdown Formatting** works too!
        - Bullet points
        - *Italics* and **bold**
        """)
    ]),

  #Static Image using html.Img              
    html.Div([
        html.H3("Image Example"),
        html.Img(src="data:image/png;base64,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", style={"width": "300px"})
    ], style={"margin": "20px 0"}),

#fig defined earlier, graphing the fig now
    html.Div([
        html.H3("Graph Example"),
        dcc.Graph(figure=fig)
    ]),
#creating tabs
    html.Div([
        html.H3("Tabs Example"),
        dcc.Tabs([
            dcc.Tab(label="Tab 1", children=[html.Div("Content for Tab 1")]),
            dcc.Tab(label="Tab 2", children=[html.Div("Content for Tab 2")])
        ])
    ])
])

#Running the app 
if __name__ == "__main__":
    url = "http://127.0.0.1:9000/"
    print(f"Your Dash app is running at: {url}")
    
    import webbrowser
    webbrowser.open(url)
    app.run(debug=True, port=9000) 
    
###@app-callback used for interactive asepct 
#ie. @app.callback(
#   Output("my-output", "children"),
#      Input ("my-input", "value)
#     )
# def update_output(value): 
#   return f"You selected {value}"

