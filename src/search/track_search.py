import numpy as np
import logging
from typing import Optional

from src.models.embedding_model import SiglipEncoder
from src.db.qdrant_client import get_qdrant_client, search_qdrant, scroll_video_frames
log = logging.getLogger(__name__)

_model: Optional[SiglipEncoder] = None


def get_model() -> SiglipEncoder:
    global _model
    if _model is None:
        _model = SiglipEncoder()
    return _model


# ---------------------------------------------------------------------------
# DANTE DP
# ---------------------------------------------------------------------------

def run_dante_dp(
    similarity_matrix: np.ndarray,
    lambda_penalty: float = 0.0001,
) -> tuple[float, list[int]]:
    """
    Chạy thuật toán DANTE DP trên ma trận similarity của MỘT video.

    Args:
        similarity_matrix: numpy array (N, T)
                           N = số sự kiện (queries)
                           T = số keyframe trong video
        lambda_penalty:    hệ số phạt khoảng cách thời gian

    Returns:
        max_score: điểm DANTE cao nhất
        path:      list index nội bộ keyframe [t0, t1, ..., t_{N-1}]
    """
    N, T = similarity_matrix.shape

    dp = np.full((N, T), -np.inf)
    trace = np.zeros((N, T), dtype=int)

    dp[0, :] = similarity_matrix[0, :]

    for i in range(1, N):
        running_max = -np.inf
        best_tau = -1

        for t in range(1, T):
            val_to_check = dp[i - 1, t - 1] + lambda_penalty * (t - 1)
            if val_to_check > running_max:
                running_max = val_to_check
                best_tau = t - 1

            dp[i, t] = similarity_matrix[i, t] + running_max - lambda_penalty * t
            trace[i, t] = best_tau

    max_score = float(np.max(dp[N - 1, :]))
    last_t = int(np.argmax(dp[N - 1, :]))

    path = []
    cur_t = last_t
    for i in range(N - 1, -1, -1):
        path.append(cur_t)
        cur_t = int(trace[i, cur_t])
    path.reverse()

    return max_score, path


# ---------------------------------------------------------------------------
# TRAKE SEARCH
# ---------------------------------------------------------------------------

def trake_search(
    queries: list[str],
    collection_name: str,
    top_k_candidates: int = 50,
    top_k_results: int = 5,
    lambda_penalty: float = 0.0001,
) -> list[dict]:
    """
    Tìm kiếm chuỗi sự kiện bằng DANTE DP.

    Payload Qdrant mỗi điểm gồm:
        qdrant_id, fps, frame_filename, frame_order, frame_webp_path,
        global_frame_index, pts_time, video_name

    Args:
        queries:           list câu truy vấn mô tả từng sự kiện theo thứ tự
        collection_name:   tên collection trong Qdrant
        top_k_candidates:  số keyframe lấy từ Qdrant ở bước lọc thô
        top_k_results:     số video trả về sau khi rerank
        lambda_penalty:    hệ số phạt khoảng cách thời gian cho DANTE

    Returns:
        list[dict] top_k_results video, sắp xếp theo dante_score giảm dần.
        Mỗi phần tử:
            - video_name:     tên video (ví dụ "K02_V001")
            - dante_score:    điểm DANTE
            - keyframe_path:  list global_frame_index tương ứng với từng sự kiện
            - frame_webp_paths: list đường dẫn ảnh tương ứng với từng sự kiện
    """
    model = get_model()
    qdrant = get_qdrant_client()

    # ------------------------------------------------------------------
    # BƯỚC 1: Mã hóa toàn bộ câu truy vấn → N vectors
    # ------------------------------------------------------------------
    log.info(f"Encoding {len(queries)} queries...")
    query_vectors: list[np.ndarray] = [model.encode_text(q) for q in queries]
    Q = np.array(query_vectors, dtype=np.float32)  # (N, dim)

    # ------------------------------------------------------------------
    # BƯỚC 2: Lọc thô — search theo vector query đầu tiên để lấy candidate videos
    # ------------------------------------------------------------------
    log.info("Retrieving candidate keyframes from Qdrant...")
    candidate_hits = search_qdrant(
        client=qdrant,
        collection_name=collection_name,
        query_vector=query_vectors[0].tolist(),
        top_k=top_k_candidates,
    )

    # Lấy tập hợp video_name không trùng lặp từ payload
    candidate_video_names: list[str] = list(
        {hit.payload["video_name"] for hit in candidate_hits if "video_name" in hit.payload}
    )
    log.info(f"Found {len(candidate_video_names)} candidate videos: {candidate_video_names}")

    if not candidate_video_names:
        log.warning("No candidate videos found, returning empty results")
        return []

    # ------------------------------------------------------------------
    # BƯỚC 3 + 4: Với mỗi video, scroll toàn bộ frames → tính similarity → DANTE
    # ------------------------------------------------------------------
    results = []

    for video_name in candidate_video_names:
        # Scroll toàn bộ frames của video, sort theo frame_order
        log.info(f"Scrolling frames for video={video_name}...")
        frame_points = scroll_video_frames(
            client=qdrant,
            collection_name=collection_name,
            video_id=video_name,   # filter theo payload field "video_name"
            with_vectors=True,
        )

        if not frame_points:
            log.warning(f"No frames found for video={video_name}, skipping")
            continue

        # Lấy embeddings và metadata theo đúng thứ tự frame_order
        video_embeddings = np.array(
            [p.vector for p in frame_points], dtype=np.float32
        )  # (T, dim)

        # ------------------------------------------------------------------
        # Tính Cosine Similarity — vectors đã L2-normalized nên dot = cosine
        # ------------------------------------------------------------------
        S = Q @ video_embeddings.T  # (N, T)

        # Chạy DANTE DP
        score, path = run_dante_dp(S, lambda_penalty=lambda_penalty)

        # Chuyển path (index nội bộ 0..T-1) → global_frame_index và frame_webp_path thực
        keyframe_path = [
            frame_points[t].payload["global_frame_index"] for t in path
        ]
        frame_webp_paths = [
            frame_points[t].payload["frame_webp_path"] for t in path
        ]

        results.append({
            "video_name": video_name,
            "dante_score": score,
            "keyframe_path": keyframe_path,
            "frame_webp_paths": frame_webp_paths,
        })

        log.info(f"video={video_name} | score={score:.4f} | frames={keyframe_path}")

    # ------------------------------------------------------------------
    # BƯỚC 5: Rerank theo dante_score giảm dần
    # ------------------------------------------------------------------
    results.sort(key=lambda x: x["dante_score"], reverse=True)
    top_results = results[:top_k_results]

    log.info(f"Returning top {len(top_results)} videos")
    return top_results