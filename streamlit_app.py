"""Streamlit app to log made three-point shots and track the season goal."""

import os
from datetime import date

import altair as alt
import pandas as pd
import streamlit as st
from sqlalchemy import Engine, create_engine

from three_point_tracker.stats import (
    cumulative_totals,
    required_weekly_pace,
    weekly_totals,
    weekly_trends,
)
from three_point_tracker.storage import create_tables, load_shots, log_shots

PLAYERS = ("Giulia", "Martina")
TEAM = "Together"
GOAL = 250
SEASON_END = date(2027, 5, 31)
DEFAULT_DATABASE_URL = "sqlite:///shots.db"


@st.cache_resource
def get_engine() -> Engine:
    """Connect to the database named by DATABASE_URL and ensure its schema.

    Returns:
        SQLAlchemy engine shared by all sessions
    """
    engine = create_engine(
        os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL), pool_pre_ping=True
    )
    create_tables(engine)
    return engine


st.set_page_config(
    page_title="Three-point tracker", page_icon=":material/sports_basketball:"
)
st.title("Three-point tracker")
st.caption(f"Goal: {GOAL} made threes together by {SEASON_END:%d %B %Y}")

engine = get_engine()

with st.form("log_shots", border=True):
    player = st.segmented_control(
        "Player", PLAYERS, default=PLAYERS[0], required=True, key="player"
    )
    shot_date = st.date_input("Date", max_value="today", key="shot_date")
    made = st.number_input("Threes made", min_value=0, step=1, key="made")
    if st.form_submit_button("Save", type="primary", icon=":material/save:"):
        log_shots(engine, player, shot_date, made)
        st.toast(f"Saved {made} threes for {player} on {shot_date:%d %b}")

shots = load_shots(engine)
if shots.empty:
    st.info("No shots logged yet. Add the first entry above.")
    st.stop()

team_shots = (
    shots.groupby("shot_date", as_index=False)["made"].sum().assign(player=TEAM)
)
all_shots = pd.concat([team_shots, shots])
weekly = weekly_totals(all_shots)
team_weekly = weekly.loc[weekly["player"] == TEAM, "made"]
team_trend = weekly_trends(weekly)[TEAM]
totals = all_shots.groupby("player")["made"].sum()

with st.container(border=True):
    total_column, average_column, pace_column = st.columns(3)
    total_column.metric(
        "Total made",
        f"{totals[TEAM]} / {GOAL}",
        delta=", ".join(f"{name} {totals[name]}" for name in totals.index.drop(TEAM)),
        delta_arrow="off",
        delta_color="off",
    )
    average_column.metric(
        "Weekly average",
        f"{team_weekly.mean():.1f}",
        delta=f"{team_trend:+.1f} per week",
        delta_arrow="off" if team_trend == 0 else "auto",
        delta_color="off" if team_trend == 0 else "normal",
    )
    pace = required_weekly_pace(int(totals[TEAM]), GOAL, date.today(), SEASON_END)
    pace_column.metric(
        "Needed per week",
        f"{pace:.1f}",
        delta=f"{max(GOAL - totals[TEAM], 0)} to go",
        delta_arrow="off",
        delta_color="off",
    )

series_order = [TEAM, *PLAYERS]
series_color = alt.Color("player:N", title=None, scale=alt.Scale(domain=series_order))

st.subheader("Progress towards the goal")
progress = (
    alt.Chart(cumulative_totals(all_shots))
    .mark_line(point=True)
    .encode(
        x=alt.X("shot_date:T", title="Date"),
        y=alt.Y("total:Q", title="Threes made"),
        color=series_color,
        tooltip=["player", "shot_date", "made", "total"],
    )
)
goal_line = (
    alt.Chart(pd.DataFrame({"goal": [GOAL]}))
    .mark_rule(strokeDash=[6, 4])
    .encode(y="goal:Q")
)
st.altair_chart(progress + goal_line, alt=f"Cumulative threes made against {GOAL}")

st.subheader("Weekly breakdown")
weekly_lines = (
    alt.Chart(weekly)
    .mark_line(point=True)
    .encode(
        x=alt.X("week_start:T", title="Week starting"),
        y=alt.Y("made:Q", title="Threes made"),
        color=series_color,
        tooltip=["player", "week_start", "made"],
    )
)
team_trend_line = (
    alt.Chart(weekly[weekly["player"] == TEAM])
    .transform_regression("week_start", "made", groupby=["player"])
    .mark_line(strokeDash=[6, 4], opacity=0.6)
    .encode(x="week_start:T", y="made:Q", color=series_color)
)
st.caption("The dashed line shows the trend of the combined weekly total.")
st.altair_chart(
    weekly_lines + team_trend_line, alt="Threes made per week with combined trend"
)
