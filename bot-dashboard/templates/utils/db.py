"""Capa de datos — única puerta a la base. Toda query vive acá, parametrizada,
en timezone America/Bogota y pasando por el filtro de cuentas de test."""

import os
from datetime import date, datetime
from typing import Optional
from zoneinfo import ZoneInfo

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")
TZ = "America/Bogota"  # la DB guarda timestamptz en UTC; la UI opera en GMT-5

# pg8000 (pure-Python) funciona en Python 3.12+ y Streamlit Cloud, donde psycopg2
# no tiene wheels y rompe el build. make_url(...).set(...) evita bugs de .replace().
_engine = create_engine(make_url(DATABASE_URL).set(drivername="postgresql+pg8000"))

# --- Cuentas de test/eval que escriben a las mismas tablas que el bot real ------
# TODO: ajustá a los sentinels que usen tu bot / repos de evals.
_TEST_CLIENT_NUMBERS = ("eval", "verify", "smoke", "test")
_TEST_CLIENT_LIKE = ("debug-%", "test-%", "smoke%")
_TEST_CONV_LIKE = ("eval-%", "verify-%", "debug-%")


def today_bogota() -> date:
    """Hoy en GMT-5. Usar esto, no date.today() (que usa la TZ del servidor)."""
    return datetime.now(ZoneInfo(TZ)).date()


def query_df(sql: str, params: Optional[dict] = None) -> pd.DataFrame:
    with _engine.connect() as conn:
        return pd.read_sql_query(text(sql), conn, params=params or {})


def date_filter(
    date_col: str,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    client_col: Optional[str] = "client_number",
    conv_col: Optional[str] = "conversation_id",
) -> tuple[str, dict]:
    """Construye el WHERE: rango de fechas (en GMT-5) + exclusión de cuentas de test.
    Toda query nueva debe pasar por acá para heredar el filtro. date_to es EXCLUSIVO.
    Drill-downs por usuario explícito: pasar client_col=None, conv_col=None."""
    clauses: list[str] = []
    params: dict = {}
    if date_from:
        clauses.append(f"DATE({date_col} AT TIME ZONE '{TZ}') >= :date_from")
        params["date_from"] = date_from
    if date_to:
        clauses.append(f"DATE({date_col} AT TIME ZONE '{TZ}') < :date_to")
        params["date_to"] = date_to
    if client_col and _TEST_CLIENT_NUMBERS:
        keys = []
        for i, v in enumerate(_TEST_CLIENT_NUMBERS):
            params[f"tc_{i}"] = v
            keys.append(f":tc_{i}")
        clauses.append(f"{client_col} NOT IN ({', '.join(keys)})")
        for i, pat in enumerate(_TEST_CLIENT_LIKE):
            params[f"tcl_{i}"] = pat
            clauses.append(f"{client_col} NOT LIKE :tcl_{i}")
    if conv_col:
        for i, pat in enumerate(_TEST_CONV_LIKE):
            params[f"tconv_{i}"] = pat
            clauses.append(f"{conv_col} NOT LIKE :tconv_{i}")
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    return where, params


# --- Queries de ejemplo (ajustá tabla/columnas a tu esquema) --------------------
# TODO: 'interactions' es un placeholder — cambialo por la tabla que escribe tu bot.

def get_kpis(date_from: Optional[date] = None, date_to: Optional[date] = None) -> dict:
    where, params = date_filter("created_at", date_from, date_to)
    sql = f"""
        SELECT
            COUNT(DISTINCT client_number)   AS n_users,
            COUNT(DISTINCT conversation_id) AS n_sessions,
            COUNT(*)                        AS n_messages
        FROM interactions
        {where}
    """
    return query_df(sql, params).iloc[0].to_dict()


def get_daily_activity(date_from: Optional[date] = None, date_to: Optional[date] = None) -> pd.DataFrame:
    where, params = date_filter("created_at", date_from, date_to)
    sql = f"""
        SELECT DATE(created_at AT TIME ZONE '{TZ}')::text AS day,
               COUNT(*)                                   AS messages,
               COUNT(DISTINCT client_number)              AS users
        FROM interactions
        {where}
        GROUP BY 1
        ORDER BY 1
    """
    return query_df(sql, params)
