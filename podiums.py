"""Select podium finishers and their qualification and final runs."""


def get_event_podiums(data):
    """Filter flattened runs to ranks 1–3 in Results Final 2 or Results Final."""
    return data.loc[
        data["rank"].isin([1, 2, 3])
        & data["round"].isin(["Results Final 2", "Results Final"])
    ].sort_values(["event", "event_date", "venue", "discipline", "rank"]).reset_index(drop=True)


def get_podium_runs(data):
    """Return podium finishers' qualification and final runs with podium_rank.

    Match each run to one podium result by event, date, venue, discipline and
    FIS code. Keep rank as the placing in that run's round.
    """
    keys = ["event", "event_date", "venue", "discipline", "fis_code"]
    lookup = get_event_podiums(data)[keys + ["rank"]].rename(
        columns={"rank": "podium_rank"}
    )
    if lookup[keys].isna().any().any():
        raise ValueError("Podium results must have all five identifying fields.")
    if lookup.duplicated(keys).any():
        raise ValueError("Multiple podium results found for the same athlete and event.")

    rounds = [
        "Results Qualification",
        "Results Qualification 1",
        "Results Qualification 2",
        "QUALIFICATION RUN 1 RESULTS Qualification",
        "Results Final 1",
        "QUALIFICATION RUN 1 RESULTS Final 1",
        "Results Final 2",
        "QUALIFICATION RUN 1 RESULTS Final 2",
        "Results Final",
    ]
    runs = data.loc[data["round"].isin(rounds)].merge(
        lookup, on=keys, how="inner", validate="many_to_one"
    )
    return runs.sort_values(
        ["event", "event_date", "venue", "discipline", "podium_rank", "round"]
    ).reset_index(drop=True)
