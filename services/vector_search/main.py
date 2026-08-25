"""
Vector Search Service — Port 8002
Wraps ChromaDB + sentence-transformers for semantic search and temporal trend analysis.
Reads data from shared SQLite database.
"""
import os
import time
import sqlite3
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

import chromadb
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

os.environ["USE_TF"] = "0"
os.environ["TRANSFORMERS_NO_TF"] = "1"

# ── Paths ─────────────────────────────────────────────────────────────────────
SHARED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
DB_PATH = os.path.join(SHARED_DIR, "reviews.db")
CHROMA_DB_PATH = os.path.join(SHARED_DIR, "chroma_db")
COLLECTION_NAME = "customer_reviews"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ── Singletons ────────────────────────────────────────────────────────────────
_chroma_client = None
_collection = None
_embedding_model = None
_last_index_time = None
_index_doc_count = 0


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        print(f"[VectorSearch] Loading embedding model: {EMBEDDING_MODEL}")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        print("[VectorSearch] Embedding model loaded.")
    return _embedding_model


def _get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        os.makedirs(CHROMA_DB_PATH, exist_ok=True)
        print(f"[VectorSearch] Initializing ChromaDB at: {CHROMA_DB_PATH}")
        _chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    return _chroma_client


def _get_collection():
    global _collection
    if _collection is None:
        client = _get_chroma_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def _reviews_db_modified() -> bool:
    global _last_index_time
    if _last_index_time is None:
        return True
    try:
        return os.path.getmtime(DB_PATH) > _last_index_time
    except OSError:
        return True


def build_index() -> bool:
    global _last_index_time, _index_doc_count, _collection

    print("[VectorSearch] Building vector index from:", DB_PATH)
    start_time = time.time()

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        reviews = [dict(row) for row in conn.execute("SELECT * FROM reviews").fetchall()]
        conn.close()
    except Exception as e:
        print(f"[VectorSearch] ERROR reading SQLite DB: {e}")
        return False

    if not reviews:
        return False

    model = _get_embedding_model()
    client = _get_chroma_client()

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    _collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    ids, documents, metadatas = [], [], []
    for r in reviews:
        enriched_text = (
            f"{r['product']} {r['model']} review: {r['text']} "
            f"Rating: {r['rating']}/5. Category: {r.get('category_tag', 'Unknown')}."
        )
        ids.append(r["review_id"])
        documents.append(enriched_text)
        metadatas.append({
            "review_id": r["review_id"],
            "product": r["product"],
            "model": r["model"],
            "rating": r["rating"],
            "date": r["date"],
            "year_month": r["year_month"],
            "month": int(r["date"][5:7]),
            "category_tag": r.get("category_tag", "Unknown"),
            "reviewer": r["reviewer"],
            "original_text": r["text"],
        })

    print(f"[VectorSearch] Generating embeddings for {len(documents)} reviews...")
    embeddings = model.encode(documents, show_progress_bar=True, batch_size=64).tolist()

    BATCH_SIZE = 100
    for i in range(0, len(ids), BATCH_SIZE):
        _collection.add(
            ids=ids[i : i + BATCH_SIZE],
            documents=documents[i : i + BATCH_SIZE],
            embeddings=embeddings[i : i + BATCH_SIZE],
            metadatas=metadatas[i : i + BATCH_SIZE],
        )

    elapsed = time.time() - start_time
    _last_index_time = time.time()
    _index_doc_count = len(ids)
    print(f"[VectorSearch] Index built: {_index_doc_count} docs in {elapsed:.2f}s")
    return True


def ensure_index() -> bool:
    collection = _get_collection()
    count = collection.count()
    if count == 0 or _reviews_db_modified():
        print("[VectorSearch] Index stale or empty — rebuilding...")
        return build_index()
    global _index_doc_count
    _index_doc_count = count
    print(f"[VectorSearch] Index current: {count} docs.")
    return True


def _get_index_status_data() -> dict:
    try:
        count = _get_collection().count()
    except Exception:
        count = 0
    return {
        "doc_count": count,
        "last_built": (
            datetime.fromtimestamp(_last_index_time).isoformat() if _last_index_time else None
        ),
        "collection_name": COLLECTION_NAME,
        "embedding_model": EMBEDDING_MODEL,
        "db_path": CHROMA_DB_PATH,
    }


def _build_where_filter(filters: dict) -> Optional[dict]:
    if not filters:
        return None
    conditions = []
    if filters.get("product"):
        conditions.append({"product": {"$eq": filters["product"]}})
    if filters.get("sentiment") == "negative":
        conditions.append({"rating": {"$lte": 3}})
    elif filters.get("sentiment") == "positive":
        conditions.append({"rating": {"$gte": 4}})
    if filters.get("months"):
        months = filters["months"]
        if len(months) == 1:
            conditions.append({"month": {"$eq": months[0]}})
        else:
            conditions.append({"month": {"$in": months}})
    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


def do_semantic_search(query: str, filters: dict = None, n_results: int = 15) -> list:
    collection = _get_collection()
    model = _get_embedding_model()
    query_embedding = model.encode(query).tolist()
    where_filter = _build_where_filter(filters)

    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter if where_filter else None,
            include=["metadatas", "distances", "documents"],
        )
    except Exception as e:
        print(f"[VectorSearch] Search error (retrying without filter): {e}")
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["metadatas", "distances", "documents"],
        )

    matched = []
    if results and results["metadatas"] and results["metadatas"][0]:
        for i, meta in enumerate(results["metadatas"][0]):
            distance = results["distances"][0][i] if results["distances"] else 0
            similarity = 1 - distance
            matched.append({
                "review_id": meta["review_id"],
                "product": meta["product"],
                "model": meta["model"],
                "rating": meta["rating"],
                "date": meta["date"],
                "reviewer": meta["reviewer"],
                "text": meta["original_text"],
                "category_tag": meta["category_tag"],
                "similarity_score": round(similarity, 4),
                "year_month": meta["year_month"],
            })
    return matched


def do_temporal_trend_search(query: str, product: str = None, n_results: int = 50) -> dict:
    collection = _get_collection()
    model = _get_embedding_model()
    query_embedding = model.encode(query).tolist()
    where_filter = {"product": {"$eq": product}} if product else None

    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter,
            include=["metadatas", "distances", "documents"],
        )
    except Exception as e:
        print(f"[VectorSearch] Temporal search error: {e}")
        return {"monthly_data": [], "direction": "unknown", "total_count": 0, "matched_reviews": []}

    if not results or not results["metadatas"] or not results["metadatas"][0]:
        return {"monthly_data": [], "direction": "unknown", "total_count": 0, "matched_reviews": []}

    monthly_buckets: dict = defaultdict(list)
    matched_reviews = []

    for i, meta in enumerate(results["metadatas"][0]):
        distance = results["distances"][0][i]
        similarity = 1 - distance
        if similarity < 0.3:
            continue
        ym = meta["year_month"]
        review = {
            "review_id": meta["review_id"],
            "product": meta["product"],
            "model": meta["model"],
            "rating": meta["rating"],
            "date": meta["date"],
            "reviewer": meta["reviewer"],
            "text": meta["original_text"],
            "category_tag": meta["category_tag"],
            "similarity_score": round(similarity, 4),
            "year_month": ym,
        }
        monthly_buckets[ym].append(review)
        matched_reviews.append(review)

    sorted_months = sorted(monthly_buckets.keys())
    monthly_data = []
    for ym in sorted_months:
        bucket = monthly_buckets[ym]
        avg_rating = sum(r["rating"] for r in bucket) / len(bucket) if bucket else 0
        complaint_count = sum(1 for r in bucket if r["rating"] <= 3)
        monthly_data.append({
            "month": ym,
            "total_count": len(bucket),
            "complaint_count": complaint_count,
            "avg_rating": round(avg_rating, 2),
            "avg_similarity": round(
                sum(r["similarity_score"] for r in bucket) / len(bucket), 4
            ),
        })

    # Trend direction: compare first half vs second half of recent months
    direction = "stable"
    if len(monthly_data) >= 2:
        recent = monthly_data[-3:] if len(monthly_data) >= 3 else monthly_data[-2:]
        counts = [m["complaint_count"] for m in recent]
        if len(counts) >= 2:
            half = len(counts) // 2
            first_avg = sum(counts[:half]) / max(half, 1)
            second_avg = sum(counts[half:]) / max(len(counts) - half, 1)
            if first_avg > 0:
                change_pct = ((second_avg - first_avg) / first_avg) * 100
            elif second_avg > 0:
                change_pct = 100.0
            else:
                change_pct = 0.0
            if change_pct > 15:
                direction = "rising"
            elif change_pct < -15:
                direction = "declining"

    return {
        "monthly_data": monthly_data,
        "direction": direction,
        "total_count": len(matched_reviews),
        "matched_reviews": matched_reviews[:10],
    }


# ── FastAPI app ───────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[VectorSearch] Startup — ensuring index...")
    ensure_index()
    print("[VectorSearch] Ready.")
    yield


app = FastAPI(title="Vector Search Service", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SemanticSearchRequest(BaseModel):
    query: str
    filters: Optional[dict] = None
    n_results: int = 15


class TemporalSearchRequest(BaseModel):
    query: str
    product: Optional[str] = None
    n_results: int = 50


@app.get("/health")
def health():
    try:
        count = _get_collection().count()
    except Exception:
        count = 0
    return {"status": "ok", "service": "vector-search", "index_doc_count": count}


@app.post("/search/semantic")
def semantic_search(req: SemanticSearchRequest):
    """Semantic vector search across the review index."""
    return do_semantic_search(req.query, req.filters, req.n_results)


@app.post("/search/temporal")
def temporal_trend_search(req: TemporalSearchRequest):
    """Temporal trend analysis — groups semantically relevant reviews by month."""
    return do_temporal_trend_search(req.query, req.product, req.n_results)


@app.post("/index/build")
def trigger_build():
    """Force rebuild the ChromaDB index from reviews.json."""
    success = build_index()
    return {"success": success, **_get_index_status_data()}


@app.get("/index/status")
def index_status():
    """Return current index health and metadata."""
    return _get_index_status_data()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8002, reload=False)
