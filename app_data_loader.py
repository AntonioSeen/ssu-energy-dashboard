"""
app_data_loader.py — REPLACEMENT for lines ~168-471 of app_helpppp.py.

Before: dashboard re-cleans raw CSVs at every page load, ignoring
weekly_energy.csv. This duplicated the pipeline's logic and ran on every
cache miss.

After: dashboard reads weekly_energy.csv directly. energy_core.py is
imported only for backfill when a week is missing from the CSV (e.g.
pipeline hasn't run yet today). This preserves the "raw overrides stale"
behaviour WITHOUT duplicating the cleaning code.

Drop this at the top of app.py and delete the old _parse_cell,
_process_one_csv, _process_raw_csvs, POINT_ID_MAP, UNIT_TO_KWH, and
load_daily_data functions.
"""
from __future__ import annotations
import os
from collections import defaultdict

import pandas as pd
import streamlit as st

from energy_core import (
    POINT_ID_MAP, UNIT_TO_KWH, ENERGY_UNITS, VALID_UNITS,
    RAW_CSV_RE, process_csv, to_kwh,
)

BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
WEEKLY_CSV_PATH = os.path.join(BASE_DIR, "weekly_energy.csv")
WEEKLY_COLS     = ["week", "building", "kWh", "gas_therm",
                   "water_gallon", "heating_dd", "normalized_kWh"]


def _find_raw_csvs():
    """Discover raw CSVs in ./, ./raw_data, ./uploads."""
    found = set()
    for d in (BASE_DIR, os.path.join(BASE_DIR, "raw_data"),
              os.path.join(BASE_DIR, "uploads")):
        if not os.path.isdir(d):
            continue
        for fname in os.listdir(d):
            if RAW_CSV_RE.match(fname):
                found.add(os.path.join(d, fname))
    return sorted(found)


def _backfill_from_raw(existing_weeks: set[str]) -> pd.DataFrame:
    """
    If raw CSVs exist for dates whose ISO-week is NOT yet in weekly_energy.csv,
    clean them on the fly so the dashboard isn't blind between pipeline runs.
    Weeks already present in the CSV are skipped — the pipeline is authoritative.
    """
    files = _find_raw_csvs()
    if not files:
        return pd.DataFrame(columns=WEEKLY_COLS)
    agg = defaultdict(lambda: defaultdict(lambda: {"kWh": 0.0, "gas": 0.0, "water": 0.0}))
    for fp in files:
        cleaned, _ = process_csv(fp)
        if cleaned.empty:
            continue
        cleaned["_dt"]   = pd.to_datetime(cleaned["timestamp"])
        cleaned["_week"] = (cleaned["_dt"] - pd.to_timedelta(
            cleaned["_dt"].dt.weekday, unit="D")).dt.date.astype(str)
        for _, r in cleaned.iterrows():
            wk, bld = r["_week"], r["building"]
            if wk in existing_weeks:
                continue                                # pipeline already has it
            if r["table"] == "energy":
                agg[wk][bld]["kWh"] += to_kwh(r["value"], r["unit"])
            elif r["table"] == "gas":
                agg[wk][bld]["gas"] += r["value"]
            elif r["table"] == "water":
                agg[wk][bld]["water"] += r["value"]
    rows = []
    for wk in sorted(agg):
        for bld in sorted(agg[wk]):
            b = agg[wk][bld]
            rows.append({
                "week": wk, "building": bld,
                "kWh": round(b["kWh"], 6),
                "gas_therm": round(b["gas"], 6),
                "water_gallon": round(b["water"], 6),
                "heating_dd": 0.0,
                "normalized_kWh": round(b["kWh"], 6),
            })
    return pd.DataFrame(rows, columns=WEEKLY_COLS)


@st.cache_data(ttl=300, show_spinner=False)
def load_weekly() -> pd.DataFrame:
    """
    Authoritative weekly DataFrame for the dashboard.

    Priority:
      1. weekly_energy.csv (pipeline output)   — trusted baseline
      2. Raw-CSV backfill                      — only for weeks NOT in #1

    This replaces the old daily-cleaning logic. daily_energy.csv is no
    longer consulted anywhere.
    """
    if os.path.exists(WEEKLY_CSV_PATH):
        weekly = pd.read_csv(WEEKLY_CSV_PATH)
        for c in WEEKLY_COLS:
            if c not in weekly.columns:
                weekly[c] = 0.0
        weekly = weekly[WEEKLY_COLS].copy()
    else:
        weekly = pd.DataFrame(columns=WEEKLY_COLS)

    existing_weeks = set(weekly["week"].astype(str)) if not weekly.empty else set()
    backfill = _backfill_from_raw(existing_weeks)

    combined = pd.concat([weekly, backfill], ignore_index=True) if not backfill.empty else weekly
    combined = combined[combined["kWh"] >= 0].copy()
    return combined
