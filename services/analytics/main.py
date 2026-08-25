"""
Analytics Service — Port 8003
Provides dashboard summaries, complaint trend analysis, and product breakdowns using SQLite.
"""
import os
import sqlite3
from collections import defaultdict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ── Paths ─────────────────────────────────────────────────────────────────────
SHARED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
DB_PATH = os.path.join(SHARED_DIR, "reviews.db")

# ── Complaint templates (just for titles now) ─────────────────────────────────
COMPLAINT_TITLES = {
    "Switch Melting": "Power Switch Overheating & Melting",
    "Blower Grinding Noise": "Blower Fan Mechanical Noise & Rattling",
    "Clicking Sound": "Ceiling Fan Motor Clicking & Ticking",
    "Wobbling Regulator": "Ceiling Fan Wobbling & High-Speed Vibration",
    "Filter Light Bug": "Filter Indicator Light Sensor Bug",
    "Chemical Odor": "Filter Plastic & Chemical Odor Emission",
}

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_dashboard_summary() -> dict:
    conn = get_db_connection()
    
    # Total reviews and average rating
    row = conn.execute("SELECT COUNT(*) as total, AVG(rating) as avg_rating FROM reviews").fetchone()
    total_reviews = row["total"] or 0
    avg_rating = row["avg_rating"] or 0.0
    
    # Ratings breakdown
    ratings_rows = conn.execute("SELECT rating, COUNT(*) as count FROM reviews GROUP BY rating").fetchall()
    ratings_breakdown = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for r in ratings_rows:
        ratings_breakdown[r["rating"]] = r["count"]
        
    # Product breakdown
    prod_rows = conn.execute("""
        SELECT product, COUNT(*) as count, AVG(rating) as avg_rating,
               SUM(CASE WHEN rating <= 2 THEN 1 ELSE 0 END) as neg_count
        FROM reviews
        GROUP BY product
    """).fetchall()
    
    product_breakdown = {}
    for r in prod_rows:
        product_breakdown[r["product"]] = {
            "count": r["count"],
            "avg_rating": round(r["avg_rating"], 1),
            "negative_rate_pct": round((r["neg_count"] / r["count"]) * 100, 1) if r["count"] > 0 else 0.0
        }
        
    # Complaint Trends (monthly aggregation in SQL)
    trend_rows = conn.execute("""
        SELECT category_tag, year_month as month, COUNT(*) as count, AVG(rating) as avg_rating
        FROM reviews
        WHERE category_tag != 'Praise' AND category_tag != 'Other Complaints'
        GROUP BY category_tag, year_month
        ORDER BY category_tag, year_month
    """).fetchall()
    
    # Group the results by tag
    grouped_trends = defaultdict(list)
    for r in trend_rows:
        grouped_trends[r["category_tag"]].append({
            "month": r["month"],
            "count": r["count"],
            "avg_rating": round(r["avg_rating"], 1)
        })
        
    # Calculate velocity and alerts
    trends = []
    alerts = []
    
    for tag, monthly_data in grouped_trends.items():
        total_count = sum(m["count"] for m in monthly_data)
        
        # Calculate total avg rating for the tag across all months
        tag_avg_row = conn.execute(
            "SELECT AVG(rating) as avg_rt FROM reviews WHERE category_tag = ?", (tag,)
        ).fetchone()
        tag_avg = tag_avg_row["avg_rt"] or 0.0
        
        velocity = 0.0
        status = "Stable"
        if len(monthly_data) >= 2:
            prev_cnt = monthly_data[-2]["count"]
            curr_cnt = monthly_data[-1]["count"]
            velocity = ((curr_cnt - prev_cnt) / prev_cnt * 100) if prev_cnt > 0 else curr_cnt * 100.0
            if velocity > 10.0:
                status = "Rising"
            elif velocity < -10.0:
                status = "Falling"
                
        title = COMPLAINT_TITLES.get(tag, tag)
        is_alert = status == "Rising" and tag_avg < 2.5
        
        trend_obj = {
            "tag": tag,
            "title": title,
            "total_count": total_count,
            "avg_rating": round(tag_avg, 1),
            "velocity_pct": round(velocity, 1),
            "status": status,
            "monthly_data": monthly_data,
            "is_alert": is_alert
        }
        trends.append(trend_obj)
        
        if is_alert:
            alerts.append({
                "tag": tag,
                "title": title,
                "total_count": total_count,
                "velocity_pct": round(velocity, 1),
                "avg_rating": round(tag_avg, 1)
            })

    conn.close()

    return {
        "total_reviews": total_reviews,
        "avg_rating": round(avg_rating, 2),
        "ratings_breakdown": ratings_breakdown,
        "product_breakdown": product_breakdown,
        "complaint_trends": trends,
        "alerts": alerts,
    }


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Analytics Service", version="1.0.0")
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
        return {"status": "ok", "service": "analytics", "review_count": count}
    except Exception as e:
        return {"status": "error", "service": "analytics", "error": str(e)}

@app.get("/dashboard")
def dashboard():
    """Return full dashboard summary using SQL aggregation."""
    return get_dashboard_summary()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8003, reload=False)
