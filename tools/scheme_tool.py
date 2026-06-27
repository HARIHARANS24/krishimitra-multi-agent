"""
tools/scheme_tool.py
======================
Government scheme search & eligibility explanation, used by the
Government Scheme Agent. Reads from the `government_schemes` table
(see database/seed_data.py for the curated demo dataset).
"""

from __future__ import annotations

from dataclasses import dataclass

from database.db_manager import DatabaseManager


@dataclass
class SchemeMatch:
    scheme_name: str
    description: str
    eligibility: str
    benefits: str
    official_link: str | None
    relevance_note: str


def search_schemes(
    keyword: str | None = None,
    state: str | None = None,
    db: DatabaseManager | None = None,
) -> list[SchemeMatch]:
    db = db or DatabaseManager()
    rows = db.search_schemes(keyword=keyword, state=state)

    matches = []
    for row in rows:
        relevance_bits = []
        if keyword:
            relevance_bits.append(f"matched search term '{keyword}'")
        if state:
            applicable = row.get("applicable_states", "")
            if applicable == "ALL":
                relevance_bits.append("available nationwide")
            else:
                relevance_bits.append(f"available in {applicable}")
        relevance_note = "; ".join(relevance_bits) if relevance_bits else "general agriculture scheme"

        matches.append(
            SchemeMatch(
                scheme_name=row["scheme_name"],
                description=row["description"],
                eligibility=row["eligibility"],
                benefits=row["benefits"],
                official_link=row.get("official_link"),
                relevance_note=relevance_note,
            )
        )
    return matches


def explain_eligibility(scheme_name: str, farmer_profile: dict, db: DatabaseManager | None = None) -> str:
    """Produce a plain-language eligibility explanation for one scheme
    given a farmer's profile (land_area_acres, state, etc.). This is a
    rule-of-thumb explainer, not a legal determination -- the
    Coordinator Agent always surfaces the official link for the
    farmer to verify.
    """
    db = db or DatabaseManager()
    rows = db.search_schemes(keyword=scheme_name)
    if not rows:
        return f"Scheme '{scheme_name}' not found in the knowledge base. Please check the official portal."

    scheme = rows[0]
    land_area = farmer_profile.get("land_area_acres")
    state = farmer_profile.get("state")

    lines = [f"Eligibility criteria for {scheme['scheme_name']}: {scheme['eligibility']}"]

    if state and scheme.get("applicable_states") not in (None, "ALL") and state not in scheme["applicable_states"]:
        lines.append(
            f"Note: this scheme appears limited to {scheme['applicable_states']}, and your registered state is "
            f"{state}. Please verify on the official portal, as eligibility rules can change."
        )
    else:
        lines.append("Based on your profile, you likely meet the general eligibility criteria.")

    if land_area is not None and land_area > 5 and "small and marginal" in scheme["eligibility"].lower():
        lines.append(
            f"Note: your farm size ({land_area} acres) is larger than the 'small and marginal farmer' "
            "category typically referenced by this scheme -- benefit amounts or eligibility may differ."
        )

    lines.append("Always confirm final eligibility on the official scheme portal before applying.")
    return " ".join(lines)
