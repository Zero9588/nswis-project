"""Explore the saved Australian jump difficulty summary with Streamlit."""

from datetime import datetime
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from australian_analysis import ROUND_ORDER

DATA_PATH = Path(__file__).resolve().parent / "outputs" / "aus_jump_difficulty_by_round.csv"
JUMPS = {
    "jump_1_degree_diff_mean": "Jump 1",
    "jump_2_degree_diff_mean": "Jump 2",
}
COLUMNS = ["athlete", "fis_code", "round", "run_count", *JUMPS]


def load_summary(path=DATA_PATH):
    """Read a fresh snapshot and reject ambiguous or invalid summary rows."""
    data = pd.read_csv(path, dtype={"athlete": "string", "fis_code": "string"})
    missing = set(COLUMNS) - set(data.columns)
    if missing:
        raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")
    data = data[COLUMNS].copy()
    for column in ["athlete", "fis_code", "round"]:
        if data[column].isna().any() or data[column].str.strip().eq("").any():
            raise ValueError(f"{column} must not be blank.")
    if not data["round"].isin(ROUND_ORDER).all():
        raise ValueError("The summary contains unrecognised rounds.")
    if data.duplicated(["fis_code", "round"]).any():
        raise ValueError("Expected one row per FIS code and round.")
    if data.groupby("fis_code")["athlete"].nunique().gt(1).any():
        raise ValueError("A FIS code has multiple athlete names.")
    for column in ["run_count", *JUMPS]:
        data[column] = pd.to_numeric(data[column], errors="raise")
        values = data[column].dropna()
        if not np.isfinite(values).all() or values.lt(0).any():
            raise ValueError(f"{column} must contain finite, non-negative values.")
    counts = data["run_count"]
    if counts.isna().any() or counts.lt(1).any() or counts.mod(1).ne(0).any():
        raise ValueError("Run counts must be positive whole numbers.")
    data["run_count"] = counts.astype(int)
    data["round"] = pd.Categorical(data["round"], categories=ROUND_ORDER, ordered=True)
    return data.sort_values(["athlete", "fis_code", "round"]).reset_index(drop=True)


PODIUM = {
    "Men's Moguls": {
        "Jump 1": [0.92, 0.982077922, 1.00775],
        "Jump 2": [0.920625, 1.010779221, 1.029],
    },
    "Women's Moguls": {
        "Jump 1": [0.99171875, 1.007307692, 1.007308],
        "Jump 2": [0.91359375, 0.931025641, 0.937564],
    },
}


def load_disciplines(path=DATA_PATH.parent / "aus_runs.csv"):
    """Use recorded discipline, never infer it from an athlete's name."""
    from australian_analysis import organise_athlete_runs
    runs = organise_athlete_runs(pd.read_csv(path, dtype={"fis_code": "string"}))
    identities = runs[["fis_code", "discipline"]].drop_duplicates()
    if identities["discipline"].isna().any() or not identities["discipline"].isin(PODIUM).all():
        raise ValueError("Source contains a missing or unsupported discipline; review before comparing.")
    if identities.duplicated("fis_code").any():
        raise ValueError("An athlete has multiple disciplines; split their summary by discipline before comparing.")
    return identities.set_index("fis_code")["discipline"].to_dict()


def compare_athlete(data, fis_code, discipline):
    """Keep every round, including absent athlete results, and exact benchmarks."""
    selected = data.loc[data["fis_code"].eq(fis_code)].set_index("round").reindex(ROUND_ORDER)
    rows = []
    for column, jump in JUMPS.items():
        for index, round_name in enumerate(ROUND_ORDER):
            value = selected.loc[round_name, column]
            benchmark = PODIUM[discipline][jump][index]
            rows.append({"round": round_name, "jump": jump, "athlete_mean": value,
                         "podium_mean": benchmark, "gap": value - benchmark,
                         "run_count": selected.loc[round_name, "run_count"]})
    return pd.DataFrame(rows)


def main():
    st.set_page_config(page_title="Athlete vs podium", page_icon="🎿", layout="wide")
    st.title("Jump difficulty · Athlete vs podium")
    st.write("Compare an Australian athlete's average difficulty with the podium average in each round.")
    try:
        data = load_summary()
        disciplines = load_disciplines()
        if not set(data["fis_code"]).issubset(disciplines):
            raise ValueError("Athlete discipline is missing from aus_runs.csv. Refresh the analysis exports.")
        modified = datetime.fromtimestamp(DATA_PATH.stat().st_mtime)
    except (OSError, ValueError, pd.errors.ParserError) as error:
        st.error(f"Could not load the jump difficulty summary: {error}")
        st.info("Run `python australian_analysis.py` to generate the summary from outputs/aus_runs.csv.")
        st.stop()
    if data.empty:
        st.info("The summary has no athlete results yet. Refresh the source data and rerun the analysis.")
        st.stop()

    identities = data[["fis_code", "athlete"]].drop_duplicates()
    labels = dict(zip(identities["fis_code"], identities["athlete"] + " (" + identities["fis_code"] + ")"))
    code = st.selectbox("Select athlete", list(labels), format_func=labels.get)
    discipline = disciplines[code]
    comparison = compare_athlete(data, code, discipline)
    st.caption(f"Podium benchmark: {discipline}")
    st.caption(f"Athlete summary updated {modified:%d %b %Y, %H:%M} (local time). Podium averages supplied by you.")
    st.button("Reload saved CSV")

    st.subheader(labels[code])
    # st.caption("Gap = athlete average − podium average. Positive means higher difficulty; negative means lower difficulty.")
    # for panel, round_name in zip(st.columns(3), ROUND_ORDER):
    #     with panel:
    #         st.markdown(f"### {round_name}")
    #         group = comparison.loc[comparison["round"].eq(round_name)]
    #         count = group["run_count"].iloc[0]
    #         st.caption("No recorded runs" if pd.isna(count) else f"{int(count)} recorded runs")
    #         for row in group.itertuples():
    #             available = pd.notna(row.athlete_mean)
    #             st.metric(row.jump, f"{row.athlete_mean:.3f}" if available else "No data",
    #                       delta=f"{row.gap:+.3f} vs podium" if available else None,
    #                       delta_color="off")
    #             st.caption(f"Podium average: {row.podium_mean:.6f}")

    st.subheader("Round comparison")
    shared_max = float(comparison[["athlete_mean", "podium_mean"]].max().max()) * 1.1
    values = comparison.melt(
        id_vars=["round", "jump"], value_vars=["athlete_mean", "podium_mean"],
        var_name="source", value_name="difficulty")
    values["series"] = values["source"].map({"athlete_mean": "Athlete", "podium_mean": "Podium"}) + " · " + values["jump"]
    series_order = ["Athlete · Jump 1", "Podium · Jump 1", "Athlete · Jump 2", "Podium · Jump 2"]
    chart = alt.Chart(values.dropna(subset=["difficulty"])).mark_bar().encode(
        x=alt.X("round:N", title=None, sort=ROUND_ORDER, axis=alt.Axis(labelAngle=0)),
        xOffset=alt.XOffset("series:N", sort=series_order, scale=alt.Scale(domain=series_order)),
        y=alt.Y("difficulty:Q", title="Mean difficulty (multiplier)", scale=alt.Scale(domain=[0, shared_max])),
        color=alt.Color("series:N", title=None, sort=series_order,
                        scale=alt.Scale(domain=series_order, range=["#167d9a", "#a3ceda", "#b57916", "#efd398"]),
                        legend=alt.Legend(orient="top")),
        tooltip=[alt.Tooltip("round:N", title="Round"), alt.Tooltip("series:N", title="Average"),
                 alt.Tooltip("difficulty:Q", title="Difficulty", format=".6f")],
    ).properties(height=420)
    st.altair_chart(chart, width="stretch")
    st.caption("Missing athlete results are omitted from the charts; podium benchmarks remain visible.")

    st.subheader("Comparison details")
    st.dataframe(comparison, hide_index=True, width="stretch", column_config={
        "round": "Round", "jump": "Jump",
        "athlete_mean": st.column_config.NumberColumn("Athlete average", format="%.6f"),
        "podium_mean": st.column_config.NumberColumn("Podium average", format="%.6f"),
        "gap": st.column_config.NumberColumn("Gap to podium", format="%+.6f"),
        "run_count": st.column_config.NumberColumn("Recorded runs", format="%d"),
    })
    export = comparison.assign(discipline=discipline, athlete=data.loc[data.fis_code.eq(code), "athlete"].iloc[0], fis_code=code)
    st.download_button("Download athlete comparison", export.to_csv(index=False).encode("utf-8"),
                       file_name=f"athlete_{code}_vs_podium.csv", mime="text/csv")
    with st.expander("About these averages"):
        st.markdown(
            "- Podium benchmarks are the supplied averages for the selected athlete's recorded discipline; they do not refresh with the athlete CSV.\n"
            "- Athlete means pool recorded events and seasons within their recorded discipline. The benchmark's event coverage is not specified, so this is not a matched-event comparison.\n"
            "- Difficulty values are multipliers, not execution scores; higher difficulty alone does not establish better performance.\n"
            "- Run counts include missing difficulty; each jump's mean may use fewer observations. Missing means are not zero.\n"
            "- Qualification attempts remain separate observations."
        )


if __name__ == "__main__":
    main()
