from pydantic import BaseModel, Field
from typing import Optional


class SearchRequest(BaseModel):
    query:      str           = Field(..., description="Text query (tiếng Việt hoặc tiếng Anh)")
    top_k:      int           = Field(10, ge=1, le=100)
    video_name: Optional[str] = Field(None, description="Filter theo video cụ thể")


class TrakeSearchRequest(BaseModel):
    queries:          list[str] = Field(..., min_length=2, description="List sự kiện theo thứ tự thời gian (tối thiểu 2)")
    top_k:            int       = Field(5, ge=1, le=20)
    top_k_candidates: int       = Field(50, ge=10, le=200, description="Số keyframe lọc thô từ Qdrant")
    lambda_penalty:   float     = Field(0.0001, ge=0.0, le=1.0, description="Hệ số phạt khoảng cách DANTE")


class LLMSearchRequest(BaseModel):
    query:      str           = Field(..., description="Query dài/phức tạp — LLM sẽ tách thành chunks")
    top_k:      int           = Field(10, ge=1, le=100)
    video_name: Optional[str] = Field(None)