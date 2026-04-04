import os
import pymongo
from pymongo import MongoClient, errors as mongo_errors
from src.utils.logger import log
from dotenv import load_dotenv
from typing import Optional
import ssl  

load_dotenv()

MONGO_URI = os.environ["MONGO_URI"]
MONGO_DB  = os.environ["MONGO_DB"]

_client: Optional[MongoClient] = None
_db: Optional[pymongo.database.Database] = None


def get_db() -> pymongo.database.Database:
    global _client, _db
    if _db is not None:
        log.info("Reusing existing MongoDB connection")
        return _db
    try:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        _client = MongoClient(
            MONGO_URI,
            tls=True,
            tlsAllowInvalidCertificates=True,
            ssl_context=ssl_context,
            serverSelectionTimeoutMS=5000,
        )
        _client.admin.command("ping")
        _db = _client[MONGO_DB]
        log.info(f"Connected to MongoDB, database: {MONGO_DB}")
        return _db
    except mongo_errors.ServerSelectionTimeoutError as e:
        log.error(f"MongoDB connection timeout: {e}")
        raise
    except Exception as e:
        log.error(f"Failed to connect to MongoDB: {e}")
        raise


def search_mongo(
    db: pymongo.database.Database,
    collection_name: str,
    qdrant_id: str,
) -> Optional[dict]:
    """
    Tìm document theo qdrant_id trong collection chỉ định.
    Loại bỏ trường _id (ObjectId) trước khi trả về.
    """
    try:
        doc = db[collection_name].find_one(
            {"qdrant_id": qdrant_id},
            {"_id": 0},  
        )
        if doc:
            return doc
        log.warning(f"No MongoDB doc found for qdrant_id: {qdrant_id}")
        return None
    except mongo_errors.PyMongoError as e:
        log.error(f"MongoDB query error for qdrant_id {qdrant_id}: {e}")
        return None


def batch_search_mongo(
    db: pymongo.database.Database,
    collection_name: str,
    qdrant_ids: list[str],
) -> dict[str, dict]:
    """
    Tìm nhiều documents cùng lúc bằng $in query thay vì N lần find_one.
    Trả về dict {qdrant_id: doc} để lookup O(1).
    """
    try:
        cursor = db[collection_name].find(
            {"qdrant_id": {"$in": qdrant_ids}},
            {"_id": 0},
        )
        result = {doc["qdrant_id"]: doc for doc in cursor}
        missing = set(qdrant_ids) - set(result.keys())
        if missing:
            log.warning(f"Missing {len(missing)} docs in MongoDB: {missing}")
        return result
    except mongo_errors.PyMongoError as e:
        log.error(f"MongoDB batch query error: {e}")
        return {}
