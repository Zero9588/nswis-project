"""Compare ten podium-finisher metrics across rounds without querying MongoDB.

Run: .venv/Scripts/python.exe score_analysis.py
Reads outputs/podium_runs.csv and writes outputs/podium_scores_by_round.csv.
Each output row represents one athlete, event and metric. No charts are created.
See SCORE_ANALYSIS.md for column definitions and validation rules.
"""

from pathlib import Path

import pandas as pd


EVENT_COLUMNS = ["event", "event_date", "venue", "discipline"]
ATHLETE_KEY = EVENT_COLUMNS + ["fis_code"]
ROUND_LABELS = {
    "Results Qualification": "Qualification",
    "QUALIFICATION RUN 1 RESULTS Qualification": "Qualification",
    "Results Qualification 1": "Qualification",
    "Results Qualification 2": "Qualification",
    "Results Final 1": "Final 1",
    "QUALIFICATION RUN 1 RESULTS Final 1": "Final 1",
    "Results Final 2": "Deciding Final",
    "QUALIFICATION RUN 1 RESULTS Final 2": "Deciding Final",
    "Results Final": "Deciding Final",
}
ROUND_ORDER = ["Qualification", "Final 1", "Deciding Final"]
METRICS = [
    "run_score",
    "air_total",
    "turns_total",
    "time_points",
    "jump_1_degree_diff",
    "jump_2_degree_diff",
    "jump_1_judge_6_score",
    "jump_1_judge_7_score",
    "jump_2_judge_6_score",
    "jump_2_judge_7_score",
]
OUTPUT_COLUMNS = EVENT_COLUMNS + ["athlete", "fis_code", "podium_rank", "metric"] + ROUND_ORDER


def compare_scores_by_round(data):
    """Reshape flattened podium runs into ten metric rows per athlete/event.

    Input is the DataFrame exported by get_podium_runs(). Identity uses event,
    event_date, venue, discipline and fis_code; names are display labels only.
    Round aliases are combined before melting metrics. More than one run in
    a combined round raises ValueError, even if its metric values are missing.
    This ensures every metric refers to the same actual run.

    The input is not modified. All ten metric rows are retained, including
    entirely missing metrics. Missing values export as blank CSV cells.
    """
    required = ATHLETE_KEY + ["athlete", "podium_rank", "round"] + METRICS
    missing = [column for column in required if column not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    runs = data[required].copy()
    if runs.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    if runs[ATHLETE_KEY + ["round"]].isna().any().any():
        raise ValueError("Event identifiers, FIS code and round must not be missing.")
    runs["fis_code"] = runs["fis_code"].astype("string")
    unknown = runs.loc[~runs["round"].isin(ROUND_LABELS), "round"].unique()
    if len(unknown):
        raise ValueError(f"Unrecognised rounds: {unknown.tolist()}")

    # Validate original run records, not individual non-null metric cells.
    runs["round"] = runs["round"].map(ROUND_LABELS)
    duplicate = runs.duplicated(ATHLETE_KEY + ["round"], keep=False)
    if duplicate.any():
        details = runs.loc[duplicate, ATHLETE_KEY + ["round"]].drop_duplicates()
        raise ValueError(
            "Multiple runs map to the same athlete/event/round; retain separate "
            f"rounds and review before combining: {details.to_dict('records')}"
        )
    for column in METRICS + ["podium_rank"]:
        runs[column] = pd.to_numeric(runs[column], errors="raise")
    if not runs["podium_rank"].isin([1, 2, 3]).all():
        raise ValueError("Every run must have a podium_rank of 1, 2 or 3.")
    runs["podium_rank"] = runs["podium_rank"].astype("Int64")
    labels = runs[ATHLETE_KEY + ["athlete", "podium_rank"]].drop_duplicates()
    if labels.duplicated(ATHLETE_KEY).any():
        raise ValueError("Athlete name or podium_rank differs between runs for the same athlete/event.")

    # Melt ten columns to metric/value rows, then pivot only the round axis.
    values = runs.melt(
        id_vars=ATHLETE_KEY + ["round"],
        value_vars=METRICS,
        var_name="metric",
        value_name="value",
    )
    scores = values.pivot(index=ATHLETE_KEY + ["metric"], columns="round", values="value")
    scores = scores.reindex(columns=ROUND_ORDER).reset_index()
    scores.columns.name = None
    result = scores.merge(labels, on=ATHLETE_KEY, validate="many_to_one")
    result["metric"] = pd.Categorical(result["metric"], categories=METRICS, ordered=True)
    result = result[OUTPUT_COLUMNS].sort_values(
        EVENT_COLUMNS + ["podium_rank", "fis_code", "metric"]
    ).reset_index(drop=True)
    result["metric"] = result["metric"].astype("string")
    return result


def main():
    output_dir = Path(__file__).resolve().parent / "outputs"
    source = output_dir / "podium_runs.csv"
    if not source.exists():
        raise FileNotFoundError(f"Run main.py first to create {source}")
    runs = pd.read_csv(source, dtype={"fis_code": "string"})
    comparison = compare_scores_by_round(runs)
    destination = output_dir / "podium_scores_by_round.csv"
    comparison.to_csv(destination, index=False)
    print(f"Saved {len(comparison)} athlete/event/metric comparisons to {destination}")


if __name__ == "__main__":
    main()
