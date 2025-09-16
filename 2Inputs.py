#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 16 11:29:11 2025

@author: katedamato
"""



from dash import Dash, dcc, html, Input, Output

app = Dash(__name__)

app.layout = html.Div([
    html.H2("Basic Dashboard2"),

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
    
    dcc.Dropdown(
        id="variable-dropdown2",
        options=[
            {"label": "a", "value": "a"},
            {"label": "b", "value": "b"},
            {"label": "c", "value": "c"}
        ],
        value="a",
        clearable=False
    ),


    html.Div(id="output-text"),  # placeholder to show result
    


])

# callback: input is dropdown value, output is text
#children property is content inside component
@app.callback(
    Output("output-text", "children"),
    Input("variable-dropdown2", "value"),
    Input("variable-dropdown", "value")
)
def update_output(selected_var1, selected_var2):
    return selected_var1 + selected_var2






if __name__ == "__main__":
    url = "http://127.0.0.1:9000/"
    print(f"Your Dash app is running at: {url}")
    
    import webbrowser
    webbrowser.open(url)
    app.run(debug=True, port=9000)   
