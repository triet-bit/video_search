from fastapi import APIRouter, Depends, HTTPException
from src.api.dependencies import get_mongo_db

router = APIRouter()

@router.get("/{qdrant_id}")
def get_frame(qdrant_id: str, mongo = Depends(get_mongo_db)):
    frame = mongo.embeddings.find_one({"qdrant_id": qdrant_id}, {"_id": 0})
    if not frame:
        raise HTTPException(status_code=404, detail="Frame not found")
    return frame
