import logging
import numpy as np
from fastapi import APIRouter, Depends, Request

from src.api.schemas.request import SearchRequest, TrakeSearchRequest, LLMSearchRequest
from src.api.schemas.response import (
    SearchResponse, FrameResult,
    TrakeSearchResponse, TrakeVideoResult, TrakeFrameResult,
    LLMSearchResponse,
)
from src.api.dependencies import get_qdrant_client, get_mongo_db
from src.db.qdrant_client import search_qdrant, batch_search_qdrant, merge_and_dedup, scroll_video_frames
from src.db.mongo_client import batch_search_mongo
from src.search.track_search import run_dante_dp
from src.models.translator import translate_to_english, translate_many

log = logging.getLogger(__name__)

COLLECTION_NAME  = "HCMAI-SIGLIP"
MONGO_COLLECTION = "embeddings"

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_frame_results(hits: list, mongo_docs: dict) -> list[FrameResult]:
    results = []
    for hit in hits:
        payload   = hit.payload or {}
        qdrant_id = payload.get("qdrant_id", str(hit.id))
        doc = mongo_docs.get(qdrant_id)
        if not doc:
            log.warning(f"Skipping qdrant_id={qdrant_id}: not found in MongoDB")
            continue
        results.append(FrameResult(
            qdrant_id          = qdrant_id,
            video_name         = doc.get("video_name", payload.get("video_name", "")),
            frame_filename     = doc.get("frame_filename", ""),
            frame_order        = doc["frame_order"],
            pts_time           = doc["pts_time"],
            fps                = doc["fps"],
            global_frame_index = doc["global_frame_index"],
            frame_webp_path    = doc["frame_webp_path"],
            score              = hit.score,
        ))
    return results


def _rerank(reranker, query: str, hits: list, mongo_docs: dict, top_k: int) -> list:
    valid = [h for h in hits if mongo_docs.get(h.payload.get("qdrant_id", str(h.id)))]
    paths = [mongo_docs[h.payload.get("qdrant_id", str(h.id))]["frame_webp_path"] for h in valid]
    try:
        indices = reranker.batch_rerank(query=query, image_paths=paths, top_k=top_k)
        return [valid[i] for i in indices]
    except Exception as e:
        log.error(f"Rerank failed, fallback to vector order: {e}")
        return valid[:top_k]


# ===========================================================================
# NHÁNH 1 — POST /search/vector
# ===========================================================================

@router.post("/vector", response_model=SearchResponse)
async def vector_search(
    request: Request,
    body: SearchRequest,
    qdrant = Depends(get_qdrant_client),
    mongo  = Depends(get_mongo_db),
):
    encoder  = request.app.state.encoder
    reranker = request.app.state.reranker

    translated = await translate_to_english(body.query)
    log.info(f"[vector] '{body.query}' → '{translated}'")

    query_vector = encoder.encode_text(translated).tolist()

    hits = search_qdrant(
        client=qdrant, collection_name=COLLECTION_NAME,
        query_vector=query_vector, top_k=body.top_k * 3,
        video_name=body.video_name,
    )
    if not hits:
        return SearchResponse(query=body.query, translated_query=translated, results=[], total=0)

    qdrant_ids = [h.payload.get("qdrant_id", str(h.id)) for h in hits]
    mongo_docs = batch_search_mongo(mongo, MONGO_COLLECTION, qdrant_ids)

    final = _rerank(reranker, translated, hits, mongo_docs, body.top_k) if reranker else hits[:body.top_k]
    results = _build_frame_results(final, mongo_docs)
    return SearchResponse(query=body.query, translated_query=translated, results=results, total=len(results))


# ===========================================================================
# NHÁNH 2 — POST /search/trake
# ===========================================================================

@router.post("/trake", response_model=TrakeSearchResponse)
async def trake_search(
    request: Request,
    body: TrakeSearchRequest,
    qdrant = Depends(get_qdrant_client),
):
    encoder = request.app.state.encoder

    translated_queries = await translate_many(body.queries)
    log.info(f"[trake] {body.queries} → {translated_queries}")

    query_vectors = [encoder.encode_text(q) for q in translated_queries]
    Q = np.array(query_vectors, dtype=np.float32)

    candidate_hits = search_qdrant(
        client=qdrant, collection_name=COLLECTION_NAME,
        query_vector=query_vectors[0].tolist(), top_k=body.top_k_candidates,
    )
    candidate_videos = list(
        {h.payload["video_name"] for h in candidate_hits if "video_name" in h.payload}
    )
    log.info(f"[trake] {len(candidate_videos)} candidate videos")

    if not candidate_videos:
        return TrakeSearchResponse(
            queries=body.queries, translated_queries=translated_queries, results=[], total=0
        )

    dante_results = []
    for video_name in candidate_videos:
        frame_points = scroll_video_frames(
            client=qdrant, collection_name=COLLECTION_NAME,
            video_id=video_name, with_vectors=True,
        )
        if not frame_points:
            continue

        V = np.array([p.vector for p in frame_points], dtype=np.float32)
        S = Q @ V.T

        score, path = run_dante_dp(S, lambda_penalty=body.lambda_penalty)

        event_frames = [
            TrakeFrameResult(
                query              = body.queries[i],
                global_frame_index = frame_points[path[i]].payload["global_frame_index"],
                frame_webp_path    = frame_points[path[i]].payload["frame_webp_path"],
            )
            for i in range(len(body.queries))
        ]
        dante_results.append(TrakeVideoResult(
            video_name=video_name, dante_score=score, event_frames=event_frames,
        ))
        log.info(f"[trake] video={video_name} score={score:.4f}")

    dante_results.sort(key=lambda x: x.dante_score, reverse=True)
    top = dante_results[:body.top_k]
    return TrakeSearchResponse(
        queries=body.queries, translated_queries=translated_queries,
        results=top, total=len(top),
    )


# ===========================================================================
# NHÁNH 3 — POST /search/llm
# ===========================================================================

@router.post("/llm", response_model=LLMSearchResponse)
async def llm_search(
    request: Request,
    body: LLMSearchRequest,
    qdrant = Depends(get_qdrant_client),
    mongo  = Depends(get_mongo_db),
):
    encoder         = request.app.state.encoder
    prompt_splitter = request.app.state.prompt_splitter
    reranker        = request.app.state.reranker

    translated = await translate_to_english(body.query)
    log.info(f"[llm] '{body.query}' → '{translated}'")

    chunks      = await prompt_splitter.split(translated)
    chunk_texts = [c.text for c in chunks]
    log.info(f"[llm] chunks={chunk_texts}")

    query_vectors = [encoder.encode_text(t).tolist() for t in chunk_texts]
    fetch_k       = min(body.top_k * len(chunks) * 2, body.top_k * 6)

    batch_results = batch_search_qdrant(
        client=qdrant, collection_name=COLLECTION_NAME,
        query_vectors=query_vectors, top_k=fetch_k,
        video_name=body.video_name,
    )
    merged = merge_and_dedup(batch_results, top_k=body.top_k * 3)
    if not merged:
        return LLMSearchResponse(
            original_query=body.query, translated_query=translated,
            chunks=chunk_texts, results=[], total=0,
        )

    qdrant_ids = [h.payload.get("qdrant_id", str(h.id)) for h in merged]
    mongo_docs = batch_search_mongo(mongo, MONGO_COLLECTION, qdrant_ids)

    final = _rerank(reranker, translated, merged, mongo_docs, body.top_k) if reranker else merged[:body.top_k]
    results = _build_frame_results(final, mongo_docs)
    return LLMSearchResponse(
        original_query=body.query, translated_query=translated,
        chunks=chunk_texts, results=results, total=len(results),
    )