"""Select podium finishers and their qualification and final runs."""


def get_athlete_standings(data):
    """Count final wins and podiums per discipline/FIS code, best first.

    Final 2 is the deciding round when present; otherwise use Results Final.
    Include the alternate NorAm Final 2 label, but never Final 1 placings.
    Count an athlete at most once per event, rejecting conflicting ranks.
    """
    podiums = get_event_podiums(data).sort_values("event_date").copy()
    podiums["final_win"] = podiums["rank"].eq(1).astype(int)
    standings = podiums.groupby(["discipline", "fis_code"], as_index=False).agg(
        athlete=("athlete", "last"),
        country=("country", "last"),
        final_wins=("final_win", "sum"),
        podium_finishes=("rank", "size"),
    )
    return standings.sort_values(
        ["discipline", "final_wins", "podium_finishes", "athlete", "fis_code"],
        ascending=[True, False, False, True, True],
    ).reset_index(drop=True)


def get_event_podiums(data):
    """Return one podium result per athlete/event from the deciding final.

    Prefer Final 2 (including the NorAm alias) over Results Final when both
    exist. Exclude Final 1, collapse duplicate results and reject conflicts.
    """
    event_keys = ["event", "event_date", "venue", "discipline"]
    keys = event_keys + ["fis_code"]
    finals = data.loc[data["round"].isin([
        "Results Final 2", "QUALIFICATION RUN 1 RESULTS Final 2", "Results Final"
    ])].copy()
    has_final_2 = finals["round"].str.endswith("Final 2").groupby(
        [finals[key] for key in event_keys], dropna=False
    ).transform("any")
    finals = finals.loc[~has_final_2 | finals["round"].str.endswith("Final 2")]
    podiums = finals.loc[finals["rank"].isin([1, 2, 3])].copy()
    if podiums[keys].isna().any().any():
        raise ValueError("Final podium results must have event identifiers and FIS codes.")
    if (podiums.groupby(keys)["rank"].nunique() > 1).any():
        raise ValueError("Conflicting final podium ranks for the same athlete and event.")
    podiums = podiums.sort_values("event_date").drop_duplicates(keys)
    return podiums.sort_values(
        ["event", "event_date", "venue", "discipline", "rank"]
    ).reset_index(drop=True)



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
