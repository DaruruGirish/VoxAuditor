"""
QA Agent Service — Port 8004
Hybrid retrieval pipeline: classifies queries, extracts filters, and calls the
Vector Search Service (port 8002) via HTTP — no direct Python imports.

This is the key microservices pattern: inter-service communication via REST.
"""
import re
import os
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

os.environ["USE_TF"] = "0"
os.environ["TRANSFORMERS_NO_TF"] = "1"

# ── Inter-service URL ─────────────────────────────────────────────────────────
VECTOR_SEARCH_URL = os.getenv("VECTOR_SEARCH_URL", "http://localhost:8002")

# ── NLP helpers (mirrors qa_agent.py) ────────────────────────────────────────
STEM_MAPPING = {
    "melting": "melt", "melted": "melt", "melts": "melt",
    "burns": "burn", "burning": "burn", "burnt": "burn",
    "clicking": "click", "clicked": "click", "clicks": "click",
    "ticking": "tick", "ticks": "tick",
    "wobbles": "wobble", "wobbling": "wobble", "wobbled": "wobble",
    "shaking": "shake", "shakes": "shake",
    "grinding": "grind",
    "noises": "noise", "noisy": "noise", "noice": "noise",
    "rattles": "rattle", "rattling": "rattle",
    "smells": "smell", "smelled": "smell", "smelling": "smell",
    "odors": "odor", "odours": "odor",
    "filters": "filter", "filtr": "filter",
    "sensors": "sensor", "lights": "light",
}

TREND_KEYWORDS = [
    "over time", "getting worse", "getting better", "rising", "falling", "declining",
    "trend", "increasing", "decreasing", "month over month", "mom", "growing",
    "spike", "surge", "seasonal", "compare months", "historically", "trajectory",
    "improve", "improving", "deteriorating", "worsening", "pattern over",
]

COMPARATIVE_KEYWORDS = [
    "vs", "versus", "compare", "compared to", "which is better", "which is worse",
    "difference between", "between summer and winter",
]


def clean_and_stem(text: str) -> list:
    words = re.findall(r"\b\w+\b", text.lower())
    return [STEM_MAPPING.get(w, w) for w in words]


def classify_query(query: str) -> str:
    normalized = query.lower()
    for kw in TREND_KEYWORDS:
        if kw in normalized:
            return "trend"
    for kw in COMPARATIVE_KEYWORDS:
        if kw in normalized:
            return "comparative"
    return "factual"


def extract_entities_and_filters(query: str) -> dict:
    normalized = query.lower()
    product = None
    sentiment = None
    months = []

    # Product detection
    if any(kw in normalized for kw in ["heater", "heating", "calido", "solace"]):
        product = "Space Heater"
    elif any(kw in normalized for kw in ["fan", "florence", "stealth", "ceiling"]):
        product = "Ceiling Fan"
    elif any(kw in normalized for kw in ["purifier", "freshia", "meditate"]):
        product = "Air Purifier"

    # Sentiment
    if any(w in normalized for w in ["bad", "terrible", "poor", "worst", "unhappy", "angry", "mad", "broken", "fail", "complaint", "issue", "problem"]):
        sentiment = "negative"
    elif any(w in normalized for w in ["good", "great", "excellent", "praise", "happy", "love", "like", "best"]):
        sentiment = "positive"

    # Month detection
    month_names = {
        "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
        "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8,
        "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }
    for mname, mnum in month_names.items():
        if re.search(r"\b" + mname + r"\b", normalized):
            months.append(mnum)
    if "winter" in normalized:
        months.extend([11, 12, 1, 2])
    elif "summer" in normalized:
        months.extend([4, 5, 6, 7, 8])

    # Keywords for context
    stopwords = {
        "why", "are", "what", "is", "the", "on", "in", "with", "about", "for",
        "to", "of", "and", "a", "an", "have", "has", "do", "does", "did", "get",
        "any", "how", "many", "there", "over", "time", "getting", "worse", "better",
        "trend", "rising", "falling",
    }
    product_keywords = {"heater", "fan", "purifier", "space", "ceiling", "air"}
    query_words = clean_and_stem(query)
    keywords = [w for w in query_words if w not in stopwords and w not in product_keywords and len(w) > 2]

    return {
        "product": product,
        "sentiment": sentiment,
        "months": list(set(months)),
        "keywords": keywords,
    }


# ── HTTP helpers (call Vector Search Service) ─────────────────────────────────
async def call_semantic_search(query: str, filters: dict = None, n_results: int = 20) -> list:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{VECTOR_SEARCH_URL}/search/semantic",
            json={"query": query, "filters": filters, "n_results": n_results},
        )
        resp.raise_for_status()
        return resp.json()


async def call_temporal_trend_search(query: str, product: str = None, n_results: int = 60) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{VECTOR_SEARCH_URL}/search/temporal",
            json={"query": query, "product": product, "n_results": n_results},
        )
        resp.raise_for_status()
        return resp.json()


# ── Response builders ─────────────────────────────────────────────────────────
async def _build_trend_response(query: str, filters: dict, steps: list) -> dict:
    steps.append("[Trend Mode] Calling vector-search service for temporal analysis...")

    trend_data = await call_temporal_trend_search(query, product=filters["product"], n_results=60)

    steps.append(f"[Trend Mode] Retrieved {trend_data['total_count']} semantically relevant reviews.")
    steps.append(f"[Trend Mode] Trend direction detected: {trend_data['direction'].upper()}")

    if trend_data["total_count"] == 0:
        steps.append("[Trend Mode] No matching reviews — aborting to prevent hallucination.")
        return {
            "answer": "I do not know. I could not find enough semantically relevant reviews to analyze "
                      "a trend for this topic. As a strict rule against hallucination, I cannot answer "
                      "without direct review evidence.",
            "citations": [],
            "execution_steps": steps,
        }

    prod_label = filters["product"] if filters["product"] else "all products"
    direction = trend_data["direction"]

    direction_emoji = {"rising": "📈", "declining": "📉", "stable": "➡️", "unknown": "❓"}
    direction_text = {
        "rising": "**increasing** over time",
        "declining": "**decreasing** over time",
        "stable": "**relatively stable**",
        "unknown": "unclear due to limited data",
    }

    answer_lines = [
        f"{direction_emoji.get(direction, '')} Based on semantic analysis of "
        f"**{trend_data['total_count']} relevant reviews** for **{prod_label}**, "
        f"this issue is {direction_text.get(direction, 'unknown')}."
    ]

    if trend_data["monthly_data"]:
        answer_lines.append("\n### Month-by-Month Breakdown:")
        for m in trend_data["monthly_data"]:
            bar = "█" * m["complaint_count"] + "░" * max(0, 5 - m["complaint_count"])
            answer_lines.append(
                f"- **{m['month']}**: {m['complaint_count']} complaints "
                f"(avg rating: {m['avg_rating']}/5) {bar}"
            )

    if direction == "rising":
        answer_lines.append(
            "\n⚠️ **Alert**: This issue shows an upward trend. The volume of complaints is "
            "increasing in recent months, suggesting the problem may be worsening."
        )
    elif direction == "declining":
        answer_lines.append(
            "\n✅ **Good news**: This issue appears to be declining. Fewer complaints are "
            "being reported in recent months."
        )
    else:
        answer_lines.append(
            "\nℹ️ The complaint volume for this issue is relatively consistent across months."
        )

    citations = []
    citation_id_map = {}
    for r in trend_data["matched_reviews"][:6]:
        cit_num = len(citation_id_map) + 1
        citation_id_map[r["review_id"]] = cit_num
        r_copy = r.copy()
        r_copy["citation_number"] = cit_num
        citations.append(r_copy)

    if citations:
        answer_lines.append("\n### Representative Reviews:")
        for c in citations:
            answer_lines.append(
                f"- [Review #{c['citation_number']}] ({c['date']}, {c['rating']}/5): "
                f"\"{c['text'][:100]}...\""
            )

    steps.append(f"Trend analysis complete. {len(citations)} citations attached.")
    return {"answer": "\n".join(answer_lines), "citations": citations, "execution_steps": steps}


async def _build_factual_response(query: str, filters: dict, steps: list) -> dict:
    steps.append("[Factual Mode] Calling vector-search service for semantic search...")

    search_filters = {}
    if filters["product"]:
        search_filters["product"] = filters["product"]
    if filters["sentiment"]:
        search_filters["sentiment"] = filters["sentiment"]
    if filters["months"]:
        search_filters["months"] = filters["months"]

    matched_reviews = await call_semantic_search(
        query, filters=search_filters if search_filters else None, n_results=20
    )

    steps.append(f"[Vector Search] Retrieved {len(matched_reviews)} semantically similar reviews.")

    if matched_reviews:
        top_score = matched_reviews[0]["similarity_score"]
        avg_score = sum(r["similarity_score"] for r in matched_reviews) / len(matched_reviews)
        steps.append(f"[Vector Search] Similarity — Top: {top_score:.3f}, Average: {avg_score:.3f}")
        matched_reviews = [r for r in matched_reviews if r["similarity_score"] >= 0.25]
        steps.append(f"[Vector Search] After threshold (>=0.25): {len(matched_reviews)} reviews remain.")

    if not matched_reviews:
        steps.append("No semantically relevant reviews found. Aborting to prevent hallucination.")
        feedback_msg = "I do not know. "
        if filters["product"]:
            feedback_msg += f"I could not find any semantically relevant reviews for '{filters['product']}' "
        else:
            feedback_msg += "I could not find any relevant reviews "
        feedback_msg += "matching your query. As a strict rule against hallucination, I cannot answer without direct review evidence."
        return {"answer": feedback_msg, "citations": [], "execution_steps": steps}

    categories: dict = {}
    total_rating = 0
    praise_count = 0
    complaint_count = 0

    for r in matched_reviews:
        total_rating += r["rating"]
        cat = r.get("category_tag", "Other")
        if cat == "Praise" or r["rating"] >= 4:
            praise_count += 1
        else:
            complaint_count += 1
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(r)

    avg_rating = round(total_rating / len(matched_reviews), 2)
    steps.append(f"Analysis: Avg Rating={avg_rating}, Praise={praise_count}, Complaints={complaint_count}")

    prod_label = filters["product"] if filters["product"] else "consumer products"
    answer_lines = [
        f"Based on **{len(matched_reviews)} semantically matched reviews** for **{prod_label}**, "
        f"the average rating is **{avg_rating}/5.0**."
    ]

    citations = []
    citation_id_map: dict = {}

    def get_citation_num(review_id: str) -> int:
        if review_id not in citation_id_map:
            citation_id_map[review_id] = len(citation_id_map) + 1
        return citation_id_map[review_id]

    complaint_categories = [c for c in categories if c not in ("Praise", "Other")]
    if complaint_categories:
        answer_lines.append("\n### Key Customer Issues Found:")
        for cat in sorted(complaint_categories):
            cat_reviews = categories[cat][:3]
            review_refs = []
            details_list = []
            for r in cat_reviews:
                num = get_citation_num(r["review_id"])
                citations.append(r)
                review_refs.append(f"[Review #{num}]")
                snippet = r.get("complaint_snippet", r["text"][:80])
                details_list.append(f'"{snippet}"')
            answer_lines.append(
                f"- **{cat}** (similarity: {cat_reviews[0]['similarity_score']:.2f}): "
                f"Customers report {' '.join(review_refs)}: {', '.join(details_list)}."
            )

    if "Praise" in categories and filters["sentiment"] != "negative":
        answer_lines.append("\n### Customer Praise & Positive Feedback:")
        for r in categories["Praise"][:3]:
            num = get_citation_num(r["review_id"])
            citations.append(r)
            sentences = re.split(r"[.!?]+", r["text"])
            snippet = sentences[0].strip() if sentences else r["text"][:60]
            answer_lines.append(f"- [Review #{num}]: \"{snippet}\"")

    # De-duplicate and sort citations
    unique_citations = []
    seen_ids: set = set()
    for c in citations:
        if c["review_id"] not in seen_ids:
            seen_ids.add(c["review_id"])
            c_copy = c.copy()
            c_copy["citation_number"] = citation_id_map[c["review_id"]]
            unique_citations.append(c_copy)
    unique_citations.sort(key=lambda x: x["citation_number"])

    steps.append("Response synthesized with vector-retrieved citations.")
    return {"answer": "\n".join(answer_lines), "citations": unique_citations, "execution_steps": steps}


async def answer_question(query: str) -> dict:
    """Main orchestration — classify, extract, route, respond."""
    steps = [f"Received query: '{query}'"]

    query_type = classify_query(query)
    steps.append(f"[Query Classification] Type: {query_type.upper()}")

    filters = extract_entities_and_filters(query)
    steps.append(
        f"Parsed constraints: product={filters['product']}, sentiment={filters['sentiment']}, "
        f"months={filters['months']}, keywords={filters['keywords']}"
    )

    if query_type == "trend":
        return await _build_trend_response(query, filters, steps)
    else:
        # comparative falls back to factual for now
        return await _build_factual_response(query, filters, steps)


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="QA Agent Service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QARequest(BaseModel):
    query: str


@app.get("/health")
async def health():
    # Verify vector-search is reachable
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{VECTOR_SEARCH_URL}/health")
            vs_status = resp.json().get("status", "unknown")
    except Exception:
        vs_status = "unreachable"
    return {
        "status": "ok",
        "service": "qa-agent",
        "vector_search_dependency": vs_status,
    }


@app.post("/qa")
async def post_qa(req: QARequest):
    """Answer a natural language question using RAG over the review corpus."""
    try:
        result = await answer_question(req.query)
        return result
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Vector Search Service error: {exc}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8004, reload=False)
