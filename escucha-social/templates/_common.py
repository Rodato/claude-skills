# TEMPLATE de la skill `escucha-social`. Copiar a pipeline/_common.py.
# Genérico: no toca el tema de la escucha. Ajustar solo ACTOR_ID si cambia el actor.
"""Utilidades compartidas: config, cliente Apify, ventanas temporales, guardado de raw.

Portado de narrativas-2026/pipeline/_common.py. El actor solo pagina histórico de forma
fiable con since:/until:, por eso el backfill se hace por ventanas y no en una sola corrida.
"""
from __future__ import annotations

import json
import logging
import os
import random
import re
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import yaml
from apify_client import ApifyClient
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config.yaml"
DATA_DIR = ROOT / "data" / "raw"

# Actor pay-per-result que corre en plan Free (~$0.25/1K resultados).
ACTOR_ID = "kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest"

# El actor redirige sus logs al cliente; con 175 corridas eso es ilegible.
for _n in ("apify_client", "apify", f"apify.{ACTOR_ID.split('/')[-1]}"):
    logging.getLogger(_n).setLevel(logging.WARNING)


class QuotaExceeded(RuntimeError):
    """La cuenta de Apify agotó su tope mensual.

    Se distingue de un fallo transitorio a propósito: el 2026-09-11 la cuenta free tocó su
    tope de USD 5 a mitad del barrido y, como el error se trataba igual que un timeout, se
    perdieron 128 corridas seguidas en silencio — y el hueco no fue aleatorio sino todo el
    final de la lista de keywords (los bloques `riesgo` y `temas_org` quedaron en cero).
    Un tope de cuota no se reintenta: se aborta y se avisa."""


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg["window"]["start"] = _as_date(cfg["window"]["start"])
    cfg["window"]["end"] = _as_date(cfg["window"]["end"])
    return cfg


def _as_date(v) -> date:
    if isinstance(v, date):
        return v
    return datetime.strptime(str(v), "%Y-%m-%d").date()


def get_client() -> ApifyClient:
    load_dotenv(ROOT / ".env")
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        raise RuntimeError("APIFY_TOKEN no encontrado. Pega el token en .env (ver .env.example).")
    return ApifyClient(token)


def slug(s: str) -> str:
    """Etiqueta segura para nombres de archivo a partir de una keyword."""
    s = (s or "").lower()
    for a, b in zip("áéíóúüñ", "aeiouun"):
        s = s.replace(a, b)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "kw"


def chunk_windows(start: date, end: date, mode: str = "month") -> list[tuple[date, date]]:
    """Ventanas (lo, hi) consecutivas que cubren [start, end].

    week  → bloques de 7 días.
    month → bloques de mes calendario.
    since:/until: de X es [since, until) — until exclusivo — así que cada ventana usa
    hi = inicio de la siguiente, sin solaparse."""
    out: list[tuple[date, date]] = []
    cur = start
    while cur <= end:
        if mode == "month":
            nxt = (cur.replace(day=1) + timedelta(days=32)).replace(day=1)
        else:
            nxt = cur + timedelta(days=7)
        hi = min(nxt, end + timedelta(days=1))
        out.append((cur, hi))
        cur = nxt
    return out


def build_query(kw: dict, lo: date, hi: date, lang: str | None) -> str:
    """Query de X para una keyword y ventana. phrase:true → búsqueda de frase exacta."""
    term = f'"{kw["q"]}"' if kw.get("phrase", True) else kw["q"]
    parts = [term]
    if lang:
        parts.append(f"lang:{lang}")
    parts.append(f"since:{lo.isoformat()}")
    parts.append(f"until:{hi.isoformat()}")
    return " ".join(parts)


def run_actor(client: ApifyClient, run_input: dict,
              max_retries: int = 6) -> tuple[list[dict], dict]:
    """Corre el actor y devuelve (items_limpios, meta). Filtra placeholders del actor.

    El plan Free de Apify tope 5 corridas concurrentes y rechaza de inmediato la que sobra.
    Como el rechazo es instantáneo, sin reintento se pierde la corrida entera: por eso se
    reintenta con backoff cuando el error es de concurrencia o de rate limit."""
    run = None
    for attempt in range(max_retries + 1):
        try:
            run = client.actor(ACTOR_ID).call(run_input=run_input)
            break
        except Exception as e:
            msg = str(e).lower()
            if "usage hard limit" in msg or "monthly usage" in msg:
                raise QuotaExceeded(str(e)) from e
            transitorio = any(t in msg for t in
                              ("concurrent", "rate limit", "too many requests", "429"))
            if not transitorio or attempt == max_retries:
                raise
            time.sleep(min(60, 8 * (attempt + 1)) + random.uniform(0, 4))
    dataset_id = run.default_dataset_id
    items = list(client.dataset(dataset_id).iterate_items())
    items = [it for it in items
             if isinstance(it, dict)
             and not it.get("noResults")
             and it.get("type") != "mock_tweet"
             and str(it.get("id")) != "-1"]
    meta = {"actor": ACTOR_ID, "run_id": run.id, "dataset_id": dataset_id, "input": run_input}
    return items, meta


def save_run_output(platform: str, label: str, items: list[dict], extra: dict | None = None) -> Path:
    """Guarda items crudos como JSON con timestamp. Devuelve el path."""
    out_dir = DATA_DIR / platform
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_label = "".join(c if c.isalnum() or c in "-_" else "_" for c in label)
    path = out_dir / f"{ts}__{safe_label}.json"
    payload = {
        "platform": platform,
        "label": label,
        "fetched_at_utc": ts,
        "count": len(items),
        "extra": extra or {},
        "items": items,
    }
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
    return path
