import json
import random
from datetime import datetime, timedelta

# Seed for reproducibility
random.seed(42)

PRODUCTS = {
    "Space Heater": {
        "models": ["Calido PTC 2000W", "Solace 1500W Oil Filled", "OFR 11 Wave"],
        "complaints": [
            {
                "tag": "Switch Melting",
                "phrases": [
                    "the switch melted after 2 hours of use, very dangerous!",
                    "smell of burning plastic and found the power switch was completely melted.",
                    "switch got extremely hot and then melted down. cheap quality toggle.",
                    "dangerous product! the main button melted and fused. fire hazard!",
                    "switch button burnt and melted within a month. had to return it."
                ],
                "months": [11, 12, 1, 2],  # Winter months (Nov, Dec, Jan, Feb)
                "rating_range": (1, 2)
            },
            {
                "tag": "Blower Grinding Noise",
                "phrases": [
                    "blower fan makes a loud grinding noise, cannot sleep with this on.",
                    "heating works but there is a constant rattling sound from the blower.",
                    "fan inside rattles and clicks. very annoying background noise.",
                    "noisy blower! sounds like something is loose inside.",
                    "vibrates a lot and makes a squeaking sound at high speed."
                ],
                "months": [10, 11, 12, 1, 2, 3],
                "rating_range": (2, 3)
            }
        ],
        "praise": [
            "heats up the room very quickly. love the rotating base.",
            "compact and powerful. keeps my bedroom warm all night.",
            "great safety features, it shuts off when tipped over.",
            "good build quality and silent operation. worth the money.",
            "excellent heating. remote control is very handy."
        ]
    },
    "Ceiling Fan": {
        "models": ["Florence 1200mm", "Efficiencia Neo energy saving", "Stealth Air Premium"],
        "complaints": [
            {
                "tag": "Clicking Sound",
                "phrases": [
                    "makes an annoying clicking noise at speed 3 and 4. click click click all night.",
                    "ticking sound coming from the motor canopy. very distracting.",
                    "perfect fan but has a rhythmic clicking sound that is frustrating.",
                    "constant clicking noise when regulator is set to medium.",
                    "motor makes a faint clicking or ticking sound when running."
                ],
                "months": [3, 4, 5, 6, 7, 8],  # Summer months (Mar - Aug)
                "rating_range": (2, 3)
            },
            {
                "tag": "Wobbling Regulator",
                "phrases": [
                    "fan wobbles like crazy at speed 5. looks like it will fall down.",
                    "shakes and wobbles. mounting rod is not stable.",
                    "excessive vibration at high speed, regulator doesn't seem to control it well.",
                    "wobbling issue right out of the box. installer tried to balance it but failed.",
                    "shakes a lot on full speed, makes creaking sounds from the ceiling."
                ],
                "months": [4, 5, 6, 7, 8],
                "rating_range": (1, 3)
            }
        ],
        "praise": [
            "very stylish fan, looks premium in my living room.",
            "absolutely silent and high air delivery. energy saving is a plus.",
            "easy to install and works perfectly with the smart remote.",
            "breeze is powerful. quality shines through.",
            "very quiet motor and modern aesthetic."
        ]
    },
    "Air Purifier": {
        "models": ["Freshia AP-40", "Freshia AP-20", "Studio Meditate"],
        "complaints": [
            {
                "tag": "Filter Light Bug",
                "phrases": [
                    "changed the filter but the red replacement light won't reset or turn off.",
                    "filter light stays solid red even after putting in a brand new genuine filter.",
                    "reset button for the filter light does not work. sensor issue.",
                    "red light for filter change is stuck. reset instructions in manual don't work.",
                    "solid red filter indicator light won't turn off. air flow is fine though."
                ],
                "months": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],  # Year-round
                "rating_range": (2, 3)
            },
            {
                "tag": "Chemical Odor",
                "phrases": [
                    "blows out a weird chemical plastic smell. makes my eyes water.",
                    "strange odor from the new filter, smells like chemical glue.",
                    "purifier works but emits a plastic/ozone-like smell on turbo mode.",
                    "smell of chemicals for the first few days of use. very unpleasant.",
                    "emits a chemical scent. filter needs to be aired out first."
                ],
                "months": [10, 11, 12, 1],  # Winter smog season (Oct - Jan) when sales peak
                "rating_range": (1, 3)
            }
        ],
        "praise": [
            "clears smoke and cooking odors in minutes. sleep mode is dead silent.",
            "digital AQI display is very accurate. notice a huge difference in my allergies.",
            "sleek design, looks like a premium speaker. auto mode works great.",
            "great air purifier. filter is easy to change and value for money.",
            "essential for winters. clears Delhi pollution and smog effortlessly."
        ]
    }
}

NAMES = [
    "Aarav Sharma", "Aditya Patel", "Amit Singh", "Ananya Sen", "Arjun Mehta", 
    "Devika Nair", "Ishaan Joshi", "Kabir Gupta", "Meera Rao", "Neha Verma",
    "Pranav Kulkarni", "Rohan Das", "Siddharth Reddy", "Tanvi Bhatia", "Vikram Malhotra",
    "Sneha Iyer", "Rahul Bose", "Pooja Trivedi", "Rajesh Kapoor", "Divya Pillai"
]

MESSY_PREFIXES = [
    "so, ", "hey, ", "actually ", "buying this was a mistake. ", "honestly, ", 
    "very disappointed! ", "Super happy! ", "writing this after 3 weeks of usage. ",
    "i usually don't write reviews but ", "good brand but "
]

MESSY_SUFFIXES = [
    "!!", "...", " absolute waste of money.", " hope customer care calls me.",
    " highly recommended.", " not happy at all.", " buy something else.",
    " pros: looks good. cons: fails after some time.", " 👍", " 👎"
]

def generate_reviews():
    reviews = []
    current_date = datetime(2026, 7, 15)  # Let's say current date is July 15, 2026
    start_date = current_date - timedelta(days=365) # Span 1 year back
    
    review_id_counter = 1000
    
    # We want around 220 reviews in total, distributed across products
    for product_type, config in PRODUCTS.items():
        # Generate ~75 reviews per product type
        num_reviews = random.randint(70, 80)
        
        for _ in range(num_reviews):
            # Decide if it's a complaint or a praise (approx 55% complaints, 45% praise for testing trends)
            is_complaint = random.random() < 0.55
            
            # Select random date within the 1-year window
            delta_days = random.randint(0, 365)
            r_date = start_date + timedelta(days=delta_days)
            r_month = r_date.month
            
            model = random.choice(config["models"])
            reviewer = random.choice(NAMES)
            
            text_parts = []
            if random.random() < 0.5:
                text_parts.append(random.choice(MESSY_PREFIXES))
                
            tag = "Praise"
            
            if is_complaint:
                # Find complaints that fit this month or fall back to any complaint
                valid_complaints = [c for c in config["complaints"] if r_month in c["months"]]
                if not valid_complaints:
                    valid_complaints = config["complaints"]
                
                selected_complaint = random.choice(valid_complaints)
                tag = selected_complaint["tag"]
                phrase = random.choice(selected_complaint["phrases"])
                text_parts.append(phrase)
                rating = random.randint(*selected_complaint["rating_range"])
            else:
                phrase = random.choice(config["praise"])
                text_parts.append(phrase)
                rating = random.randint(4, 5)
                
            if random.random() < 0.5:
                text_parts.append(random.choice(MESSY_SUFFIXES))
                
            # Clean text formatting slightly, but keep typos
            text = " ".join(text_parts)
            # Add occasional random typos
            if random.random() < 0.3:
                text = text.replace("switch", "swich").replace("noise", "noice").replace("wobble", "woble").replace("filter", "filtr")
                
            reviews.append({
                "review_id": f"REV-{review_id_counter}",
                "product": product_type,
                "model": model,
                "rating": rating,
                "date": r_date.strftime("%Y-%m-%d"),
                "reviewer": reviewer,
                "text": text,
                "category_tag": tag
            })
            review_id_counter += 1
            
    # Sort reviews by date descending
    reviews.sort(key=lambda x: x["date"], reverse=True)
    
    with open("reviews.json", "w") as f:
        json.dump(reviews, f, indent=2)
        
    print(f"Successfully generated {len(reviews)} reviews and saved to reviews.json")

if __name__ == "__main__":
    generate_reviews()
