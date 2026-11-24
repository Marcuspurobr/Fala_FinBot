"""Conexão com o MongoDB. Um único cliente é criado e reaproveitado."""
from functools import lru_cache

from pymongo import MongoClient
from pymongo.database import Database

from .config import require_mongo_uri


@lru_cache(maxsize=1)
def get_client() -> MongoClient:
    return MongoClient(require_mongo_uri())


def get_db() -> Database:
    # O banco é o que está na connection string
    return get_client().get_default_database()
