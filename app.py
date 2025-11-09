from dash import Dash, dcc, html, dash_table, Output, Input
from pymongo import MongoClient
from dotenv import load_dotenv
import pandas as pd
import plotly.express as px
import threading, queue, os

load_dotenv()
uri = os.getenv("MONGO_URI")

client = MongoClient(uri)
db = client["Testing"]
collection = db["users"]

event_queue = queue.Queue()

def watch_mongo():
    with client.watch() as stream:
        for change in stream:
            event_queue.put(True)

thread = threading.Thread(target=watch_mongo, daemon=True)
thread.start()


def load_data():
    return pd.DataFrame(list(collection.find({}, {"_id": 0})))

app = Dash(__name__)

AESTHETIC_CSS = {
    "fontFamily": "Montserrat, sans-serif",
    "background": "linear-gradient(135deg, #dfe9f3, #ffffff)",
    "minHeight": "100vh",
    "padding": "30px"
}

CARD_STYLE = {
    "background": "rgba(255, 255, 255, 0.55)",
    "backdropFilter": "blur(10px)",
    "borderRadius": "18px",
    "boxShadow": "0 8px 20px rgba(0,0,0,0.08)",
    "padding": "25px",
    "marginBottom": "30px"
}

TITLE_STYLE = {
    "textAlign": "center",
    "fontSize": "36px",
    "fontWeight": "700",
    "color": "#2C3E50",
    "marginBottom": "15px",
}

app.layout = html.Div([
    html.H1("Users", style=TITLE_STYLE),

    html.Div([
        html.Div(id="table", style=CARD_STYLE),
        html.Div([
            dcc.Graph(id="age_chart", style={"marginBottom": "30px"}),
            dcc.Graph(id="country_chart"),
        ], style=CARD_STYLE),
    ], style={"maxWidth": "1200px", "margin": "0 auto"}),

    dcc.Interval(id="trigger", interval=10000)
], style=AESTHETIC_CSS)

@app.callback(
    [Output("table", "children"),
     Output("age_chart", "figure"),
     Output("country_chart", "figure")],
    [Input("trigger", "n_intervals")]
)
def update_dashboard(_):
    if not event_queue.empty():
        event_queue.get()

    df = load_data()

    table = dash_table.DataTable(
        data=df.to_dict('records'),
        page_size=10,
        style_table={"overflowX": "auto"},
        style_header={
            "backgroundColor": "#6A9FB5",
            "color": "white",
            "fontWeight": "bold",
            "border": "0",
        },
        style_cell={
            "textAlign": "center",
            "padding": "12px",
            "backgroundColor": "rgba(255,255,255,0.7)",
            "border": "0px",
            "fontSize": "14px"
        }
    )

    fig_age = px.histogram(
        df, x="age", title="Distribución de Edad",
        color_discrete_sequence=["#6A9FB5"]
    )
    fig_age.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.5)",
        title_font_size=20
    )

    df_country = df["country"].value_counts().reset_index()
    df_country.columns = ["country", "count"]
    fig_country = px.bar(
        df_country, x="country", y="count",
        title="Usuarios por País",
        color_discrete_sequence=["#6A9FB5"]
    )
    fig_country.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.5)",
        title_font_size=20
    )

    return table, fig_age, fig_country

if __name__ == "__main__":
    app.run(debug=True)
