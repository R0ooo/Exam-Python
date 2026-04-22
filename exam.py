import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

# ============================ Données =========================#
df = pd.read_csv(r"C:\Users\compteadmin\Documents\python\supermarket_sales.csv")
df["Date"] = pd.to_datetime(df["Date"])
df["Week"] = df["Date"].dt.to_period("W").apply(lambda r: r.start_time)

villes = sorted(df["City"].unique())
sexes  = sorted(df["Gender"].unique())

# ============================ Application =====================#
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO])

# ============================ Style global =====================#
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Supermarket Dashboard</title>
        {%favicon%}
        {%css%}
        <style>
            html, body {
                height: 100%;
                margin: 0;
                overflow: hidden;
            }
            .graph-card .card-body {
                padding: 6px;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# ============================ Card =====================#
def card(title, id):
    return dbc.Card(
        dbc.CardBody([
            html.P(title, className="text-muted mb-1", style={"fontSize": "0.75rem"}),
            html.H5(id=id, className="fw-bold text-primary mb-0"),
        ], style={"padding": "8px 12px"}),
        className="shadow-sm h-100"
    )

# ============================ Lignes et colonnes =====================#

app.layout = dbc.Container([

    # == Ligne 1 : Titre + Filtres + KPI =================#
    dbc.Row([
        dbc.Col(
            html.H5("🛒 Supermarket Sales", className="fw-bold mb-0 mt-1"),
            md=3
        ),
        dbc.Col(
            dcc.Dropdown(
                id="filter-city",
                options=[{"label": "Toutes les villes", "value": "Toutes"}] +
                        [{"label": v, "value": v} for v in villes],
                value="Toutes",
                clearable=False,
            ),
            md=2
        ),
        dbc.Col(
            dcc.Dropdown(
                id="filter-gender",
                options=[{"label": "Tous les sexes", "value": "Tous"}] +
                        [{"label": s, "value": s} for s in sexes],
                value="Tous",
                clearable=False,
            ),
            md=2
        ),
        dbc.Col(card("💰 Montant total (€)", "kpi-total"),  md=2),
        dbc.Col(card("⭐ Évaluation moyenne", "kpi-rating"), md=2),
    ], align="center", className="mb-1 mt-1 g-3"),

    # == Ligne 2 : Graphiques ( camembert et histogramme) =================#
    dbc.Row([
        dbc.Col(
            dbc.Card(dbc.CardBody(
                dcc.Graph(id="graph-histo", style={"height": "40vh"},
                          config={"displayModeBar": False})
            ), className="shadow-sm graph-card"),
            md=6
        ),
        dbc.Col(
            dbc.Card(dbc.CardBody(
                dcc.Graph(id="graph-pie", style={"height": "40vh"},
                          config={"displayModeBar": False})
            ), className="shadow-sm graph-card"),
            md=6
        ),
    ], className="mb-1 g-1"),

    # == Ligne 3 : Graphiques (évolution) =================#
    dbc.Row([
        dbc.Col(
            dbc.Card(dbc.CardBody(
                dcc.Graph(id="graph-line", style={"height": "40vh"},
                          config={"displayModeBar": False})
            ), className="shadow-sm graph-card"),
            md=12
        ),
    ], className="g-1"),

], fluid=True, style={"height": "100vh", "overflow": "hidden", "padding": "8px 16px"})


# ================= Callback ==============================#
@app.callback(
    Output("kpi-total",   "children"),
    Output("kpi-rating",  "children"),
    Output("graph-histo", "figure"),
    Output("graph-pie",   "figure"),
    Output("graph-line",  "figure"),
    Input("filter-city",   "value"),
    Input("filter-gender", "value"),
)
def update_dashboard(city, gender):
    # Filtrage
    dff = df.copy()
    if city   != "Toutes": dff = dff[dff["City"]   == city]
    if gender != "Tous":   dff = dff[dff["Gender"] == gender]

    # KPIs
    total_achats = f"{dff['Total'].sum():,.2f} €" if len(dff) > 0 else "N/A"
    avg_rating   = f"{dff['Rating'].mean():.2f} / 10" if len(dff) > 0 else "N/A"

    LAYOUT_BASE = dict(
        margin=dict(l=30, r=15, t=35, b=30),
        template="plotly_white",
        font=dict(size=11),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    # Histogramme
    fig_histo = px.histogram(
        dff, x="Total", color="Gender",
        facet_col="City" if city == "Toutes" else None,
        nbins=25,
        title="Répartition des montants d'achats",
        labels={"Total": "Montant (€)", "Gender": "Sexe"},
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig_histo.update_layout(**LAYOUT_BASE, barmode="group")

    # Camembert
    pie_data = dff.groupby("Product line", as_index=False)["Total"].sum()
    fig_pie = px.pie(
    pie_data, names="Product line", values="Total",
    title="Ventes par catégorie de produit",
    color_discrete_sequence=px.colors.qualitative.Pastel,
    hole=0.35,
)
    fig_pie.update_traces(textposition="inside", textinfo="percent", textfont_size=10)
    fig_pie.update_layout(
        margin=dict(l=10, r=10, t=35, b=10),
        template="plotly_white",
        font=dict(size=10),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5,
            font=dict(size=9),
        ),
)


    # Évolution hebdomadaire
    line_data = (
        dff.groupby(["Week", "City"], as_index=False)["Total"]
           .sum().sort_values("Week")
    )
    fig_line = px.line(
        line_data, x="Week", y="Total", color="City",
        markers=True,
        title="Évolution hebdomadaire des ventes par ville",
        labels={"Week": "Semaine", "Total": "Montant (€)", "City": "Ville"},
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    fig_line.update_layout(**LAYOUT_BASE)

    return total_achats, avg_rating, fig_histo, fig_pie, fig_line


if __name__ == "__main__":
    app.run(debug=True, port=8051, jupyter_mode="external")