import sqlite3
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import mannwhitneyu
 
DB_PATH = "cell-count.db"
FREQ_TABLE_PATH = "outputs/frequency_table.csv"
POPULATIONS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]
ALPHA = 0.05
 
# Load frequency table from Part 2
freq = pd.read_csv(FREQ_TABLE_PATH)
 
# Get sample metadata from the database
conn = sqlite3.connect(DB_PATH)
metadata = pd.read_sql_query("""
    SELECT sa.sample_id AS sample, su.response, sa.sample_type, su.condition, su.treatment
    FROM subjects su
    JOIN samples sa ON su.subject_id = sa.subject_id
""", conn)
conn.close()
 
# Filter to melanoma, miraclib, PBMC samples with a recorded response
df = freq.merge(metadata, on="sample")
df = df[
    (df["condition"]   == "melanoma") &
    (df["treatment"]   == "miraclib") &
    (df["sample_type"] == "PBMC") &
    (df["response"].isin(["yes", "no"]))
].copy()
 
# Boxplot: one box per population, split by response
plot_df = df.copy()
plot_df["response"] = plot_df["response"].map({"yes": "Responder", "no": "Non-responder"})
 
fig, ax = plt.subplots(figsize=(11, 6))
sns.boxplot(
    data=plot_df,
    x="population",
    y="percentage",
    hue="response",
    hue_order=["Responder", "Non-responder"],
    palette={"Responder": "#4C72B0", "Non-responder": "#DD8452"},
    width=0.55,
    linewidth=1.2,
    flierprops=dict(marker="o", markersize=2.5, alpha=0.4),
    ax=ax,
)
ax.set_title("Cell Population Relative Frequencies: Responders vs Non-Responders\nMelanoma · Miraclib · PBMC", fontsize=13, fontweight="bold", pad=14)
ax.set_xlabel("Cell Population", fontsize=11)
ax.set_ylabel("Relative Frequency (%)", fontsize=11)
ax.legend(title="Response", fontsize=10, title_fontsize=10)
sns.despine()
plt.tight_layout()
plt.savefig("outputs/boxplot.png", dpi=150)
plt.close()
print("Boxplot saved to: outputs/boxplot.png")
 
# Mann-Whitney U test for each population
results = []
for pop in POPULATIONS:
    r  = df[(df["response"] == "yes")  & (df["population"] == pop)]["percentage"]
    nr = df[(df["response"] == "no")   & (df["population"] == pop)]["percentage"]
    stat, p = mannwhitneyu(r, nr, alternative="two-sided")
    results.append({
        "population":             pop,
        "n_responders":           len(r),
        "n_non_responders":       len(nr),
        "responder_median_%":     round(r.median(), 4),
        "non_responder_median_%": round(nr.median(), 4),
        "mann_whitney_u":         round(stat, 2),
        "p_value":                round(p, 6),
        "significant":            p < ALPHA,
    })
 
results_df = pd.DataFrame(results).sort_values("p_value").reset_index(drop=True)
results_df.to_csv("outputs/statistical_results.csv", index=False)
print("Statistical results saved to: outputs/statistical_results.csv")
print(results_df.to_string(index=False))
