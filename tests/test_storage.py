"""Tests for shot persistence, run against an in-memory database."""

from datetime import date

import pandas as pd
import pytest
from sqlalchemy import Engine, create_engine

from three_point_tracker.storage import create_tables, load_shots, log_shots


@pytest.fixture
def engine() -> Engine:
    """In-memory SQLite engine with the schema created."""
    memory_engine = create_engine("sqlite://")
    create_tables(memory_engine)
    return memory_engine


def test_load_shots_returns_logged_entries(engine: Engine) -> None:
    log_shots(engine, "Giulia", date(2026, 11, 20), 12)

    result = load_shots(engine)

    assert result.to_dict("records") == [
        {"player": "Giulia", "shot_date": pd.Timestamp("2026-11-20"), "made": 12}
    ]


def test_log_shots_replaces_entry_for_same_player_and_date(engine: Engine) -> None:
    log_shots(engine, "Giulia", date(2026, 11, 20), 12)
    log_shots(engine, "Martina", date(2026, 11, 20), 7)

    log_shots(engine, "Giulia", date(2026, 11, 20), 15)

    result = load_shots(engine).set_index("player")["made"]
    assert result.to_dict() == {"Giulia": 15, "Martina": 7}


def test_log_shots_rejects_negative_count(engine: Engine) -> None:
    with pytest.raises(ValueError, match="non-negative"):
        log_shots(engine, "Giulia", date(2026, 11, 20), -1)
