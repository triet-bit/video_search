"""
FastAPI dependency injection.
Các hàm này được gọi bởi Depends() trong router,
lấy client từ app.state thay vì tạo mới mỗi request.
"""
from fastapi import Request
from src.db.qdrant_client import QdrantClient
import pymongo


def get_qdrant_client(request: Request) -> QdrantClient:
    return request.app.state.qdrant


def get_mongo_db(request: Request) -> pymongo.database.Database:
    return request.app.state.mongo