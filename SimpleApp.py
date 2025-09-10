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

    html.Div(id="output-text")  # placeholder to show result

])

# callback: input is dropdown value, output is text
#children property is content inside component
@app.callback(
    Output("output-text", "value"),
    Input("variable-dropdown", "value")
)
def update_output(selected_var):
    return f"You selected: {selected_var}"

if __name__ == "__main__":
    url = "http://127.0.0.1:9000/"
    print(f"Your Dash app is running at: {url}")
    
    import webbrowser
    webbrowser.open(url)
    app.run(debug=True, port=9000)   

