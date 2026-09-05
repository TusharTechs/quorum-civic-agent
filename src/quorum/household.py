"""The household profile that stake matching reasons against."""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROFILE = PROJECT_ROOT / "config" / "household.json"


def load_profile(path: Path | None = None) -> dict:
    return json.loads((path or DEFAULT_PROFILE).read_text(encoding="utf-8"))


def describe(profile: dict) -> str:
    """Render the profile as prose for a model prompt."""
    people = "; ".join(
        ", ".join(f"{k}={v}" for k, v in person.items())
        for person in profile.get("household", [])
    )
    return (
        f"Address: {profile['address']} (Council District {profile['council_district']})\n"
        f"Tenure: {profile['tenure']}, dwelling {profile['dwelling_sqft']} sq ft, "
        f"assessed ${profile['assessed_value_usd']:,}\n"
        f"Parking: {profile['parking']}; vehicles: {profile['vehicles']}\n"
        f"Mobility needs: {profile['mobility_needs']}\n"
        f"People: {people}\n"
        f"Stated interests: {', '.join(profile['stated_interests'])}"
    )
