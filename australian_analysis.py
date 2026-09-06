"""Organise Australian runs and average jump difficulty by athlete and round.

Run `python australian_analysis.py` after main.py has exported aus_runs.csv.
Reads outputs/aus_runs.csv without modifying it or querying MongoDB.
Writes aus_runs_by_round.csv and aus_jump_difficulty_by_round.csv in outputs/.
See AUSTRALIAN_ANALYSIS.md for round mapping and averaging rules.
"""

from pathlib import Path

import pandas as pd


ROUND_ORDER = ["Qualification", "Final 1", "Deciding Final"]
ROUND_LABELS = {
    "Results Qualification": "Qualification",
    "Results Qualification 1": "Qualification",
    "Results Qualification 2": "Qualification",
    "QUALIFICATION RUN 1 RESULTS Qualification": "Qualification",
    "Results Final 1": "Final 1",
    "QUALIFICATION RUN 1 RESULTS Final 1": "Final 1",
    "Results Final 2": "Deciding Final",
    "QUALIFICATION RUN 1 RESULTS Final 2": "Deciding Final",
    "Results Final": "Deciding Final",
}
SUMMARY_ROUNDS = ["Results Overall", "OVERALL RESULTS - - Partial"]


def organise_athlete_runs(data):
    """Standardise round labels and sort individual runs without aggregating.

    Only overall summaries are excluded. Multiple qualification runs remain
    separate, and original_round preserves their source labels. Unknown labels
    and missing athlete identifiers raise ValueError for review.

    Args:
        data (pd.DataFrame): Raw AUS runs from aus_runs.csv, including athlete,
            fis_code, country, round and the four event identifiers. Dates
            should already use YYYY-MM-DD for chronological string sorting.

    Returns:
        pd.DataFrame: A new table with all source columns plus original_round.
            round contains the three standard labels. Input is not modified.
            An empty input with the required columns produces an empty table.

    Raises:
        ValueError: Required columns are absent, country is not AUS, a round
            is unknown, or a retained run has a missing athlete name/FIS code.

    Call this on raw labels, not on its own standardised output. Records are
    not deduplicated; repeated source rows would remain repeated observations.
    """
    required = ["athlete", "fis_code", "country", "round", "event_date", "event", "venue", "discipline"]
    missing = [column for column in required if column not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    if not data["country"].eq("AUS").fillna(False).all():
        raise ValueError("Expected only AUS records in aus_runs.csv.")
    recognised = data["round"].isin(list(ROUND_LABELS) + SUMMARY_ROUNDS)
    if not recognised.all():
        raise ValueError(f"Unrecognised rounds: {data.loc[~recognised, 'round'].unique().tolist()}")
    runs = data.loc[~data["round"].isin(SUMMARY_ROUNDS)].copy()
    if runs[["fis_code", "athlete"]].isna().any().any():
        raise ValueError("Athlete names and FIS codes must not be missing.")
    runs["fis_code"] = runs["fis_code"].astype("string")
    # Keep source labels so separate qualification attempts remain auditable.
    runs["original_round"] = runs["round"]
    runs["round"] = pd.Categorical(
        runs["round"].map(ROUND_LABELS), categories=ROUND_ORDER, ordered=True
    )
    runs = runs.sort_values(
        ["athlete", "fis_code", "round", "event_date", "event", "venue", "discipline", "original_round"]
    ).reset_index(drop=True)
    runs["round"] = runs["round"].astype("string")
    return runs


def average_jump_difficulty(runs):
    """Return one row per FIS code/standardised round, averaged across events.

    Each recorded run has equal weight. Missing difficulty values are excluded
    from that jump's mean; run_count counts all rows in the group. No missing
    values are replaced with zero. Names are labels, not grouping identifiers.

    Args:
        runs (pd.DataFrame): Output from organise_athlete_runs(), also containing
            jump_1_degree_diff and jump_2_degree_diff. Numeric strings are accepted.

    Returns:
        pd.DataFrame: athlete, fis_code, round, run_count and the two
            jump_N_degree_diff_mean columns, sorted by athlete and round order.
            Only observed groups are included; an all-missing mean is NaN.

    Raises:
        ValueError: A round is not standardised, one FIS code has conflicting
            names, or a difficulty value cannot be converted to a number.
        KeyError: A required input column is absent.

    Events and disciplines are pooled within each FIS code/round group. The
    function does not modify its input or check for duplicated source runs.
    """
    data = runs.copy()
    if not data["round"].isin(ROUND_ORDER).all():
        raise ValueError("Call organise_athlete_runs() before averaging difficulty.")
    names = data[["fis_code", "athlete"]].drop_duplicates()
    if names.duplicated("fis_code").any():
        raise ValueError("Multiple names found for the same FIS code; review athlete labels.")
    for column in ["jump_1_degree_diff", "jump_2_degree_diff"]:
        data[column] = pd.to_numeric(data[column], errors="raise")
    averages = data.groupby(["fis_code", "round"], observed=True).agg(
        # size counts all runs; mean independently skips each jump's missing values.
        run_count=("round", "size"),
        jump_1_degree_diff_mean=("jump_1_degree_diff", "mean"),
        jump_2_degree_diff_mean=("jump_2_degree_diff", "mean"),
    ).reset_index().merge(names, on="fis_code", validate="many_to_one")
    averages["round"] = pd.Categorical(averages["round"], categories=ROUND_ORDER, ordered=True)
    averages = averages.sort_values(["athlete", "fis_code", "round"]).reset_index(drop=True)
    averages["round"] = averages["round"].astype("string")
    return averages[["athlete", "fis_code", "round", "run_count",
                     "jump_1_degree_diff_mean", "jump_2_degree_diff_mean"]]


def main():
    """Read saved AUS runs and replace the two derived CSV exports.

    Both transformations finish before writing begins. Files are written
    sequentially, so an I/O error can leave only the first export refreshed.
    Missing source files and write errors propagate to the caller. No source
    data is changed, and no MongoDB connection or plotting is performed.
    """
    output_dir = Path(__file__).resolve().parent / "outputs"
    source = output_dir / "aus_runs.csv"
    if not source.exists():
        raise FileNotFoundError(f"Run main.py first to create {source}")
    data = pd.read_csv(source, dtype={"fis_code": "string"})
    runs = organise_athlete_runs(data)
    averages = average_jump_difficulty(runs)
    runs.to_csv(output_dir / "aus_runs_by_round.csv", index=False)
    averages.to_csv(output_dir / "aus_jump_difficulty_by_round.csv", index=False)
    print(f"Saved {len(runs)} runs; excluded {len(data) - len(runs)} overall summary rows.")
    print(f"Saved {len(averages)} athlete/round averages to {output_dir / 'aus_jump_difficulty_by_round.csv'}")


if __name__ == "__main__":
    main()
