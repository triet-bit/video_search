import certifi
from qdrant_client import QdrantClient
from pymongo import MongoClient

print("--- KIỂM TRA QDRANT ---")
q_url = "https://2a6572a3-ef7c-4e34-bffe-5d68629636a4.us-east-1-1.aws.cloud.qdrant.io"
q_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6MjA4ZjlkNDUtYmY4YS00NjZhLWI5NzUtMThjOWYxNmJiZTZkIn0.tMZyw39VAYzAxhOmpcAczKLgvp2R4oTz2bDf9aSK5lw"
q_client = QdrantClient(url=q_url, api_key=q_key)
colls = q_client.get_collections()
if any(c.name == "HCMAI-SIGLIP" for c in colls.collections):
    cnt = q_client.count("HCMAI-SIGLIP").count
    print(f"Số lượng vector trong Qdrant: {cnt}")
else:
    print("❌ LỖI: Không tìm thấy Collection 'HCMAI-SIGLIP' trên Qdrant!")

print("\n--- KIỂM TRA MONGODB ---")
m_uri = "mongodb+srv://triethuynhminh2206_db_user:Om2WF4WCTgMsQy3K@cluster0.esppg8d.mongodb.net/"
m_client = MongoClient(m_uri, tlsCAFile=certifi.where())
m_db = m_client["HCMAIDB"]
cnt_mongo = m_db["embeddings"].count_documents({})
print(f"Số lượng file trên MongoDB: {cnt_mongo}")

if cnt_mongo > 0:
    doc = m_db["embeddings"].find_one()
    print("Mẫu 1 ID của MongoDB:", doc.get("qdrant_id", "Không có trường qdrant_id"))
