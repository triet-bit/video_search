import faiss
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
import json

BIN_FILE = "data/faiss_index.bin"
MAPPING_DATA = "data/metadata.json"
BATCH_SIZE = 1000
COLLECTION_NAME = "keyframes"

qdrant_client = QdrantClient(host='localhost', port=6333)

# ✅ Đọc index gốc, KHÔNG unwrap
faiss_index = faiss.read_index(BIN_FILE)

# ✅ Lấy sub-index để đọc ntotal và d, nhưng GIỮ index gốc để reconstruct
if isinstance(faiss_index, faiss.IndexIDMap):
    inner_index = faiss_index.index
    total_vectors = faiss_index.ntotal   # lấy từ IndexIDMap
    vector_dim = inner_index.d           # lấy dim từ inner
else:
    inner_index = faiss_index
    total_vectors = faiss_index.ntotal
    vector_dim = faiss_index.d

print("Num of vectors", total_vectors)
print("Num of dims", vector_dim)
print("Index type:", type(faiss_index))

# ✅ Tạo collection nếu chưa có
existing = [c.name for c in qdrant_client.get_collections().collections]
if COLLECTION_NAME in existing:
    qdrant_client.delete_collection(COLLECTION_NAME)
    print(f"🗑️ Đã xóa collection cũ '{COLLECTION_NAME}' (dim cũ != {vector_dim})")

qdrant_client.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(size=vector_dim, distance=Distance.COSINE)
)
print(f"✅ Đã tạo lại collection '{COLLECTION_NAME}' với dim={vector_dim}")
with open(MAPPING_DATA, 'r') as f:
    mapping_data = json.load(f)

# ✅ Reconstruct toàn bộ vectors một lần (nhanh hơn loop)
print("Đang reconstruct tất cả vectors...")
all_vectors = np.zeros((total_vectors, vector_dim), dtype=np.float32)
inner_index.reconstruct_n(0, total_vectors, all_vectors)

points_batch = []
for i in range(total_vectors):
    try:
        vector_list = all_vectors[i].tolist()
        data = mapping_data[str(i)]

        points_batch.append(
            PointStruct(
                id=i,
                vector=vector_list,
                payload={**data}
            )
        )

        if len(points_batch) == BATCH_SIZE:
            qdrant_client.upsert(
                collection_name=COLLECTION_NAME,
                points=points_batch
            )
            print(f"✅ Done {i + 1}/{total_vectors}")
            points_batch = []

    except Exception as e:
        print(f"❌ Error at {i}: {e}")
        break

if points_batch:
    qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points_batch)
    print(f"✅ Đã đẩy nốt {len(points_batch)} vectors cuối.")

print("🎉 Migration hoàn tất!")