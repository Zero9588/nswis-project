"""MongoDB connection and data retrieval."""

import os

from dotenv import load_dotenv
from pymongo import MongoClient


def get_database_data(database_name="Interview", collection_name="MogulsData"):
    """Return all collection documents as a list using MONGODB_URI from .env.

    Raise ValueError if the URI is missing, or RuntimeError if the document
    count changes during retrieval. MongoDB connection errors propagate.
    """
    load_dotenv()
    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise ValueError("Set MONGODB_URI in your .env file before fetching data.")

    with MongoClient(uri) as client:
        collection = client[database_name][collection_name]
        expected_count = collection.count_documents({})
        data = list(collection.find())
        if len(data) != expected_count:
            raise RuntimeError(
                "Collection count changed during export; rerun to verify completeness."
            )

    return data
