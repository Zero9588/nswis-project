"""Flatten MongoDB records into analysis-ready tables."""

import pandas as pd


def flatten_moguls_data(data):
    """Return one row per document with selected event, athlete and run fields.

    Jump columns use jump_number (1 or 2), regardless of list order.
    Missing values are preserved for export as blank cells. Invalid dates or
    numeric values raise ValueError rather than silently discarding data.
    """
    columns = {
        "event.event": "event",
        "event.event_date": "event_date",
        "event.venue": "venue",
        "event.discipline": "discipline",
        "event.level": "round",
        "athlete.name": "athlete",
        "athlete.fis_code": "fis_code",
        "athlete.nsa_code": "country",
        "athlete.rank": "rank",
        "run.run_score": "run_score",
        "run.time_points": "time_points",
        "run.turns.total": "turns_total",
        "run.air.total": "air_total",
    }
    normalized = pd.json_normalize(data)
    flattened = normalized.reindex(columns=columns).rename(columns=columns)
    flattened["fis_code"] = flattened["fis_code"].astype("string")
    jump_fields = {
        "jump_number": "jump_number",
        "type": "type",
        "degree_diff": "degree_diff",
        "judge_scores.6": "judge_6_score",
        "judge_scores.7": "judge_7_score",
    }
    jump_columns = [
        f"jump_{number}_{name}"
        for number in (1, 2)
        for name in jump_fields.values()
    ]
    jump_rows = []
    for jumps in normalized.get("run.air.jumps", pd.Series(index=normalized.index, dtype=object)):
        row = {}
        if isinstance(jumps, list):
            seen = set()
            for jump in jumps:
                number = jump.get("jump_number")
                if number not in (1, 2) or number in seen:
                    raise ValueError(f"Expected unique jump numbers 1 or 2; got {number!r}")
                seen.add(number)
                values = pd.json_normalize(jump).iloc[0]
                for source, name in jump_fields.items():
                    row[f"jump_{number}_{name}"] = values.get(source, pd.NA)
        elif jumps is not None and not pd.isna(jumps):
            raise ValueError("Expected run.air.jumps to be a list or missing")
        jump_rows.append(row)
    flattened = pd.concat(
        [flattened, pd.DataFrame(jump_rows, columns=jump_columns, index=normalized.index)],
        axis=1,
    )
    flattened["event_date"] = pd.to_datetime(
        flattened["event_date"], format="%d %b %Y", errors="raise"
    ).dt.strftime("%Y-%m-%d")
    numeric_columns = ["rank", "run_score", "time_points", "turns_total", "air_total"]
    numeric_columns += [column for column in jump_columns if not column.endswith("_type")]
    for column in numeric_columns:
        flattened[column] = pd.to_numeric(flattened[column], errors="raise")
    for column in ["rank", "jump_1_jump_number", "jump_2_jump_number"]:
        flattened[column] = flattened[column].astype("Int64")
    return flattened
