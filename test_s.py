import certifi
from qdrant_client import QdrantClient
from src.db.qdrant_client import get_qdrant_client
from pymongo import MongoClient
q_url = "https://2a6572a3-ef7c-4e34-bffe-5d68629636a4.us-east-1-1.aws.cloud.qdrant.io"
q_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6MjA4ZjlkNDUtYmY4YS00NjZhLWI5NzUtMThjOWYxNmJiZTZkIn0.tMZyw39VAYzAxhOmpcAczKLgvp2R4oTz2bDf9aSK5lw"
q_client = get_qdrant_client(url=q_url, api_key=q_key)
result = q_client.query_points(
    collection_name="HCMAI_SIGLIP",
    query=[0.0] * 1152,  # vector giả, chỉ để xem payload
    limit=1
)
print(result.points[0].payload)