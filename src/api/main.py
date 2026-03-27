import os
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.db.qdrant_client import get_qdrant_client
from src.db.mongo_client import get_db
from src.models.embedding_model import SiglipEncoder
from src.models.reranking_model import BLIP2Reranker
from src.models.llm_model import PromptSplitter
from src.api.routers import search, frame, video
from src.utils.logger import setup_logging

load_dotenv()
setup_logging()

log = logging.getLogger(__name__)

QDRANT_HOST     = os.getenv("QDRANT_HOST",  "localhost")
QDRANT_PORT     = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_HTTPS    = os.getenv("QDRANT_HTTPS", "false").lower() == "true"
ENABLE_RERANKER = os.getenv("ENABLE_RERANKER", "true").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ──────────────────────────────────────────────────────────
    log.info("Starting up...")

    app.state.qdrant = get_qdrant_client(
        host=QDRANT_HOST,
        port=QDRANT_PORT,
        https=QDRANT_HTTPS,
    )
    app.state.mongo = get_db()

    log.info("Loading SiglipEncoder...")
    app.state.encoder = SiglipEncoder()

    app.state.prompt_splitter = PromptSplitter()

    if ENABLE_RERANKER:
        log.info("Loading BLIP2Reranker...")
        app.state.reranker = BLIP2Reranker()
    else:
        log.info("Reranker disabled (ENABLE_RERANKER=false)")
        app.state.reranker = None

    log.info("Startup complete.")
    yield

    # ── SHUTDOWN ─────────────────────────────────────────────────────────
    log.info("Shutting down...")


def create_app() -> FastAPI:
    app = FastAPI(
        title="HCMAI Video Search API",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Search routes — 3 nhánh
    app.include_router(search.router, prefix="/search", tags=["Search"])

    # Utility routes
    app.include_router(frame.router, prefix="/frame", tags=["Frame"])
    app.include_router(video.router, prefix="/video", tags=["Video"])

    @app.get("/health", tags=["Health"])
    def health():
        return {"status": "ok"}

    return app


app = create_app()