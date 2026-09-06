import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("MONGODB_URI")

print("URI loaded:", uri is not None)

client = MongoClient(uri)

client.admin.command("ping")
print("Connected to MongoDB!")
print("Databases:", client.list_database_names())

db = client["Interview"]
collection = db["MogulsData"]

expected_count = collection.count_documents({})
data = list(collection.find())
print(f"Collection documents: {expected_count}; exported documents: {len(data)}")
if len(data) != expected_count:
    raise RuntimeError("Collection count changed during export; rerun to verify completeness.")

import pandas as pd

df = pd.DataFrame(data)
df.to_csv("mongodb_data.csv", index=False)

print(df.head())
print("Saved mongodb_data.csv")
