"""
tests/conftest.py
====================
Shared pytest fixtures: an isolated, seeded SQLite database per test
session so tests never touch the real database file.
"""

from __future__ import annotations

import pytest

from database.db_manager import DatabaseManager
from database.seed_data import seed


@pytest.fixture()
def test_db(tmp_path):
    db_path = tmp_path / "test_krishimitra.db"
    db = DatabaseManager(db_path=str(db_path))
    seed(db)
    return db


@pytest.fixture()
def sample_farm_context():
    return {
        "region": "Tirunelveli",
        "soil_type": "red",
        "season": "kharif",
        "rainfall_mm": 850,
        "crop_name": "Groundnut",
        "state": "Tamil Nadu",
        "land_area_acres": 3.5,
    }
