# Loblaw Bio — Immune Cell Clinical Trial Analysis

Analysis of immune cell population data from a clinical trial evaluating the drug candidate **miraclib**.

---

## How to Run

### Requirements
Python 3.10+ is required. All dependencies are listed in `requirements.txt`.

### Setup
```bash
make setup
```

### Run the full pipeline
```bash
make pipeline
```
This will:
1. Initialize the SQLite database and load `cell-count.csv`
2. Generate the cell population frequency table (`outputs/frequency_table.csv`)
3. Run statistical analysis and produce the boxplot (`outputs/boxplot.png`, `outputs/statistical_results.csv`)
4. Run the baseline subset analysis (`outputs/subset_*.csv`)

### Launch the dashboard
```bash
make dashboard
```
Then open [http://localhost:8050](http://localhost:8050) in your browser.

---

## Database Schema

Three normalized tables:

```
subjects (subject_id PK, project, condition, age, sex, treatment, response)
    │
    └──< samples (sample_id PK, subject_id FK, sample_type, time_from_treatment_start)
              │
              └──< cell_counts (sample_id PK/FK, b_cell, cd8_t_cell, cd4_t_cell, nk_cell, monocyte)
```

**`subjects`** stores one row per patient. All subject-level metadata (demographics, treatment, response) lives here rather than being repeated on every sample row.

**`samples`** stores one row per biological sample. It links to `subjects` via `subject_id` and holds sample-level metadata like sample type and timepoint.

**`cell_counts`** stores one row per sample with the raw cell counts for each of the five immune populations.

### Rationale

Separating the three concerns — who the patient is, what sample was collected, and what was measured — follows standard third normal form (3NF). This avoids repeating patient demographics across every sample row and keeps the schema clean and queryable at any level.

### Scalability

This design scales well:
- **Hundreds of projects**: `project` is a field on `subjects`. A dedicated `projects` table could be added if project-level metadata (e.g. trial name, PI, start date) were needed.
- **Thousands of samples**: The schema is already row-per-sample. Adding indexes on commonly filtered columns (`condition`, `treatment`, `sample_type`, `time_from_treatment_start`) would keep queries fast at scale.
- **New cell populations or assay types**: A new measurement type could be added as a new table (e.g. `cytokine_levels`) linked to `samples` by `sample_id`, without touching the existing schema.
- **New analytics**: Because subject metadata and measurements are separated, analytical queries can easily aggregate at the subject, sample, project, or population level without restructuring data.

---

## Code Structure

```
.
├── load_data.py          # Part 1: initialize DB and load cell-count.csv
├── frequency.py           # Part 2: compute relative frequencies per sample
├── stats_analysis.py     # Part 3: Mann-Whitney U tests + boxplot
├── subset_analysis.py    # Part 4: baseline subset queries
├── dashboard.py          # Interactive Dash dashboard
├── cell-count.csv        # Input data
├── outputs/              # All generated tables and plots
├── requirements.txt
└── Makefile
```

Each part of the analysis is its own standalone script that can be run independently. They share the SQLite database (`cell-count.db`) as the single source of truth, and later scripts consume outputs from earlier ones (e.g. `stats_analysis.py` reads `outputs/frequency_table.csv` produced by `frequency.py`). This makes the pipeline easy to follow, debug, and extend.

---

## Dashboard

The dashboard is built with [Dash](https://dash.plotly.com/) and covers all four parts of the analysis:

- **Part 2**: Interactive bar chart of average cell population frequencies, filterable by condition and sample type
- **Part 3**: Boxplot comparing responders vs non-responders, with the statistical results table highlighted for significant populations
- **Part 4**: Baseline subset breakdowns by project, response, and sex, with the key B cell average callout

Run `make dashboard` and open [http://localhost:8050](http://localhost:8050).