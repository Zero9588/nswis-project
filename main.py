from database import get_database_data
from transformations import flatten_moguls_data
from podiums import get_event_podiums, get_podium_runs

data = get_database_data()
print(f"Retrieved {len(data)} documents from MongoDB")

flat_df = flatten_moguls_data(data)
flat_df.to_csv("moguls_flat.csv", index=False)
print(flat_df.head())
print("Saved moguls_flat.csv")

podiums = get_event_podiums(flat_df)
podiums.to_csv("event_podiums.csv", index=False)
print(f"Saved {len(podiums)} podium finishers to event_podiums.csv")

podium_runs = get_podium_runs(flat_df)
podium_runs.to_csv("podium_runs.csv", index=False)
print(f"Saved {len(podium_runs)} podium finishers' runs to podium_runs.csv")
