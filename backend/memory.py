import chromadb
from chromadb.config import Settings
from datetime import datetime
from backend.embeddings import embed

_client = None
_collection = None

COLLECTION_NAME = "research_memory"

def get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(
            path="./data/chroma_db",
            settings=Settings(anonymized_telemetry=False)
        )
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
    return _collection


def save_memory(session_id: str, content: str, metadata: dict = {}) -> str:
    """Save a memory chunk to Chroma."""
    collection = get_collection()
    doc_id = f"{session_id}_{datetime.utcnow().isoformat()}"
    embedding = embed(content)
    collection.add(
        ids=[doc_id],
        embeddings=[embedding],
        documents=[content],
        metadatas=[{
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            **metadata
        }]
    )
    return doc_id


def search_memory(query: str, session_id: str = None, n_results: int = 5) -> list[dict]:
    """Search memory by semantic similarity."""
    collection = get_collection()
    where = {"session_id": session_id} if session_id else None
    results = collection.query(
        query_embeddings=[embed(query)],
        n_results=n_results,
        where=where,
        include=["documents", "metadatas", "distances"]
    )
    memories = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        memories.append({
            "content": doc,
            "metadata": meta,
            "relevance": round(1 - dist, 3)
        })
    return memories


def get_all_memories(session_id: str) -> list[dict]:
    """Retrieve all memories for a session ordered by time."""
    collection = get_collection()
    results = collection.get(
        where={"session_id": session_id},
        include=["documents", "metadatas"]
    )
    memories = []
    for doc, meta in zip(results["documents"], results["metadatas"]):
        memories.append({"content": doc, "metadata": meta})
    memories.sort(key=lambda x: x["metadata"].get("timestamp", ""))
    return memories
