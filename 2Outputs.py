#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 16 10:59:55 2025

@author: katedamato
"""

#static input and connect to output and make basic interactive app 
#taking input and using information to get 2 outputs 
#2 (diffreent types) inputs and funnel them into one output - sentence 




from dash import Dash, dcc, html, Input, Output

app = Dash(__name__)

app.layout = html.Div([
    html.H2("Basic Dashboard"),

    dcc.Dropdown(
        id="variable-dropdown",
        options=[
            {"label": "a", "value": "a"},
            {"label": "b", "value": "b"},
            {"label": "c", "value": "c"}
        ],
        value="a",
        clearable=False
    ),

    html.Div(id="output-text"),  # placeholder to show result
    
    html.Div(id="output-text2")

])

# callback: input is dropdown value, output is text
#children property is content inside component
@app.callback(
    Output("output-text", "children"),
    Output("output-text2", "children"),
    Input("variable-dropdown", "value")
)
def update_output(selected_var):
    return selected_var, selected_var






if __name__ == "__main__":
    url = "http://127.0.0.1:9000/"
    print(f"Your Dash app is running at: {url}")
    
    import webbrowser
    webbrowser.open(url)
    app.run(debug=True, port=9000)   
