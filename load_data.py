import sqlite3
import csv
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "cell-count.db")
CSV_PATH = os.path.join(os.path.dirname(__file__), "cell-count.csv")

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS subjects ( 
    subject_id TEXT PRIMARY KEY,
    project     TEXT    NOT NULL,
    condition   TEXT,
    age         INTEGER,
    sex         TEXT,
    treatment   TEXT,
    response    TEXT
);
 
CREATE TABLE IF NOT EXISTS samples (
    sample_id                   TEXT    PRIMARY KEY,
    subject_id                  TEXT    NOT NULL REFERENCES subjects(subject_id),
    sample_type                 TEXT,     
    time_from_treatment_start   INTEGER
);
 
CREATE TABLE IF NOT EXISTS cell_counts (
    sample_id   TEXT    PRIMARY KEY REFERENCES samples(sample_id),
    b_cell      INTEGER NOT NULL DEFAULT 0,
    cd8_t_cell  INTEGER NOT NULL DEFAULT 0,
    cd4_t_cell  INTEGER NOT NULL DEFAULT 0,
    nk_cell     INTEGER NOT NULL DEFAULT 0,
    monocyte    INTEGER NOT NULL DEFAULT 0
);
"""
def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()
    print("Database schema initialized")

def load_csv(conn: sqlite3.Connection, csv_path: str) -> None:
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
 
    subjects_seen = set()
    subject_rows = []
    sample_rows = []
    count_rows = []
 
    for row in rows:
        subject_id = row["subject"]
 
        # Collect unique subjects only
        if subject_id not in subjects_seen:
            subjects_seen.add(subject_id)
            response = row["response"].strip() if row["response"].strip() else None
            subject_rows.append((
                subject_id,
                row["project"],
                row["condition"],
                int(row["age"]) if row["age"].strip() else None,
                row["sex"],
                row["treatment"],
                response,
            ))
 
        sample_rows.append((
            row["sample"],
            subject_id,
            row["sample_type"],
            int(row["time_from_treatment_start"]) if row["time_from_treatment_start"].strip() else None,
        ))
 
        count_rows.append((
            row["sample"],
            int(row["b_cell"]),
            int(row["cd8_t_cell"]),
            int(row["cd4_t_cell"]),
            int(row["nk_cell"]),
            int(row["monocyte"]),
        ))
 
    conn.executemany(
        "INSERT OR IGNORE INTO subjects VALUES (?,?,?,?,?,?,?)",
        subject_rows,
    )
    conn.executemany(
        "INSERT OR IGNORE INTO samples VALUES (?,?,?,?)",
        sample_rows,
    )
    conn.executemany(
        "INSERT OR IGNORE INTO cell_counts VALUES (?,?,?,?,?,?)",
        count_rows,
    )
    conn.commit()
 
    print(f"Loaded {len(subject_rows)} subjects, {len(sample_rows)} samples, {len(count_rows)} cell count records.")
def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed existing database at {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    try:
        init_db(conn)
        load_csv(conn, CSV_PATH)
    finally:
        conn.close()
    print(f"Database ready at: {DB_PATH}")

if __name__ == "__main__":
    main()