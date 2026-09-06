from pathlib import Path

from database import get_database_data
from transformations import flatten_moguls_data
from podiums import get_event_podiums, get_podium_runs

OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

data = get_database_data()
print(f"Retrieved {len(data)} documents from MongoDB")

flat_df = flatten_moguls_data(data)
flat_df.to_csv(OUTPUT_DIR / "moguls_flat.csv", index=False)
print(flat_df.head())
print("Saved outputs/moguls_flat.csv")

aus_runs = flat_df.loc[flat_df["country"].eq("AUS")].copy()
aus_runs = aus_runs.sort_values(
    ["athlete", "fis_code", "round", "event_date", "event", "venue", "discipline"]
).reset_index(drop=True)
aus_runs.to_csv(OUTPUT_DIR / "aus_runs.csv", index=False)
print(f"Saved {len(aus_runs)} Australian athletes' runs to outputs/aus_runs.csv")

podiums = get_event_podiums(flat_df)
podiums.to_csv(OUTPUT_DIR / "event_podiums.csv", index=False)
print(f"Saved {len(podiums)} podium finishers to outputs/event_podiums.csv")

podium_runs = get_podium_runs(flat_df)
podium_runs.to_csv(OUTPUT_DIR / "podium_runs.csv", index=False)
print(f"Saved {len(podium_runs)} podium finishers' runs to outputs/podium_runs.csv")
