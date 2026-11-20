"""Aggregations of logged shots used by the dashboard."""

from datetime import date

import numpy as np
import pandas as pd

DAYS_PER_WEEK = 7


def cumulative_totals(shots: pd.DataFrame) -> pd.DataFrame:
    """Add each player's running total of made shots.

    Args:
        shots: DataFrame with columns player, shot_date and made

    Returns:
        The entries sorted by date with an extra total column
    """
    ordered = shots.sort_values("shot_date")
    return ordered.assign(total=ordered.groupby("player")["made"].cumsum())


def weekly_totals(shots: pd.DataFrame) -> pd.DataFrame:
    """Sum made shots per player and Monday-to-Sunday week.

    Weeks without entries between a player's first and last logged week
    count as zero, so they lower the weekly average.

    Args:
        shots: DataFrame with columns player, shot_date (datetime64) and made

    Returns:
        DataFrame with columns player, week_start (Monday) and made
    """
    return (
        shots.set_index("shot_date")
        .groupby("player")["made"]
        .resample("W-MON", closed="left", label="left")
        .sum()
        .reset_index()
        .rename(columns={"shot_date": "week_start"})
    )


def _slope(values: pd.Series) -> float:
    """Return the least-squares slope of values against their position."""
    if len(values) < 2:
        return 0.0
    return float(np.polyfit(np.arange(len(values)), values.to_numpy(), 1)[0])


def weekly_trends(weekly: pd.DataFrame) -> pd.Series:
    """Measure how each player's weekly total changes from week to week.

    Args:
        weekly: Output of weekly_totals

    Returns:
        Series indexed by player with the change in made shots per week;
        positive means increasing, negative decreasing, zero constant
    """
    return weekly.groupby("player")["made"].agg(_slope)


def required_weekly_pace(total: int, goal: int, today: date, season_end: date) -> float:
    """Compute the shots per week still needed to reach the goal in time.

    Args:
        total: Shots made so far
        goal: Shots to reach by the end of the season
        today: Current date
        season_end: Last day of the season

    Returns:
        Shots per week needed over the remaining season; zero once the goal
        is reached, the full remainder if the season is over
    """
    remaining = max(goal - total, 0)
    weeks_left = max((season_end - today).days / DAYS_PER_WEEK, 1.0)
    return remaining / weeks_left
