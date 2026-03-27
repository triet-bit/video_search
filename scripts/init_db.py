from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from elasticsearch import Elasticsearch
CONN = "mongodb://localhost:27018/"
def test_mongo_connection(): 
    client = None 
    try:
        client = MongoClient(CONN, serverSelectionTimeoutMS=5000) # Set a timeout
        client.admin.command('serverStatus')
        print("Connection successful!")
    except ServerSelectionTimeoutError as err: 
        print('timeout')
    except Exception as e: 
        print('unexpected error')
    finally: 
        if client: 
            client.close()
            print("connection close")
def test_qdrant_connection(): # Sửa lỗi chính tả ở tên hàm nhé
    try:
        client = QdrantClient(host="localhost", port=6333)
        
        # Kiểm tra xem collection đã tồn tại chưa để tránh lỗi
        if not client.collection_exists("keyframes"):
            client.create_collection(
                collection_name="keyframes",
                # Sửa thành 768 chiều của BEiT-3, dùng khoảng cách COSINE
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
            )
            print("Kết nối Qdrant thành công và đã tạo collection 'keyframes'!")
        else:
            print("Kết nối Qdrant thành công (Collection 'keyframes' đã có sẵn).")
    except Exception as e:
        print(f"Lỗi kết nối Qdrant: {e}")
def test_es_connection():
    try:
        # Kết nối tới Elasticsearch
        es = Elasticsearch("http://localhost:9200")
        if es.ping():
            index_name = "ocr_text"
            
            # Khởi tạo Index với bộ phân tích tiếng Việt (Vietnamese Analyzer)
            if not es.indices.exists(index=index_name):
                mappings = {
                    "properties": {
                        "keyframe_id": {"type": "keyword"},
                        "text": {"type": "text", "analyzer": "standard"}
                    }
                }
                es.indices.create(index=index_name, mappings=mappings)
                print("Kết nối Elasticsearch thành công và đã tạo index 'ocr_text' với Vietnamese analyzer!")
            else:
                print("Kết nối Elasticsearch thành công (Index 'ocr_text' đã có sẵn).")
        else:
            print("Không thể ping tới Elasticsearch.")
    except Exception as e:
        print(f"Lỗi kết nối Elasticsearch: {e}")   
if __name__ == "__main__": 
    print("--- BẮT ĐẦU KIỂM TRA HẠ TẦNG ---")
    test_mongo_connection()
    test_qdrant_connection()
    test_es_connection()
    print("--- HOÀN TẤT ---")