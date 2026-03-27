import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from typing import Optional

log = logging.getLogger(__name__)

_qdrant_client: Optional[QdrantClient] = None


def get_qdrant_client(
    host: str = "localhost",
    port: int = 6333,
    https: bool = False,
    prefer_grpc: bool = False,
    timeout: int = 60,
) -> QdrantClient:
    global _qdrant_client
    if _qdrant_client is not None:
        log.info("Reusing existing Qdrant client")
        return _qdrant_client
    try:
        _qdrant_client = QdrantClient(
            host=host,
            port=port,
            https=https,
            prefer_grpc=prefer_grpc,
            timeout=timeout,
        )
        log.info(f"Connected to Qdrant at {host}:{port}")
        return _qdrant_client
    except Exception as e:
        log.error(f"Failed to connect to Qdrant: {e}")
        raise


def search_qdrant(
    client: QdrantClient,
    collection_name: str,
    query_vector: list[float],
    top_k: int = 10,
    video_name: Optional[str] = None,   # Bug fix: search.py truyền limit= nhưng hàm không nhận
    with_payload: bool = True,
    with_vectors: bool = False,
) -> list:
    """
    Search Qdrant với optional filter theo video_name.
    """
    query_filter = None
    if video_name:
        query_filter = Filter(
            must=[FieldCondition(key="video_name", match=MatchValue(value=video_name))]
        )
    try:
        results = client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=top_k,
            with_payload=with_payload,
            with_vectors=with_vectors,
        )
        log.info(f"Qdrant search returned {len(results)} results")
        return results
    except Exception as e:
        log.error(f"Qdrant search error: {e}")
        return []


def scroll_video_frames(
    client: QdrantClient,
    collection_name: str,
    video_id: str,
    with_vectors: bool = True,
    batch_size: int = 100,
) -> list:
    """
    Lấy TOÀN BỘ frames của một video bằng scroll (không dùng similarity search).

    Dùng cho DANTE — cần đủ T frames theo đúng thứ tự thời gian, không bị giới hạn
    bởi similarity score như search_qdrant.

    Args:
        client:           QdrantClient
        collection_name:  tên collection
        video_id:         video_id cần lấy (filter theo payload field "video_id")
        with_vectors:     có lấy embedding vector không (True để tính similarity matrix)
        batch_size:       số điểm lấy mỗi lần scroll (tối đa 100 theo Qdrant limit)

    Returns:
        list các Record đã được sắp xếp theo frame_index tăng dần
    """
    video_filter = Filter(
        must=[FieldCondition(key="video_id", match=MatchValue(value=video_id))]
    )

    all_points = []
    offset = None  # None = bắt đầu từ đầu

    try:
        while True:
            points, next_offset = client.scroll(
                collection_name=collection_name,
                scroll_filter=video_filter,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=with_vectors,
            )

            all_points.extend(points)

            # next_offset = None nghĩa là đã hết dữ liệu
            if next_offset is None:
                break
            offset = next_offset

        # Sắp xếp theo frame_index để đảm bảo thứ tự thời gian đúng
        all_points.sort(key=lambda p: p.payload.get("frame_index", 0))

        log.info(f"Scrolled {len(all_points)} frames for video_id={video_id}")
        return all_points

    except Exception as e:
        log.error(f"Qdrant scroll error for video_id={video_id}: {e}")
        return []


def batch_search_qdrant(
    client: QdrantClient,
    collection_name: str,
    query_vectors: list[list[float]],
    top_k: int = 10,
    video_name: Optional[str] = None,
) -> list[list]:
    """
    Batch search: tìm kiếm nhiều vectors cùng lúc, dùng cho multi-chunk query.
    Trả về list of list kết quả tương ứng với từng query_vector.
    """
    all_results = []
    for vec in query_vectors:
        results = search_qdrant(
            client=client,
            collection_name=collection_name,
            query_vector=vec,
            top_k=top_k,
            video_name=video_name,
        )
        all_results.append(results)
    return all_results


def merge_and_dedup(
    batch_results: list[list],
    top_k: int = 10,
) -> list:
    """
    Merge kết quả từ nhiều chunk queries, dedup theo qdrant_id,
    giữ score cao nhất, sort giảm dần.
    """
    seen: dict[str, object] = {}
    for results in batch_results:
        for hit in results:
            qid = hit.payload.get("qdrant_id", str(hit.id))
            if qid not in seen or hit.score > seen[qid].score:
                seen[qid] = hit
    merged = sorted(seen.values(), key=lambda h: h.score, reverse=True)
    return merged[:top_k]