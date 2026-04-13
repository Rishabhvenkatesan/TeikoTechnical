import sqlite3
import pandas as pd
import os
 
DB_PATH = "cell-count.db"
OUTPUT_DIR = "outputs"
 
conn = sqlite3.connect(DB_PATH)
 
# Melanoma PBMC samples at baseline treated with miraclib
df = pd.read_sql_query("""
    SELECT su.subject_id, su.project, su.sex, su.response,
           sa.sample_id, cc.b_cell
    FROM subjects su
    JOIN samples sa ON su.subject_id = sa.subject_id
    JOIN cell_counts cc ON sa.sample_id = cc.sample_id
    WHERE su.condition = 'melanoma'
      AND su.treatment = 'miraclib'
      AND sa.sample_type = 'PBMC'
      AND sa.time_from_treatment_start = 0
""", conn)
conn.close()
 
print(f"Total baseline samples: {len(df)}\n")
 
# Samples per project
samples_per_project = df.groupby("project")["sample_id"].count().reset_index()
samples_per_project.columns = ["project", "n_samples"]
print("Samples per project:")
print(samples_per_project.to_string(index=False))
 
# Subjects per response group (unique subjects)
subjects = df.drop_duplicates("subject_id")
response_counts = subjects.groupby("response")["subject_id"].count().reset_index()
response_counts.columns = ["response", "n_subjects"]
print("\nSubjects by response:")
print(response_counts.to_string(index=False))
 
# Subjects per sex
sex_counts = subjects.groupby("sex")["subject_id"].count().reset_index()
sex_counts.columns = ["sex", "n_subjects"]
print("\nSubjects by sex:")
print(sex_counts.to_string(index=False))
 
# Average B cells for male melanoma responders at baseline
avg_bcell = df[(df["sex"] == "M") & (df["response"] == "yes")]["b_cell"].mean()
print(f"\nAverage B cells (male responders, time=0) for following question: {avg_bcell:.2f}")
 
# Save outputs
os.makedirs(OUTPUT_DIR, exist_ok=True)
samples_per_project.to_csv(f"{OUTPUT_DIR}/subset_samples_per_project.csv", index=False)
response_counts.to_csv(f"{OUTPUT_DIR}/subset_response_counts.csv", index=False)
sex_counts.to_csv(f"{OUTPUT_DIR}/subset_sex_counts.csv", index=False)
print("\nSubset analysis saved to outputs/")