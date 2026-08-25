"""
Review Store Service — Port 8001
Serves customer reviews from shared/reviews.db with SQL filtering and pagination.
"""
import os
import sqlite3
from typing import Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

# ── Paths ────────────────────────────────────────────────────────────────────
SHARED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
DB_PATH = os.path.join(SHARED_DIR, "reviews.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Review Store Service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    try:
        conn = get_db_connection()
        count = conn.execute("SELECT COUNT(*) as count FROM reviews").fetchone()["count"]
        conn.close()
        return {"status": "ok", "service": "review-store", "review_count": count}
    except Exception as e:
         return {"status": "error", "service": "review-store", "error": str(e)}


@app.get("/reviews")
def get_reviews(
    product: Optional[str] = None,
    rating: Optional[str] = None,
    category_tag: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
):
    """Return filtered and paginated reviews via SQL."""
    conn = get_db_connection()
    
    query = "SELECT * FROM reviews WHERE 1=1"
    count_query = "SELECT COUNT(*) as total FROM reviews WHERE 1=1"
    params = []
    
    if product:
        query += " AND product = ?"
        count_query += " AND product = ?"
        params.append(product)
        
    if rating:
        allowed_ratings = []
        try:
            allowed_ratings = [int(r.strip()) for r in rating.split(",") if r.strip()]
        except ValueError:
            pass
        if allowed_ratings:
            placeholders = ",".join("?" * len(allowed_ratings))
            query += f" AND rating IN ({placeholders})"
            count_query += f" AND rating IN ({placeholders})"
            params.extend(allowed_ratings)
            
    if category_tag:
        query += " AND category_tag = ?"
        count_query += " AND category_tag = ?"
        params.append(category_tag)
        
    if search:
        query += " AND (LOWER(text) LIKE ? OR LOWER(reviewer) LIKE ?)"
        count_query += " AND (LOWER(text) LIKE ? OR LOWER(reviewer) LIKE ?)"
        search_term = f"%{search.lower()}%"
        params.extend([search_term, search_term])
        
    total = conn.execute(count_query, params).fetchone()["total"]
    
    start = (page - 1) * limit
    query += " LIMIT ? OFFSET ?"
    params.extend([limit, start])
    
    rows = conn.execute(query, params).fetchall()
    conn.close()
    
    # Convert sqlite3.Row to dict for JSON serialization
    reviews = [dict(row) for row in rows]

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "reviews": reviews,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=False)
