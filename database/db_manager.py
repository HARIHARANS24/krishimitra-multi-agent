"""
database/db_manager.py
========================
Thin, dependency-light data access layer over SQLite.

Security note: every query in this module uses parameterized
placeholders ("?") -- never raw string interpolation -- so user input
can never alter SQL structure (defense against SQL injection), even
though security/input_validation.py already sanitizes inputs upstream.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

from config.settings import settings

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


class DatabaseManager:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or settings.database_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _ensure_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    # ------------------------------------------------------------------
    # Generic helpers
    # ------------------------------------------------------------------
    def execute(self, query: str, params: Iterable[Any] = ()) -> int:
        with self.connect() as conn:
            cur = conn.execute(query, tuple(params))
            return cur.lastrowid

    def fetch_all(self, query: str, params: Iterable[Any] = ()) -> list[dict]:
        with self.connect() as conn:
            cur = conn.execute(query, tuple(params))
            return [dict(row) for row in cur.fetchall()]

    def fetch_one(self, query: str, params: Iterable[Any] = ()) -> dict | None:
        with self.connect() as conn:
            cur = conn.execute(query, tuple(params))
            row = cur.fetchone()
            return dict(row) if row else None

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------
    def create_user(self, display_name: str, phone_hash: str | None, preferred_language: str = "en") -> int:
        return self.execute(
            "INSERT INTO users (display_name, phone_hash, preferred_language) VALUES (?, ?, ?)",
            (display_name, phone_hash, preferred_language),
        )

    def get_user(self, user_id: int) -> dict | None:
        return self.fetch_one("SELECT * FROM users WHERE user_id = ?", (user_id,))

    # ------------------------------------------------------------------
    # Farm profiles
    # ------------------------------------------------------------------
    def create_farm_profile(
        self,
        user_id: int,
        farm_name: str,
        region: str,
        soil_type: str,
        land_area_acres: float,
        district: str | None = None,
        state: str | None = None,
        irrigation_source: str | None = None,
    ) -> int:
        return self.execute(
            """INSERT INTO farm_profiles
               (user_id, farm_name, region, district, state, soil_type, land_area_acres, irrigation_source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, farm_name, region, district, state, soil_type, land_area_acres, irrigation_source),
        )

    def get_farm_profiles_for_user(self, user_id: int) -> list[dict]:
        return self.fetch_all("SELECT * FROM farm_profiles WHERE user_id = ?", (user_id,))

    # ------------------------------------------------------------------
    # Crop history
    # ------------------------------------------------------------------
    def add_crop_history(self, farm_id: int, crop_name: str, season: str, **kwargs) -> int:
        return self.execute(
            """INSERT INTO crop_history (farm_id, crop_name, season, sown_date, harvest_date, yield_kg, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                farm_id,
                crop_name,
                season,
                kwargs.get("sown_date"),
                kwargs.get("harvest_date"),
                kwargs.get("yield_kg"),
                kwargs.get("notes"),
            ),
        )

    def get_crop_history(self, farm_id: int) -> list[dict]:
        return self.fetch_all(
            "SELECT * FROM crop_history WHERE farm_id = ? ORDER BY created_at DESC", (farm_id,)
        )

    # ------------------------------------------------------------------
    # Weather logs
    # ------------------------------------------------------------------
    def log_weather(self, region: str, observed_date: str, **kwargs) -> int:
        return self.execute(
            """INSERT INTO weather_logs (region, observed_date, temperature_c, rainfall_mm, humidity_pct,
               forecast_summary, source) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                region,
                observed_date,
                kwargs.get("temperature_c"),
                kwargs.get("rainfall_mm"),
                kwargs.get("humidity_pct"),
                kwargs.get("forecast_summary"),
                kwargs.get("source", "simulated"),
            ),
        )

    def get_recent_weather(self, region: str, limit: int = 7) -> list[dict]:
        return self.fetch_all(
            "SELECT * FROM weather_logs WHERE region = ? ORDER BY observed_date DESC LIMIT ?",
            (region, limit),
        )

    # ------------------------------------------------------------------
    # Advisory logs (explainability audit trail)
    # ------------------------------------------------------------------
    def log_advisory(
        self,
        agent_name: str,
        query_text: str,
        recommendation: str,
        confidence_score: float,
        reasoning: dict,
        user_id: int | None = None,
        farm_id: int | None = None,
    ) -> int:
        return self.execute(
            """INSERT INTO advisory_logs
               (user_id, farm_id, agent_name, query_text, recommendation, confidence_score, reasoning_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                farm_id,
                agent_name,
                query_text,
                recommendation,
                confidence_score,
                json.dumps(reasoning, ensure_ascii=False),
            ),
        )

    def get_advisory_history(self, user_id: int, limit: int = 20) -> list[dict]:
        return self.fetch_all(
            "SELECT * FROM advisory_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        )

    # ------------------------------------------------------------------
    # Market data
    # ------------------------------------------------------------------
    def upsert_market_price(
        self, crop_name: str, market_name: str, region: str, price_per_quintal: float, price_date: str, trend: str
    ) -> int:
        return self.execute(
            """INSERT INTO market_data (crop_name, market_name, region, price_per_quintal, price_date, trend)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (crop_name, market_name, region, price_per_quintal, price_date, trend),
        )

    def get_market_prices(self, crop_name: str, region: str | None = None) -> list[dict]:
        if region:
            return self.fetch_all(
                "SELECT * FROM market_data WHERE crop_name = ? AND region = ? ORDER BY price_date DESC",
                (crop_name, region),
            )
        return self.fetch_all(
            "SELECT * FROM market_data WHERE crop_name = ? ORDER BY price_date DESC", (crop_name,)
        )

    # ------------------------------------------------------------------
    # Government schemes
    # ------------------------------------------------------------------
    def search_schemes(self, keyword: str | None = None, state: str | None = None) -> list[dict]:
        query = "SELECT * FROM government_schemes WHERE 1=1"
        params: list[Any] = []
        if keyword:
            query += " AND (scheme_name LIKE ? OR description LIKE ? OR eligibility LIKE ?)"
            like = f"%{keyword}%"
            params.extend([like, like, like])
        if state:
            query += " AND (applicable_states LIKE ? OR applicable_states = 'ALL')"
            params.append(f"%{state}%")
        return self.fetch_all(query, params)

    def add_scheme(self, scheme_name: str, description: str, eligibility: str, benefits: str, **kwargs) -> int:
        return self.execute(
            """INSERT INTO government_schemes
               (scheme_name, description, eligibility, benefits, applicable_states, official_link)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                scheme_name,
                description,
                eligibility,
                benefits,
                kwargs.get("applicable_states", "ALL"),
                kwargs.get("official_link"),
            ),
        )


# A module-level singleton for convenience in the Streamlit app / agents.
db = DatabaseManager()
