"""
SSU Campus Energy Dashboard
Reads from raw interval CSVs (YYYYMMDD.csv / YYYYMMDDint.csv) using the exact
same cleaning logic as master_pipeline.py, then falls back to daily_energy.csv
for historical dates not covered by raw files.

Raw CSV discovery order (all are scanned and merged):
  1. Same directory as this file
  2. ./raw_data/
  3. ./uploads/

Raw-CSV results ALWAYS override daily_energy.csv for the same date — this
prevents corrupted DB-generated CSVs from poisoning the dashboard.
"""

import base64
import datetime
import glob
import os
import re
from collections import defaultdict

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

def load_weekly() -> pd.DataFrame:
    """
    Read weekly_energy.csv from the same directory as this script.
    This replaces the external app_data_loader module so the app is fully
    self-contained and works on Streamlit Community Cloud without any
    additional files beyond weekly_energy.csv, daily_energy.csv, and
    dashboard_header.png.
    """
    base = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base, "weekly_energy.csv")
    if not os.path.exists(csv_path):
        return pd.DataFrame(columns=["week", "building", "kWh", "gas_therm",
                                     "water_gallon", "heating_dd", "normalized_kWh"])
    df = pd.read_csv(csv_path, low_memory=False)
    # Normalise week column — accept YYYY-MM-DD or YYYY-MM-DD/YYYY-MM-DD
    df["week"] = df["week"].astype(str).str.strip().str.split("/").str[0]
    df["week"] = pd.to_datetime(df["week"], errors="coerce").dt.strftime("%Y-%m-%d")
    df = df.dropna(subset=["week"]).copy()
    # Ensure numeric columns
    for col in ["kWh", "gas_therm", "water_gallon", "heating_dd", "normalized_kWh"]:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return df

st.set_page_config(
    page_title="SSU Campus Energy Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ══════════════════════════════════════════════════════════════════════════════
# STYLES
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

html, body, [class*="css"], p, label, button {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    font-size: 16px;
}
span:not([data-testid="stIconMaterial"]):not(.material-symbols-rounded):not(.material-icons),
div:not([data-testid="stIconMaterial"]) {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
[data-testid="stIconMaterial"],
span[data-testid="stIconMaterial"],
.material-symbols-rounded,
.material-icons {
    font-family: 'Material Symbols Rounded', 'Material Symbols Outlined',
                 'Material Icons', sans-serif !important;
    font-feature-settings: 'liga' 1 !important;
    -webkit-font-feature-settings: 'liga' 1 !important;
    font-variant-ligatures: normal !important;
    text-rendering: optimizeLegibility !important;
    visibility: visible !important;
    display: inline-block !important;
    width: auto !important;
    height: auto !important;
    opacity: 1 !important;
}

.stApp { background-color: #f4f6f8 !important; color: #111827 !important; }

.block-container {
    padding-top: 2.5rem !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    padding-bottom: 3rem !important;
    max-width: 1400px !important;
}

section[data-testid="stSidebar"] { background-color: #1b3a5c !important; border-right: none !important; }
section[data-testid="stSidebar"] *:not([data-testid="stIconMaterial"]):not(.material-symbols-rounded):not(.material-icons) {
    color: #c8d9ea !important;
    font-family: 'Inter', sans-serif !important;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #ffffff !important; font-weight: 700 !important; font-size: 1.1rem !important; }
section[data-testid="stSidebar"] .stRadio > label { color: #a3bcd0 !important; font-size: 0.82rem !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.1em !important; }
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label { font-size: 1.05rem !important; font-weight: 500 !important; color: #c8d9ea !important; text-transform: none !important; letter-spacing: 0 !important; }
section[data-testid="stSidebar"] .stMultiSelect > label,
section[data-testid="stSidebar"] .stSelectbox > label { color: #a3bcd0 !important; font-size: 0.82rem !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.1em !important; }
section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.12) !important; }

[data-testid="collapsedControl"] { background-color: #1b3a5c !important; border-right: 2px solid #2a5180 !important; }
[data-testid="collapsedControl"] button [data-testid="stIconMaterial"],
button[data-testid="baseButton-headerNoPadding"] [data-testid="stIconMaterial"] {
    color: #c8d9ea !important;
    font-size: 1.6rem !important;
}

h1 { font-family: 'Inter', sans-serif !important; font-size: 2.5rem !important; font-weight: 800 !important; color: #111827 !important; letter-spacing: -0.04em !important; line-height: 1.1 !important; margin-bottom: 2px !important; margin-top: 0 !important; }
h2, h3 { font-family: 'Inter', sans-serif !important; font-weight: 700 !important; color: #111827 !important; }

[data-testid="stMetric"] { background: #ffffff !important; border: 1px solid #e2e8f0 !important; border-radius: 12px !important; padding: 20px 22px !important; box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important; }
[data-testid="stMetricLabel"] p { font-size: 0.82rem !important; font-weight: 700 !important; color: #6b7280 !important; text-transform: uppercase !important; letter-spacing: 0.1em !important; margin-bottom: 4px !important; }
[data-testid="stMetricValue"] { font-size: 2.2rem !important; font-weight: 800 !important; color: #111827 !important; letter-spacing: -0.03em !important; line-height: 1.15 !important; }
[data-testid="stMetricDelta"] { font-size: 0.92rem !important; font-weight: 600 !important; }
[data-testid="stMetricDelta"] svg { display: none !important; }

.sec-label { font-family: 'Inter', sans-serif; font-size: 1.05rem; font-weight: 700; color: #111827; text-transform: none; letter-spacing: 0; padding-bottom: 10px; border-bottom: 2px solid #e2e8f0; margin: 28px 0 16px 0; }

.rw-box { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px 18px; text-align: right; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.rw-label { font-size: 0.72rem; font-weight: 700; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.1em; display: block; margin-bottom: 4px; }
.rw-value { font-size: 1.1rem; font-weight: 700; color: #111827; }

.card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px 22px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.card-title { font-size: 1.1rem; font-weight: 700; color: #111827; margin-bottom: 4px; }
.card-sub { font-size: 0.88rem; color: #6b7280; margin-bottom: 14px; }

.topbld { margin-bottom: 14px; }
.topbld-header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 5px; }
.topbld-name { font-size: 1.0rem; font-weight: 600; color: #111827; }
.topbld-val { font-size: 0.95rem; font-weight: 600; color: #6b7280; }
.topbld-track { background: #f1f5f9; border-radius: 3px; height: 8px; overflow: hidden; }
.topbld-fill { height: 100%; background: #1b3a5c; border-radius: 3px; }

.alert-red   { background: #fef2f2; border-left: 4px solid #dc2626; border-radius: 0 8px 8px 0; padding: 12px 16px; font-size: 0.95rem; color: #7f1d1d; font-weight: 500; margin-bottom: 12px; }
.alert-amber { background: #fffbeb; border-left: 4px solid #f59e0b; border-radius: 0 8px 8px 0; padding: 12px 16px; font-size: 0.95rem; color: #78350f; font-weight: 500; margin-bottom: 12px; }
.alert-blue  { background: #eff6ff; border-left: 4px solid #3b82f6; border-radius: 0 8px 8px 0; padding: 12px 16px; font-size: 0.95rem; color: #1e40af; font-weight: 500; margin-bottom: 12px; }
.alert-green { background: #f0fdf4; border-left: 4px solid #16a34a; border-radius: 0 8px 8px 0; padding: 12px 16px; font-size: 0.95rem; color: #166534; font-weight: 500; margin-bottom: 12px; }

.lb-row { display: flex; align-items: center; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 14px 18px; margin-bottom: 8px; gap: 14px; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }
.lb-rank { font-size: 1.5rem; font-weight: 800; color: #1b3a5c; min-width: 46px; text-align: center; line-height: 1; flex-shrink: 0; }
.lb-rank.gold   { color: #b45309; }
.lb-rank.silver { color: #64748b; }
.lb-rank.bronze { color: #92400e; }
.lb-name { font-size: 1.1rem; font-weight: 700; color: #111827; }
.lb-sub { font-size: 0.9rem; color: #6b7280; margin-top: 4px; line-height: 1.5; }
.lb-pct { font-size: 1.8rem; font-weight: 800; text-align: right; line-height: 1.1; min-width: 90px; flex-shrink: 0; letter-spacing: -0.03em; }
.lb-pct-lbl { font-size: 0.72rem; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.08em; text-align: right; }
.streak { background: #fff7ed; border: 1px solid #fed7aa; border-radius: 6px; padding: 3px 10px; font-size: 0.85rem; color: #c2410c; font-weight: 700; white-space: nowrap; flex-shrink: 0; }

.goal-box { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 22px 24px; margin-top: 18px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.goal-lbl { font-size: 0.78rem; font-weight: 700; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px; }
.goal-status { font-size: 1.4rem; font-weight: 800; margin-bottom: 14px; line-height: 1.25; letter-spacing: -0.02em; }
.prog-bg { background: #e5e7eb; border-radius: 6px; height: 12px; overflow: hidden; margin-bottom: 8px; }
.prog-fill { height: 100%; border-radius: 6px; }

.di-table { width: 100%; border-collapse: collapse; font-size: 0.92rem; }
.di-table th { background: #f1f5f9; color: #374151; font-weight: 700; padding: 11px 14px; text-align: left; border-bottom: 2px solid #e2e8f0; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.08em; }
.di-table td { padding: 10px 14px; border-bottom: 1px solid #f1f5f9; color: #111827; vertical-align: middle; }
.di-table tr:hover td { background: #f8fafc; }
.badge { display: inline-block; padding: 3px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: 700; }
.badge-ok     { background: #dcfce7; color: #166534; }
.badge-open   { background: #fee2e2; color: #991b1b; }
.badge-review { background: #fef3c7; color: #92400e; }
.badge-skip   { background: #f1f5f9; color: #6b7280; }
.badge-raw    { background: #dbeafe; color: #1e40af; }

div[data-testid="column"] { padding: 0 6px !important; }

@media (max-width: 768px) {
    h1 { font-size: 1.6rem !important; }
    [data-testid="stMetricValue"] { font-size: 1.5rem !important; }
    .lb-row { flex-wrap: wrap; gap: 8px; }
    .lb-pct { font-size: 1.3rem !important; }
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PIPELINE CONSTANTS  (must match master_pipeline.py exactly)
# ══════════════════════════════════════════════════════════════════════════════
UNIT_TO_KWH = {
    "kWh":    1.0,
    "BTU":    0.000293071,
    "MBTU":   293.071,
    "kBTU":   0.293071,   # _MBTU label in BMS files is actually kBTU
    "tonref": 3.51685,
    "therm":  29.3071,
}
VALID_UNITS  = {"kWh", "therm", "BTU", "tonref", "MBTU", "kBTU", "gallon"}
ENERGY_UNITS = {"kWh", "BTU", "MBTU", "kBTU", "tonref"}

# point-id → (building_name, canonical_unit)
POINT_ID_MAP = {
    "1f97c82e-36e60525": ("Art Building",                "BTU"),
    "1f97c82e-d1a92673": ("Art Building",                "BTU"),
    "1f97c82e-525ca261": ("Schulz Info Center",          "BTU"),
    "1f97c82e-c34c4f2e": ("Schulz Info Center",          "kWh"),
    "206e94b8-3b05cb50": ("Schulz Info Center",          "therm"),
    "1f97c82e-dd011464": ("ETC",                         "kWh"),
    "1f98265e-39835c84": ("Green Music Center",          "BTU"),
    "234aa956-82d369b2": ("Green Music Center",          "kBTU"),   # _MBTU in file → kBTU
    "234ab131-e413ba29": ("Green Music Center",          "kWh"),
    "234aab84-c656a0e0": ("Green Music Center",          "therm"),
    "234aa782-f7b1eef2": ("Green Music Center",          "gallon"),
    "1f98265e-cbf77175": ("Rachel Carson Hall",          "kWh"),
    "234aa121-a983880d": ("Rachel Carson Hall",          "BTU"),
    "234aa43b-a73abf5e": ("Rachel Carson Hall",          "BTU"),
    "206d9425-f3361ab6": ("Ives Hall",                   "kWh"),
    "234e3195-7d72fbdc": ("Ives Hall",                   "BTU"),
    "234e3195-c20a1a8e": ("Ives Hall",                   "BTU"),
    "206db469-c986212b": ("Physical Education",          "kWh"),
    "20c9b2e1-d7263cf1": ("Salazar Hall",                "kWh"),
    "234e4c64-930d1fd6": ("Salazar Hall",                "kWh"),
    "20c9b4d5-5ea6aa0b": ("Salazar Hall",                "BTU"),
    "234a6e2b-318cf13d": ("Boiler Plant",                "therm"),
    "234e3ee2-b06b6c8c": ("Nichols Hall",                "BTU"),
    "234e3ee2-f6fcea18": ("Nichols Hall",                "BTU"),
    "234e40da-635bc7c1": ("Nichols Hall",                "kWh"),
    "20c9aa07-acd1558a": ("Student Center",              "kWh"),
    "234e5dff-6fe20abd": ("Student Center",              "BTU"),
    "234e5dff-8d8eb031": ("Student Center",              "BTU"),
    "234e61c5-021da430": ("Student Health Center",       "BTU"),
    "234e61c5-83f6cf71": ("Student Health Center",       "BTU"),
    "250ea73e-3b55a6cf": ("Wine Spectator Learning Ctr", "kWh"),
    "251810ce-f429b841": ("Stevenson Hall",              "kWh"),
    "267fcb62-ed42e3b3": ("Stevenson Hall",              "BTU"),
    "267e6fd0-93d67a62": ("Darwin Hall",                 "kWh"),
    "214981c7-5530731e": ("Campus Misc",                 "kWh"),
    "214981c7-63077e46": ("Campus Misc",                 "kWh"),
    "214981c7-dd0b1593": ("Campus Misc",                 "kWh"),
}

_RAW_CSV_RE = re.compile(r"^(\d{8})(int)?\.csv$", re.IGNORECASE)


# ══════════════════════════════════════════════════════════════════════════════
# PIPELINE CLEANING LOGIC
# ══════════════════════════════════════════════════════════════════════════════
def _parse_cell(value):
    """
    Extract (numeric_value, unit_string) from a raw cell like '123.45kWh',
    '184.92_MBTU', '27332409.59BTU'.

    Critical rule (matches master_pipeline.py):
        _MBTU suffix → remapped to kBTU (BMS sends kBTU but labels it _MBTU)
    """
    if pd.isna(value):
        return None, None
    s = str(value).strip()
    if not s:
        return None, None
    m = re.match(r"^([\d.]+)(_?)([a-zA-Z]+)$", s)
    if not m:
        # Try bare numeric
        try:
            return float(s), None
        except ValueError:
            return None, None
    num        = float(m.group(1))
    underscore = m.group(2)
    unit       = m.group(3)
    # THE critical remap
    if underscore == "_" and unit == "MBTU":
        unit = "kBTU"
    if unit in VALID_UNITS:
        return num, unit
    return num, None


def _process_one_csv(filepath: str) -> dict:
    """
    Process a single raw CSV file.
    Returns: { date_str: { building: { 'kWh': float, 'therm': float, 'gallon': float } } }
    """
    try:
        df = pd.read_csv(filepath, low_memory=False)
    except Exception:
        return {}

    if df.empty or len(df.columns) < 2:
        return {}

    ts_col = df.columns[0]
    try:
        df["_ts"] = pd.to_datetime(
            df[ts_col].astype(str).str.replace(r"\s*Los_Angeles$", "", regex=True),
            errors="coerce",
        )
    except Exception:
        return {}

    df["_date"] = df["_ts"].dt.date.astype(str)
    df = df[df["_date"] != "NaT"].copy()
    if df.empty:
        return {}

    # accumulator: { date: { building: { unit_bucket: float } } }
    acc: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))

    for col in df.columns:
        if col in (ts_col, "_ts", "_date"):
            continue
        if "p:sonomastate:r:" not in col:
            continue
        pid = col.split("p:sonomastate:r:")[-1].strip()
        if pid not in POINT_ID_MAP:
            continue
        building, map_unit = POINT_ID_MAP[pid]

        for _, row in df.iterrows():
            date_str = row["_date"]
            cell     = row[col]
            if pd.isna(cell):
                continue

            val_n, val_u = _parse_cell(cell)
            if val_n is None:
                continue

            # Determine final unit (pipeline priority logic)
            if val_u and val_u in VALID_UNITS:
                # Cell carries an explicit unit — trust it, EXCEPT gas override
                if map_unit == "therm" and val_u != "MBTU":
                    final_unit = "therm"
                else:
                    final_unit = val_u
            else:
                final_unit = map_unit

            # Route to bucket
            if final_unit in ENERGY_UNITS:
                kwh = val_n * UNIT_TO_KWH[final_unit]
                acc[date_str][building]["kWh"] += kwh
            elif final_unit == "therm":
                acc[date_str][building]["therm"] += val_n
            elif final_unit == "gallon":
                acc[date_str][building]["gallon"] += val_n

    return {d: dict(bmap) for d, bmap in acc.items()}


def _find_raw_csv_files() -> list[str]:
    """
    Scan for raw CSV files matching YYYYMMDD.csv or YYYYMMDDint.csv in:
      - same directory as this script
      - ./raw_data/
      - ./uploads/
    Returns sorted list of absolute paths.
    """
    base = os.path.dirname(os.path.abspath(__file__))
    search_dirs = [
        base,
        os.path.join(base, "raw_data"),
        os.path.join(base, "uploads"),
    ]
    found = set()
    for d in search_dirs:
        if not os.path.isdir(d):
            continue
        for fname in os.listdir(d):
            if _RAW_CSV_RE.match(fname):
                found.add(os.path.join(d, fname))
    return sorted(found)


@st.cache_data(ttl=300, show_spinner=False)
def _process_raw_csvs() -> tuple[pd.DataFrame, set]:
    """
    Process all discovered raw CSV files using the pipeline cleaning logic.
    Returns:
        (daily_df, raw_dates_set)
        daily_df   — DataFrame with columns [date, building, kWh, gas_therm, water_gallon]
        raw_dates_set — set of date strings covered by raw CSVs
    """
    files = _find_raw_csv_files()
    if not files:
        return pd.DataFrame(columns=["date", "building", "kWh", "gas_therm", "water_gallon"]), set()

    # Merge results from all files; same-date same-building values are summed
    merged: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    for fp in files:
        result = _process_one_csv(fp)
        for date_str, bmap in result.items():
            for building, ubuckets in bmap.items():
                for bucket, val in ubuckets.items():
                    merged[date_str][building][bucket] += val

    rows = []
    for date_str in sorted(merged):
        for building in sorted(merged[date_str]):
            ub = merged[date_str][building]
            rows.append({
                "date":         date_str,
                "building":     building,
                "kWh":          round(ub.get("kWh", 0.0), 6),
                "gas_therm":    round(ub.get("therm", 0.0), 6),
                "water_gallon": round(ub.get("gallon", 0.0), 6),
            })

    df = pd.DataFrame(rows)
    raw_dates = set(df["date"].unique()) if not df.empty else set()
    return df, raw_dates


@st.cache_data(ttl=300, show_spinner=False)
def load_daily_data() -> pd.DataFrame:
    """
    Build the authoritative daily DataFrame:
      1. Load daily_energy.csv (historical fallback)
      2. Process raw CSVs
      3. Drop daily_energy rows for any date that raw CSVs cover
      4. Append raw-CSV rows
    Result columns: [date, building, kWh, gas_therm, water_gallon]
    """
    DAILY_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "daily_energy.csv")

    # --- Raw CSV layer ---
    raw_df, raw_dates = _process_raw_csvs()

    # --- Historical layer ---
    hist_rows = []
    if os.path.exists(DAILY_CSV):
        hist = pd.read_csv(DAILY_CSV)
        for col in ("gas_therm", "water_gallon"):
            if col not in hist.columns:
                hist[col] = 0.0
        hist["date"] = hist["date"].astype(str).str.strip()
        # Only keep dates NOT covered by raw CSVs
        hist_filtered = hist[~hist["date"].isin(raw_dates)].copy()
        hist_rows = hist_filtered[["date", "building", "kWh", "gas_therm", "water_gallon"]].to_dict("records")

    combined_rows = hist_rows
    if not raw_df.empty:
        combined_rows += raw_df[["date", "building", "kWh", "gas_therm", "water_gallon"]].to_dict("records")

    if not combined_rows:
        return pd.DataFrame(columns=["date", "building", "kWh", "gas_therm", "water_gallon"])

    daily = pd.DataFrame(combined_rows)
    daily["date"] = pd.to_datetime(daily["date"], errors="coerce")
    daily = daily.dropna(subset=["date"]).copy()
    daily["date"] = daily["date"].dt.normalize()
    # Aggregate (in case both sources overlap after filtering — shouldn't, but safe)
    daily = (
        daily.groupby(["date", "building"])
        .agg(kWh=("kWh", "sum"), gas_therm=("gas_therm", "sum"), water_gallon=("water_gallon", "sum"))
        .reset_index()
    )
    daily = daily[daily["kWh"] >= 0].copy()
    return daily, raw_dates


@st.cache_data(ttl=300, show_spinner=False)
def load_data() -> pd.DataFrame:
    """
    Read weekly_energy.csv directly (new pipeline output).
    Returns (weekly_df, raw_dates) to preserve the old tuple signature.
    """
    weekly = load_weekly()
    if weekly.empty:
        return pd.DataFrame(columns=["week", "building", "kWh", "gas_therm", "water_gallon",
                                     "heating_dd", "normalized_kWh"]), set()
    # Ensure week is a string (YYYY-MM-DD) for downstream comparisons
    if pd.api.types.is_datetime64_any_dtype(weekly["week"]):
        weekly = weekly.copy()
        weekly["week"] = weekly["week"].dt.date.astype(str)
    weekly = weekly[weekly["kWh"] > 0].copy()
    return weekly, set()


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
PLOT_BG   = "#ffffff"
PLOT_GRID = "#f1f5f9"
PLOT_TEXT = "#111827"
C_NAVY    = "#1b3a5c"
C_GREEN   = "#16a34a"
C_RED     = "#dc2626"
C_AMBER   = "#d97706"
C_MUTED   = "#6b7280"
C_SLATE   = "#64748b"

BUILDINGS_STATUS = {
    "Green Music Center":          "ok",
    "Nichols Hall":                "ok",
    "Rachel Carson Hall":          "ok",
    "Wine Spectator Learning Ctr": "review",
    "Student Center":              "ok",
    "Physical Education":          "ok",
    "Ives Hall":                   "ok",
    "Campus Misc":                 "ok",
}

SENSOR_REGISTRY = [
    ("Green Music Center",          "234ab131-e413ba29", "Electric", "kWh",   "OK",      "Active — primary electric meter, ~85 kWh per reading"),
    ("Green Music Center",          "1f98265e-39835c84", "Thermal",  "BTU",   "OK",      "Active — chilled water cooling loop"),
    ("Green Music Center",          "234aa956-82d369b2", "Thermal",  "kBTU",  "OK",      "Active — heating hot water loop (BMS labels as _MBTU, pipeline remaps to kBTU)"),
    ("Green Music Center",          "234aab84-c656a0e0", "Gas",      "therm", "Missing", "No data received"),
    ("Green Music Center",          "234aa782-f7b1eef2", "Water",    "gallon","Missing", "No data received"),
    ("Nichols Hall",                "234e3ee2-f6fcea18", "Thermal",  "BTU",   "OK",      "Active — heating hot water loop, ~20,000 kWh/day"),
    ("Nichols Hall",                "234e3ee2-b06b6c8c", "Thermal",  "BTU",   "OK",      "Active — chilled water cooling loop, reporting zero"),
    ("Nichols Hall",                "234e40da-635bc7c1", "Electric", "kWh",   "OK",      "Active — reporting zero, meter may be offline"),
    ("Physical Education",          "206db469-c986212b", "Electric", "kWh",   "OK",      "Active — consistent readings, ~11 kWh per reading"),
    ("Rachel Carson Hall",          "1f98265e-cbf77175", "Electric", "kWh",   "Missing", "No data received"),
    ("Rachel Carson Hall",          "234aa121-a983880d", "Thermal",  "BTU",   "OK",      "Active — chilled water cooling loop, minor daily gaps"),
    ("Rachel Carson Hall",          "234aa43b-a73abf5e", "Thermal",  "BTU",   "OK",      "Active — heating hot water loop, reporting zero"),
    ("Ives Hall",                   "234e3195-7d72fbdc", "Thermal",  "BTU",   "OK",      "Active — heating hot water loop, 950–1,243 kWh/day"),
    ("Ives Hall",                   "234e3195-c20a1a8e", "Thermal",  "BTU",   "OK",      "Active — chilled water cooling loop, reporting zero"),
    ("Ives Hall",                   "206d9425-f3361ab6", "Electric", "kWh",   "OK",      "Active — reporting zero, meter may be offline"),
    ("Student Center",              "234e5dff-8d8eb031", "Thermal",  "BTU",   "OK",      "Active — heating hot water loop, variable output"),
    ("Student Center",              "234e5dff-6fe20abd", "Thermal",  "BTU",   "OK",      "Active — chilled water cooling loop"),
    ("Student Center",              "20c9aa07-acd1558a", "Electric", "kWh",   "OK",      "Active — reporting zero, meter may be offline"),
    ("Wine Spectator Learning Ctr", "250ea73e-3b55a6cf", "Electric", "kWh",   "Review",  "Only ~25% of expected readings received — kWh may be understated"),
    ("Art Building",                "1f97c82e-36e60525", "Thermal",  "BTU",   "Missing", "No data received"),
    ("Art Building",                "1f97c82e-d1a92673", "Thermal",  "BTU",   "Missing", "No data received"),
    ("Boiler Plant",                "234a6e2b-318cf13d", "Gas",      "therm", "Missing", "No data received"),
    ("Darwin Hall",                 "267e6fd0-93d67a62", "Electric", "kWh",   "Missing", "No data received"),
    ("ETC",                         "1f97c82e-dd011464", "Electric", "kWh",   "Missing", "No data received"),
    ("Salazar Hall",                "20c9b2e1-d7263cf1", "Electric", "kWh",   "Missing", "No data received"),
    ("Salazar Hall",                "234e4c64-930d1fd6", "Electric", "kWh",   "Missing", "No data received"),
    ("Salazar Hall",                "20c9b4d5-5ea6aa0b", "Thermal",  "BTU",   "Missing", "No data received"),
    ("Schulz Info Center",          "1f97c82e-c34c4f2e", "Electric", "kWh",   "Missing", "No data received"),
    ("Schulz Info Center",          "1f97c82e-525ca261", "Thermal",  "BTU",   "Missing", "No data received"),
    ("Schulz Info Center",          "206e94b8-3b05cb50", "Gas",      "therm", "Missing", "No data received"),
    ("Stevenson Hall",              "251810ce-f429b841", "Electric", "kWh",   "Missing", "No data received"),
    ("Stevenson Hall",              "267fcb62-ed42e3b3", "Thermal",  "BTU",   "Missing", "No data received"),
    ("Student Health Center",       "234e61c5-021da430", "Thermal",  "BTU",   "OK",      "Active — chilled water cooling loop, reporting zero"),
    ("Student Health Center",       "234e61c5-83f6cf71", "Thermal",  "BTU",   "OK",      "Active — chilled water cooling loop, reporting zero"),
    ("Campus Misc",                 "214981c7-dd0b1593", "Electric", "kWh",   "PGE",     "PG&E utility account meter"),
    ("Campus Misc",                 "214981c7-5530731e", "Electric", "kWh",   "PGE",     "PG&E utility account meter"),
    ("Campus Misc",                 "214981c7-63077e46", "Electric", "kWh",   "PGE",     "PG&E utility account meter"),
]


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def plot_base(height=300):
    return dict(
        paper_bgcolor=PLOT_BG, plot_bgcolor=PLOT_BG,
        font=dict(family="Inter, sans-serif", color=PLOT_TEXT, size=18, weight=700),
        margin=dict(l=8, r=60, t=36, b=8),
        height=height,
        xaxis=dict(
            gridcolor=PLOT_GRID, zerolinecolor="#e2e8f0", linecolor="#e2e8f0",
            tickfont=dict(size=16, family="Inter", color=PLOT_TEXT, weight=700),
            title_font=dict(size=16, family="Inter", color=PLOT_TEXT, weight=700),
        ),
        yaxis=dict(
            gridcolor=PLOT_GRID, zerolinecolor="#e2e8f0", linecolor="#e2e8f0",
            tickfont=dict(size=16, family="Inter", color="#111827", weight=700),
            title_font=dict(size=16, family="Inter", color="#111827", weight=700),
        ),
    )


def week_label(w):
    """Convert '2026-02-02' → 'Feb 2 – Feb 8, 2026'"""
    try:
        start = pd.to_datetime(str(w).split("/")[0].strip())
        end   = start + pd.Timedelta(days=6)
        ss = start.strftime("%b ") + start.strftime("%d").lstrip("0")
        es = end.strftime("%b ")   + end.strftime("%d").lstrip("0")
        return f"{ss} – {es}, {end.year}"
    except Exception:
        return str(w)


def fmt_kwh(v):
    if v >= 1_000_000: return f"{v/1_000_000:.2f} GWh"
    if v >= 1_000:     return f"{v/1000:.1f} MWh"
    return f"{v:,.0f} kWh"


def fmt_cost(v):
    return f"${abs(v):,.0f}"


def badge_html(status):
    cls = {"OK": "badge-ok", "Missing": "badge-open", "Review": "badge-review",
           "PGE": "badge-skip", "Raw CSV": "badge-raw"}.get(status, "badge-skip")
    label = "Missing Data" if status == "Missing" else status
    return f'<span class="badge {cls}">{label}</span>'


# ══════════════════════════════════════════════════════════════════════════════
# LOAD DATA
# ══════════════════════════════════════════════════════════════════════════════
_load_result = load_data()
if isinstance(_load_result, tuple):
    df_all, _raw_dates_loaded = _load_result
else:
    df_all, _raw_dates_loaded = _load_result, set()

if df_all.empty:
    st.error("No energy data found. Place weekly_energy.csv and/or raw CSV files "
             "(YYYYMMDD.csv / YYYYMMDDint.csv) in the same folder as app.py.")
    st.stop()

all_weeks = sorted(df_all["week"].unique())

# Determine which weeks are sourced from raw CSVs
_daily_result = load_daily_data()
_daily_df = _daily_result[0] if isinstance(_daily_result, tuple) else _daily_result
_raw_dates_loaded = _daily_result[1] if isinstance(_daily_result, tuple) else set()

def _week_has_raw(w):
    try:
        start = pd.to_datetime(str(w))
        dates = [(start + pd.Timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
        return any(d in _raw_dates_loaded for d in dates)
    except Exception:
        return False

_raw_weeks = {w for w in all_weeks if _week_has_raw(w)}
_n_raw_files = len(_find_raw_csv_files())


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # Data source banner
    if _n_raw_files > 0:
        st.markdown(
            f'<div style="background:rgba(59,130,246,0.15);border-radius:8px;padding:8px 12px;'
            f'margin-bottom:12px;font-size:0.82rem;color:#93c5fd;font-weight:600;">'
            f'⚡ {_n_raw_files} raw CSV file{"s" if _n_raw_files != 1 else ""} loaded<br>'
            f'<span style="font-weight:400;color:#7ab4d4">{len(_raw_dates_loaded)} date(s) from raw CSVs</span>'
            f'</div>',
            unsafe_allow_html=True)

    # Red-border style for all sidebar dropdowns/selectboxes/multiselects
    st.markdown("""
<style>
section[data-testid="stSidebar"] .stSelectbox > div > div,
section[data-testid="stSidebar"] .stMultiSelect > div > div[data-baseweb="select"] {
    border: 2px solid #dc2626 !important;
    border-radius: 6px !important;
}
section[data-testid="stSidebar"] .stSelectbox > div > div > div,
section[data-testid="stSidebar"] .stMultiSelect > div > div[data-baseweb="select"] > div {
    color: #ffffff !important;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] .sidebar-title {
    color: #4dabf7 !important;
    font-size: 1.25rem !important;
    font-weight: 800 !important;
}
</style>
""", unsafe_allow_html=True)

    st.markdown("**View Mode**")
    role = st.radio("mode", ["Student (Gamified)", "Admin (Basic)"],
                    label_visibility="collapsed")
    st.markdown("---")

    # ── TIME RANGE ──────────────────────────────────────────────────────────
    st.markdown('<p style="color:#4dabf7;font-size:1.25rem;font-weight:800;margin-bottom:4px;">Time Range</p>', unsafe_allow_html=True)
    time_filter = st.radio("time", ["Weekly", "Monthly", "Yearly"],
                           horizontal=True, label_visibility="collapsed")

    df_all["_wstart"] = pd.to_datetime(df_all["week"], errors="coerce")

    # Compute the latest week for defaulting
    _latest_week_default = all_weeks[-1] if all_weeks else None

    if time_filter == "Weekly":
        avail_w = all_weeks
        st.markdown("**Select up to 4 weeks**")
        _default_weeks = [_latest_week_default] if _latest_week_default else []
        selected_weeks = st.multiselect(
            "weeks", avail_w, default=_default_weeks,
            format_func=week_label, label_visibility="collapsed")
        df_view      = df_all.copy()
        period_label = week_label

    elif time_filter == "Monthly":
        df_all["_period"] = df_all["_wstart"].dt.to_period("M").astype(str)
        monthly = (df_all.groupby(["_period", "building"])
                   .agg(kWh=("kWh", "sum"), gas_therm=("gas_therm", "sum"),
                        water_gallon=("water_gallon", "sum"))
                   .reset_index().rename(columns={"_period": "week"}))
        all_periods = sorted(monthly["week"].unique())
        def month_label(p):
            try:    return pd.to_datetime(p + "-01").strftime("%B %Y")
            except: return str(p)
        st.markdown("**Select up to 4 months**")
        selected_weeks = st.multiselect(
            "months", all_periods, default=[],
            format_func=month_label, label_visibility="collapsed")
        df_view      = monthly
        period_label = month_label

    else:  # Yearly
        df_all["_period"] = df_all["_wstart"].dt.year.astype(str)
        yearly = (df_all.groupby(["_period", "building"])
                  .agg(kWh=("kWh", "sum"), gas_therm=("gas_therm", "sum"),
                       water_gallon=("water_gallon", "sum"))
                  .reset_index().rename(columns={"_period": "week"}))
        all_periods = sorted(yearly["week"].unique())
        def year_label(p): return str(p)
        st.markdown("**Select years**")
        selected_weeks = st.multiselect(
            "years", all_periods, default=[],
            format_func=year_label, label_visibility="collapsed")
        df_view      = yearly
        period_label = year_label

    st.markdown("---")

    # ── COST ────────────────────────────────────────────────────────────────
    st.markdown('<p style="color:#4dabf7;font-size:1.25rem;font-weight:800;margin-bottom:4px;">Cost</p>', unsafe_allow_html=True)
    st.markdown('<p style="color:#a3bcd0;font-size:0.82rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:2px;">Estimated Cost Rate ($/kWh)</p>', unsafe_allow_html=True)
    COST_RATE_OPTIONS = {
        "$0.10 / kWh": 0.10,
        "$0.12 / kWh": 0.12,
        "$0.15 / kWh (default)": 0.15,
        "$0.18 / kWh": 0.18,
        "$0.20 / kWh": 0.20,
        "$0.25 / kWh": 0.25,
        "$0.30 / kWh": 0.30,
    }
    selected_rate_label = st.selectbox(
        "cost_rate", list(COST_RATE_OPTIONS.keys()),
        index=2, label_visibility="collapsed")
    ENERGY_RATE = COST_RATE_OPTIONS[selected_rate_label]
    st.markdown(
        f'<div style="font-size:0.8rem;color:#a3bcd0;margin-top:4px;margin-bottom:2px;">'
        f'All cost estimates use <b style="color:#ffffff">${ENERGY_RATE:.2f}/kWh</b></div>',
        unsafe_allow_html=True)
    st.markdown("---")

    # ── BUILDING DETAIL ──────────────────────────────────────────────────────
    st.markdown('<p style="color:#4dabf7;font-size:1.25rem;font-weight:800;margin-bottom:4px;">Building Detail</p>', unsafe_allow_html=True)

    # We need the building list — compute ahead of the main page body
    # It will be reused in the Overview section too
    _sidebar_bld_options = []
    if all_weeks:
        _temp_by_bld = df_all.groupby(["week", "building"])["kWh"].sum().reset_index()
        _all_bld_kwh = _temp_by_bld.groupby("building")["kWh"].sum().sort_values(ascending=False).reset_index()
        _sidebar_bld_options = _all_bld_kwh["building"].tolist()

    _sidebar_sel_bld = st.selectbox(
        "sidebar_bld_detail",
        ["(None)"] + _sidebar_bld_options,
        index=0,
        label_visibility="collapsed"
    )

    # Show building summary card in sidebar if a building is selected
    if _sidebar_sel_bld and _sidebar_sel_bld != "(None)" and all_weeks:
        _sb_latest = all_weeks[-1]
        _sb_bld_by_week = df_all[df_all["building"] == _sidebar_sel_bld].groupby("week")["kWh"].sum()
        _sb_latest_kwh = float(_sb_bld_by_week.get(_sb_latest, 0.0))
        _sb_cost = _sb_latest_kwh * ENERGY_RATE
        _sb_start = pd.to_datetime(_sb_latest)
        _sb_end   = _sb_start + pd.Timedelta(days=6)
        _sb_range = f"{_sb_start.strftime('%b %-d')} – {_sb_end.strftime('%b %-d, %Y')}"
        st.markdown(
            f'<div style="background:#132d4a;border:1px solid #2a5180;border-radius:8px;'
            f'padding:10px 12px;margin-top:6px;">'
            f'<div style="font-size:0.72rem;font-weight:700;color:#a3bcd0;text-transform:uppercase;'
            f'letter-spacing:0.1em;">{_sidebar_sel_bld} — {_sb_range}</div>'
            f'<div style="font-size:1.2rem;font-weight:800;color:#ffffff;margin-top:4px;">'
            f'{_sb_latest_kwh/1000:.1f} MWh</div>'
            f'<div style="font-size:0.85rem;font-weight:700;color:#93c5fd;margin-top:2px;">'
            f'Est. Cost: ${_sb_cost:,.0f} @ ${ENERGY_RATE:.2f}/kWh</div>'
            f'</div>',
            unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("**Section**")
    if role == "Student (Gamified)":
        nav_opts = ["📊 Overview", "🏆 Leaderboard", "🔥 Thermal", "🔍 Data Integrity"]
    else:
        nav_opts = ["📊 Overview", "🔥 Thermal", "🔍 Data Integrity"]
    _tab = st.radio("nav", nav_opts, label_visibility="collapsed")
    active_tab = ("Overview" if "Overview" in _tab else
                  "Leaderboard" if "Leaderboard" in _tab else
                  "Thermal" if "Thermal" in _tab else "DataIntegrity")

    st.markdown("---")

    # Latest date — show actual latest day not week
    if all_weeks:
        _latest_day_display = (pd.to_datetime(all_weeks[-1]) + pd.Timedelta(days=6)).strftime("%B %d, %Y")
    else:
        _latest_day_display = "—"
    st.markdown(
        f'<div style="font-size:0.82rem;color:#6a9cc0;line-height:1.8;">'
        f'{len(all_weeks)} week(s) in database<br>'
        f'Latest: {_latest_day_display}</div>',
        unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SELECTION STATE
# ══════════════════════════════════════════════════════════════════════════════
if selected_weeks:
    if len(selected_weeks) > 4:
        st.warning("Maximum 4 periods can be selected at once. Showing the most recent 4.")
        selected_weeks = sorted(selected_weeks)[-4:]

    sorted_sel       = sorted(selected_weeks)
    latest_week      = sorted_sel[-1]
    by_bld           = df_view.groupby(["week", "building"])["kWh"].sum().reset_index()
    campus_cur       = by_bld[by_bld["week"] == latest_week]["kWh"].sum()
    campus_cost      = campus_cur * ENERGY_RATE
    campus_total_sel = by_bld[by_bld["week"].isin(sorted_sel)]["kWh"].sum()
    campus_total_cost = campus_total_sel * ENERGY_RATE
    prev_week        = sorted_sel[-2] if len(sorted_sel) >= 2 else None
    campus_prev      = by_bld[by_bld["week"] == prev_week]["kWh"].sum() if prev_week else None
    pct_change       = ((campus_cur - campus_prev) / campus_prev * 100) if campus_prev else None
else:
    sorted_sel        = []
    latest_week       = None
    by_bld            = pd.DataFrame(columns=["week", "building", "kWh"])
    campus_total_sel  = 0.0
    campus_total_cost = 0.0
    prev_week         = None
    campus_prev       = None
    pct_change        = None


# ══════════════════════════════════════════════════════════════════════════════
# OVERVIEW TAB
# ══════════════════════════════════════════════════════════════════════════════
if active_tab == "Overview":

    st.image(
        "dashboard_header.png",
        use_container_width=True
    )

    
    # All-time campus energy chart
    _at = df_all.dropna(subset=["_wstart"]).copy()
    _at["_month"] = _at["_wstart"].dt.to_period("M")
    _at_monthly = (
        _at.groupby("_month")["kWh"].sum()
        .reset_index()
        .sort_values("_month")
    )
    _at_monthly["_label"] = _at_monthly["_month"].dt.strftime("%b %Y")
    _at_monthly["_mwh"]   = _at_monthly["kWh"] / 1000
    _at_total_kwh  = float(_at_monthly["kWh"].sum())
    _at_total_cost = _at_total_kwh * ENERGY_RATE

    # Dynamic date range label
    if not _at_monthly.empty:
        _first_month = _at_monthly["_month"].iloc[0].to_timestamp().strftime("%b %Y")
        _at_section_label = f"Campus Energy — {_first_month} to Present"
    else:
        _at_section_label = "Campus Energy — All Time"
    st.markdown(f'<div class="sec-label">{_at_section_label}</div>', unsafe_allow_html=True)

    at1, at2, at3 = st.columns(3)
    at1.metric("Total Energy Consumed", fmt_kwh(_at_total_kwh))
    at2.metric("Total Energy Cost", fmt_cost(_at_total_cost))
    at3.metric("Cost Per kWh", f"${ENERGY_RATE:.2f}")

    # Vertical bar chart — scales well across years
    y_at_max = _at_monthly["_mwh"].max() * 1.35 if not _at_monthly.empty else 1
    _n_months = len(_at_monthly)
    _bar_chart_height = max(380, min(520, 320 + _n_months * 4))
    fig_at = go.Figure(go.Bar(
        x=_at_monthly["_label"],
        y=_at_monthly["_mwh"],
        marker_color=C_NAVY,
        text=[f"{v:.1f}" for v in _at_monthly["_mwh"]],
        textposition="outside",
        textfont=dict(size=max(9, min(16, int(340 / max(_n_months, 1)))), color="#374151", family="Inter", weight=700),
        hovertemplate="<b>%{x}</b><br>%{y:.1f} MWh  ·  $%{customdata:,.0f}<extra></extra>",
        customdata=_at_monthly["kWh"] * ENERGY_RATE,
    ))
    _tick_angle = -45 if _n_months > 18 else 0
    _tick_size  = max(9, min(16, int(340 / max(_n_months, 1))))
    fig_at.update_layout(
        **plot_base(height=_bar_chart_height),
        bargap=0.25, yaxis_title="MWh", xaxis_title="",
    )
    fig_at.update_xaxes(tickangle=_tick_angle, tickfont=dict(size=_tick_size, family="Inter", color=PLOT_TEXT, weight=700))
    fig_at.update_yaxes(range=[0, y_at_max], tickfont=dict(size=14, family="Inter", color=PLOT_TEXT, weight=700))
    st.plotly_chart(fig_at, use_container_width=True)

    if not selected_weeks:
        st.markdown(
            '<div class="alert-blue" style="margin-top:4px;">'
            '👈  Select a time period from the sidebar to see detailed building breakdowns.</div>',
            unsafe_allow_html=True)

    else:
        missing_blds = [b for b, s in BUILDINGS_STATUS.items() if s not in ("ok", "review")]
        if missing_blds:
            st.markdown(
                f'<div class="alert-amber">⚠️ <b>Missing Data:</b> '
                f'{", ".join(sorted(missing_blds))} have no FTP sensor data. '
                f'See the Data Integrity tab for details.</div>',
                unsafe_allow_html=True)

        # Campus KPIs
        st.markdown('<div class="sec-label">Consumption During Selected Periods — All Buildings</div>', unsafe_allow_html=True)
        k1, k2 = st.columns(2)
        k1_label = (f"Energy During — {period_label(sorted_sel[0])}"
                    if len(sorted_sel) == 1
                    else f"Energy During — {len(sorted_sel)} Periods Combined")
        k1.metric(k1_label, fmt_kwh(campus_total_sel))
        k2.metric(f"Estimated Energy Cost (@ ${ENERGY_RATE}/kWh)", fmt_cost(campus_total_cost))

        # All Buildings chart
        max_periods = 4
        chart_weeks = sorted_sel[-max_periods:]
        n_periods   = len(chart_weeks)
        chart_title = (f"All Buildings — {period_label(chart_weeks[0])}"
                       if n_periods == 1
                       else f"All Buildings — {period_label(chart_weeks[0])} to {period_label(chart_weeks[-1])}")
        st.markdown(f'<div class="sec-label">{chart_title}</div>', unsafe_allow_html=True)

        if n_periods == 1:
            ldf = (by_bld[by_bld["week"] == chart_weeks[0]]
                   .sort_values("kWh", ascending=True).copy())
            ldf["disp"] = ldf["kWh"] / 1000
            fig_all = go.Figure(go.Bar(
                name=period_label(chart_weeks[0]),
                y=ldf["building"], x=ldf["disp"],
                orientation="h", marker_color=C_NAVY,
                text=[f"{v:.1f}" for v in ldf["disp"]],
                textposition="outside",
                textfont=dict(size=19, color="#111827", family="Inter", weight=700),
                hovertemplate="<b>%{y}</b><br>%{x:.1f} MWh<extra></extra>",
            ))
            fig_all.update_layout(
                **plot_base(height=max(340, len(ldf) * 68)),
                xaxis_title="MWh", yaxis_title="", showlegend=False)
            fig_all.update_yaxes(tickfont=dict(size=17, color="#111827", family="Inter", weight=700))
            fig_all.update_xaxes(tickfont=dict(size=17, color="#111827", family="Inter", weight=700))
            st.plotly_chart(fig_all, use_container_width=True)
        else:
            palette = [C_NAVY, "#3b82f6", "#6366f1", C_SLATE]
            all_blds = sorted(by_bld[by_bld["week"].isin(chart_weeks)]["building"].unique())
            latest_bld_kwh = (by_bld[by_bld["week"] == chart_weeks[-1]]
                              .set_index("building")["kWh"].reindex(all_blds).fillna(0))
            all_blds_sorted = latest_bld_kwh.sort_values(ascending=True).index.tolist()
            fig_all = go.Figure()
            for idx, wk in enumerate(chart_weeks):
                wk_data = (by_bld[by_bld["week"] == wk]
                           .set_index("building")["kWh"]
                           .reindex(all_blds_sorted).fillna(0) / 1000)
                fig_all.add_trace(go.Bar(
                    name=period_label(wk),
                    y=all_blds_sorted, x=wk_data.values,
                    orientation="h",
                    marker_color=palette[idx % len(palette)],
                    text=[f"{v:.1f}" if v > 0 else "" for v in wk_data.values],
                    textposition="outside",
                    textfont=dict(size=19, color="#111827", family="Inter", weight=700),
                    hovertemplate=f"<b>%{{y}}</b><br>{period_label(wk)}: %{{x:.1f}} MWh<extra></extra>",
                ))
            fig_all.update_layout(
                **plot_base(height=max(380, len(all_blds_sorted) * 82)),
                barmode="group", bargap=0.15, bargroupgap=0.05,
                xaxis_title="MWh", yaxis_title="", showlegend=True,
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1,
                    font=dict(size=16, family="Inter", color=PLOT_TEXT),
                    bgcolor="#ffffff", bordercolor="#e2e8f0", borderwidth=1),
            )
            fig_all.update_yaxes(tickfont=dict(size=17, color="#111827", family="Inter", weight=700))
            fig_all.update_xaxes(tickfont=dict(size=17, color="#111827", family="Inter", weight=700))
            st.plotly_chart(fig_all, use_container_width=True)

        # Building detail
        st.markdown('<div class="sec-label">Building Detail — Select a Building to View Details</div>', unsafe_allow_html=True)

        # Build dropdown from ALL buildings present in ANY selected period,
        # sorted by total kWh across all selected periods (highest first).
        bld_kwh_all_sel = (by_bld[by_bld["week"].isin(sorted_sel)]
                           .groupby("building")["kWh"].sum()
                           .sort_values(ascending=False)
                           .reset_index())
        bld_order = bld_kwh_all_sel["building"].tolist()
        # Metric cards still reflect the latest selected week (0 if no data that week)
        bld_kwh_lkp = (by_bld[by_bld["week"] == latest_week]
                       .set_index("building")["kWh"].to_dict())

        sel_bld = st.selectbox(
            "Select a building (sorted highest to lowest kWh)",
            bld_order, index=0,
            format_func=lambda b: b,
            label_visibility="collapsed")

        if BUILDINGS_STATUS.get(sel_bld, "ok") == "review":
            st.markdown(
                f'<div class="alert-amber">⚠️ <b>{sel_bld}</b> — '
                f'Only ~25% of expected daily 15-minute intervals received. '
                f'The kWh shown may be understated.</div>',
                unsafe_allow_html=True)

        b_cur  = (by_bld[(by_bld["building"] == sel_bld) &
                         (by_bld["week"].isin(sorted_sel))]["kWh"].sum())
        b_cost = b_cur * ENERGY_RATE
        # Short display name for the metric card only — prevents long names from
        # wrapping to a second line in Streamlit's uppercase metric label.
        # Does NOT affect the dropdown, trend chart title, or alert banners.
        _bld_short = "Wine Spectator LC" if sel_bld == "Wine Spectator Learning Ctr" else sel_bld

        bm1, bm2 = st.columns(2)
        bm1_label = (f"{_bld_short} — {period_label(sorted_sel[0])}"
                     if len(sorted_sel) == 1
                     else f"{_bld_short} — {len(sorted_sel)} Selected Periods")
        bm2_label = (f"Estimated Cost (@ ${ENERGY_RATE}/kWh)"
                     if len(sorted_sel) == 1
                     else f"Combined Cost of {len(sorted_sel)} Periods (@ ${ENERGY_RATE}/kWh)")
        bm1.metric(bm1_label, fmt_kwh(b_cur))
        bm2.metric(bm2_label, fmt_cost(b_cost))

        st.markdown(
            f'<div style="font-size:1.05rem;font-weight:700;color:#111827;font-family:Inter,sans-serif;'
            f'margin-top:6px;margin-bottom:2px;">{sel_bld} — {time_filter} Trend</div>',
            unsafe_allow_html=True)

        bld_trend = (by_bld[
            (by_bld["building"] == sel_bld) &
            (by_bld["week"].isin(sorted_sel))
        ].sort_values("week").copy())
        if len(bld_trend) >= 1:
            bld_trend["label"] = bld_trend["week"].apply(period_label)
            bld_trend["disp"]  = bld_trend["kWh"] / 1000
            # Fix: bars with 0 kWh must show as exactly 0 (no rendering artefact)
            bld_trend["disp"] = bld_trend["disp"].clip(lower=0.0)
            fig_trend = go.Figure(go.Bar(
                x=bld_trend["label"], y=bld_trend["disp"],
                marker_color=C_NAVY,
                text=[f"{v:.1f} MWh" if v > 0 else "0" for v in bld_trend["disp"]],
                textposition="outside",
                textfont=dict(size=16, color=PLOT_TEXT, family="Inter", weight=700),
                hovertemplate="<b>%{x}</b><br>%{y:.1f} MWh<extra></extra>",
                showlegend=False,
                base=0,
            ))
            yt = bld_trend["disp"].max() * 1.3 if (not bld_trend.empty and bld_trend["disp"].max() > 0) else 1
            fig_trend.update_layout(**plot_base(height=280), bargap=0.45, yaxis_title="MWh")
            fig_trend.update_yaxes(range=[0, yt], tickfont=dict(size=16, family="Inter", weight=700))
            fig_trend.update_xaxes(tickfont=dict(size=16, family="Inter", color=PLOT_TEXT, weight=700))
            st.plotly_chart(fig_trend, use_container_width=True)

        # Total campus energy — selected periods
        st.markdown('<div class="sec-label">Total Campus Energy — All Selected Periods</div>',
                    unsafe_allow_html=True)
        campus_by_week = (by_bld[by_bld["week"].isin(sorted_sel)]
                          .groupby("week")["kWh"].sum()
                          .reset_index().sort_values("week"))
        campus_by_week["label"] = campus_by_week["week"].apply(period_label)
        campus_by_week["disp"]  = campus_by_week["kWh"] / 1000
        fig_campus = go.Figure(go.Bar(
            x=campus_by_week["label"],
            y=campus_by_week["disp"],
            marker_color=C_NAVY,
            text=[f"{v:.1f} MWh" for v in campus_by_week["disp"]],
            textposition="outside",
            textfont=dict(size=16, color=PLOT_TEXT, family="Inter", weight=700),
            hovertemplate="<b>%{x}</b><br>%{y:.1f} MWh<br>$%{customdata:,.0f}<extra></extra>",
            customdata=campus_by_week["kWh"] * ENERGY_RATE,
        ))
        y_max = campus_by_week["disp"].max() * 1.3 if not campus_by_week.empty else 1
        fig_campus.update_layout(**plot_base(height=300), bargap=0.45, yaxis_title="MWh")
        fig_campus.update_yaxes(range=[0, y_max], tickfont=dict(size=16, family="Inter", weight=700))
        fig_campus.update_xaxes(tickfont=dict(size=16, family="Inter", color=PLOT_TEXT, weight=700))
        st.plotly_chart(fig_campus, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# LEADERBOARD TAB
# ══════════════════════════════════════════════════════════════════════════════
elif active_tab == "Leaderboard":

    if not selected_weeks:
        st.title("Building Energy Leaderboard")
        st.markdown(
            '<div class="alert-blue" style="margin-top:8px;">'
            '👈  Select at least two periods from the sidebar to unlock leaderboard rankings.</div>',
            unsafe_allow_html=True)
        st.stop()

    st.markdown(
        f'<div style="width:100%;margin-bottom:24px;border-radius:12px;overflow:hidden;'
        f'box-shadow:0 4px 20px rgba(0,0,0,0.18);border:1px solid rgba(255,255,255,0.10);">'
        f'<img src="data:image/png;base64,{_LOGO_B64_LB}" '
        f'style="width:100%;height:auto;display:block;" '
        f'alt="SSU Campus Energy Dashboard"/>'
        f'</div>',
        unsafe_allow_html=True)
    hcol_l2, hcol_r2 = st.columns([3, 1])
    with hcol_l2:
        st.title("Building Energy Leaderboard")
        st.markdown(
            '<p style="font-size:1.05rem;color:#6b7280;margin-top:2px;line-height:1.5;">'
            'Ranked by <b style="color:#111827">% reduction</b> compared to the prior selected week.</p>',
            unsafe_allow_html=True)

    lb_latest = sorted_sel[-1]
    lb_prev   = sorted_sel[-2] if len(sorted_sel) >= 2 else None

    with hcol_r2:
        cmp_str = (f"{period_label(lb_prev)}  vs  {period_label(lb_latest)}"
                   if lb_prev else period_label(lb_latest))
        st.markdown(
            f'<div style="margin-top:32px"><div class="rw-box">'
            f'<span class="rw-label">Comparing</span>'
            f'<span class="rw-value">{cmp_str}</span>'
            f'</div></div>', unsafe_allow_html=True)

    if lb_prev is None:
        st.info("Select two or more weeks in the sidebar to unlock the leaderboard rankings.")
        st.stop()

    c_df = (by_bld[by_bld["week"] == lb_latest][["building", "kWh"]]
            .rename(columns={"kWh": "kWh_c"}))
    p_df = (by_bld[by_bld["week"] == lb_prev][["building", "kWh"]]
            .rename(columns={"kWh": "kWh_p"}))
    cmp  = pd.merge(c_df, p_df, on="building", how="outer").fillna(0)
    cmp  = cmp[(cmp["kWh_c"] > 0) | (cmp["kWh_p"] > 0)].copy()
    cmp["delta_kwh"]  = cmp["kWh_p"] - cmp["kWh_c"]
    cmp["delta_pct"]  = cmp.apply(
        lambda r: r["delta_kwh"] / r["kWh_p"] * 100 if r["kWh_p"] > 0 else 0.0, axis=1)
    cmp["cost_saved"] = cmp["delta_kwh"] * ENERGY_RATE

    all_pvt = (by_bld.pivot_table(index="week", columns="building",
                                   values="kWh", aggfunc="sum").fillna(0).sort_index())
    streak_map = {}
    for b in all_pvt.columns:
        s, k = all_pvt[b].values, 0
        for i in range(len(s) - 1, 0, -1):
            if s[i] < s[i - 1]: k += 1
            else: break
        streak_map[b] = k
    cmp["streak"] = cmp["building"].map(streak_map).fillna(0).astype(int)

    lb = cmp.sort_values(["delta_pct", "delta_kwh"], ascending=[False, False]).reset_index(drop=True)

    tot_c    = float(cmp["kWh_c"].sum())
    tot_p    = float(cmp["kWh_p"].sum())
    tot_pct  = (tot_p - tot_c) / tot_p * 100 if tot_p > 0 else 0.0
    n_better = int((cmp["delta_pct"] > 0.5).sum())
    n_worse  = int((cmp["delta_pct"] < -0.5).sum())
    d_col    = C_GREEN if tot_pct >= 0 else C_RED

    st.markdown(
        f'<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px;margin-top:8px;">'
        f'<div style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:7px 14px;font-size:0.92rem;color:#4b5563;font-weight:500;">'
        f'🏫 <b style="color:#111827">{len(lb)}</b> buildings ranked</div>'
        f'<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:7px 14px;font-size:0.92rem;color:#166534;font-weight:600;">'
        f'✅ {n_better} used less</div>'
        f'<div style="background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:7px 14px;font-size:0.92rem;color:#991b1b;font-weight:600;">'
        f'⚠️ {n_worse} used more</div>'
        f'<div style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:7px 14px;font-size:0.92rem;color:#4b5563;font-weight:500;">'
        f'Campus: <b style="color:{d_col}">{tot_pct:+.1f}%</b></div>'
        f'</div>', unsafe_allow_html=True)

    rank_cls  = ["gold", "silver", "bronze"]
    rows_html = ""
    for i, row in lb.iterrows():
        pct      = float(row["delta_pct"])
        kwh_abs  = abs(int(float(row["delta_kwh"])))
        saved    = pct > 0.5
        neutral  = abs(pct) <= 0.5
        bld      = str(row["building"])
        p_kwh    = fmt_kwh(float(row["kWh_p"]))
        c_kwh    = fmt_kwh(float(row["kWh_c"]))
        cost_abs = abs(float(row["cost_saved"]))

        if saved:
            pts_col  = C_GREEN;  pct_disp = f"+{pct:.1f}%"
            act_str  = f"{fmt_kwh(kwh_abs)} saved"
            cost_str = f"💰 {fmt_cost(cost_abs)} saved"
        elif neutral:
            pts_col  = C_MUTED;  pct_disp = "≈ 0%"
            act_str  = "No significant change";  cost_str = ""
        else:
            pts_col  = C_RED;    pct_disp = f"{pct:.1f}%"
            act_str  = f"{fmt_kwh(kwh_abs)} more used"
            cost_str = f"💸 {fmt_cost(cost_abs)} extra"

        rc  = rank_cls[i] if i < 3 else ""
        rd  = f"#{i + 1}"
        streak_tag = (f'<span class="streak">🔥 {int(row["streak"])}w streak</span>'
                      if row["streak"] > 0 else "")
        gap_tag = ""
        if BUILDINGS_STATUS.get(bld) == "review":
            gap_tag = ('<span style="font-size:0.72rem;font-weight:700;color:#92400e;'
                       'background:#fef3c7;border-radius:4px;padding:2px 7px;margin-left:7px;">'
                       'PARTIAL DATA</span>')

        rows_html += (
            '<div class="lb-row">'
            f'<div class="lb-rank {rc}">{rd}</div>'
            '<div style="flex:1;min-width:0">'
            f'<div class="lb-name">{bld}{gap_tag}</div>'
            '<div class="lb-sub">'
            f'<span style="color:{pts_col};font-weight:700">{act_str}</span>'
            + (f'  ·  {cost_str}' if cost_str else '') +
            f'<br><span style="color:#9ca3af;font-size:0.82rem">'
            f'{period_label(lb_prev)}: {p_kwh} → {period_label(lb_latest)}: {c_kwh}</span>'
            '</div></div>'
            + streak_tag +
            f'<div style="text-align:right;min-width:88px">'
            f'<div class="lb-pct" style="color:{pts_col}">{pct_disp}</div>'
            f'<div class="lb-pct-lbl">% change</div>'
            f'</div></div>'
        )
    st.markdown(rows_html, unsafe_allow_html=True)

    st.markdown('<div class="sec-label">Highlights</div>', unsafe_allow_html=True)
    saved_df  = lb[lb["delta_pct"] > 0.5]
    wasted_df = lb[lb["delta_pct"] < -0.5]
    streak_df = lb[lb["streak"] > 0].sort_values("streak", ascending=False)

    hc1, hc2, hc3 = st.columns(3)
    if not saved_df.empty:
        t = saved_df.iloc[0]
        hc1.metric("🥇 Best Reduction", t["building"],
                   f"{float(t['delta_pct']):.1f}%  ·  {fmt_kwh(int(float(t['delta_kwh'])))} saved")
    else:
        hc1.metric("🥇 Best Reduction", "—", "No reductions this period")

    if not wasted_df.empty:
        w = wasted_df.iloc[-1]
        hc2.metric("⚠️ Highest Increase", w["building"],
                   f"{abs(float(w['delta_pct'])):.1f}%  ·  {fmt_cost(abs(float(w['cost_saved'])))} extra")
    else:
        hc2.metric("⚠️ Highest Increase", "—", "All buildings improved 🎉")

    if not streak_df.empty:
        s = streak_df.iloc[0]
        hc3.metric("🔥 Longest Streak", s["building"],
                   f"{int(s['streak'])} week{'s' if s['streak'] != 1 else ''} of reductions")
    else:
        hc3.metric("🔥 Longest Streak", "—", "Reduce 2+ weeks in a row to earn one")

    st.markdown('<div class="sec-label">Campus Goal — 5% Weekly Reduction</div>',
                unsafe_allow_html=True)
    GOAL     = 5.0
    progress = min(max(-tot_pct / GOAL * 100, 0.0), 100.0) if tot_pct < 0 else min(tot_pct / GOAL * 100, 100.0)
    achieved = tot_pct >= GOAL
    bar_col  = C_GREEN if achieved else C_AMBER
    txt_col  = "#166534" if achieved else "#92400e"

    if achieved:
        status = f"🎉 Goal achieved! Campus used {tot_pct:.1f}% less this period."
    elif tot_pct > 0:
        status = f"Reduced by {tot_pct:.1f}% — {GOAL - tot_pct:.1f}% more to hit the {GOAL:.0f}% target."
    else:
        status = f"Campus energy up {abs(tot_pct):.1f}% — need to cut {GOAL + abs(tot_pct):.1f}% to reach {GOAL:.0f}%."

    st.markdown(f"""
<div class="goal-box">
  <div class="goal-lbl">Weekly Campus Target — {GOAL:.0f}% Reduction</div>
  <div class="goal-status" style="color:{txt_col}">{status}</div>
  <div class="prog-bg"><div class="prog-fill" style="width:{progress:.1f}%;background:{bar_col}"></div></div>
  <div style="display:flex;justify-content:space-between;font-size:0.88rem;color:{C_MUTED};margin-top:6px;font-weight:500;">
    <span>{progress:.0f}% of goal reached</span>
    <span>Campus change: {tot_pct:+.1f}%  ·  Target: -{GOAL:.0f}%</span>
  </div>
</div>""", unsafe_allow_html=True)



# ══════════════════════════════════════════════════════════════════════════════
# THERMAL TAB
# ══════════════════════════════════════════════════════════════════════════════
elif active_tab == "Thermal":

    st.title("🔥 Thermal Energy Usage")
    st.markdown(
        '<p style="font-size:1.05rem;color:#6b7280;margin-top:2px;line-height:1.5;">'
        'Thermal energy (BTU/kBTU meters converted to kWh) as a proportion of total campus electricity. '
        'Thermal includes heating hot water and chilled water cooling loops.</p>',
        unsafe_allow_html=True)

    # ── Thermal conversion note ──────────────────────────────────────────────
    # Thermal kWh comes from BTU and kBTU sensors in df_all (already converted by pipeline).
    # We identify thermal buildings as those that ONLY have BTU/kBTU sources (no direct kWh electric meter)
    # vs electric buildings. The pipeline stores everything in kWh already, so we use
    # the SENSOR_REGISTRY to classify each building's contribution.

    # Buildings with thermal sensors
    _thermal_buildings = set()
    _electric_buildings = set()
    for _b, _sid, _util, _unit, _st, _notes in SENSOR_REGISTRY:
        if _util == "Thermal" and _st == "OK":
            _thermal_buildings.add(_b)
        if _util == "Electric" and _st == "OK":
            _electric_buildings.add(_b)

    # BTU conversion factor used in pipeline (1 BTU = 0.000293071 kWh)
    # Thermal fraction: approximate — buildings with thermal sensors contribute their kWh
    # as thermal. We compute per-building totals from df_all.
    # Since thermal and electric are summed into kWh in df_all already,
    # we split by building type using the registry.

    # All-time monthly thermal data
    _th_at = df_all.dropna(subset=["_wstart"]).copy()
    _th_at["_month"] = _th_at["_wstart"].dt.to_period("M")

    _th_thermal = _th_at[_th_at["building"].isin(_thermal_buildings)]
    _th_electric = _th_at[_th_at["building"].isin(_electric_buildings) & ~_th_at["building"].isin(_thermal_buildings)]
    _th_all_monthly = _th_at.groupby("_month")["kWh"].sum().reset_index().sort_values("_month")
    _th_therm_monthly = _th_thermal.groupby("_month")["kWh"].sum().reset_index().sort_values("_month")

    _th_all_monthly["_label"] = _th_all_monthly["_month"].dt.strftime("%b %Y")
    _th_therm_monthly = _th_therm_monthly.rename(columns={"kWh": "thermal_kWh"})
    _th_merged = pd.merge(
        _th_all_monthly.rename(columns={"kWh": "total_kWh"}),
        _th_therm_monthly[["_month", "thermal_kWh"]],
        on="_month", how="left"
    ).fillna({"thermal_kWh": 0.0})
    _th_merged["electric_kWh"] = (_th_merged["total_kWh"] - _th_merged["thermal_kWh"]).clip(lower=0)
    _th_merged["thermal_pct"] = (_th_merged["thermal_kWh"] / _th_merged["total_kWh"].replace(0, float("nan")) * 100).fillna(0)

    _th_total_kwh   = float(_th_merged["total_kWh"].sum())
    _th_thermal_kwh = float(_th_merged["thermal_kWh"].sum())
    _th_electric_kwh = float(_th_merged["electric_kWh"].sum())
    _th_avg_pct = (_th_thermal_kwh / _th_total_kwh * 100) if _th_total_kwh > 0 else 0.0
    _th_total_cost   = _th_total_kwh * ENERGY_RATE
    _th_thermal_cost = _th_thermal_kwh * ENERGY_RATE

    st.markdown('<div class="sec-label">All-Time Thermal Overview</div>', unsafe_allow_html=True)
    tc1, tc2, tc3 = st.columns(3)
    tc1.metric("Total Campus kWh (All Time)", fmt_kwh(_th_total_kwh))
    tc2.metric("Thermal Portion (kWh equiv)", fmt_kwh(_th_thermal_kwh))
    tc3.metric("Avg Thermal Share", f"{_th_avg_pct:.1f}%")

    # Stacked bar chart — thermal vs non-thermal by month
    st.markdown('<div class="sec-label">Monthly Energy Split — Thermal vs Electric</div>', unsafe_allow_html=True)
    _n_th_months = len(_th_merged)
    _th_tick_angle = -45 if _n_th_months > 18 else 0
    _th_tick_size  = max(9, min(15, int(340 / max(_n_th_months, 1))))
    fig_th_stack = go.Figure()
    fig_th_stack.add_trace(go.Bar(
        name="Electric (kWh meters)",
        x=_th_merged["_label"],
        y=_th_merged["electric_kWh"] / 1000,
        marker_color=C_NAVY,
        hovertemplate="<b>%{x}</b><br>Electric: %{y:.1f} MWh<extra></extra>",
    ))
    fig_th_stack.add_trace(go.Bar(
        name="Thermal (BTU/kBTU → kWh)",
        x=_th_merged["_label"],
        y=_th_merged["thermal_kWh"] / 1000,
        marker_color="#ef4444",
        hovertemplate="<b>%{x}</b><br>Thermal: %{y:.1f} MWh<extra></extra>",
    ))
    fig_th_stack.update_layout(
        **plot_base(height=max(380, min(520, 320 + _n_th_months * 4))),
        barmode="stack", bargap=0.25, yaxis_title="MWh",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1,
                    font=dict(size=14, family="Inter"), bgcolor="#ffffff",
                    bordercolor="#e2e8f0", borderwidth=1),
    )
    fig_th_stack.update_xaxes(tickangle=_th_tick_angle, tickfont=dict(size=_th_tick_size, family="Inter", color=PLOT_TEXT, weight=700))
    fig_th_stack.update_yaxes(tickfont=dict(size=14, family="Inter", color=PLOT_TEXT, weight=700))
    st.plotly_chart(fig_th_stack, use_container_width=True)

    # Thermal % over time line chart
    st.markdown('<div class="sec-label">Thermal Share (%) Over Time</div>', unsafe_allow_html=True)
    fig_th_pct = go.Figure(go.Scatter(
        x=_th_merged["_label"],
        y=_th_merged["thermal_pct"],
        mode="lines+markers",
        line=dict(color="#ef4444", width=2.5),
        marker=dict(size=7, color="#ef4444"),
        hovertemplate="<b>%{x}</b><br>Thermal: %{y:.1f}%<extra></extra>",
        name="Thermal %",
    ))
    fig_th_pct.update_layout(
        **plot_base(height=280),
        yaxis_title="Thermal %",
    )
    fig_th_pct.update_xaxes(tickangle=_th_tick_angle, tickfont=dict(size=_th_tick_size, family="Inter", color=PLOT_TEXT, weight=700))
    fig_th_pct.update_yaxes(ticksuffix="%", tickfont=dict(size=14, family="Inter", color=PLOT_TEXT, weight=700))
    st.plotly_chart(fig_th_pct, use_container_width=True)

    # If a time period is selected, show building-level thermal breakdown
    if selected_weeks:
        st.markdown('<div class="sec-label">Thermal Breakdown — Selected Periods</div>', unsafe_allow_html=True)
        _th_sel = df_view[df_view["week"].isin(sorted_sel)].copy()
        _th_bld = _th_sel.groupby("building")["kWh"].sum().reset_index()
        _th_bld["is_thermal"] = _th_bld["building"].isin(_thermal_buildings)
        _th_bld_thermal = _th_bld[_th_bld["is_thermal"]].sort_values("kWh", ascending=False)
        _th_bld_total = float(_th_bld["kWh"].sum())
        _th_bld_th_total = float(_th_bld_thermal["kWh"].sum())

        tsel1, tsel2, tsel3 = st.columns(3)
        tsel1.metric("Total Energy (Selected)", fmt_kwh(_th_bld_total))
        tsel2.metric("Thermal Energy (Selected)", fmt_kwh(_th_bld_th_total))
        tsel3.metric("Thermal Share", f"{(_th_bld_th_total/_th_bld_total*100) if _th_bld_total>0 else 0:.1f}%")

        if not _th_bld_thermal.empty:
            fig_th_bld = go.Figure(go.Bar(
                y=_th_bld_thermal["building"],
                x=_th_bld_thermal["kWh"] / 1000,
                orientation="h",
                marker_color="#ef4444",
                text=[f"{v/1000:.1f} MWh" for v in _th_bld_thermal["kWh"]],
                textposition="outside",
                textfont=dict(size=14, color="#111827", family="Inter", weight=700),
                hovertemplate="<b>%{y}</b><br>%{x:.1f} MWh<extra></extra>",
            ))
            fig_th_bld.update_layout(
                **plot_base(height=max(280, len(_th_bld_thermal) * 60)),
                xaxis_title="MWh", yaxis_title="",
            )
            st.plotly_chart(fig_th_bld, use_container_width=True)
        else:
            st.info("No thermal sensor data available for the selected period.")

        # Weekly trend for thermal
        _th_campus_week = (
            _th_sel[_th_sel["building"].isin(_thermal_buildings)]
            .groupby("week")["kWh"].sum().reset_index().sort_values("week")
        )
        if not _th_campus_week.empty:
            st.markdown('<div class="sec-label">Thermal Trend — Selected Periods</div>', unsafe_allow_html=True)
            _th_campus_week["label"] = _th_campus_week["week"].apply(period_label)
            _th_campus_week["disp"]  = _th_campus_week["kWh"] / 1000
            _th_campus_week["disp"]  = _th_campus_week["disp"].clip(lower=0.0)
            fig_th_trend = go.Figure(go.Bar(
                x=_th_campus_week["label"],
                y=_th_campus_week["disp"],
                marker_color="#ef4444",
                text=[f"{v:.1f} MWh" if v > 0 else "0" for v in _th_campus_week["disp"]],
                textposition="outside",
                textfont=dict(size=14, color=PLOT_TEXT, family="Inter", weight=700),
                hovertemplate="<b>%{x}</b><br>%{y:.1f} MWh Thermal<extra></extra>",
                base=0,
            ))
            _th_yt = _th_campus_week["disp"].max() * 1.3 if _th_campus_week["disp"].max() > 0 else 1
            fig_th_trend.update_layout(**plot_base(height=280), bargap=0.45, yaxis_title="MWh (Thermal)")
            fig_th_trend.update_yaxes(range=[0, _th_yt])
            st.plotly_chart(fig_th_trend, use_container_width=True)
    else:
        st.markdown(
            '<div class="alert-blue" style="margin-top:4px;">'
            '👈  Select a time period from the sidebar to see detailed thermal breakdowns by building.</div>',
            unsafe_allow_html=True)

    st.markdown(
        '<div style="font-size:0.85rem;color:#9ca3af;margin-top:12px;">'
        'Thermal readings include BTU and kBTU sensors (heating hot water &amp; chilled water loops) '
        'converted to kWh using pipeline constants: BTU × 0.000293071, kBTU × 0.293071. '
        'All underlying numbers are identical to the Overview page.'
        '</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# DATA INTEGRITY TAB
# ══════════════════════════════════════════════════════════════════════════════
elif active_tab == "DataIntegrity":

    st.markdown(
        f'<div style="width:100%;margin-bottom:24px;border-radius:12px;overflow:hidden;'
        f'box-shadow:0 4px 20px rgba(0,0,0,0.18);border:1px solid rgba(255,255,255,0.10);">'
        f'<img src="data:image/png;base64,{_LOGO_B64_DI}" '
        f'style="width:100%;height:auto;display:block;" '
        f'alt="SSU Campus Energy Dashboard"/>'
        f'</div>',
        unsafe_allow_html=True)
    st.title("Data Integrity Report")
    st.markdown(
        '<p style="font-size:1.05rem;color:#6b7280;margin-top:2px;line-height:1.5;">'
        'Full sensor registry, verified data, gap analysis, and deployment notes.</p>',
        unsafe_allow_html=True)

    # Source breakdown
    st.markdown('<div class="sec-label">Data Source Summary</div>', unsafe_allow_html=True)
    src1, src2, src3 = st.columns(3)
    src1.metric("Raw CSV Files Loaded", str(_n_raw_files))
    src2.metric("Dates from Raw CSVs", str(len(_raw_dates_loaded)))
    src3.metric("Total Weeks Available", str(len(all_weeks)))

    if _n_raw_files > 0:
        _raw_week_labels_di = [week_label(w) for w in sorted(_raw_weeks)]
        _weeks_str_di = ", ".join(_raw_week_labels_di) if len(_raw_week_labels_di) <= 4 else f"{len(_raw_week_labels_di)} weeks"
        st.markdown(
            f'<div class="alert-green">'
            f'✅ <b>Live Raw Data Active:</b> {_n_raw_files} raw CSV file(s) processed directly '
            f'using pipeline cleaning logic. Weeks sourced from raw files: <b>{_weeks_str_di}</b>. '
            f'All other weeks use weekly_energy.csv.</div>',
            unsafe_allow_html=True)

    # Latest week verified data table
    _di_latest   = all_weeks[-1]
    _di_earliest = all_weeks[0]
    wdf = df_all[df_all["week"] == _di_latest].sort_values("kWh", ascending=False)

    st.markdown(
        f'<div class="sec-label">Verified Data — {week_label(_di_latest)}'
        + (' <span style="color:#3b82f6;font-size:0.75rem;font-weight:700;'
           'background:#dbeafe;border-radius:4px;padding:2px 8px;margin-left:6px;">'
           '⚡ FROM RAW CSV</span>' if _di_latest in _raw_weeks else '') +
        '</div>',
        unsafe_allow_html=True)

    v_tbl = ('<table class="di-table"><thead><tr>'
             f'<th>Building</th><th>kWh</th><th>MWh</th>'
             f'<th>Est. Energy Cost @ ${ENERGY_RATE:.2f}/kWh equiv</th><th>Status</th>'
             '</tr></thead><tbody>')
    total_kwh = 0.0
    for _, r in wdf.iterrows():
        kwh   = r["kWh"]
        total_kwh += kwh
        bst   = BUILDINGS_STATUS.get(r["building"], "ok")
        smap  = {"ok": "OK", "review": "Review", "open": "Missing Data"}
        sbadge = badge_html(smap.get(bst, bst))
        src_badge = (' <span style="font-size:0.72rem;background:#dbeafe;color:#1e40af;'
                     'border-radius:3px;padding:1px 5px;font-weight:700;">RAW</span>'
                     if _di_latest in _raw_weeks else "")
        v_tbl += (f'<tr><td><b>{r["building"]}</b>{src_badge}</td>'
                  f'<td>{kwh:,.1f}</td><td>{kwh/1000:.2f}</td>'
                  f'<td>${kwh * ENERGY_RATE:,.0f}</td><td>{sbadge}</td></tr>')
    v_tbl += (f'<tr style="background:#f8fafc;font-weight:700;">'
              f'<td>CAMPUS TOTAL</td><td>{total_kwh:,.1f}</td><td>{total_kwh/1000:.2f}</td>'
              f'<td>${total_kwh * ENERGY_RATE:,.0f}</td><td></td></tr>')
    v_tbl += '</tbody></table>'
    st.markdown(f'<div class="card">{v_tbl}</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div style="font-size:0.85rem;color:#9ca3af;margin-top:8px;margin-bottom:4px;">'
        f'Showing most recent week: {week_label(_di_latest)}. '
        f'kWh includes both electric meters and thermal energy sensors (heating &amp; cooling loops) '
        f'converted to kWh. Gas and water meters currently have no data available.'
        f'</div>', unsafe_allow_html=True)

    # Building data status chart
    _bld_sensor_statuses = defaultdict(list)
    for _b, _sid, _util, _unit, _st, _notes in SENSOR_REGISTRY:
        _bld_sensor_statuses[_b].append(_st)

    _bld_chart_data = []
    for _b, _sts in _bld_sensor_statuses.items():
        _ok   = sum(1 for s in _sts if s in ("OK", "PGE"))
        _miss = sum(1 for s in _sts if s == "Missing")
        _rev  = sum(1 for s in _sts if s == "Review")
        _tot  = len(_sts)
        if _rev > 0 or (_ok > 0 and _miss > 0):
            _lbl = "Partial Data"; _col = "#d97706"; _fill = round(_ok / _tot, 4) if _tot else 0
        elif _miss == _tot:
            _lbl = "No Data"; _col = "#dc2626"; _fill = 0.0
        else:
            _lbl = "Active"; _col = "#16a34a"; _fill = 1.0
        _bld_chart_data.append({"building": _b, "label": _lbl, "color": _col,
                                 "fill": _fill, "ok": _ok, "total": _tot})
    _order_map = {"Active": 0, "Partial Data": 1, "No Data": 2}
    _bld_chart_data.sort(key=lambda x: (_order_map[x["label"]], x["building"]))

    _n_active  = sum(1 for d in _bld_chart_data if d["label"] == "Active")
    _n_partial = sum(1 for d in _bld_chart_data if d["label"] == "Partial Data")
    _n_nodata  = sum(1 for d in _bld_chart_data if d["label"] == "No Data")
    _partial_names = [d["building"] for d in _bld_chart_data if d["label"] == "Partial Data"]

    st.markdown('<div class="sec-label">Building Data Status</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="display:flex;gap:20px;flex-wrap:wrap;margin-bottom:14px;">'
        '<span style="font-family:Inter,sans-serif;font-size:0.88rem;font-weight:600;color:#16a34a;">'
        '● Active — all meters reporting</span>'
        '<span style="font-family:Inter,sans-serif;font-size:0.88rem;font-weight:600;color:#d97706;">'
        '● Partial — some meters missing</span>'
        '<span style="font-family:Inter,sans-serif;font-size:0.88rem;font-weight:600;color:#dc2626;">'
        '● No Data — no readings received</span>'
        '</div>', unsafe_allow_html=True)

    _blds_c  = [d["building"] for d in _bld_chart_data]
    _fills_c = [d["fill"]     for d in _bld_chart_data]
    _cols_c  = [d["color"]    for d in _bld_chart_data]
    _texts_inside = [
        f'{d["label"]}  ({d["ok"]}/{d["total"]} meters active)' if d["fill"] > 0 else ''
        for d in _bld_chart_data
    ]
    _texts_outside = [
        f'{d["label"]}  ({d["ok"]}/{d["total"]} meters active)' if d["fill"] == 0 else ''
        for d in _bld_chart_data
    ]

    fig_status = go.Figure()
    fig_status.add_trace(go.Bar(
        y=_blds_c, x=[1.0] * len(_bld_chart_data), orientation="h",
        marker_color="#f1f5f9", marker_line_width=0,
        showlegend=False, hoverinfo="skip",
    ))
    fig_status.add_trace(go.Bar(
        y=_blds_c, x=_fills_c, orientation="h",
        marker_color=_cols_c, marker_line_width=0,
        text=_texts_inside, textposition="inside", insidetextanchor="start",
        textfont=dict(size=12, color="#ffffff", family="Inter"),
        hovertemplate="<b>%{y}</b><br>%{customdata}<extra></extra>",
        customdata=[f'{d["label"]}  ({d["ok"]}/{d["total"]} meters active)' for d in _bld_chart_data],
        showlegend=False,
    ))
    fig_status.add_trace(go.Bar(
        y=_blds_c, x=[0.01 if d["fill"] == 0 else 0 for d in _bld_chart_data], orientation="h",
        marker_color='rgba(0,0,0,0)', marker_line_width=0,
        text=_texts_outside, textposition="outside",
        textfont=dict(size=11, family="Inter"),
        hoverinfo='skip', showlegend=False,
    ))
    fig_status.update_layout(
        paper_bgcolor=PLOT_BG, plot_bgcolor=PLOT_BG,
        font=dict(family="Inter, sans-serif", color=PLOT_TEXT, size=13),
        height=max(380, len(_bld_chart_data) * 36),
        barmode="overlay", bargap=0.28,
        margin=dict(l=8, r=20, t=20, b=8),
        xaxis=dict(
            range=[0, 1.0], tickformat=".0%", title="Meter Coverage",
            gridcolor=PLOT_GRID, zerolinecolor="#e2e8f0", linecolor="#e2e8f0",
            tickfont=dict(size=12, family="Inter", color=PLOT_TEXT),
        ),
        yaxis=dict(
            autorange="reversed", gridcolor="rgba(0,0,0,0)",
            zerolinecolor="#e2e8f0", linecolor="#e2e8f0",
            tickfont=dict(size=12, color="#111827", family="Inter"),
        ),
    )
    st.plotly_chart(fig_status, use_container_width=True)

    # Data summary cards
    st.markdown('<div class="sec-label">Data Summary</div>', unsafe_allow_html=True)

    _start_dt  = pd.to_datetime(_di_earliest)
    _end_dt    = pd.to_datetime(_di_latest) + pd.Timedelta(days=6)
    _start_str = _start_dt.strftime("%B %d, %Y") if _start_dt else _di_earliest
    _end_str   = _end_dt.strftime("%B %d, %Y")   if _end_dt   else _di_latest
    _now_str   = datetime.datetime.now().strftime("%B %d, %Y  —  %I:%M %p")
    _partial_note = (
        ", ".join(_partial_names) + " have partial meter coverage."
        if _partial_names else "No partial-coverage buildings."
    )

    _lbl_style = ('font-size:0.75rem;font-weight:700;color:#9ca3af;text-transform:uppercase;'
                  'letter-spacing:0.1em;font-family:Inter,sans-serif;')
    _val_style = 'font-size:1.05rem;font-weight:700;color:#111827;font-family:Inter,sans-serif;'

    ds1, ds2 = st.columns(2)
    ds1.markdown(
        f'<div class="card">'
        f'<div style="line-height:1;"><span style="{_lbl_style}">Starting Date</span></div>'
        f'<div style="margin:4px 0 18px;"><span style="{_val_style}">{_start_str}</span></div>'
        f'<div style="line-height:1;"><span style="{_lbl_style}">Latest Date in Database</span></div>'
        f'<div style="margin:4px 0 18px;"><span style="{_val_style}">{_end_str}</span></div>'
        f'<div style="line-height:1;"><span style="{_lbl_style}">Last Updated</span></div>'
        f'<div style="margin:4px 0 0;"><span style="{_val_style}">{_now_str}</span></div>'
        f'</div>', unsafe_allow_html=True)

    ds2.markdown(
        f'<div class="card">'
        f'<div style="line-height:1;"><span style="{_lbl_style}">Reporting Buildings</span></div>'
        f'<div style="margin:4px 0 18px;">'
        f'<span style="font-size:1.05rem;font-weight:700;color:#16a34a;font-family:Inter,sans-serif;">{_n_active} fully active</span>'
        f'<span style="font-size:1.05rem;font-weight:700;color:#d97706;font-family:Inter,sans-serif;margin-left:10px;">+ {_n_partial} partial</span></div>'
        f'<div style="line-height:1;"><span style="{_lbl_style}">Buildings with No Data</span></div>'
        f'<div style="margin:4px 0 18px;"><span style="font-size:1.05rem;font-weight:700;color:#dc2626;font-family:Inter,sans-serif;">{_n_nodata} buildings</span></div>'
        f'<div style="line-height:1;"><span style="{_lbl_style}">Partial Data Note</span></div>'
        f'<div style="margin:4px 0 0;"><span style="font-size:0.9rem;font-weight:500;color:#78350f;font-family:Inter,sans-serif;">{_partial_note}</span></div>'
        f'</div>', unsafe_allow_html=True)

    # Utility coverage
    st.markdown('<div class="sec-label">Utility Coverage</div>', unsafe_allow_html=True)
    u1, u2, u3 = st.columns(3)
    u1.markdown(
        '<div class="card"><div class="card-title">⚡ Electricity</div>'
        '<div style="font-size:0.95rem;color:#374151;line-height:1.8;margin-top:6px;">'
        '<b>Status:</b> Active for 8 buildings<br>'
        '<b>Source:</b> FTP interval meters (kWh)<br>'
        f'<b>Rate:</b> ${ENERGY_RATE:.2f}/kWh (estimated, adjustable in sidebar)'
        '</div></div>', unsafe_allow_html=True)
    u2.markdown(
        '<div class="card"><div class="card-title">🔥 Gas</div>'
        '<div style="font-size:0.95rem;color:#374151;line-height:1.8;margin-top:6px;">'
        '<b>Status:</b> No data available<br>'
        '<b>Meters:</b> Boiler Plant, Green Music Center, Schulz Info Center<br>'
        '<b>Note:</b> Meters registered but no readings received'
        '</div></div>', unsafe_allow_html=True)
    u3.markdown(
        '<div class="card"><div class="card-title">💧 Water</div>'
        '<div style="font-size:0.95rem;color:#374151;line-height:1.8;margin-top:6px;">'
        '<b>Status:</b> No data available<br>'
        '<b>Meter:</b> Green Music Center<br>'
        '<b>Note:</b> Meter registered but no readings received'
        '</div></div>', unsafe_allow_html=True)

    # Full sensor registry
    st.markdown('<div class="sec-label">Full Sensor Registry — All 37 Sensors</div>',
                unsafe_allow_html=True)
    tbl = ('<table class="di-table"><thead><tr>'
           '<th>Building</th><th>Sensor ID</th><th>Utility</th><th>Raw Unit</th>'
           '<th>Status</th><th>Notes</th>'
           '</tr></thead><tbody>')
    for bld, sid, util, unit, status, notes in SENSOR_REGISTRY:
        sbadge = badge_html(status)
        tbl += (f'<tr><td><b>{bld}</b></td>'
                f'<td><code style="background:#f1f5f9;padding:2px 6px;border-radius:3px;font-size:0.82rem">{sid}</code></td>'
                f'<td>{util}</td><td>{unit}</td><td>{sbadge}</td>'
                f'<td style="color:#6b7280;font-size:0.88rem">{notes}</td></tr>')
    tbl += '</tbody></table>'
    st.markdown(f'<div class="card" style="overflow-x:auto">{tbl}</div>', unsafe_allow_html=True)

    # Unit conversions
    st.markdown('<div class="sec-label">Unit Conversions Applied</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="card">'
        '<div style="font-size:0.95rem;color:#374151;line-height:2.2;">'
        '<span style="display:inline-block;background:#e8eef5;color:#1b3a5c;font-weight:600;padding:2px 12px;border-radius:6px;font-family:Inter,sans-serif;">BTU × 0.000293071 = kWh</span><br>'
        '<span style="display:inline-block;background:#e8eef5;color:#1b3a5c;font-weight:600;padding:2px 12px;border-radius:6px;font-family:Inter,sans-serif;">kBTU × 0.293071 = kWh</span><br>'
        '<span style="display:inline-block;background:#fff7ed;color:#92400e;font-weight:600;padding:2px 12px;border-radius:6px;font-family:Inter,sans-serif;">'
        '_MBTU cell value → remapped to kBTU before conversion (BMS label quirk)</span><br>'
        '<span style="display:inline-block;background:#e8eef5;color:#1b3a5c;font-weight:600;padding:2px 12px;border-radius:6px;font-family:Inter,sans-serif;">therm × 29.3071 = kWh</span><br>'
        '<span style="display:inline-block;background:#e8eef5;color:#1b3a5c;font-weight:600;padding:2px 12px;border-radius:6px;font-family:Inter,sans-serif;">kWh → kWh direct</span><br>'
        '<span style="display:inline-block;background:#e8eef5;color:#1b3a5c;font-weight:600;padding:2px 12px;border-radius:6px;font-family:Inter,sans-serif;">Water (gallon) → stored as-is, no conversion</span>'
        '</div></div>', unsafe_allow_html=True)

    # Pipeline info
    st.markdown('<div class="sec-label">Pipeline</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="card">'
        '<div style="font-size:0.95rem;color:#374151;line-height:1.9;">'
        '<b>Schedule:</b> Daily, 6 AM (cron job)<br>'
        '<b>DB:</b> 193.203.166.234 | u209446640_SSUEnergy<br>'
        '</div></div>', unsafe_allow_html=True)
