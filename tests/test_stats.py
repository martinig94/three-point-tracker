"""Tests for the dashboard aggregations."""

from datetime import date

import pandas as pd
import pytest

from three_point_tracker.stats import (
    cumulative_totals,
    required_weekly_pace,
    weekly_totals,
    weekly_trends,
)


@pytest.fixture
def shots() -> pd.DataFrame:
    """Entries for two players; Giulia skips the week of 9 November."""
    return pd.DataFrame(
        {
            "player": ["Giulia", "Martina", "Giulia", "Giulia"],
            "shot_date": pd.to_datetime(
                ["2026-11-18", "2026-11-03", "2026-11-02", "2026-11-04"]
            ),
            "made": [9, 4, 5, 2],
        }
    )


def test_cumulative_totals_accumulates_per_player_in_date_order(
    shots: pd.DataFrame,
) -> None:
    result = cumulative_totals(shots)

    giulia = result[result["player"] == "Giulia"]
    assert giulia["total"].tolist() == [5, 7, 16]
    assert result[result["player"] == "Martina"]["total"].tolist() == [4]


def test_weekly_totals_groups_by_monday_week_and_fills_gaps(
    shots: pd.DataFrame,
) -> None:
    result = weekly_totals(shots)

    giulia = result[result["player"] == "Giulia"]
    assert giulia["week_start"].tolist() == list(
        pd.to_datetime(["2026-11-02", "2026-11-09", "2026-11-16"])
    )
    assert giulia["made"].tolist() == [7, 0, 9]


def test_weekly_trends_reports_slope_per_player(shots: pd.DataFrame) -> None:
    result = weekly_trends(weekly_totals(shots))

    assert result["Giulia"] == pytest.approx(1.0)
    assert result["Martina"] == 0.0


@pytest.mark.parametrize(
    ("total", "today", "expected"),
    [
        (50, date(2027, 5, 3), 50.0),
        (250, date(2027, 5, 3), 0.0),
        (240, date(2027, 6, 30), 10.0),
    ],
)
def test_required_weekly_pace(total: int, today: date, expected: float) -> None:
    result = required_weekly_pace(total, 250, today, date(2027, 5, 31))

    assert result == pytest.approx(expected)
