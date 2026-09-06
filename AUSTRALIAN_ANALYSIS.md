# Australian jump difficulty analysis

Run `python australian_analysis.py` from your activated virtual environment.
It reads `outputs/aus_runs.csv`; run `main.py` first to refresh that source.
All paths are relative to the script. No database queries or charts are made,
and the source CSV is preserved.

## Outputs

- `outputs/aus_runs_by_round.csv`: individual runs, sorted by athlete, FIS code,
  round order and event date. All source fields remain, plus `original_round`.
- `outputs/aus_jump_difficulty_by_round.csv`: one row per athlete FIS code and
  round, containing `athlete`, `fis_code`, `round`, `run_count`,
  `jump_1_degree_diff_mean`, and `jump_2_degree_diff_mean`.

## Round rules

| Source round | Standardised round |
| --- | --- |
| Results Qualification, Qualification 1 or Qualification 2 | Qualification |
| Results Final 1 | Final 1 |
| Results Final or Final 2 | Deciding Final |

The recognised `QUALIFICATION RUN 1 RESULTS` prefixed labels follow their
ending: Qualification, Final 1 or Final 2. `Results Overall` and
`OVERALL RESULTS - - Partial` are excluded. Unknown labels raise an error.

Qualification 1 and Qualification 2 are **not combined into one run**. Both
remain individual rows under Qualification, distinguished by `original_round`.
This differs from the podium score pivot, which requires one run per combined
round. The Australian analysis averages all recorded individual runs.

## Averages and identity

Group by `fis_code` and standardised `round`, across all events in the source.
Athlete names are display labels; inconsistent names for one FIS code are
flagged for review. FIS codes are read as text to preserve leading zeros.
Only athlete/round combinations that exist are exported.

Each row contributes equally to the mean. Two qualification runs at an event
therefore contribute twice, while an event with one contributes once. These
are averages of recorded runs, not averages of event averages.

Difficulty values are multipliers, not score points. Missing values are
excluded separately for each jump's mean and never replaced by zero.
`run_count` counts every run; when difficulty is missing, the number of values
used for that mean can be lower. An entirely missing mean exports as blank.
Numeric values are not rounded before export.

For example, jump 1 values of 0.8 and 1.0 produce a mean of 0.9. If jump 2 is
missing on the first run and 1.0 on the second, its mean is 1.0, while run_count
is still 2. An athlete who never reached Deciding Final has no row for that round.

## Function interface and input contract

| Function | Input | Output |
| --- | --- | --- |
| `organise_athlete_runs(data)` | Raw AUS run DataFrame | Sorted individual runs with standardised round and original_round |
| `average_jump_difficulty(runs)` | Organised runs containing both jump difficulty columns | Athlete/round means and run counts |
| `main()` | Reads the saved source CSV | Writes both derived CSVs and prints row counts |

The organiser requires `athlete`, `fis_code`, `country`, `round`, `event_date`,
`event`, `venue` and `discipline`. Averaging additionally requires
`jump_1_degree_diff` and `jump_2_degree_diff`. Dates are expected in the
YYYY-MM-DD format supplied by `transformations.py`; the organiser does not
parse them again. Call the organiser on the raw CSV, not on its own output.
Both transformation functions return new DataFrames without changing their inputs.

To use the functions from Python:

```python
import pandas as pd
from australian_analysis import organise_athlete_runs, average_jump_difficulty

source = pd.read_csv("outputs/aus_runs.csv", dtype={"fis_code": "string"})
runs = organise_athlete_runs(source)
averages = average_jump_difficulty(runs)
```

## Validation and troubleshooting

| Condition | Behaviour / action |
| --- | --- |
| Source CSV missing | Run main.py to create it |
| Required field absent | Regenerate the source with the current flattening/export code |
| Non-AUS or missing country | Organiser raises ValueError; inspect the source selection |
| Unknown or missing round | Organiser raises ValueError; review the label before extending ROUND_LABELS |
| Missing retained athlete name/FIS code | Organiser raises ValueError; correct the source identity |
| Multiple names for one FIS code | Averaging raises ValueError; review name consistency |
| Non-numeric difficulty | Numeric conversion raises ValueError; inspect the original value |
| Empty input with required columns | Empty outputs with headers |
| CSV locked by another application | Close the file and rerun the script |

Validation completes before either export is written. The two files are then
written sequentially; a write error could leave one refreshed and the other
unchanged. After fixing the error, rerun to refresh both files.

## Interpretation and verification

These are descriptive averages across the recorded events, seasons and
disciplines for each athlete, with no date or discipline filter. They do not
measure jump execution quality or establish why scores changed. Compare the
number of runs and event coverage alongside the means.

The script does not remove or detect duplicated source runs: duplicates would
receive extra weight. Multiple legitimate qualification runs intentionally
remain separate. `aus_runs_by_round.csv` keeps event details and original labels
so the observations contributing to each mean can be inspected.

For the dataset checked when this analysis was added:

- 339 input rows became 334 run rows after excluding five overall summaries.
- Those runs produced 41 athlete/round groups.
- Each group mean was checked against its source observations.
- Separate qualification attempts, missing difficulty values and empty inputs
  were checked with small in-memory examples.

These counts are a historical verification snapshot, not hard-coded limits.
After a data refresh, check that the sum of run_count equals the number of
organised run rows and inspect each changed round label or identity error.

When extending the analysis, update ROUND_LABELS only after confirming a new
label's meaning. To add another average, update the aggregation, exported column
list and documentation together. Keep original_round to preserve traceability.
