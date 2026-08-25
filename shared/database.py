import json
import sqlite3
import os
import re

SHARED_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(SHARED_DIR, "reviews.json")
DB_PATH = os.path.join(SHARED_DIR, "reviews.db")

COMPLAINT_TEMPLATES = [
    {
        "tag": "Switch Melting",
        "keywords": [r"switch", r"swich", r"button", r"toggle", r"melt", r"burnt", r"burn", r"fire", r"hazard"],
        "min_matches": 2,
    },
    {
        "tag": "Blower Grinding Noise",
        "keywords": [r"blower", r"fan", r"noise", r"noice", r"grinding", r"rattle", r"rattling", r"squeak", r"loose"],
        "min_matches": 2,
    },
    {
        "tag": "Clicking Sound",
        "keywords": [r"click", r"clicking", r"tick", r"ticking", r"sound", r"noise", r"noice", r"rhythmic"],
        "min_matches": 2,
    },
    {
        "tag": "Wobbling Regulator",
        "keywords": [r"wobble", r"woble", r"shake", r"shakes", r"vibrate", r"vibration", r"mounting", r"rod", r"unstable"],
        "min_matches": 2,
    },
    {
        "tag": "Filter Light Bug",
        "keywords": [r"filter", r"filtr", r"light", r"indicator", r"red", r"reset", r"sensor", r"stuck"],
        "min_matches": 2,
    },
    {
        "tag": "Chemical Odor",
        "keywords": [r"chemical", r"smell", r"odor", r"odour", r"plastic", r"ozone", r"glue", r"scent"],
        "min_matches": 2,
    },
]

def extract_complaint_snippet(text: str, keywords: list) -> str:
    sentences = re.split(r"[.!?]+", text)
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if any(re.search(r"\b" + kw, sentence, re.IGNORECASE) for kw in keywords):
            return sentence
    return text[:80] + "..." if len(text) > 80 else text

def enrich_review(r: dict):
    text = r["text"]
    is_praise = r["rating"] >= 4
    matched_tag = None
    matched_snippet = ""

    for tmpl in COMPLAINT_TEMPLATES:
        matches = sum(
            1 for kw in tmpl["keywords"]
            if re.search(r"\b" + kw, text, re.IGNORECASE)
        )
        if matches >= tmpl["min_matches"]:
            matched_tag = tmpl["tag"]
            matched_snippet = extract_complaint_snippet(text, tmpl["keywords"])
            break

    if matched_tag:
        r["category_tag"] = matched_tag
        r["complaint_snippet"] = matched_snippet
    elif is_praise:
        r["category_tag"] = "Praise"
        r["complaint_snippet"] = ""
    else:
        r["category_tag"] = "Other Complaints"
        r["complaint_snippet"] = text[:60] + "..."
    
    return r

def setup_database():
    print(f"Setting up SQLite database at {DB_PATH}")
    
    # Remove existing DB if we want a fresh migration
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create reviews table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            review_id TEXT PRIMARY KEY,
            product TEXT,
            model TEXT,
            rating INTEGER,
            date TEXT,
            year_month TEXT,
            reviewer TEXT,
            text TEXT,
            category_tag TEXT,
            complaint_snippet TEXT
        )
    ''')
    
    # Create an index on date for faster time-series queries
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_reviews_date ON reviews(date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_reviews_year_month ON reviews(year_month)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_reviews_rating ON reviews(rating)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_reviews_product ON reviews(product)')

    try:
        with open(JSON_PATH, "r") as f:
            reviews = json.load(f)
    except FileNotFoundError:
        print("reviews.json not found. Database created but empty.")
        conn.close()
        return

    print(f"Migrating {len(reviews)} reviews...")
    count = 0
    for r in reviews:
        r = enrich_review(r)
        
        # derive year_month for fast grouping (e.g. '2026-01')
        year_month = r["date"][:7] 
        
        cursor.execute('''
            INSERT INTO reviews (review_id, product, model, rating, date, year_month, reviewer, text, category_tag, complaint_snippet)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            r["review_id"],
            r["product"],
            r["model"],
            r["rating"],
            r["date"],
            year_month,
            r["reviewer"],
            r["text"],
            r["category_tag"],
            r["complaint_snippet"]
        ))
        count += 1

    conn.commit()
    conn.close()
    print(f"Migration complete. {count} rows inserted.")

if __name__ == "__main__":
    setup_database()
