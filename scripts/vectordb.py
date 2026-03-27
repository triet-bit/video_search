import pprint
import os
import logging
from time import sleep
from functools import lru_cache

import pandas as pd
from pymongo import MongoClient, errors as mongo_errors
from pymongo import UpdateOne
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from concurrent.futures import ThreadPoolExecutor, as_completed

# ──────────────────────────────────────────────
# LOGGING
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
QDRANT_HOST       = "hypergamous-somewhat-hiroko.ngrok-free.dev"
QDRANT_COLLECTION = "HCMAI_SIGLIP"
MONGO_URI = "mongodb://localhost:27018"
MONGO_DB          = "HCMAIDB"
MAPPINGS_CSV      = "/home/minhtriet/Documents/batch2mapping"

SCROLL_LIMIT      = 1000   # số point mỗi lần scroll
MAX_RETRIES       = 3      # số lần retry khi lỗi
RETRY_DELAY       = 2      # giây chờ giữa các retry
MAX_WORKERS       = 4      # số thread xử lý song song

# ──────────────────────────────────────────────
# CLIENTS
# ──────────────────────────────────────────────
qdrant = QdrantClient(host="localhost", port=6333, https=False, prefer_grpc=False, timeout=60)
mongo  = MongoClient(MONGO_URI)
db     = mongo[MONGO_DB]

db.embeddings.create_index("qdrant_id", unique=True)
log.info("✅ MongoDB index created")

# ──────────────────────────────────────────────
# CACHE CSV — tránh đọc lại mỗi frame
# ──────────────────────────────────────────────
@lru_cache(maxsize=512)
def load_mapping(video_name: str) -> pd.DataFrame:
    """Load và cache CSV mapping theo video_name."""
    path = os.path.join(MAPPINGS_CSV, video_name, video_name + ".csv")
    df = pd.read_csv(path)
    df.set_index("frame_order", inplace=True)   # index để lookup O(1)
    return df

# ──────────────────────────────────────────────
# BUILD DOC từ một Qdrant point
# ──────────────────────────────────────────────
def build_doc(r) -> dict | None:
    """Trả về document dict hoặc None nếu không tìm được mapping."""
    p            = r.payload
    video_name   = p.get("video_name")
    frame_fname  = p.get("frame_filename").replace(".jpg", "") 
    frame_order  = p.get("frame_order")
    log.info(f"frame_filename raw: '{frame_fname}'")  # thêm dòng này tạm thời

    try:
        mapping = load_mapping(video_name)
        row     = mapping.loc[frame_order]
    except KeyError:
        log.warning(f"frame_order={frame_order} không có trong CSV của {video_name}")
        return None
    except FileNotFoundError:
        log.warning(f"Không tìm thấy CSV cho video: {video_name}")
        return None

    return {
        "qdrant_id":          r.id,
        "video_name":         video_name,
        "frame_filename":     frame_fname,
        "frame_order":        frame_order,
        "pts_time":           row["pts_time"],
        "fps":                row["fps"],
        "global_frame_index": row["global_frame_index"],
        "frame_webp_path":    f"{video_name}/{frame_fname}.webp",
    }

# ──────────────────────────────────────────────
# UPSERT BATCH VÀO MONGODB (idempotent)
# ──────────────────────────────────────────────
def upsert_batch(batch: list[dict]) -> int:
    """Upsert theo qdrant_id — chạy lại script không bị trùng."""
    if not batch:
        return 0
    ops = [
        UpdateOne(
            {"qdrant_id": doc["qdrant_id"]},
            {"$setOnInsert": doc},
            upsert=True
        )
        for doc in batch
    ]
    result = db.embeddings.bulk_write(ops, ordered=False)
    return result.upserted_count

# ──────────────────────────────────────────────
# SCROLL MỘT PAGE với retry
# ──────────────────────────────────────────────
def scroll_page(offset):
    """Scroll Qdrant, retry nếu gặp lỗi mạng."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return qdrant.scroll(
                collection_name=QDRANT_COLLECTION,
                limit=SCROLL_LIMIT,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
        except (UnexpectedResponse, Exception) as e:
            log.warning(f"Scroll lỗi (lần {attempt}/{MAX_RETRIES}): {e}")
            if attempt == MAX_RETRIES:
                raise
            sleep(RETRY_DELAY * attempt)

# ──────────────────────────────────────────────
# XỬ LÝ MỘT BATCH SONG SONG
# ──────────────────────────────────────────────
def process_batch(results) -> list[dict]:
    """Build docs song song bằng ThreadPoolExecutor."""
    docs = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(build_doc, r): r for r in results}
        for future in as_completed(futures):
            try:
                doc = future.result()
                if doc:
                    docs.append(doc)
            except Exception as e:
                log.error(f"Lỗi khi build doc: {e}")
    return docs

# ──────────────────────────────────────────────
# MAIN LOOP
# ──────────────────────────────────────────────
def main():
    offset = None
    total  = 0

    log.info("🔍 Bắt đầu scroll Qdrant...")

    while True:
        # 1. Lấy một page từ Qdrant
        results, next_offset = scroll_page(offset)
        if not results:
            break

        # 2. Build docs song song
        docs = process_batch(results)

        # 3. Upsert vào MongoDB
        if docs:
            try:
                inserted = upsert_batch(docs)
                total   += inserted
                log.info(f"  → Page xong | upserted: {inserted} | tổng cộng: {total}")
            except mongo_errors.BulkWriteError as bwe:
                # Bỏ qua duplicate key, log các lỗi khác
                non_dup = [e for e in bwe.details["writeErrors"] if e["code"] != 11000]
                if non_dup:
                    log.error(f"Bulk write lỗi không phải duplicate: {non_dup}")

        if next_offset is None:
            break
        offset = next_offset

    log.info(f"\n✅ Hoàn tất! Tổng upserted: {total}")
    log.info("\nSample document:")
    pprint.pprint(db.embeddings.find_one())
# ──────────────────────────────────────────────
# KIỂM TRA KẾT NỐI
# ──────────────────────────────────────────────
def check_connections() -> bool:
    """Kiểm tra Qdrant và MongoDB trước khi chạy."""
    ok = True

    # --- Qdrant ---
    try:
        info = qdrant.get_collection(QDRANT_COLLECTION)
        count = info.points_count
        log.info(f"✅ Qdrant OK — collection '{QDRANT_COLLECTION}' có {count:,} points")
    except Exception as e:
        log.error(f"❌ Qdrant FAIL — {e}")
        ok = False

    # --- MongoDB ---
    try:
        mongo.admin.command("ping")
        collections = db.list_collection_names()
        log.info(f"✅ MongoDB OK — database '{MONGO_DB}', collections: {collections}")
    except Exception as e:
        log.error(f"❌ MongoDB FAIL — {e}")
        ok = False

    # --- Thư mục CSV ---
    if os.path.isdir(MAPPINGS_CSV):
        n = len(os.listdir(MAPPINGS_CSV))
        log.info(f"✅ MAPPINGS_CSV OK — {n} thư mục tìm thấy tại '{MAPPINGS_CSV}'")
    else:
        log.error(f"❌ MAPPINGS_CSV FAIL — không tìm thấy thư mục '{MAPPINGS_CSV}'")
        ok = False

    return ok

if __name__ == "__main__":
    #main()
    log.info("🔌 Kiểm tra kết nối...")
    if not check_connections():
        log.error("🚫 Có kết nối bị lỗi. Dừng lại.")
        exit(1)

    log.info("─" * 50)
    main()