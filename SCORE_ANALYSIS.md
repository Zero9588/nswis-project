# Podium score analysis

## Run the analysis

From the project folder, with the virtual environment active:

```powershell
python score_analysis.py
```

Alternatively, use `.\.venv\Scripts\python.exe score_analysis.py`.
The script reads `outputs/podium_runs.csv` and replaces
`outputs/podium_scores_by_round.csv`. Paths are relative to the script, so the
working directory does not affect where files are read or written.
It does not connect to MongoDB. To refresh the source data, run `main.py` first.
It creates no visualisations. Previously generated charts are not updated or deleted.

## Output structure

Each row represents **one athlete at one event, for one metric**. Every
athlete/event has ten rows, even when a metric has no recorded values.

| Column | Meaning |
| --- | --- |
| `event`, `event_date`, `venue`, `discipline` | Identify the event, keeping men's and women's results separate |
| `athlete` | Athlete display name |
| `fis_code` | Athlete identifier; read as text to preserve leading zeros |
| `podium_rank` | Final podium placing, repeated across metrics |
| `metric` | Which of the ten measurements the row contains |
| `Qualification` | Measurement from the sole recorded qualification run |
| `Final 1` | Measurement from Final 1, if recorded |
| `Deciding Final` | Measurement from Final or Final 2 |

| Metric | Meaning | Unit |
| --- | --- | --- |
| `run_score` | Overall run score | Points |
| `air_total` | Combined air component | Points |
| `turns_total` | Turns component | Points |
| `time_points` | Time component, not elapsed time | Points |
| `jump_1_degree_diff` | First jump difficulty | Multiplier |
| `jump_2_degree_diff` | Second jump difficulty | Multiplier |
| `jump_1_judge_6_score` | Judge 6 score for jump 1 | Points |
| `jump_1_judge_7_score` | Judge 7 score for jump 1 | Points |
| `jump_2_judge_6_score` | Judge 6 score for jump 2 | Points |
| `jump_2_judge_7_score` | Judge 7 score for jump 2 | Points |

For example, one athlete has a `run_score` row and a separate `air_total` row,
each with values across the three round columns. Difficulty multipliers are
not points and should not be added to the score components.
Individual judge scores are preserved as recorded, without averaging or applying
difficulty multipliers. Judge numbers identify judging positions at that event,
not necessarily the same person across events.
Empty cells mean the run or metric is missing, not zero.
CSV does not store column types: load `fis_code` with
`pd.read_csv(path, dtype={"fis_code": "string"})`.

## How the transformation works

`compare_scores_by_round(data)` in `score_analysis.py` accepts the full flattened
podium-run DataFrame and returns the comparison without changing its input.

1. Validate required columns, identifying fields, numeric measurements and podium places.
2. Map source round labels to the three output rounds. Qualification,
   Qualification 1 and Qualification 2 all map to Qualification. Final and
   Final 2 map to Deciding Final. The recognised `QUALIFICATION RUN 1 RESULTS`
   prefixed labels map according to their ending, just like the standard labels.
3. Check original run records for conflicts using **event + event_date + venue +
   discipline + fis_code + combined round**. More than one matching run raises
   an error with identifying details. This includes two actual qualification
   runs, both Final and Final 2, and duplicate rows. The check runs before
   reshaping metrics, including when some measurements are blank: metrics from
   different runs are never combined into a synthetic run.
4. Use `melt()` to reshape ten metric columns into `metric` and `value` rows.
5. Use `pivot()` to turn rounds into columns. No scores are averaged or summed.
6. Attach name and podium placing using the five athlete/event identifiers,
   validating that each identifier combination has one set of labels.
7. Sort by event, podium placing, FIS code and the documented metric order.

Unknown rounds, inconsistent names or podium ranks, missing identifiers,
invalid numeric values and overlapping rounds stop the export for review.
There is no automatic choice of best or latest score. When validation fails,
an existing output CSV remains the result of the previous successful run.

Only podium finishers and runs present in `podium_runs.csv` are analysed.
This script does not infer missing qualifications, change podium selection,
or calculate new competition scores. To add a future metric, ensure it is
exported in `podium_runs.csv`, then extend `METRICS` and this documentation.
