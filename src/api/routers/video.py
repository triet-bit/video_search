from fastapi import APIRouter, Depends, HTTPException
from src.api.dependencies import get_mongo_db

router = APIRouter()

@router.get("/{video_name}")
def get_video(video_name: str, mongo = Depends(get_mongo_db)):
    frames = list(mongo.embeddings.find(
        {"video_name": video_name},
        {"_id": 0}
    ).sort("frame_order", 1))
    if not frames:
        raise HTTPException(status_code=404, detail="Video not found")
    return {"video_name": video_name, "total_frames": len(frames), "frames": frames}
