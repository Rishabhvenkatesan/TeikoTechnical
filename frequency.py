import pandas as pd
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "cell-count.db")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
 
POPULATIONS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]
def get_frequency_table(conn: sqlite3.Connection) -> pd.DataFrame:
    query = """
        SELECT
            sa.sample_id AS sample,
            cc.b_cell,
            cc.cd8_t_cell,
            cc.cd4_t_cell,
            cc.nk_cell,
            cc.monocyte
        FROM samples sa
        JOIN cell_counts cc ON sa.sample_id = cc.sample_id
    """
    df = pd.read_sql_query(query, conn)
 
    df["total_count"] = df[POPULATIONS].sum(axis=1)
 
    df_long = df.melt(
        id_vars=["sample", "total_count"],
        value_vars=POPULATIONS,
        var_name="population",
        value_name="count",
    )
 
    df_long["percentage"] = (df_long["count"] / df_long["total_count"] * 100).round(4)
 
    # Final column order
    df_long = df_long[["sample", "total_count", "population", "count", "percentage"]]
    df_long = df_long.sort_values(["sample", "population"]).reset_index(drop=True)
 
    return df_long
 
 
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
 
    conn = sqlite3.connect(DB_PATH)
    try:
        freq_table = get_frequency_table(conn)
    finally:
        conn.close()
 
    out_path = os.path.join(OUTPUT_DIR, "frequency_table.csv")
    freq_table.to_csv(out_path, index=False)
    print(f"Frequency table saved to: {out_path}")
    print(freq_table.head(10).to_string(index=False))
 
 
if __name__ == "__main__":
    main()