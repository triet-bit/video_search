import os
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import Optional

load_dotenv()
GEMINI_API_KEY = os.environ["GOOGLE_API_KEY"]

SYSTEM_PROMPT = """Bạn là hệ thống phân tích truy vấn tìm kiếm video.
Nhiệm vụ: tách một query mô tả cảnh video thành các visual chunk ngắn gọn,
mỗi chunk mô tả một khía cạnh visual độc lập có thể tìm kiếm riêng.

Quy tắc:
1. Mỗi chunk tối đa 15 từ tiếng Anh (để SigLIP encode hiệu quả)
2. Dịch sang tiếng Anh, giữ nguyên visual detail quan trọng
3. Ưu tiên: subject/action > clothing/appearance > background/environment
4. Tối đa 4 chunks, tối thiểu 2 chunks
5. KHÔNG thêm thông tin không có trong query gốc

Trả về JSON duy nhất, không có markdown, không có giải thích:
{
  "chunks": [
    {"text": "...", "chunk_type": "subject|action|background|attribute", "priority": 1},
    {"text": "...", "chunk_type": "...", "priority": 2}
  ]
}"""

USER_PROMPT_TEMPLATE = """Query cần tách:
\"\"\"{query}\"\"\"

Hãy trả về JSON theo đúng format yêu cầu."""

MODEL_NAME = "gemini-2.5-flash"


class VisualChunk(BaseModel):
    text:       str
    chunk_type: str = Field(default="subject")
    priority:   int = Field(default=1)


class ChunkResponse(BaseModel):
    chunks: list[VisualChunk]


# Bug fix: syntax sai _shared_client = Optional[...] = None
_shared_client: Optional[genai.Client] = None


def get_llm_client() -> genai.Client:
    global _shared_client
    if _shared_client is None:
        _shared_client = genai.Client(api_key=GEMINI_API_KEY)
    return _shared_client


class PromptSplitter:
    async def _call_llm(self, query: str) -> list[VisualChunk]:
        response = await get_llm_client().aio.models.generate_content(
            model=MODEL_NAME,
            contents=USER_PROMPT_TEMPLATE.format(query=query),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.1,
                response_mime_type="application/json",
                response_schema=ChunkResponse,
            ),
        )
        return response.parsed.chunks

    async def split(self, query: str) -> list[VisualChunk]:
        try:
            chunks = await self._call_llm(query)
            if chunks:
                return sorted(chunks, key=lambda x: x.priority)
        except Exception as e:
            print(f"[PromptSplitter] LLM error: {e}, dùng fallback")
        return self._fallback_split(query)

    def _fallback_split(self, query: str) -> list[VisualChunk]:
        raw = [c.strip() for c in re.split(r"[.,;\n]+", query) if c.strip()]
        if not raw:
            raw = [query.strip()]
        return [
            VisualChunk(text=chunk, chunk_type="subject", priority=i + 1)
            for i, chunk in enumerate(raw)
        ]