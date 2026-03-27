from pydantic import BaseModel
from typing import Optional


class FrameResult(BaseModel):
    qdrant_id:          str
    video_name:         str
    frame_filename:     str
    frame_order:        int
    pts_time:           float
    fps:                float
    global_frame_index: int
    frame_webp_path:    str
    score:              Optional[float] = None


class SearchResponse(BaseModel):
    query:            str
    translated_query: str
    results:          list[FrameResult]
    total:            int


class TrakeFrameResult(BaseModel):
    query:              str    # query gốc tương ứng với sự kiện này
    global_frame_index: int
    frame_webp_path:    str


class TrakeVideoResult(BaseModel):
    video_name:   str
    dante_score:  float
    event_frames: list[TrakeFrameResult]  # len == len(queries)


class TrakeSearchResponse(BaseModel):
    queries:             list[str]
    translated_queries:  list[str]
    results:             list[TrakeVideoResult]
    total:               int


# --- LLM ---

class LLMSearchResponse(BaseModel):
    original_query:   str
    translated_query: str
    chunks:           list[str]   # LLM tách ra từ query
    results:          list[FrameResult]
    total:            int