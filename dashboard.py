import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, dash_table, Input, Output

DB_PATH = "cell-count.db"
POPULATIONS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]

# Data loading

def load_frequency_table():
    return pd.read_csv("outputs/frequency_table.csv")

def load_stats():
    return pd.read_csv("outputs/statistical_results.csv")

def load_metadata():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT su.subject_id, su.project, su.condition, su.sex,
               su.treatment, su.response,
               sa.sample_id, sa.sample_type, sa.time_from_treatment_start,
               cc.b_cell, cc.cd8_t_cell, cc.cd4_t_cell, cc.nk_cell, cc.monocyte
        FROM subjects su
        JOIN samples sa ON su.subject_id = sa.subject_id
        JOIN cell_counts cc ON sa.sample_id = cc.sample_id
    """, conn)
    conn.close()
    df["total_count"] = df[POPULATIONS].sum(axis=1)
    for p in POPULATIONS:
        df[f"{p}_pct"] = df[p] / df["total_count"] * 100
    return df

freq   = load_frequency_table()
stats  = load_stats()
meta   = load_metadata()

# Subset for Part 3 boxplot
part3 = meta[
    (meta["condition"]   == "melanoma") &
    (meta["treatment"]   == "miraclib") &
    (meta["sample_type"] == "PBMC") &
    (meta["response"].isin(["yes", "no"]))
].copy()
part3["Response"] = part3["response"].map({"yes": "Responder", "no": "Non-responder"})

# Subset for Part 4
part4 = meta[
    (meta["condition"]              == "melanoma") &
    (meta["treatment"]              == "miraclib") &
    (meta["sample_type"]            == "PBMC") &
    (meta["time_from_treatment_start"] == 0)
].copy()

# App 

app = Dash(__name__)
app.title = "Loblaw Bio — Immune Cell Dashboard"

COLORS = {"bg": "#f8f9fa", "card": "#ffffff", "blue": "#4C72B0", "orange": "#DD8452"}

def card(children, style=None):
    base = {"background": COLORS["card"], "borderRadius": "8px",
            "padding": "24px", "marginBottom": "24px",
            "boxShadow": "0 1px 4px rgba(0,0,0,0.08)"}
    if style:
        base.update(style)
    return html.Div(children, style=base)

def section_title(text):
    return html.H3(text, style={"marginTop": 0, "marginBottom": "16px",
                                "color": "#1a1a2e", "fontWeight": 600})

app.layout = html.Div(style={"backgroundColor": COLORS["bg"], "minHeight": "100vh",
                              "fontFamily": "Inter, sans-serif", "padding": "32px 48px"}, children=[

    html.H1("Loblaw Bio — Immune Cell Clinical Trial Dashboard",
            style={"color": "#1a1a2e", "marginBottom": "8px"}),
    html.P("Miraclib clinical trial · Immune cell population analysis",
           style={"color": "#666", "marginBottom": "32px"}),

    # Part 2: Frequency Table 
    card([
        section_title("Part 2 | Cell Population Frequencies by Sample"),
        html.Div([
            html.Label("Filter by condition:", style={"marginRight": "12px", "fontWeight": 500}),
            dcc.Dropdown(
                id="p2-condition",
                options=[{"label": "All", "value": "all"}] +
                        [{"label": c, "value": c} for c in sorted(meta["condition"].unique())],
                value="all", clearable=False,
                style={"width": "220px", "display": "inline-block", "marginRight": "24px"}
            ),
            html.Label("Filter by sample type:", style={"marginRight": "12px", "fontWeight": 500}),
            dcc.Dropdown(
                id="p2-sampletype",
                options=[{"label": "All", "value": "all"}] +
                        [{"label": s, "value": s} for s in sorted(meta["sample_type"].unique())],
                value="all", clearable=False,
                style={"width": "180px", "display": "inline-block"}
            ),
        ], style={"marginBottom": "16px", "display": "flex", "alignItems": "center"}),
        dcc.Graph(id="p2-bar"),
    ]),

    # Part 3: Statistical Analysis 
    card([
        section_title("Part 3 | Responders vs Non-Responders (Melanoma | Miraclib | PBMC)"),
        html.Div([
            html.Div([
                dcc.Graph(id="p3-boxplot",
                          figure=px.box(
                              part3.melt(id_vars=["Response"],
                                         value_vars=[f"{p}_pct" for p in POPULATIONS],
                                         var_name="population", value_name="percentage")
                                   .assign(population=lambda d: d["population"].str.replace("_pct", "", regex=False)),
                              x="population", y="percentage", color="Response",
                              color_discrete_map={"Responder": COLORS["blue"], "Non-responder": COLORS["orange"]},
                              labels={"population": "Cell Population", "percentage": "Relative Frequency (%)"},
                              title="Relative Frequency by Population"
                          ).update_layout(plot_bgcolor="white", paper_bgcolor="white"))
            ], style={"width": "60%"}),
            html.Div([
                html.H4("Statistical Results (Mann-Whitney U, α=0.05)",
                        style={"marginTop": 0, "fontSize": "14px"}),
                dash_table.DataTable(
                    data=stats.to_dict("records"),
                    columns=[{"name": c, "id": c} for c in stats.columns],
                    style_table={"overflowX": "auto"},
                    style_cell={"fontSize": "12px", "padding": "6px 10px", "textAlign": "left"},
                    style_header={"fontWeight": 600, "backgroundColor": "#f0f0f0"},
                    style_data_conditional=[{
                        "if": {"filter_query": "{significant} = True"},
                        "backgroundColor": "#e8f4e8", "fontWeight": 600
                    }]
                ),
                html.P("Highlighted rows are statistically significant (p < 0.05).",
                       style={"fontSize": "12px", "color": "#555", "marginTop": "12px"})
            ], style={"width": "38%", "paddingLeft": "24px"}),
        ], style={"display": "flex", "alignItems": "flex-start"}),
    ]),

    # ── Part 4: Subset Analysis ───────────────────────────────────────────────
    card([
        section_title("Part 4 | Baseline Subset Analysis (Melanoma | Miraclib | PBMC | Time=0)"),
        html.Div([

            # Samples per project
            html.Div([
                dcc.Graph(figure=px.bar(
                    part4.groupby("project")["sample_id"].count().reset_index()
                         .rename(columns={"sample_id": "n_samples"}),
                    x="project", y="n_samples", title="Samples per Project",
                    color="project", color_discrete_sequence=[COLORS["blue"], COLORS["orange"]],
                    labels={"n_samples": "Number of Samples"}
                ).update_layout(showlegend=False, plot_bgcolor="white", paper_bgcolor="white"))
            ], style={"width": "33%"}),

            # Subjects by response
            html.Div([
                dcc.Graph(figure=px.pie(
                    part4.drop_duplicates("subject_id").groupby("response")["subject_id"]
                         .count().reset_index().rename(columns={"subject_id": "n_subjects"}),
                    names="response", values="n_subjects",
                    title="Subjects by Response",
                    color_discrete_sequence=[COLORS["orange"], COLORS["blue"]]
                ).update_layout(paper_bgcolor="white"))
            ], style={"width": "33%"}),

            # Subjects by sex
            html.Div([
                dcc.Graph(figure=px.pie(
                    part4.drop_duplicates("subject_id").groupby("sex")["subject_id"]
                         .count().reset_index().rename(columns={"subject_id": "n_subjects"}),
                    names="sex", values="n_subjects",
                    title="Subjects by Sex",
                    color_discrete_sequence=[COLORS["blue"], COLORS["orange"]]
                ).update_layout(paper_bgcolor="white"))
            ], style={"width": "33%"}),

        ], style={"display": "flex"}),

        # Key stat callout
        html.Div([
            html.Span("Avg B cells — Male Responders at Baseline: ", style={"fontWeight": 500}),
            html.Span(
                f"{part4[(part4['sex'] == 'M') & (part4['response'] == 'yes')]['b_cell'].mean():.2f}",
                style={"fontSize": "20px", "fontWeight": 700, "color": COLORS["blue"]}
            ),
        ], style={"marginTop": "16px", "padding": "12px 20px",
                  "backgroundColor": "#eef2fb", "borderRadius": "6px",
                  "display": "inline-block"})
    ]),
])

# Callbacks 

@app.callback(Output("p2-bar", "figure"),
              Input("p2-condition", "value"),
              Input("p2-sampletype", "value"))
def update_freq_chart(condition, sampletype):
    filtered = meta.copy()
    if condition != "all":
        filtered = filtered[filtered["condition"] == condition]
    if sampletype != "all":
        filtered = filtered[filtered["sample_type"] == sampletype]

    # Show up to 100 samples as a stacked bar so filtering visibly changes the chart
    filtered = filtered.head(100)

    melted = filtered.melt(
        id_vars=["sample_id"],
        value_vars=[f"{p}_pct" for p in POPULATIONS],
        var_name="population", value_name="percentage"
    )
    melted["population"] = melted["population"].str.replace("_pct", "", regex=False)

    fig = px.bar(melted, x="sample_id", y="percentage", color="population",
                 barmode="stack",
                 labels={"sample_id": "Sample", "percentage": "Relative Frequency (%)", "population": "Population"},
                 title=f"Cell Population Frequencies per Sample — {condition} | {sampletype}")
    fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                      xaxis_showticklabels=False,
                      uirevision=f"{condition}-{sampletype}")
    return fig


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)