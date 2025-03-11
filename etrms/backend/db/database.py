import os
from pymongo import MongoClient
from pymongo.database import Database

# MongoDB connection settings
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.environ.get("MONGO_DB", "etrms")

# MongoDB client instance
_client = None

def get_client() -> MongoClient:
    """Get the MongoDB client instance"""
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
    return _client

def get_db() -> Database:
    """Get the MongoDB database instance"""
    client = get_client()
    return client[MONGO_DB]

def close_client():
    """Close the MongoDB client connection"""
    global _client
    if _client is not None:
        _client.close()
        _client = None 