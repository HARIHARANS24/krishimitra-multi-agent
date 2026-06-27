"""
database/seed_data.py
=======================
Populates a fresh database with realistic demo data so the Streamlit
app and tests have something to show immediately, without needing
live API keys. Run directly: `python -m database.seed_data`
"""

from __future__ import annotations

from datetime import date, timedelta

from database.db_manager import DatabaseManager

SAMPLE_SCHEMES = [
    dict(
        scheme_name="PM-KISAN",
        description="Income support of Rs. 6000/year paid in three installments directly to "
        "small and marginal farmer families.",
        eligibility="All landholding farmer families, subject to exclusion criteria for "
        "higher-income categories and institutional landholders.",
        benefits="Rs. 2000 every 4 months via direct bank transfer.",
        applicable_states="ALL",
        official_link="https://pmkisan.gov.in",
    ),
    dict(
        scheme_name="Pradhan Mantri Fasal Bima Yojana (PMFBY)",
        description="Crop insurance scheme protecting farmers against yield loss due to "
        "natural calamities, pests, and diseases.",
        eligibility="All farmers growing notified crops in notified areas, including "
        "sharecroppers and tenant farmers.",
        benefits="Low premium (2% for Kharif, 1.5% for Rabi); claim payouts on assessed loss.",
        applicable_states="ALL",
        official_link="https://pmfby.gov.in",
    ),
    dict(
        scheme_name="Soil Health Card Scheme",
        description="Provides farmers with soil nutrient status and fertilizer "
        "recommendations every two years.",
        eligibility="All farmers; cards issued through state agriculture departments.",
        benefits="Free soil testing and tailored fertilizer/nutrient recommendations.",
        applicable_states="ALL",
        official_link="https://soilhealth.dac.gov.in",
    ),
    dict(
        scheme_name="Tamil Nadu Micro Irrigation Subsidy",
        description="Subsidy for drip and sprinkler irrigation systems to improve water-use "
        "efficiency.",
        eligibility="Farmers in Tamil Nadu with valid land records; priority to small/marginal "
        "farmers.",
        benefits="Up to 100% subsidy for small/marginal farmers, 75% for others, depending on "
        "category.",
        applicable_states="Tamil Nadu",
        official_link="https://tnhorticulture.tn.gov.in",
    ),
    dict(
        scheme_name="Kisan Credit Card (KCC)",
        description="Provides farmers with timely access to credit for cultivation and "
        "allied needs.",
        eligibility="All farmers including tenant farmers, oral lessees, and self-help group "
        "members.",
        benefits="Flexible credit limit, interest subvention up to Rs. 3 lakh.",
        applicable_states="ALL",
        official_link="https://www.myscheme.gov.in/schemes/kcc",
    ),
]

SAMPLE_MARKET_DATA = [
    # crop_name, market_name, region, price_per_quintal, days_ago, trend
    ("Groundnut", "Tirunelveli Mandi", "Tirunelveli", 6200, 0, "rising"),
    ("Groundnut", "Tirunelveli Mandi", "Tirunelveli", 6050, 7, "rising"),
    ("Cotton", "Madurai Mandi", "Madurai", 7100, 0, "stable"),
    ("Cotton", "Madurai Mandi", "Madurai", 7150, 7, "stable"),
    ("Paddy", "Thanjavur Mandi", "Thanjavur", 2150, 0, "falling"),
    ("Millet", "Coimbatore Mandi", "Coimbatore", 3300, 0, "rising"),
    ("Sugarcane", "Erode Mandi", "Erode", 3450, 0, "stable"),
    ("Banana", "Tirunelveli Mandi", "Tirunelveli", 1800, 0, "rising"),
]


def seed(db: DatabaseManager | None = None) -> None:
    db = db or DatabaseManager()

    if not db.search_schemes():
        for scheme in SAMPLE_SCHEMES:
            db.add_scheme(**scheme)
        print(f"Seeded {len(SAMPLE_SCHEMES)} government schemes.")

    existing_market = db.fetch_all("SELECT COUNT(*) as c FROM market_data")
    if existing_market and existing_market[0]["c"] == 0:
        for crop, market, region, price, days_ago, trend in SAMPLE_MARKET_DATA:
            price_date = (date.today() - timedelta(days=days_ago)).isoformat()
            db.upsert_market_price(crop, market, region, price, price_date, trend)
        print(f"Seeded {len(SAMPLE_MARKET_DATA)} market price rows.")

    # Demo user + farm profile, useful for local dev / screenshots.
    existing_user = db.fetch_one("SELECT * FROM users WHERE display_name = ?", ("Demo Farmer",))
    if not existing_user:
        user_id = db.create_user(display_name="Demo Farmer", phone_hash=None, preferred_language="en")
        db.create_farm_profile(
            user_id=user_id,
            farm_name="Demo Farm",
            region="Tirunelveli",
            soil_type="red",
            land_area_acres=3.5,
            district="Tirunelveli",
            state="Tamil Nadu",
            irrigation_source="borewell",
        )
        print("Seeded demo user and farm profile.")


if __name__ == "__main__":
    seed()
