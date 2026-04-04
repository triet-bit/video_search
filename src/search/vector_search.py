from src.db.qdrant_client import get_qdrant_client
from src.utils.logger import log
client = get_qdrant_client(host="localhost",
                            port=6333,
                            https=True,
                            prefer_grpc=False,
                            timeout=500)
def single_vector_search(collection_name: str, query_vector: list[float], top_k: int = 5) -> list[dict]:
    try:
        search_result = client.query_points(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=top_k
        )
        return search_result
    except Exception as e:
        log.error(f"Vector search error in collection '{collection_name}': {e}")
        return []
def batch_vector_search(collection_name: str, query_vectors: list[list[float]], top_k: int = 5) -> list[list[dict]]:
    try:
        search_results = []
        for query_vector in query_vectors:
            result = single_vector_search(collection_name, query_vector, top_k)
            search_results.append(result)
        return search_results
    except Exception as e:
        log.error(f"Batch vector search error in collection '{collection_name}': {e}")
        return []
