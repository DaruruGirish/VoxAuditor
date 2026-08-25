"""
API Gateway — Port 8000
Single entry point for the frontend. Routes requests to the appropriate
downstream microservice via HTTP using httpx.

Route map:
  GET  /api/dashboard     → analytics:8003/dashboard
  GET  /api/reviews       → review-store:8001/reviews
  POST /api/qa            → qa-agent:8004/qa
  GET  /api/index-status  → vector-search:8002/index/status
  POST /api/reindex       → vector-search:8002/index/build
  GET  /health            → fan-out health check to all services
"""
import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import os

# ── Downstream service URLs ───────────────────────────────────────────────────
SERVICES = {
    "review-store":  os.getenv("REVIEW_STORE_URL", "http://localhost:8001"),
    "vector-search": os.getenv("VECTOR_SEARCH_URL", "http://localhost:8002"),
    "analytics":     os.getenv("ANALYTICS_URL", "http://localhost:8003"),
    "qa-agent":      os.getenv("QA_AGENT_URL", "http://localhost:8004"),
}

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Vox Auditor — API Gateway", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QARequest(BaseModel):
    query: str


# ── Health fan-out ────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    """Check health of all downstream services."""
    results = {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        for name, url in SERVICES.items():
            try:
                resp = await client.get(f"{url}/health")
                results[name] = resp.json()
            except Exception as exc:
                results[name] = {"status": "unreachable", "error": str(exc)}

    all_ok = all(r.get("status") == "ok" for r in results.values())
    return {"status": "ok" if all_ok else "degraded", "services": results}


# ── Dashboard ─────────────────────────────────────────────────────────────────
@app.get("/api/dashboard")
async def get_dashboard():
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f"{SERVICES['analytics']}/dashboard")
        resp.raise_for_status()
        return resp.json()


# ── Reviews ───────────────────────────────────────────────────────────────────
@app.get("/api/reviews")
async def get_reviews(request: Request):
    """Forward all query params to the review-store service."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{SERVICES['review-store']}/reviews",
            params=dict(request.query_params),
        )
        resp.raise_for_status()
        return resp.json()


# ── QA ────────────────────────────────────────────────────────────────────────
@app.post("/api/qa")
async def post_qa(req: QARequest):
    async with httpx.AsyncClient(timeout=90.0) as client:
        resp = await client.post(
            f"{SERVICES['qa-agent']}/qa",
            json={"query": req.query},
        )
        resp.raise_for_status()
        return resp.json()


# ── Vector index ──────────────────────────────────────────────────────────────
@app.get("/api/index-status")
async def index_status():
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{SERVICES['vector-search']}/index/status")
        resp.raise_for_status()
        return resp.json()


@app.post("/api/reindex")
async def reindex():
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(f"{SERVICES['vector-search']}/index/build")
        resp.raise_for_status()
        return resp.json()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
