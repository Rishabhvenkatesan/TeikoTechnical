import sqlite3
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, dash_table, Input, Output

DB_PATH = "cell-count.db"
POPULATIONS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]

conn = sqlite3.connect(DB_PATH)
meta = pd.read_sql_query("""
    SELECT su.subject_id, su.project, su.condition, su.sex,
           su.treatment, su.response,
           sa.sample_id, sa.sample_type, sa.time_from_treatment_start,
           cc.b_cell, cc.cd8_t_cell, cc.cd4_t_cell, cc.nk_cell, cc.monocyte
    FROM subjects su
    JOIN samples sa ON su.subject_id = sa.subject_id
    JOIN cell_counts cc ON sa.sample_id = cc.sample_id
""", conn)
conn.close()

stats = pd.read_csv("outputs/statistical_results.csv")

meta["total_count"] = meta[POPULATIONS].sum(axis=1)
for p in POPULATIONS:
    meta[f"{p}_pct"] = meta[p] / meta["total_count"] * 100

part3 = meta[
    (meta["condition"] == "melanoma") &
    (meta["treatment"] == "miraclib") &
    (meta["sample_type"] == "PBMC") &
    (meta["response"].isin(["yes", "no"]))
].copy()
part3["response"] = part3["response"].map({"yes": "Responder", "no": "Non-responder"})

part4 = meta[
    (meta["condition"] == "melanoma") &
    (meta["treatment"] == "miraclib") &
    (meta["sample_type"] == "PBMC") &
    (meta["time_from_treatment_start"] == 0)
].copy()

avg_bcell = part4[(part4["sex"] == "M") & (part4["response"] == "yes")]["b_cell"].mean()

app = Dash(__name__)
app.title = "Immune Cell Dashboard"

app.layout = html.Div(style={"padding": "20px", "fontFamily": "Arial, sans-serif"}, children=[

    html.H2("Immune Cell Population Dashboard"),
    html.Hr(),

    # Part 2
    html.H3("Cell Population Frequencies by Sample"),
    html.Div([
        html.Label("Condition: "),
        dcc.Dropdown(
            id="p2-condition",
            options=[{"label": "All", "value": "all"}] +
                    [{"label": c, "value": c} for c in sorted(meta["condition"].unique())],
            value="all", clearable=False, style={"width": "200px", "display": "inline-block", "marginRight": "20px"}
        ),
        html.Label("Sample type: "),
        dcc.Dropdown(
            id="p2-sampletype",
            options=[{"label": "All", "value": "all"}] +
                    [{"label": s, "value": s} for s in sorted(meta["sample_type"].unique())],
            value="all", clearable=False, style={"width": "160px", "display": "inline-block"}
        ),
    ], style={"marginBottom": "10px"}),
    dcc.Graph(id="p2-bar"),

    html.Hr(),

    # Part 3
    html.H3("Responders vs Non-Responders (Melanoma, Miraclib, PBMC)"),
    dcc.Graph(figure=px.box(
        part3.melt(id_vars=["response"],
                   value_vars=[f"{p}_pct" for p in POPULATIONS],
                   var_name="population", value_name="percentage")
             .assign(population=lambda d: d["population"].str.replace("_pct", "", regex=False)),
        x="population", y="percentage", color="response",
        labels={"population": "Cell Population", "percentage": "Relative Frequency (%)", "response": "Response"},
        title="Cell population frequencies by response group"
    )),
    html.H4("Statistical test results (Mann-Whitney U, alpha=0.05)"),
    dash_table.DataTable(
        data=stats.to_dict("records"),
        columns=[{"name": c, "id": c} for c in stats.columns],
        style_cell={"textAlign": "left", "padding": "6px"},
        style_header={"fontWeight": "bold"},
    ),

    html.Hr(),

    # Part 4
    html.H3("Baseline Subset (Melanoma, Miraclib, PBMC, Time=0)"),
    html.Div([
        dcc.Graph(
            figure=px.bar(
                part4.groupby("project")["sample_id"].count().reset_index().rename(columns={"sample_id": "n_samples"}),
                x="project", y="n_samples", title="Samples per project",
                labels={"n_samples": "Number of samples"}
            ),
            style={"display": "inline-block", "width": "33%"}
        ),
        dcc.Graph(
            figure=px.pie(
                part4.drop_duplicates("subject_id").groupby("response")["subject_id"]
                     .count().reset_index().rename(columns={"subject_id": "n_subjects"}),
                names="response", values="n_subjects", title="Subjects by response"
            ),
            style={"display": "inline-block", "width": "33%"}
        ),
        dcc.Graph(
            figure=px.pie(
                part4.drop_duplicates("subject_id").groupby("sex")["subject_id"]
                     .count().reset_index().rename(columns={"subject_id": "n_subjects"}),
                names="sex", values="n_subjects", title="Subjects by sex"
            ),
            style={"display": "inline-block", "width": "33%"}
        ),
    ]),
    html.P(f"Average B cell count for male responders at baseline: {avg_bcell:.2f}"),
])


@app.callback(Output("p2-bar", "figure"),
              Input("p2-condition", "value"),
              Input("p2-sampletype", "value"))
def update_freq_chart(condition, sampletype):
    filtered = meta.copy()
    if condition != "all":
        filtered = filtered[filtered["condition"] == condition]
    if sampletype != "all":
        filtered = filtered[filtered["sample_type"] == sampletype]

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
                 title=f"Cell frequencies per sample ({condition}, {sampletype})")
    fig.update_layout(xaxis_showticklabels=False, uirevision=f"{condition}-{sampletype}")
    return fig


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)