# Three-point tracker

Small Streamlit app where Giulia and Martina log the three-point shots they
made on a given date. It plots their combined cumulative progress towards 250
made threes by the end of the season, plus a weekly breakdown with a trend
line.

## Run locally

```bash
uv sync
uv run streamlit run streamlit_app.py
```

Entries are stored in the database named by the `DATABASE_URL` environment
variable (any SQLAlchemy URL). Without it, a local `shots.db` SQLite file is
used.

Players, goal and season end date are constants at the top of
`streamlit_app.py`.

## Deploy

The app runs on Streamlit Community Cloud with a hosted Postgres database
(for example Neon), because the cloud filesystem does not keep `shots.db`.

1. Create a Postgres database and copy its connection string
   (`postgresql://user:password@host/dbname?sslmode=require`).
2. On https://share.streamlit.io create an app from this repository with
   `streamlit_app.py` as the main file and Python 3.13.
3. In the app's advanced settings, add the secret
   `DATABASE_URL = "<connection string>"`. Never commit it.

The table is created on first start.

## Checks

```bash
uv run ruff format .
uv run ruff check .
uv run mypy .
uv run pytest
```
