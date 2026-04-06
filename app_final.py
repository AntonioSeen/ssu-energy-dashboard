"""
SSU Campus Energy Dashboard — app_final.py
Clean, accurate, simple. Data verified against weekly_energy.csv (pipeline output).
Week: Feb 2–8, 2026 | 8 buildings | Campus total: 203,758 kWh
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

st.set_page_config(
    page_title="SSU Campus Energy Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

html, body, [class*="css"], p, span, div, label, button {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    font-size: 16px;
}
.stApp { background-color: #f4f6f8 !important; color: #111827 !important; }
.block-container { padding-top: 1.8rem !important; padding-bottom: 3rem !important; max-width: 1400px !important; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] { background-color: #1b3a5c !important; border-right: none !important; }
section[data-testid="stSidebar"] * { color: #c8d9ea !important; font-family: 'Inter', sans-serif !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #ffffff !important; font-weight: 700 !important; font-size: 1.1rem !important; }
section[data-testid="stSidebar"] .stRadio > label { color: #a3bcd0 !important; font-size: 0.82rem !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.1em !important; }
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label { font-size: 1.05rem !important; font-weight: 500 !important; color: #c8d9ea !important; text-transform: none !important; letter-spacing: 0 !important; }
section[data-testid="stSidebar"] .stMultiSelect > label,
section[data-testid="stSidebar"] .stSelectbox > label { color: #a3bcd0 !important; font-size: 0.82rem !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.1em !important; }
section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.12) !important; }

/* ── Sidebar toggle buttons — pure CSS, no JS ── */
button[data-testid="baseButton-headerNoPadding"] {
    position: relative !important;
    background: transparent !important;
    border: none !important;
    cursor: pointer !important;
    overflow: hidden !important;
}
button[data-testid="baseButton-headerNoPadding"] * {
    visibility: hidden !important;
    font-size: 0 !important;
    width: 0 !important;
    height: 0 !important;
}
button[data-testid="baseButton-headerNoPadding"]::before {
    content: "❮" !important;
    visibility: visible !important;
    position: absolute !important;
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    color: #c8d9ea !important;
    font-family: Arial, Helvetica, sans-serif !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;
    width: auto !important;
    height: auto !important;
}
[data-testid="collapsedControl"] { background-color: #1b3a5c !important; border-right: 2px solid #2a5180 !important; }
[data-testid="collapsedControl"] button { position: relative !important; overflow: hidden !important; }
[data-testid="collapsedControl"] button * { visibility: hidden !important; font-size: 0 !important; width: 0 !important; height: 0 !important; }
[data-testid="collapsedControl"] button::before {
    content: "❯" !important;
    visibility: visible !important;
    position: absolute !important;
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    color: #c8d9ea !important;
    font-family: Arial, Helvetica, sans-serif !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;
    width: auto !important;
    height: auto !important;
}

/* ── Headings ── */
h1 { font-family: 'Inter', sans-serif !important; font-size: 2.5rem !important; font-weight: 800 !important; color: #111827 !important; letter-spacing: -0.04em !important; line-height: 1.1 !important; margin-bottom: 2px !important; margin-top: 0 !important; }
h2, h3 { font-family: 'Inter', sans-serif !important; font-weight: 700 !important; color: #111827 !important; }

/* ── Metric cards ── */
[data-testid="stMetric"] { background: #ffffff !important; border: 1px solid #e2e8f0 !important; border-radius: 12px !important; padding: 20px 22px !important; box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important; }
[data-testid="stMetricLabel"] p { font-size: 0.82rem !important; font-weight: 700 !important; color: #6b7280 !important; text-transform: uppercase !important; letter-spacing: 0.1em !important; margin-bottom: 4px !important; }
[data-testid="stMetricValue"] { font-size: 2.2rem !important; font-weight: 800 !important; color: #111827 !important; letter-spacing: -0.03em !important; line-height: 1.15 !important; }
[data-testid="stMetricDelta"] { font-size: 0.92rem !important; font-weight: 600 !important; }
[data-testid="stMetricDelta"] svg { display: none !important; }

/* ── Section labels ── */
.sec-label { font-family: 'Inter', sans-serif; font-size: 0.78rem; font-weight: 700; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.12em; padding-bottom: 8px; border-bottom: 1px solid #e2e8f0; margin: 24px 0 16px 0; }

/* ── Report window ── */
.rw-box { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px 18px; text-align: right; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.rw-label { font-size: 0.72rem; font-weight: 700; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.1em; display: block; margin-bottom: 4px; }
.rw-value { font-size: 1.1rem; font-weight: 700; color: #111827; }

/* ── White cards ── */
.card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px 22px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.card-title { font-size: 1.1rem; font-weight: 700; color: #111827; margin-bottom: 4px; }
.card-sub { font-size: 0.88rem; color: #6b7280; margin-bottom: 14px; }

/* ── Top buildings bar list ── */
.topbld { margin-bottom: 14px; }
.topbld-header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 5px; }
.topbld-name { font-size: 1.0rem; font-weight: 600; color: #111827; }
.topbld-val { font-size: 0.95rem; font-weight: 600; color: #6b7280; }
.topbld-track { background: #f1f5f9; border-radius: 3px; height: 8px; overflow: hidden; }
.topbld-fill { height: 100%; background: #1b3a5c; border-radius: 3px; }

/* ── Alert banners ── */
.alert-red   { background: #fef2f2; border-left: 4px solid #dc2626; border-radius: 0 8px 8px 0; padding: 12px 16px; font-size: 0.95rem; color: #7f1d1d; font-weight: 500; margin-bottom: 12px; }
.alert-amber { background: #fffbeb; border-left: 4px solid #f59e0b; border-radius: 0 8px 8px 0; padding: 12px 16px; font-size: 0.95rem; color: #78350f; font-weight: 500; margin-bottom: 12px; }
.alert-blue  { background: #eff6ff; border-left: 4px solid #3b82f6; border-radius: 0 8px 8px 0; padding: 12px 16px; font-size: 0.95rem; color: #1e40af; font-weight: 500; margin-bottom: 12px; }

/* ── Leaderboard ── */
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

/* ── Goal box ── */
.goal-box { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 22px 24px; margin-top: 18px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.goal-lbl { font-size: 0.78rem; font-weight: 700; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px; }
.goal-status { font-size: 1.4rem; font-weight: 800; margin-bottom: 14px; line-height: 1.25; letter-spacing: -0.02em; }
.prog-bg { background: #e5e7eb; border-radius: 6px; height: 12px; overflow: hidden; margin-bottom: 8px; }
.prog-fill { height: 100%; border-radius: 6px; }

/* ── Data tables ── */
.di-table { width: 100%; border-collapse: collapse; font-size: 0.92rem; }
.di-table th { background: #f1f5f9; color: #374151; font-weight: 700; padding: 11px 14px; text-align: left; border-bottom: 2px solid #e2e8f0; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.08em; }
.di-table td { padding: 10px 14px; border-bottom: 1px solid #f1f5f9; color: #111827; vertical-align: middle; }
.di-table tr:hover td { background: #f8fafc; }
.badge { display: inline-block; padding: 3px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: 700; }
.badge-ok     { background: #dcfce7; color: #166534; }
.badge-open   { background: #fee2e2; color: #991b1b; }
.badge-review { background: #fef3c7; color: #92400e; }
.badge-skip   { background: #f1f5f9; color: #6b7280; }

.uni-label { font-size: 0.76rem; font-weight: 700; letter-spacing: 0.16em; text-transform: uppercase; color: #9ca3af; margin-bottom: 4px; }

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
# CONSTANTS  (fact-checked against weekly_energy.csv)
# ══════════════════════════════════════════════════════════════════════════════
WEEKLY_CSV  = "weekly_energy.csv"
ENERGY_RATE = 0.15      # $/kWh — PG&E commercial rate estimate

PLOT_BG   = "#ffffff"
PLOT_GRID = "#f1f5f9"
PLOT_TEXT = "#111827"
C_NAVY    = "#1b3a5c"
C_GREEN   = "#16a34a"
C_RED     = "#dc2626"
C_AMBER   = "#d97706"
C_MUTED   = "#6b7280"
C_SLATE   = "#64748b"

# Verified from raw FTP interval files + pipeline DB
BUILDINGS_STATUS = {
    "Green Music Center":          "ok",
    "Nichols Hall":                "ok",
    "Rachel Carson Hall":          "ok",
    "Wine Spectator Learning Ctr": "review",   # 75% data gaps
    "Student Center":              "ok",
    "Physical Education":          "ok",
    "Ives Hall":                   "ok",
    "Campus Misc":                 "ok",
}

SENSOR_REGISTRY = [
    ("Green Music Center",          "234ab131-e413ba29", "Electric", "kWh",   "OK",     "Primary electric — ~85 kWh per 15-min interval"),
    ("Green Music Center",          "1f98265e-39835c84", "Thermal",  "BTU",   "OK",     "Chilled hot water BTU"),
    ("Green Music Center",          "234aa956-82d369b2", "Thermal",  "kBTU",  "OK",     "Hot water BTU (labelled _MBTU in FTP — corrected to kBTU)"),
    ("Green Music Center",          "234aab84-c656a0e0", "Gas",      "therm", "Missing","100% missing from FTP"),
    ("Green Music Center",          "234aa782-f7b1eef2", "Water",    "gallon","Missing","Meter present — all NaN in FTP files"),
    ("Nichols Hall",                "234e3ee2-f6fcea18", "Thermal",  "BTU",   "OK",     "Active — ~20,000 kWh/day thermal"),
    ("Nichols Hall",                "234e3ee2-b06b6c8c", "Thermal",  "BTU",   "OK",     "Active but 0 BTU reported"),
    ("Nichols Hall",                "234e40da-635bc7c1", "Electric", "kWh",   "OK",     "Active but 0 kWh reported"),
    ("Physical Education",          "206db469-c986212b", "Electric", "kWh",   "OK",     "Consistent — ~11 kWh per 15-min"),
    ("Rachel Carson Hall",          "1f98265e-cbf77175", "Electric", "kWh",   "Missing","Missing from interval files — data from DB (Feb 2–5)"),
    ("Rachel Carson Hall",          "234aa121-a983880d", "Thermal",  "BTU",   "OK",     "Active; 1 interval missing per day"),
    ("Rachel Carson Hall",          "234aa43b-a73abf5e", "Thermal",  "BTU",   "OK",     "Active but 0 BTU"),
    ("Ives Hall",                   "234e3195-7d72fbdc", "Thermal",  "BTU",   "OK",     "Active — ~950–1,243 kWh/day thermal"),
    ("Ives Hall",                   "234e3195-c20a1a8e", "Thermal",  "BTU",   "OK",     "Active but 0 BTU"),
    ("Ives Hall",                   "206d9425-f3361ab6", "Electric", "kWh",   "OK",     "Active but 0 kWh (meter may be offline)"),
    ("Student Center",              "234e5dff-8d8eb031", "Thermal",  "BTU",   "OK",     "Active — variable daily"),
    ("Student Center",              "234e5dff-6fe20abd", "Thermal",  "BTU",   "OK",     "Active — secondary thermal"),
    ("Student Center",              "20c9aa07-acd1558a", "Electric", "kWh",   "OK",     "Active but 0 kWh reported"),
    ("Wine Spectator Learning Ctr", "250ea73e-3b55a6cf", "Electric", "kWh",   "Review", "75% data gaps — 24 of 96 intervals received daily"),
    ("Art Building",                "1f97c82e-36e60525", "Thermal",  "BTU",   "Missing","100% missing from FTP"),
    ("Art Building",                "1f97c82e-d1a92673", "Thermal",  "BTU",   "Missing","100% missing from FTP"),
    ("Boiler Plant",                "234a6e2b-318cf13d", "Gas",      "therm", "Missing","100% missing from FTP"),
    ("Darwin Hall",                 "267e6fd0-93d67a62", "Electric", "kWh",   "Missing","100% missing from FTP"),
    ("ETC",                         "1f97c82e-dd011464", "Electric", "kWh",   "Missing","100% missing from FTP"),
    ("Salazar Hall",                "20c9b2e1-d7263cf1", "Electric", "kWh",   "Missing","100% missing from FTP"),
    ("Salazar Hall",                "234e4c64-930d1fd6", "Electric", "kWh",   "Missing","100% missing from FTP"),
    ("Salazar Hall",                "20c9b4d5-5ea6aa0b", "Thermal",  "BTU",   "Missing","100% missing from FTP"),
    ("Schulz Info Center",          "1f97c82e-c34c4f2e", "Electric", "kWh",   "Missing","100% missing from FTP"),
    ("Schulz Info Center",          "1f97c82e-525ca261", "Thermal",  "BTU",   "Missing","100% missing from FTP"),
    ("Schulz Info Center",          "206e94b8-3b05cb50", "Gas",      "therm", "Missing","100% missing from FTP"),
    ("Stevenson Hall",              "251810ce-f429b841", "Electric", "kWh",   "Missing","100% missing from FTP"),
    ("Stevenson Hall",              "267fcb62-ed42e3b3", "Thermal",  "BTU",   "Missing","100% missing from FTP"),
    ("Student Health Center",       "234e61c5-021da430", "Thermal",  "BTU",   "OK",     "Active but 0 BTU"),
    ("Student Health Center",       "234e61c5-83f6cf71", "Thermal",  "BTU",   "OK",     "Active but 0 BTU"),
    ("Campus Misc",                 "214981c7-dd0b1593", "Electric", "kWh",   "PGE",    "pgeReports FTP folder"),
    ("Campus Misc",                 "214981c7-5530731e", "Electric", "kWh",   "PGE",    "pgeReports FTP folder"),
    ("Campus Misc",                 "214981c7-63077e46", "Electric", "kWh",   "PGE",    "pgeReports FTP folder"),
]


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def plot_base(height=300):
    return dict(
        paper_bgcolor=PLOT_BG, plot_bgcolor=PLOT_BG,
        font=dict(family="Inter, sans-serif", color=PLOT_TEXT, size=13),
        margin=dict(l=8, r=60, t=36, b=8),
        height=height,
        xaxis=dict(gridcolor=PLOT_GRID, zerolinecolor="#e2e8f0",
                   linecolor="#e2e8f0", tickfont=dict(size=13, family="Inter", color=PLOT_TEXT)),
        yaxis=dict(gridcolor=PLOT_GRID, zerolinecolor="#e2e8f0",
                   linecolor="#e2e8f0", tickfont=dict(size=13, family="Inter", color="#111827")),
    )

def week_label(w):
    """Convert '2026-02-02/2026-02-08' → 'Feb 2 – Feb 8, 2026'"""
    try:
        parts = str(w).split("/")
        start = pd.to_datetime(parts[0].strip())
        end   = pd.to_datetime(parts[1].strip()) if len(parts) > 1 else start + pd.Timedelta(days=6)
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

def top_bld_bar(name, kwh, max_kwh):
    pct  = kwh / max_kwh * 100 if max_kwh > 0 else 0
    disp = fmt_kwh(kwh)
    return (f'<div class="topbld">'
            f'<div class="topbld-header">'
            f'<span class="topbld-name">{name}</span>'
            f'<span class="topbld-val">{disp}</span>'
            f'</div>'
            f'<div class="topbld-track">'
            f'<div class="topbld-fill" style="width:{pct:.0f}%"></div>'
            f'</div></div>')

def badge_html(status):
    cls = {"OK":"badge-ok","Missing":"badge-open","Review":"badge-review",
           "PGE":"badge-skip"}.get(status, "badge-skip")
    label = "Missing Data" if status == "Missing" else status
    return f'<span class="badge {cls}">{label}</span>'


# ══════════════════════════════════════════════════════════════════════════════
# LOAD DATA
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=300)
def load_data():
    if not os.path.exists(WEEKLY_CSV):
        st.error("weekly_energy.csv not found. Run local_master_pipeline.py first.")
        st.stop()
    df = pd.read_csv(WEEKLY_CSV)
    df["week"] = df["week"].astype(str).str.strip()
    if "gas_therm"    not in df.columns: df["gas_therm"]    = 0.0
    if "water_gallon" not in df.columns: df["water_gallon"] = 0.0
    if "heating_dd"   not in df.columns: df["heating_dd"]   = 0.0
    df = df[df["kWh"] > 0].copy()
    return df

df_all    = load_data()
all_weeks = sorted(df_all["week"].unique())


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        '<div style="background:#163350;margin:-1rem -1rem 0 -1rem;padding:16px 18px 14px;text-align:center;">'
        '<div style="font-size:0.62rem;font-weight:700;letter-spacing:0.2em;text-transform:uppercase;'
        'color:#6a9cc0;margin-bottom:3px;">SONOMA STATE UNIVERSITY</div>'
        '<div style="font-size:1.1rem;font-weight:700;color:#ffffff;letter-spacing:-0.01em;">'
        '⚡ Campus Energy</div></div>',
        unsafe_allow_html=True)
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    st.markdown("**View Mode**")
    role = st.radio("mode", ["Student (Gamified)", "Admin (Basic)"],
                    label_visibility="collapsed")
    st.markdown("---")

    # Time filter — Weekly is default (Daily removed)
    st.markdown("**Time Range**")
    time_filter = st.radio("time", ["Weekly", "Monthly", "Yearly"],
                           horizontal=True, label_visibility="collapsed")

    def week_start(w):
        try:    return pd.to_datetime(str(w).split("/")[0])
        except: return pd.NaT

    df_all["_wstart"] = df_all["week"].map(week_start)

    if time_filter == "Weekly":
        parsed  = [(w, week_start(w)) for w in all_weeks]
        parsed  = [(w, d) for w, d in parsed if pd.notna(d)]
        avail_w = [w for w, d in parsed] or all_weeks
        # Default: last 1 week (no comparison by default — only 1 week exists)
        st.markdown("**Select up to 4 weeks**")
        selected_weeks = st.multiselect(
            "weeks", avail_w,
            default=[avail_w[-1]] if avail_w else [],
            format_func=week_label, label_visibility="collapsed")
        df_view      = df_all.copy()
        period_label = week_label

    elif time_filter == "Monthly":
        df_all["_period"] = df_all["_wstart"].dt.to_period("M").astype(str)
        monthly = (df_all.groupby(["_period","building"])
                   .agg(kWh=("kWh","sum"), gas_therm=("gas_therm","sum"),
                        water_gallon=("water_gallon","sum"))
                   .reset_index().rename(columns={"_period":"week"}))
        all_periods = sorted(monthly["week"].unique())
        def month_label(p):
            try:    return pd.to_datetime(p + "-01").strftime("%B %Y")
            except: return str(p)
        st.markdown("**Select up to 4 months**")
        selected_weeks = st.multiselect(
            "months", all_periods,
            default=[all_periods[-1]] if all_periods else [],
            format_func=month_label, label_visibility="collapsed")
        df_view      = monthly
        period_label = month_label

    else:  # Yearly
        df_all["_period"] = df_all["_wstart"].dt.year.astype(str)
        yearly = (df_all.groupby(["_period","building"])
                  .agg(kWh=("kWh","sum"), gas_therm=("gas_therm","sum"),
                       water_gallon=("water_gallon","sum"))
                  .reset_index().rename(columns={"_period":"week"}))
        all_periods = sorted(yearly["week"].unique())
        def year_label(p): return str(p)
        st.markdown("**Select years**")
        selected_weeks = st.multiselect(
            "years", all_periods,
            default=[all_periods[-1]] if all_periods else [],
            format_func=year_label, label_visibility="collapsed")
        df_view      = yearly
        period_label = year_label

    st.markdown("---")

    # Section nav
    st.markdown("**Section**")
    if role == "Student (Gamified)":
        nav_opts = ["📊 Overview", "🏆 Leaderboard", "🔍 Data Integrity"]
    else:
        nav_opts = ["📊 Overview", "🔍 Data Integrity"]
    _tab = st.radio("nav", nav_opts, label_visibility="collapsed")
    active_tab = ("Overview" if "Overview" in _tab else
                  "Leaderboard" if "Leaderboard" in _tab else "DataIntegrity")

    st.markdown("---")
    st.markdown(
        f'<div style="font-size:0.82rem;color:#6a9cc0;line-height:1.8;">'
        f'{len(all_weeks)} week(s) in database<br>'
        f'Latest: {week_label(all_weeks[-1]) if all_weeks else "—"}</div>',
        unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# GUARDS
# ══════════════════════════════════════════════════════════════════════════════
if not selected_weeks:
    st.warning("👈  Select at least one period from the sidebar.")
    st.stop()

# Enforce max 4 periods for the all-buildings chart
if len(selected_weeks) > 4:
    st.warning("Maximum 4 periods can be selected at once. Showing the most recent 4.")
    selected_weeks = sorted(selected_weeks)[-4:]

sorted_sel  = sorted(selected_weeks)
latest_week = sorted_sel[-1]

df_sel = df_view[df_view["week"].isin(sorted_sel)]
if df_sel.empty:
    st.warning("No data for the selected period.")
    st.stop()

by_bld = df_view.groupby(["week","building"])["kWh"].sum().reset_index()

campus_cur  = by_bld[by_bld["week"] == latest_week]["kWh"].sum()
campus_cost = campus_cur * ENERGY_RATE
scale       = "MWh" if campus_cur >= 1_000 else "kWh"

# For comparison: previous period (second-to-last if multiple selected)
prev_week = sorted_sel[-2] if len(sorted_sel) >= 2 else None
campus_prev = by_bld[by_bld["week"] == prev_week]["kWh"].sum() if prev_week else None
pct_change  = ((campus_cur - campus_prev) / campus_prev * 100) if campus_prev else None

n_missing = sum(1 for s in BUILDINGS_STATUS.values() if s == "open")


# ══════════════════════════════════════════════════════════════════════════════
# OVERVIEW TAB
# ══════════════════════════════════════════════════════════════════════════════
if active_tab == "Overview":

    # ── Header ──────────────────────────────────────────────────────────────
    hcol_l, hcol_r = st.columns([3, 1])
    with hcol_l:
        st.markdown('<div class="uni-label">SONOMA STATE UNIVERSITY</div>', unsafe_allow_html=True)
        st.title("Campus Energy Dashboard")
        st.markdown(
            '<p style="font-size:1.05rem;color:#6b7280;margin-top:2px;line-height:1.5;">'
            'Weekly electricity use across campus buildings — sourced from FTP interval meters.</p>',
            unsafe_allow_html=True)
    with hcol_r:
        if len(sorted_sel) == 1:
            rw_str = week_label(sorted_sel[0])
        elif len(sorted_sel) == 2:
            rw_str = f"{week_label(sorted_sel[0])} vs {week_label(sorted_sel[1])}"
        else:
            rw_str = f"{week_label(sorted_sel[0])} – {week_label(sorted_sel[-1])}"
        st.markdown(
            f'<div style="margin-top:32px">'
            f'<div class="rw-box">'
            f'<span class="rw-label">Report Window</span>'
            f'<span class="rw-value">{rw_str}</span>'
            f'</div></div>', unsafe_allow_html=True)

    # ── Missing data notice if any ───────────────────────────────────────────
    missing_blds = [b for b, s in BUILDINGS_STATUS.items() if s not in ("ok","review")]
    if missing_blds:
        st.markdown(
            f'<div class="alert-amber" style="margin-top:12px;">⚠️ <b>Missing Data:</b> '
            f'The following buildings have no FTP sensor data and are not shown in this dashboard: '
            f'{", ".join(sorted(missing_blds))}. '
            f'See the Data Integrity tab for details.</div>',
            unsafe_allow_html=True)

    # ── Campus KPIs ──────────────────────────────────────────────────────────
    st.markdown('<div class="sec-label">Campus Overview</div>', unsafe_allow_html=True)
    k1, k2, k3 = st.columns(3)

    k1.metric(
        f"Total Campus Electricity — {week_label(latest_week)}",
        fmt_kwh(campus_cur))

    k2.metric(
        f"Estimated Electricity Cost  (@ ${ENERGY_RATE}/kWh)",
        fmt_cost(campus_cost))

    if prev_week and pct_change is not None:
        arrow = "▲" if pct_change > 0 else "▼"
        k3.metric(
            f"vs {week_label(prev_week)}",
            f"{arrow} {abs(pct_change):.1f}%",
            delta=f"{'Up' if pct_change > 0 else 'Down'} {fmt_kwh(abs(campus_cur - campus_prev))}",
            delta_color="inverse")
    else:
        k3.metric("Weeks in Database", str(len(all_weeks)),
                  delta="Select 2+ weeks to compare")

    # ── CAMPUS TOTAL CHART — top of page ────────────────────────────────────
    if len(sorted_sel) >= 2:
        st.markdown('<div class="sec-label">Total Campus Electricity — All Selected Weeks</div>',
                    unsafe_allow_html=True)

        campus_by_week = (by_bld[by_bld["week"].isin(sorted_sel)]
                          .groupby("week")["kWh"].sum()
                          .reset_index().sort_values("week"))
        campus_by_week["label"] = campus_by_week["week"].apply(week_label)
        campus_by_week["disp"]  = campus_by_week["kWh"] / 1000  # MWh

        fig_campus = go.Figure(go.Bar(
            x=campus_by_week["label"],
            y=campus_by_week["disp"],
            marker_color=C_NAVY,
            text=[f"{v:.1f} MWh" for v in campus_by_week["disp"]],
            textposition="outside",
            textfont=dict(size=13, color=PLOT_TEXT, family="Inter"),
            hovertemplate="<b>%{x}</b><br>%{y:.1f} MWh<br>$%{customdata:,.0f}<extra></extra>",
            customdata=campus_by_week["kWh"] * ENERGY_RATE,
        ))
        y_max = campus_by_week["disp"].max() * 1.3 if not campus_by_week.empty else 1
        fig_campus.update_layout(
            **plot_base(height=280),
            bargap=0.45,
            yaxis_title="MWh",
        )
        fig_campus.update_yaxes(range=[0, y_max])
        st.plotly_chart(fig_campus, use_container_width=True)

    # ── Two-column layout ────────────────────────────────────────────────────
    main_col, side_col = st.columns([1.6, 1])

    with main_col:
        # ── Building selector — sorted highest to lowest kWh ────────────────
        st.markdown('<div class="sec-label">Building Detail</div>', unsafe_allow_html=True)

        bld_kwh_latest = (by_bld[by_bld["week"] == latest_week]
                          .sort_values("kWh", ascending=False)
                          [["building","kWh"]])
        bld_order  = bld_kwh_latest["building"].tolist()
        bld_kwh_lkp = bld_kwh_latest.set_index("building")["kWh"].to_dict()

        # Default to Green Music Center (highest)
        default_bld = bld_order[0] if bld_order else None

        sel_bld = st.selectbox(
            "Select a building (sorted highest to lowest kWh)",
            bld_order,
            index=0,
            format_func=lambda b: f"{b}  —  {fmt_kwh(bld_kwh_lkp.get(b, 0))}",
            label_visibility="visible")

        # Gap warning
        bld_status = BUILDINGS_STATUS.get(sel_bld, "ok")
        if bld_status == "review":
            st.markdown(
                f'<div class="alert-amber">⚠️ <b>{sel_bld}</b> — '
                f'Only 24 of 96 daily 15-minute intervals received (75% missing). '
                f'The kWh shown is understated by approximately 4×.</div>',
                unsafe_allow_html=True)

        # Building KPIs
        b_cur  = bld_kwh_lkp.get(sel_bld, 0.0)
        b_cost = b_cur * ENERGY_RATE
        b_prev = (by_bld[(by_bld["week"] == prev_week) & (by_bld["building"] == sel_bld)]["kWh"].sum()
                  if prev_week else None)
        b_pct  = ((b_cur - b_prev) / b_prev * 100) if b_prev else None

        bm1, bm2 = st.columns(2)
        bm1.metric(
            f"Electricity — {week_label(latest_week)}",
            fmt_kwh(b_cur))
        bm2.metric(
            f"Estimated Cost  (@ ${ENERGY_RATE}/kWh)",
            fmt_cost(b_cost))

        if prev_week and b_prev is not None and b_prev > 0:
            st.markdown(
                f'<div class="alert-blue" style="margin-top:8px;">'
                f'Compared to <b>{week_label(prev_week)}</b>: '
                f'<b>{fmt_kwh(b_prev)}</b> — '
                f'{"▲" if b_pct > 0 else "▼"} <b>{abs(b_pct):.1f}%</b> '
                f'({"up" if b_pct > 0 else "down"} {fmt_kwh(abs(b_cur - b_prev))})</div>',
                unsafe_allow_html=True)

        # ── All Buildings chart — up to 4 weeks ─────────────────────────────
        max_periods = 4
        chart_weeks = sorted_sel[-max_periods:]
        n_periods   = len(chart_weeks)

        chart_title = (f"All Buildings — {week_label(chart_weeks[0])}"
                       if n_periods == 1
                       else f"All Buildings — {week_label(chart_weeks[0])} to {week_label(chart_weeks[-1])}")
        if n_periods == max_periods:
            chart_title += f" (max {max_periods} weeks shown)"

        st.markdown(f'<div class="sec-label">{chart_title}</div>', unsafe_allow_html=True)

        if n_periods == 1:
            # Single week — simple horizontal bar
            ldf = (by_bld[by_bld["week"] == chart_weeks[0]]
                   .sort_values("kWh", ascending=True).copy())
            ldf["disp"] = ldf["kWh"] / 1000  # MWh

            fig_all = go.Figure(go.Bar(
                name=week_label(chart_weeks[0]),
                y=ldf["building"],
                x=ldf["disp"],
                orientation="h",
                marker_color=C_NAVY,
                text=[f"{v:.1f}" for v in ldf["disp"]],
                textposition="outside",
                textfont=dict(size=11, color="#374151", family="Inter"),
                hovertemplate="<b>%{y}</b><br>%{x:.1f} MWh<extra></extra>",
            ))
            fig_all.update_layout(
                **plot_base(height=max(300, len(ldf) * 56)),
                xaxis_title="MWh",
                yaxis_title="",
                showlegend=False,
            )
            fig_all.update_yaxes(tickfont=dict(size=12, color="#111827", family="Inter"))
            st.plotly_chart(fig_all, use_container_width=True)

        else:
            # Multiple weeks — grouped bars, one color per week
            palette = [C_NAVY, "#3b82f6", "#6366f1", C_SLATE]
            all_blds = sorted(by_bld[by_bld["week"].isin(chart_weeks)]["building"].unique())

            # Sort buildings by latest week kWh
            latest_bld_kwh = (by_bld[by_bld["week"] == chart_weeks[-1]]
                              .set_index("building")["kWh"].reindex(all_blds).fillna(0))
            all_blds_sorted = latest_bld_kwh.sort_values(ascending=True).index.tolist()

            fig_all = go.Figure()
            for idx, wk in enumerate(chart_weeks):
                wk_data = (by_bld[by_bld["week"] == wk]
                           .set_index("building")["kWh"]
                           .reindex(all_blds_sorted).fillna(0) / 1000)
                fig_all.add_trace(go.Bar(
                    name=week_label(wk),
                    y=all_blds_sorted,
                    x=wk_data.values,
                    orientation="h",
                    marker_color=palette[idx % len(palette)],
                    text=[f"{v:.1f}" if v > 0 else "" for v in wk_data.values],
                    textposition="outside",
                    textfont=dict(size=10, color="#374151", family="Inter"),
                    hovertemplate=f"<b>%{{y}}</b><br>{week_label(wk)}: %{{x:.1f}} MWh<extra></extra>",
                ))

            fig_all.update_layout(
                **plot_base(height=max(340, len(all_blds_sorted) * 70)),
                barmode="group",
                bargap=0.15,
                bargroupgap=0.05,
                xaxis_title="MWh",
                yaxis_title="",
                showlegend=True,
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.01,
                    xanchor="right", x=1,
                    font=dict(size=12, family="Inter", color=PLOT_TEXT),
                    bgcolor="#ffffff", bordercolor="#e2e8f0", borderwidth=1),
            )
            fig_all.update_yaxes(tickfont=dict(size=12, color="#111827", family="Inter"))
            st.plotly_chart(fig_all, use_container_width=True)

        # ── Individual building trend (bottom, specific building) ────────────
        bld_trend = (by_bld[by_bld["building"] == sel_bld]
                     .sort_values("week").copy())
        if len(bld_trend) >= 2:
            bld_trend["label"] = bld_trend["week"].apply(week_label)
            bld_trend["disp"]  = bld_trend["kWh"] / 1000

            st.markdown(
                f'<div class="sec-label">{sel_bld} — Weekly Trend</div>',
                unsafe_allow_html=True)

            vals_t = bld_trend["kWh"].values
            colors_t = [C_NAVY] + [
                C_GREEN if vals_t[i] < vals_t[i-1] else C_RED
                for i in range(1, len(vals_t))
            ]
            fig_trend = go.Figure(go.Bar(
                x=bld_trend["label"],
                y=bld_trend["disp"],
                marker_color=colors_t,
                text=[f"{v:.1f} MWh" for v in bld_trend["disp"]],
                textposition="outside",
                textfont=dict(size=12, color=PLOT_TEXT, family="Inter"),
                hovertemplate="<b>%{x}</b><br>%{y:.1f} MWh<extra></extra>",
                showlegend=False,
            ))
            yt = bld_trend["disp"].max() * 1.3 if not bld_trend.empty else 1
            fig_trend.update_layout(
                **plot_base(height=260),
                bargap=0.45,
                yaxis_title="MWh",
            )
            fig_trend.update_yaxes(range=[0, yt])
            st.plotly_chart(fig_trend, use_container_width=True)

    with side_col:
        # ── Top Buildings by Electricity ─────────────────────────────────────
        top_blds = (by_bld[by_bld["week"] == latest_week]
                    .sort_values("kWh", ascending=False))
        max_kwh_top = float(top_blds["kWh"].max()) if not top_blds.empty else 1.0

        bars_html = "".join(
            top_bld_bar(str(r["building"]), float(r["kWh"]), max_kwh_top)
            for _, r in top_blds.iterrows())

        st.markdown(
            f'<div class="card">'
            f'<div class="card-title">Top Buildings by Electricity</div>'
            f'<div class="card-sub">{week_label(latest_week)}</div>'
            f'{bars_html}'
            f'</div>',
            unsafe_allow_html=True)

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        # ── Data summary card ────────────────────────────────────────────────
        st.markdown(
            '<div class="card">'
            '<div class="card-title">Data Summary</div>'
            '<div style="font-size:0.95rem;color:#374151;line-height:1.9;margin-top:6px;">'
            f'<b>Reporting buildings:</b> {len(top_blds)}<br>'
            f'<b>Missing data:</b> 8 buildings<br>'
            f'<b>Electricity rate:</b> ${ENERGY_RATE}/kWh (estimated)<br>'
            f'<b>Source:</b> FTP interval meters<br>'
            f'<b>Updated:</b> Weekly, Mon 6 AM<br>'
            f'<b>Note:</b> Wine Spectator kWh is ~4× understated due to sensor gaps.'
            '</div></div>',
            unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# LEADERBOARD TAB
# ══════════════════════════════════════════════════════════════════════════════
elif active_tab == "Leaderboard":

    hcol_l2, hcol_r2 = st.columns([3, 1])
    with hcol_l2:
        st.markdown('<div class="uni-label">SONOMA STATE UNIVERSITY</div>', unsafe_allow_html=True)
        st.title("Building Energy Leaderboard")
        st.markdown(
            '<p style="font-size:1.05rem;color:#6b7280;margin-top:2px;line-height:1.5;">'
            'Ranked by <b style="color:#111827">% reduction</b> compared to the prior selected week.</p>',
            unsafe_allow_html=True)

    lb_latest = sorted_sel[-1]
    lb_prev   = sorted_sel[-2] if len(sorted_sel) >= 2 else None

    with hcol_r2:
        if lb_prev:
            cmp_str = f"{week_label(lb_prev)}  vs  {week_label(lb_latest)}"
        else:
            cmp_str = week_label(lb_latest)
        st.markdown(
            f'<div style="margin-top:32px"><div class="rw-box">'
            f'<span class="rw-label">Comparing</span>'
            f'<span class="rw-value">{cmp_str}</span>'
            f'</div></div>', unsafe_allow_html=True)

    if lb_prev is None:
        st.info("Select two or more weeks in the sidebar to unlock the leaderboard rankings.")
        st.stop()

    # Build comparison
    c_df = (by_bld[by_bld["week"] == lb_latest][["building","kWh"]]
            .rename(columns={"kWh":"kWh_c"}))
    p_df = (by_bld[by_bld["week"] == lb_prev][["building","kWh"]]
            .rename(columns={"kWh":"kWh_p"}))
    cmp  = pd.merge(c_df, p_df, on="building", how="outer").fillna(0)
    # Exclude buildings with 0 in both periods
    cmp  = cmp[(cmp["kWh_c"] > 0) | (cmp["kWh_p"] > 0)].copy()

    cmp["delta_kwh"] = cmp["kWh_p"] - cmp["kWh_c"]
    cmp["delta_pct"] = cmp.apply(
        lambda r: r["delta_kwh"] / r["kWh_p"] * 100 if r["kWh_p"] > 0 else 0.0, axis=1)
    cmp["cost_saved"] = cmp["delta_kwh"] * ENERGY_RATE

    # Streaks
    all_pvt = (by_bld.pivot_table(index="week", columns="building",
                                   values="kWh", aggfunc="sum").fillna(0).sort_index())
    streak_map = {}
    for b in all_pvt.columns:
        s, k = all_pvt[b].values, 0
        for i in range(len(s) - 1, 0, -1):
            if s[i] < s[i-1]: k += 1
            else: break
        streak_map[b] = k
    cmp["streak"] = cmp["building"].map(streak_map).fillna(0).astype(int)

    # Sort by % change (best first)
    lb = cmp.sort_values(["delta_pct","delta_kwh"], ascending=[False, False]).reset_index(drop=True)

    tot_c    = float(cmp["kWh_c"].sum())
    tot_p    = float(cmp["kWh_p"].sum())
    tot_pct  = (tot_p - tot_c) / tot_p * 100 if tot_p > 0 else 0.0
    n_better = int((cmp["delta_pct"] > 0.5).sum())
    n_worse  = int((cmp["delta_pct"] < -0.5).sum())
    d_col    = C_GREEN if tot_pct >= 0 else C_RED

    # Summary chips
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

    # Rows
    rank_cls = ["gold","silver","bronze"]
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
            pts_col  = C_GREEN
            pct_disp = f"+{pct:.1f}%"
            act_str  = f"{fmt_kwh(kwh_abs)} saved"
            cost_str = f"💰 {fmt_cost(cost_abs)} saved"
        elif neutral:
            pts_col  = C_MUTED
            pct_disp = "≈ 0%"
            act_str  = "No significant change"
            cost_str = ""
        else:
            pts_col  = C_RED
            pct_disp = f"{pct:.1f}%"
            act_str  = f"{fmt_kwh(kwh_abs)} more used"
            cost_str = f"💸 {fmt_cost(cost_abs)} extra"

        rank_num = i + 1
        rc = rank_cls[i] if i < 3 else ""
        rd = f"#{rank_num}"

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
            f'{week_label(lb_prev)}: {p_kwh} → {week_label(lb_latest)}: {c_kwh}</span>'
            '</div></div>'
            + streak_tag +
            f'<div style="text-align:right;min-width:88px">'
            f'<div class="lb-pct" style="color:{pts_col}">{pct_disp}</div>'
            f'<div class="lb-pct-lbl">% change</div>'
            f'</div></div>'
        )
    st.markdown(rows_html, unsafe_allow_html=True)

    # Highlights
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

    # Goal
    st.markdown('<div class="sec-label">Campus Goal — 5% Weekly Reduction</div>',
                unsafe_allow_html=True)
    GOAL     = 5.0
    progress = min(max(-tot_pct / GOAL * 100, 0.0), 100.0)
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
# DATA INTEGRITY TAB
# ══════════════════════════════════════════════════════════════════════════════
elif active_tab == "DataIntegrity":

    st.markdown('<div class="uni-label">SONOMA STATE UNIVERSITY</div>', unsafe_allow_html=True)
    st.title("Data Integrity Report")
    st.markdown(
        '<p style="font-size:1.05rem;color:#6b7280;margin-top:2px;line-height:1.5;">'
        'Full sensor registry, verified data, gap analysis, and deployment notes.</p>',
        unsafe_allow_html=True)

    st.markdown('<div class="sec-label">Verified Data — Week of Feb 2–8, 2026 (from pipeline DB)</div>',
                unsafe_allow_html=True)

    wdf = pd.read_csv(WEEKLY_CSV).sort_values("kWh", ascending=False)
    v_tbl = ('<table class="di-table"><thead><tr>'
             '<th>Building</th><th>kWh (week)</th><th>MWh</th><th>Est. Cost @ $0.15/kWh</th><th>Status</th>'
             '</tr></thead><tbody>')
    total_kwh = 0.0
    for _, r in wdf.iterrows():
        kwh = r["kWh"]
        total_kwh += kwh
        bst = BUILDINGS_STATUS.get(r["building"], "ok")
        status_map = {"ok":"OK","review":"Review","open":"Missing Data"}
        sbadge = badge_html(status_map.get(bst, bst))
        v_tbl += (f'<tr><td><b>{r["building"]}</b></td>'
                  f'<td>{kwh:,.1f}</td>'
                  f'<td>{kwh/1000:.2f}</td>'
                  f'<td>${kwh * 0.15:,.0f}</td>'
                  f'<td>{sbadge}</td></tr>')
    v_tbl += (f'<tr style="background:#f8fafc;font-weight:700;">'
              f'<td>CAMPUS TOTAL</td>'
              f'<td>{total_kwh:,.1f}</td>'
              f'<td>{total_kwh/1000:.2f}</td>'
              f'<td>${total_kwh * 0.15:,.0f}</td>'
              f'<td></td></tr>')
    v_tbl += '</tbody></table>'
    st.markdown(f'<div class="card">{v_tbl}</div>', unsafe_allow_html=True)

    st.markdown(
        '<div style="font-size:0.85rem;color:#9ca3af;margin-top:8px;margin-bottom:4px;">'
        'Source: pipeline DB (energy_usage table). Week covers Mon Feb 2 through Sun Feb 8, 2026. '
        'Rachel Carson Hall kWh (12,436) comes from Feb 2–5 DB records — raw interval files only cover Feb 6–11.'
        '</div>', unsafe_allow_html=True)

    # Utility coverage — moved here from overview
    st.markdown('<div class="sec-label">Utility Coverage</div>', unsafe_allow_html=True)
    u1, u2, u3 = st.columns(3)
    u1.markdown(
        '<div class="card"><div class="card-title">⚡ Electricity</div>'
        '<div style="font-size:0.95rem;color:#374151;line-height:1.8;margin-top:6px;">'
        '<b>Status:</b> Active for 8 buildings<br>'
        '<b>Source:</b> FTP interval meters (kWh)<br>'
        '<b>Rate:</b> $0.15/kWh (estimated)'
        '</div></div>', unsafe_allow_html=True)
    u2.markdown(
        '<div class="card"><div class="card-title">🔥 Gas</div>'
        '<div style="font-size:0.95rem;color:#374151;line-height:1.8;margin-top:6px;">'
        '<b>Status:</b> Missing Data<br>'
        '<b>Meters:</b> Boiler Plant, Green Music Center, Schulz Info Center<br>'
        '<b>Note:</b> 100% missing from FTP interval files'
        '</div></div>', unsafe_allow_html=True)
    u3.markdown(
        '<div class="card"><div class="card-title">💧 Water</div>'
        '<div style="font-size:0.95rem;color:#374151;line-height:1.8;margin-top:6px;">'
        '<b>Status:</b> Missing Data<br>'
        '<b>Meter:</b> Green Music Center (234aa782-f7b1eef2)<br>'
        '<b>Note:</b> Meter present but all values are empty'
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
        '<div style="font-size:0.95rem;color:#374151;line-height:2;">'
        '<code>BTU × 0.000293071 = kWh</code><br>'
        '<code>kBTU × 0.293071 = kWh</code>  (sensor 234aa956 labelled _MBTU in FTP but values are kBTU scale)<br>'
        '<code>therm × 29.3071 = kWh</code><br>'
        '<code>kWh → kWh direct</code><br>'
        '<code>Water (gallon) → stored raw, no conversion</code>'
        '</div></div>', unsafe_allow_html=True)

    # Deployment
    st.markdown('<div class="sec-label">Deployment & Pipeline</div>', unsafe_allow_html=True)
    d1, d2 = st.columns(2)
    d1.markdown(
        '<div class="card"><div class="card-title">🚀 Best Deployment Method</div>'
        '<div style="font-size:0.95rem;color:#374151;line-height:1.9;margin-top:6px;">'
        '<b>Streamlit Community Cloud (recommended — free)</b><br>'
        '1. Push this file + weekly_energy.csv to GitHub<br>'
        '2. Go to share.streamlit.io<br>'
        '3. Connect repo → deploy → get a public URL<br><br>'
        '<b>DigitalOcean / Hostinger (paid, full control)</b><br>'
        '1. Create Ubuntu server<br>'
        '2. <code>pip install streamlit plotly pandas</code><br>'
        '3. Run behind nginx reverse proxy<br>'
        '4. Add cron job for pipeline'
        '</div></div>', unsafe_allow_html=True)
    d2.markdown(
        '<div class="card"><div class="card-title">🔄 Pipeline Schedule</div>'
        '<div style="font-size:0.95rem;color:#374151;line-height:1.9;margin-top:6px;">'
        '<b>Current:</b> Weekly, Monday 6 AM (Windows Task Scheduler)<br><br>'
        '<b>To run daily:</b> Change Task Scheduler trigger to Daily<br>'
        'Pipeline already handles date-named files (e.g. 20260317.csv)<br><br>'
        '<b>Flow:</b> FTP download → normalize → MySQL insert<br>'
        '→ weekly_energy.csv regenerated → dashboard auto-refreshes (5 min TTL)<br><br>'
        '<b>DB:</b> 193.203.166.234 | u209446640_SSUEnergy'
        '</div></div>', unsafe_allow_html=True)
