# Moguls analysis project

Retrieve moguls results, flatten nested records, and analyse podium finishers
and Australian athletes using CSV exports.

## Setup and execution

From the project folder in PowerShell, using an installed Python:

```powershell
# For a fresh checkout without a working virtual environment:
python -m venv .venv
```

Activate the environment and install the project dependencies:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

To retrieve fresh data, set `MONGODB_URI` in the local `.env` file, then run:

```powershell
python main.py
```

`main.py` connects to MongoDB, reads `Interview.MogulsData`, and replaces the
base exports in `outputs/`. It does not automatically run either analysis.

With the relevant CSVs already present, analyses run independently offline:

```powershell
python australian_analysis.py
python score_analysis.py
```

Keep `.env` private; it is excluded by `.gitignore`. Close CSVs in applications
that lock files before regenerating exports.

## Code map

| File | Responsibility |
| --- | --- |
| `app.py` | Streamlit dashboard for saved Australian jump difficulty averages |
| `database.py` | Load MongoDB configuration and retrieve documents |
| `transformations.py` | Flatten records and convert dates, identifiers and scores |
| `podiums.py` | Identify podium finishers and match their qualification/final runs |
| `main.py` | Coordinate retrieval and export base CSVs, including AUS selection |
| `australian_analysis.py` | Standardise AUS rounds and average jump difficulty by athlete |
| `score_analysis.py` | Compare ten podium-finisher metrics across rounds |

## Data flow

```text
MongoDB -> main.py -> outputs/moguls_flat.csv
                  -> outputs/aus_runs.csv -> australian_analysis.py
                  -> outputs/event_podiums.csv
                  -> outputs/podium_runs.csv -> score_analysis.py
```

The Australian analysis produces `aus_runs_by_round.csv` and
`aus_jump_difficulty_by_round.csv`. The podium analysis produces
`podium_scores_by_round.csv`. All are in `outputs/`; neither analysis creates plots.

## Interactive dashboard

Install the dependencies in your activated environment, then start the app:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL printed by Streamlit (normally http://localhost:8501).
The dashboard reads `outputs/aus_jump_difficulty_by_round.csv` without a database
connection. Select one athlete to compare both jumps across all three rounds against the
supplied podium averages for their recorded men’s or women’s discipline. Round cards show signed gaps, with paired charts,
run counts and a downloadable comparison. Missing results remain missing.
Discipline is matched by FIS code from `outputs/aus_runs.csv`; missing or mixed
disciplines produce an error instead of choosing a benchmark.
Podium benchmarks are fixed in `app.py` and do not refresh with the athlete CSV.

To refresh the summary, run `python australian_analysis.py` after updating the
source exports, then click **Reload saved CSV**. The app does not regenerate data.
Date and event filters are unavailable because this file pools all recorded events.

## Analysis guides

- [Australian analysis](AUSTRALIAN_ANALYSIS.md): round mapping, input/output
  schema, means, missing values, checks, limitations and troubleshooting.
- [Podium score analysis](SCORE_ANALYSIS.md): ten metrics, event matching and
  rules for merging round columns.

Derived files are snapshots. After refreshing data with `main.py`, rerun each
analysis you need so its outputs reflect the new source files.
