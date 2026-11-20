"""Persistence of logged three-point shots in a SQL database."""

from datetime import date

import pandas as pd
from sqlalchemy import (
    Column,
    Date,
    Engine,
    Integer,
    MetaData,
    String,
    Table,
    delete,
    insert,
    select,
)

METADATA = MetaData()
SHOTS_TABLE = Table(
    "shots",
    METADATA,
    Column("player", String, primary_key=True),
    Column("shot_date", Date, primary_key=True),
    Column("made", Integer, nullable=False),
)


def create_tables(engine: Engine) -> None:
    """Create the shots table if it does not exist yet.

    Args:
        engine: SQLAlchemy engine connected to the tracker database
    """
    METADATA.create_all(engine)


def log_shots(engine: Engine, player: str, shot_date: date, made: int) -> None:
    """Store the shots a player made on a date, replacing any earlier entry.

    Args:
        engine: SQLAlchemy engine connected to the tracker database
        player: Name of the player who took the shots
        shot_date: Day the shots were made
        made: Number of three-point shots made on that day

    Raises:
        ValueError: If made is negative
    """
    if made < 0:
        raise ValueError(f"made must be non-negative, got {made}")
    with engine.begin() as connection:
        connection.execute(
            delete(SHOTS_TABLE).where(
                SHOTS_TABLE.c.player == player,
                SHOTS_TABLE.c.shot_date == shot_date,
            )
        )
        connection.execute(
            insert(SHOTS_TABLE).values(player=player, shot_date=shot_date, made=made)
        )


def load_shots(engine: Engine) -> pd.DataFrame:
    """Load every logged entry.

    Args:
        engine: SQLAlchemy engine connected to the tracker database

    Returns:
        DataFrame with columns player, shot_date (datetime64) and made
    """
    return pd.read_sql(select(SHOTS_TABLE), engine, parse_dates=["shot_date"])
