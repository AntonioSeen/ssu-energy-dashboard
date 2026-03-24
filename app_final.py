"""
SSU Campus Energy Dashboard

Tabs (sidebar nav):
  📊 Overview      — campus KPIs, top buildings, DQM sidebar, utility coverage card
  ⚡ Electricity   — electric-only kWh per building, building detail, trend chart
  ⛽ Gas           — gas therm per building, building detail, trend chart
  💧 Water         — water gallons per building, building detail, trend chart
  🏆 Leaderboard   — % change competition (electric kWh), streaks, campus goal
  🔍 Data Integrity — sensor registry, verified readings, gap analysis, deployment info

Style: inherits 100% of original app_final.py CSS/theme (white cards, Inter font,
navy sidebar, blue/green/red palette).  Gas uses amber accent; water uses blue accent.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

st.set_page_config(
    page_title="SSU Campus Energy Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# CSS  — original style preserved exactly; gas/water accent classes added
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

html, body, [class*="css"], p, span, div, label, button {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
.stApp { background-color: #f4f6f8 !important; color: #111827 !important; }
.block-container { padding-top: 1.8rem !important; padding-bottom: 3rem !important; max-width: 1400px !important; }

/* Sidebar */
section[data-testid="stSidebar"] { background-color: #1b3a5c !important; border-right: none !important; }
section[data-testid="stSidebar"] * { color: #c8d9ea !important; font-family: 'Inter', sans-serif !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #ffffff !important; font-weight: 700 !important; font-size: 1.1rem !important; }
section[data-testid="stSidebar"] .stRadio > label { color: #a3bcd0 !important; font-size: 0.84rem !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.1em !important; }
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label { font-size: 1.05rem !important; font-weight: 500 !important; color: #c8d9ea !important; text-transform: none !important; letter-spacing: 0 !important; }
section[data-testid="stSidebar"] .stMultiSelect > label,
section[data-testid="stSidebar"] .stSelectbox > label { color: #a3bcd0 !important; font-size: 0.84rem !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.1em !important; }
section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.1) !important; }

/* Headings */
h1 { font-family: 'Inter', sans-serif !important; font-size: 2.7rem !important; font-weight: 800 !important; color: #111827 !important; letter-spacing: -0.04em !important; line-height: 1.1 !important; margin-bottom: 2px !important; margin-top: 0 !important; }
h2, h3 { font-family: 'Inter', sans-serif !important; font-weight: 700 !important; color: #111827 !important; }

/* Metric cards */
[data-testid="stMetric"] { background: #ffffff !important; border: 1px solid #e2e8f0 !important; border-radius: 12px !important; padding: 20px 22px !important; box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important; }
[data-testid="stMetricLabel"] p { font-family: 'Inter', sans-serif !important; font-size: 1rem !important; font-weight: 700 !important; color: #6b7280 !important; text-transform: uppercase !important; letter-spacing: 0.1em !important; margin-bottom: 6px !important; }
[data-testid="stMetricValue"] { font-family: 'Inter', sans-serif !important; font-size: 2.7rem !important; font-weight: 800 !important; color: #111827 !important; letter-spacing: -0.03em !important; line-height: 1.15 !important; }
[data-testid="stMetricDelta"] { font-family: 'Inter', sans-serif !important; font-size: 1.05rem !important; font-weight: 600 !important; }
[data-testid="stMetricDelta"] svg { display: none !important; }

/* Section labels */
.sec-label { font-family: 'Inter', sans-serif; font-size: 1rem; font-weight: 700; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.12em; padding-bottom: 8px; border-bottom: 1px solid #e2e8f0; margin: 26px 0 16px 0; }
.sec-label-gas   { color: #b45309; border-bottom-color: #fde68a; }
.sec-label-water { color: #1d4ed8; border-bottom-color: #bfdbfe; }

/* Report window */
.report-window-box { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px 16px; text-align: right; box-shadow: 0 1px 3px rgba(0,0,0,0.05); display: inline-block; float: right; min-width: 200px; }
.report-window-label { font-size: 0.78rem; font-weight: 700; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.1em; display: block; margin-bottom: 4px; }
.report-window-value { font-size: 1.15rem; font-weight: 700; color: #111827; white-space: nowrap; }

/* White cards */
.card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px 22px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.card-title { font-size: 1.4rem; font-weight: 700; color: #111827; margin-bottom: 5px; }
.card-sub { font-size: 1.0rem; color: #6b7280; margin-bottom: 16px; }

/* Comparison cards */
.cmp-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); height: 100%; }
.cmp-lbl { font-size: 0.82rem; font-weight: 700; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 10px; }
.cmp-val { font-family: 'Inter', sans-serif; font-size: 2.2rem; font-weight: 800; color: #111827; letter-spacing: -0.03em; line-height: 1.15; }
.cmp-footnote { font-size: 0.92rem; color: #6b7280; margin-top: 8px; }

/* Top buildings */
.topbld { margin-bottom: 13px; }
.topbld-header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 5px; }
.topbld-name { font-size: 1.15rem; font-weight: 600; color: #111827; }
.topbld-val { font-size: 1.08rem; font-weight: 600; color: #6b7280; }
.topbld-track { background: #f1f5f9; border-radius: 3px; height: 8px; overflow: hidden; }
.topbld-fill { height: 100%; background: #1b3a5c; border-radius: 3px; }

/* Data Quality Monitor */
.dqm-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; border-radius: 8px; margin-bottom: 8px; font-size: 1.05rem; font-weight: 500; }
.dqm-open   { background: #fef2f2; color: #991b1b; }
.dqm-ok     { background: #f0fdf4; color: #166534; }
.dqm-review { background: #fffbeb; color: #92400e; }
.dqm-badge { font-size: 0.92rem; font-weight: 700; padding: 3px 10px; border-radius: 4px; white-space: nowrap; }
.dqm-open   .dqm-badge { background: #fecaca; color: #991b1b; }
.dqm-ok     .dqm-badge { background: #bbf7d0; color: #166534; }
.dqm-review .dqm-badge { background: #fde68a; color: #92400e; }

/* Alert banners */
.alert-red   { background: #fef2f2; border-left: 4px solid #dc2626; border-radius: 0 8px 8px 0; padding: 12px 16px; font-size: 0.97rem; color: #7f1d1d; font-weight: 500; margin-bottom: 12px; }
.alert-amber { background: #fffbeb; border-left: 4px solid #f59e0b; border-radius: 0 8px 8px 0; padding: 12px 16px; font-size: 0.97rem; color: #78350f; font-weight: 500; margin-bottom: 12px; }

/* Leaderboard */
.lb-row { display: flex; align-items: center; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 14px 18px; margin-bottom: 8px; gap: 14px; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }
.lb-rank { font-family: 'Inter', sans-serif; font-size: 1.6rem; font-weight: 800; color: #1b3a5c; min-width: 48px; text-align: center; line-height: 1; flex-shrink: 0; }
.lb-rank.gold   { color: #b45309; }
.lb-rank.silver { color: #64748b; }
.lb-rank.bronze { color: #92400e; }
.lb-name { font-size: 1.15rem; font-weight: 700; color: #111827; }
.lb-sub { font-size: 0.95rem; color: #6b7280; margin-top: 4px; line-height: 1.55; }
.lb-pct { font-family: 'Inter', sans-serif; font-size: 1.9rem; font-weight: 800; text-align: right; line-height: 1.1; min-width: 96px; flex-shrink: 0; letter-spacing: -0.03em; }
.lb-pct-lbl { font-size: 0.75rem; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.08em; text-align: right; white-space: nowrap; }
.streak { background: #fff7ed; border: 1px solid #fed7aa; border-radius: 6px; padding: 4px 11px; font-size: 0.88rem; color: #c2410c; font-weight: 700; white-space: nowrap; flex-shrink: 0; }

/* Goal */
.goal-box { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 22px 24px; margin-top: 18px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.goal-lbl { font-size: 0.82rem; font-weight: 700; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 10px; }
.goal-status { font-family: 'Inter', sans-serif; font-size: 1.55rem; font-weight: 800; margin-bottom: 16px; line-height: 1.25; letter-spacing: -0.02em; }
.prog-bg { background: #e5e7eb; border-radius: 6px; height: 11px; overflow: hidden; margin-bottom: 8px; }
.prog-fill { height: 100%; border-radius: 6px; }

/* Data Integrity tables */
.di-table { width: 100%; border-collapse: collapse; font-size: 0.94rem; }
.di-table th { background: #f1f5f9; color: #374151; font-weight: 700; padding: 12px 16px; text-align: left; border-bottom: 2px solid #e2e8f0; font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.08em; }
.di-table td { padding: 11px 16px; border-bottom: 1px solid #f1f5f9; color: #111827; vertical-align: middle; font-size: 0.94rem; }
.di-table tr:hover td { background: #f8fafc; }
.badge { display: inline-block; padding: 3px 10px; border-radius: 4px; font-size: 0.82rem; font-weight: 700; }
.badge-ok     { background: #dcfce7; color: #166534; }
.badge-open   { background: #fee2e2; color: #991b1b; }
.badge-review { background: #fef3c7; color: #92400e; }
.badge-skip   { background: #f1f5f9; color: #6b7280; }

.uni-label { font-size: 0.80rem; font-weight: 700; letter-spacing: 0.16em; text-transform: uppercase; color: #9ca3af; margin-bottom: 4px; }

div[data-testid="column"] { padding: 0 6px !important; }

/* ── Hide Streamlit's broken sidebar collapse button entirely ──────────────
   In Streamlit 1.38+ the Material Icons font loads from Google Fonts CDN.
   When that CDN is blocked, the button shows raw text like
   "keyboard_double_arrow_right" instead of an icon. There is NO CSS or JS fix
   that works reliably — the icon is a font ligature baked into React's output.
   Solution: hide the broken button, and we add our own toggle in the sidebar. */

button[data-testid="baseButton-headerNoPadding"],
button[data-testid="baseButton-header"] {
    display: none !important;
}
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] {
    display: none !important;
}

/* Style for the SSU logo shown by st.logo() */
[data-testid="stLogo"] img,
[data-testid="stLogo"] {
    max-height: 60px !important;
    object-fit: contain !important;
}


/* ── Mobile responsiveness ─────────────────────────────────────────────── */
@media (max-width: 768px) {
    [data-testid="stMetric"] { padding: 12px 14px !important; min-height: auto !important; }
    [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
    .lb-row { flex-wrap: wrap; gap: 8px; padding: 12px 14px !important; }
    .lb-pct { font-size: 1.25rem !important; min-width: 70px !important; }
    h1 { font-size: 1.5rem !important; }
    .block-container { padding-left: 0.75rem !important; padding-right: 0.75rem !important; }
    .report-window-box { min-width: 140px !important; padding: 8px 12px !important; }
    .report-window-value { font-size: 0.82rem !important; white-space: normal !important; }
    .cmp-val { font-size: 1.4rem !important; }
    /* Stack columns on small screens */
    div[data-testid="column"] { padding: 0 3px !important; }
}
@media (max-width: 480px) {
    [data-testid="stMetricValue"] { font-size: 1.2rem !important; }
    h1 { font-size: 1.3rem !important; }
    .lb-rank { font-size: 1.1rem !important; min-width: 32px !important; }
    .lb-name { font-size: 0.9rem !important; }
}
</style>
""", unsafe_allow_html=True)

# Arrow icons: Streamlit's built-in button is hidden via CSS above.
# A working ◀ / ▶ toggle is added inside the sidebar below.
WEEKLY_CSV  = "weekly_energy.csv"
ENERGY_RATE = 0.15    # $/kWh
GAS_RATE    = 1.20    # $/therm
WATER_RATE  = 0.005   # $/gallon (~$5/1,000 gal)

PLOT_BG   = "#ffffff"
PLOT_GRID = "#f1f5f9"
PLOT_TEXT = "#111827"
C_NAVY    = "#1b3a5c"
C_GREEN   = "#16a34a"
C_RED     = "#dc2626"
C_AMBER   = "#d97706"
C_MUTED   = "#6b7280"
C_BLUE    = "#3b82f6"

WINE_NOTE = ("Only 24 of 96 daily 15-minute intervals are received "
             "(72 gaps/day = 75% missing). "
             "The kWh totals shown are ~4× understated vs actual consumption.")

BUILDINGS_STATUS = {
    "Green Music Center":          "ok",
    "Nichols Hall":                "ok",
    "Physical Education":          "ok",
    "Ives Hall":                   "ok",
    "Student Center":              "ok",
    "Wine Spectator Learning Ctr": "review",
    "Student Health Center":       "ok",
    "Art Building":                "open",
    "Boiler Plant":                "open",
    "Darwin Hall":                 "open",
    "ETC":                         "open",
    "Rachel Carson Hall":          "open",
    "Salazar Hall":                "open",
    "Schulz Info Center":          "open",
    "Stevenson Hall":              "open",
    "Campus Misc":                 "ok",
}

SENSOR_REGISTRY = [
    # (Building, Short ID, Utility, Raw unit, Status, Notes)
    ("Green Music Center",          "234ab131-e413ba29", "Electric", "kWh",    "OK",      "Primary electric — ~85 kWh/15-min"),
    ("Green Music Center",          "1f98265e-39835c84", "Thermal",  "BTU",    "OK",      "CHW cooling BTU"),
    ("Green Music Center",          "234aa956-82d369b2", "HW BTU",   "MBTU",   "OK",      "HW BTU — values arrive as _MBTU, unit correction applied"),
    ("Green Music Center",          "234aab84-c656a0e0", "Gas",      "therm",  "Open",    "100% missing from FTP"),
    ("Green Music Center",          "234aa782-f7b1eef2", "Water",    "gallon", "OK",      "Meter registered; 100% NaN in all provided files"),
    ("Nichols Hall",                "234e3ee2-f6fcea18", "HHW BTU",  "BTU",    "OK",      "Active — ~20,000 kWh/day thermal"),
    ("Nichols Hall",                "234e3ee2-b06b6c8c", "CHW BTU",  "BTU",    "OK",      "Active but reporting 0 BTU"),
    ("Nichols Hall",                "234e40da-635bc7c1", "Electric", "kWh",    "OK",      "Active but reporting 0 kWh"),
    ("Physical Education",          "206db469-c986212b", "Electric", "kWh",    "OK",      "Consistent — ~11 kWh/15-min"),
    ("Ives Hall",                   "234e3195-7d72fbdc", "HHW BTU",  "BTU",    "OK",      "Active — ~950–1,243 kWh/day thermal"),
    ("Ives Hall",                   "234e3195-c20a1a8e", "CHW BTU",  "BTU",    "OK",      "Active but 0 BTU"),
    ("Ives Hall",                   "206d9425-f3361ab6", "Electric", "kWh",    "OK",      "Active but 0 kWh (meter offline?)"),
    ("Student Center",              "234e5dff-8d8eb031", "HHW BTU",  "BTU",    "OK",      "Active — variable daily"),
    ("Student Center",              "234e5dff-6fe20abd", "CHW BTU",  "BTU",    "OK",      "Active — secondary thermal sensor"),
    ("Student Center",              "20c9aa07-acd1558a", "Electric", "kWh",    "OK",      "Active but 0 kWh"),
    ("Wine Spectator Learning Ctr", "250ea73e-3b55a6cf", "Electric", "kWh",    "Review",  "75% gaps — 24/96 intervals/day only"),
    ("Student Health Center",       "234e61c5-83f6cf71", "HHW BTU",  "BTU",    "OK",      "Active but 0 BTU — building unoccupied?"),
    ("Student Health Center",       "234e61c5-021da430", "CHW BTU",  "BTU",    "OK",      "Secondary sensor — also 0 BTU"),
    ("Art Building",                "1f97c82e-36e60525", "HHW BTU",  "BTU",    "Open",    "100% missing from FTP — unit corrected to BTU"),
    ("Art Building",                "1f97c82e-d1a92673", "CHW BTU",  "BTU",    "Open",    "100% missing from FTP"),
    ("Boiler Plant",                "234a6e2b-318cf13d", "Gas",      "therm",  "Open",    "100% missing from FTP"),
    ("Darwin Hall",                 "267e6fd0-93d67a62", "Electric", "kWh",    "Open",    "100% missing from FTP"),
    ("ETC",                         "1f97c82e-dd011464", "Electric", "kWh",    "Open",    "100% missing from FTP"),
    ("Rachel Carson Hall",          "1f98265e-cbf77175", "Electric", "kWh",    "Open",    "100% missing from FTP"),
    ("Rachel Carson Hall",          "234aa43b-a73abf5e", "HHW BTU",  "BTU",    "Open",    "100% missing + 1 slot/day gap"),
    ("Rachel Carson Hall",          "234aa121-a983880d", "CHW BTU",  "BTU",    "Open",    "100% missing from FTP"),
    ("Salazar Hall",                "20c9b2e1-d7263cf1", "Electric", "kWh",    "Open",    "100% missing from FTP"),
    ("Salazar Hall",                "234e4c64-930d1fd6", "Electric", "kWh",    "Open",    "100% missing from FTP"),
    ("Salazar Hall",                "20c9b4d5-5ea6aa0b", "HHW BTU",  "BTU",    "Open",    "100% missing — unit corrected to BTU"),
    ("Schulz Info Center",          "1f97c82e-c34c4f2e", "Electric", "kWh",    "Open",    "100% missing from FTP"),
    ("Schulz Info Center",          "1f97c82e-525ca261", "CHW BTU",  "BTU",    "Open",    "100% missing from FTP"),
    ("Schulz Info Center",          "206e94b8-3b05cb50", "Gas",      "therm",  "Open",    "100% missing from FTP"),
    ("Stevenson Hall",              "251810ce-f429b841", "Electric", "kWh",    "Open",    "100% missing from FTP"),
    ("Stevenson Hall",              "267fcb62-ed42e3b3", "HHW BTU",  "BTU",    "Open",    "100% missing from FTP"),
    ("Campus Misc",                 "214981c7-dd0b1593", "Electric", "kWh",    "PGE",     "Main Campus — pgeReports FTP folder"),
    ("Campus Misc",                 "214981c7-5530731e", "Electric", "kWh",    "PGE",     "Concession/Track — pgeReports FTP folder"),
    ("Campus Misc",                 "214981c7-63077e46", "Electric", "kWh",    "PGE",     "Scoreboard — pgeReports FTP folder"),
]

# VERIFIED_DAILY removed — daily data is now loaded dynamically from
# daily_energy.csv which the pipeline writes from real DB date aggregates.
# No hardcoded values. No fabricated dates.

UNIT_CONVERSIONS = "BTU ÷ 3,412 → kWh  |  kBTU × 0.293071 → kWh  |  therm × 29.307 → kWh  |  gallon → stored raw"


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def plot_base(height=280, accent=C_NAVY):
    return dict(
        paper_bgcolor=PLOT_BG, plot_bgcolor=PLOT_BG,
        font=dict(family="Inter, sans-serif", color=PLOT_TEXT, size=13),
        margin=dict(l=8, r=8, t=28, b=8),
        height=height,
        xaxis=dict(gridcolor=PLOT_GRID, zerolinecolor="#e2e8f0",
                   linecolor="#e2e8f0", tickfont=dict(size=13, family="Inter", color=PLOT_TEXT)),
        yaxis=dict(gridcolor=PLOT_GRID, zerolinecolor="#e2e8f0",
                   linecolor="#e2e8f0", tickfont=dict(size=13, family="Inter", color=PLOT_TEXT)),
    )

def fmt_energy(kwh, unit):
    v = kwh / 1000 if unit == "MWh" else kwh
    return f"{v:,.1f} {unit}"

def fmt_val(v, unit):
    return f"{v:,.1f} {unit}"

def fmt_cost(val):
    return f"${abs(val):,.0f}"

def week_label(w):
    try:
        s     = str(w).split("/")[0]
        start = pd.to_datetime(s)
        end   = start + pd.Timedelta(days=6)
        ss    = start.strftime("%b ") + start.strftime("%d").lstrip("0")
        es    = end.strftime("%b ")   + end.strftime("%d").lstrip("0")
        return (f"{ss} – {es}, {end.year}" if start.year == end.year
                else f"{ss}, {start.year} – {es}, {end.year}")
    except Exception:
        return str(w)

def cmp_card(label, value_html, footnote=None, accent=None):
    border = f"border-top: 3px solid {accent};" if accent else ""
    note_h = f'<div class="cmp-footnote">{footnote}</div>' if footnote else ""
    return (f'<div class="cmp-card" style="{border}">'
            f'<div class="cmp-lbl">{label}</div>'
            f'<div class="cmp-val">{value_html}</div>'
            f'{note_h}</div>')

def top_bld_html(name, val, max_val, unit="kWh", fill_color=C_NAVY):
    pct  = val / max_val * 100 if max_val > 0 else 0
    disp = val / 1000 if (unit == "kWh" and val >= 1000) else val
    disp_unit = "MWh" if (unit == "kWh" and val >= 1000) else unit
    return (f'<div class="topbld">'
            f'<div class="topbld-header">'
            f'<span class="topbld-name">{name}</span>'
            f'<span class="topbld-val">{disp:,.1f} {disp_unit}</span>'
            f'</div>'
            f'<div class="topbld-track">'
            f'<div class="topbld-fill" style="width:{pct:.0f}%;background:{fill_color}"></div>'
            f'</div></div>')

def dqm_row(label, badge, cls):
    return (f'<div class="dqm-row {cls}">'
            f'<span>{label}</span>'
            f'<span class="dqm-badge">{badge}</span>'
            f'</div>')

def badge_html(status):
    cls = {"OK":"badge-ok","Open":"badge-open","Review":"badge-review","Skip":"badge-skip",
           "PGE":"badge-skip"}.get(status, "badge-skip")
    return f'<span class="badge {cls}">{status}</span>'

def alert(msg, kind="red"):
    return f'<div class="alert-{kind}">{msg}</div>'

def build_report_window(sel_weeks, p_label_fn):
    """
    Build a clean, readable report window string from any selection:
      1 period  → "Feb 9 – Feb 15, 2026"
      2 periods → "Feb 2 – Feb 8  vs  Feb 9 – Feb 15, 2026"
      3+ periods → "Jan 26 – Mar 15, 2026  (7 periods)"
    Works for weekly, monthly, and yearly views.
    """
    if not sel_weeks:
        return "—"
    sw = sorted(sel_weeks)
    if len(sw) == 1:
        return p_label_fn(sw[0])
    if len(sw) == 2:
        return f"{p_label_fn(sw[0])}  vs  {p_label_fn(sw[1])}"
    # 3+ : show full span
    try:
        starts, ends = [], []
        for w in sw:
            s = pd.to_datetime(str(w).split("/")[0])
            starts.append(s)
            ends.append(s + pd.Timedelta(days=6))
        d_start = min(starts); d_end = max(ends)
        s_str = d_start.strftime("%b %-d")
        e_str = d_end.strftime("%b %-d, %Y")
        return f"{s_str} – {e_str}  ({len(sw)} periods)"
    except Exception:
        return f"{p_label_fn(sw[0])} – {p_label_fn(sw[-1])}  ({len(sw)} periods)"


# ══════════════════════════════════════════════════════════════════════════════
# LOAD DATA
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=300)
def load_data():
    if not os.path.exists(WEEKLY_CSV):
        st.error("⚠️  weekly_energy.csv not found — run master_pipeline_final.py first.")
        st.stop()
    df = pd.read_csv(WEEKLY_CSV)
    df["week"] = df["week"].astype(str).str.strip()
    # Ensure new columns exist when running against older CSVs
    for col, default in [("gas_therm", 0.0), ("water_gallon", 0.0),
                         ("heating_dd", 0.0), ("normalized_kWh", 0.0)]:
        if col not in df.columns:
            df[col] = default
    for col in ["gas_therm", "water_gallon", "heating_dd"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    df["normalized_kWh"] = pd.to_numeric(df["normalized_kWh"], errors="coerce").fillna(df["kWh"])
    # Keep rows where ANY meter has meaningful data
    return df[(df["kWh"] > 1) | (df["gas_therm"] > 0.01) | (df["water_gallon"] > 0.1)].copy()

df_all    = load_data()
all_weeks = sorted(df_all["week"].unique())

# ── Load daily_energy.csv (written by pipeline from raw DB date aggregates) ──
# Only dates the pipeline actually processed appear — nothing fabricated.
DAILY_CSV = "daily_energy.csv"

@st.cache_data(ttl=300)
def load_daily_data():
    if not os.path.exists(DAILY_CSV):
        return pd.DataFrame(columns=["week","building","kWh","gas_therm","water_gallon"])
    d = pd.read_csv(DAILY_CSV)
    d = d.rename(columns={"date": "week"})   # normalise column name
    d["week"] = d["week"].astype(str).str.strip()
    for col in ["kWh","gas_therm","water_gallon"]:
        if col not in d.columns:
            d[col] = 0.0
        d[col] = pd.to_numeric(d[col], errors="coerce").fillna(0.0)
    return d[(d["kWh"] > 0) | (d["gas_therm"] > 0.01) | (d["water_gallon"] > 0.1)].copy()

df_daily = load_daily_data()
all_days = sorted(df_daily["week"].unique())


# ══════════════════════════════════════════════════════════════════════════════
# SSU LOGO — uses st.logo() (Streamlit 1.35+), appears in sidebar header
# ══════════════════════════════════════════════════════════════════════════════
# Embed the SSU seal as a base64 SVG so it works offline / no CDN needed
SSU_LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">
  <circle cx="60" cy="60" r="58" fill="#1b3a5c" stroke="#c8d9ea" stroke-width="2"/>
  <text x="60" y="44" font-family="Georgia,serif" font-size="11" font-weight="bold"
        fill="#ffffff" text-anchor="middle">SONOMA STATE</text>
  <text x="60" y="58" font-family="Georgia,serif" font-size="10"
        fill="#c8d9ea" text-anchor="middle">UNIVERSITY</text>
  <text x="60" y="80" font-family="Arial,sans-serif" font-size="22" font-weight="bold"
        fill="#f0c040" text-anchor="middle">SSU</text>
  <text x="60" y="96" font-family="Arial,sans-serif" font-size="8"
        fill="#c8d9ea" text-anchor="middle">EST. 1960</text>
</svg>"""

import base64, tempfile, pathlib
_logo_bytes = SSU_LOGO_SVG.encode()
_logo_b64   = base64.b64encode(_logo_bytes).decode()
_logo_data  = f"data:image/svg+xml;base64,{_logo_b64}"

# Write to a temp file so st.logo() can read it (it needs a file path or URL)
_logo_tmp = pathlib.Path(tempfile.gettempdir()) / "ssu_logo.svg"
if not _logo_tmp.exists():
    _logo_tmp.write_bytes(_logo_bytes)

try:
    st.logo(str(_logo_tmp), size="large")
except Exception:
    pass  # st.logo not available in older Streamlit versions — graceful fallback

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # ── Custom sidebar toggle (replaces Streamlit's broken icon button) ────────
    if "sidebar_open" not in st.session_state:
        st.session_state.sidebar_open = True

    st.markdown(
        '<div style="background:#163350;margin:-1rem -1rem 0 -1rem;padding:16px 18px 14px;text-align:center;">'
        f'<img src="{_logo_data}" alt="SSU" style="height:56px;object-fit:contain;margin-bottom:8px;">'
        '<div style="font-size:0.6rem;font-weight:700;letter-spacing:0.2em;text-transform:uppercase;'
        'color:#6a9cc0;margin-bottom:2px;">SONOMA STATE UNIVERSITY</div>'
        '<div style="font-size:1.05rem;font-weight:700;color:#ffffff;letter-spacing:-0.01em;">'
        '⚡ Campus Energy</div></div>',
        unsafe_allow_html=True)
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    st.markdown("**View Mode**")
    role = st.radio("mode", ["Student (Gamified)", "Admin (Basic)"],
                    label_visibility="collapsed")
    st.markdown("---")

    st.markdown("**Time Range**")
    time_filter = st.radio("time", ["Daily", "Weekly", "Monthly", "Yearly"],
                           horizontal=True, label_visibility="collapsed")

    def week_start(w):
        try:    return pd.to_datetime(str(w).split("/")[0])
        except: return pd.NaT

    df_all["_wstart"] = df_all["week"].map(week_start)

    if time_filter == "Daily":
        def day_label(d):
            try:    return pd.to_datetime(str(d)).strftime("%a, %b %-d, %Y")
            except: return str(d)
        if not all_days:
            st.markdown(
                '<div style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 10px 10px 0;'
                'padding:16px 20px;margin:12px 0;font-size:0.95rem;color:#78350f;font-weight:500;">'
                '📅 <b>No daily data available yet.</b><br><br>'
                'The Daily view reads from <code>daily_energy.csv</code> which is written by the pipeline '
                'when it processes raw FTP interval files.<br><br>'
                '<b>To get daily data:</b><br>'
                '&nbsp;&nbsp;1. Run <code>python local_master_pipeline.py</code><br>'
                '&nbsp;&nbsp;2. Make sure interval CSV files (e.g. <code>20260317.csv</code>) are in the FTP folder<br>'
                '&nbsp;&nbsp;3. Switch back to <b>Daily</b> after the pipeline completes<br><br>'
                'In the meantime, switch to <b>Weekly</b> in the Time Range selector above to see your data.'
                '</div>',
                unsafe_allow_html=True)
            selected_weeks = []
        else:
            st.markdown("**Select Day(s)**")
            selected_weeks = st.multiselect(
                "days", all_days,
                default=[all_days[-1]] if all_days else [],
                format_func=day_label, label_visibility="collapsed")
        df_view      = df_daily.copy()
        period_label = day_label

    elif time_filter == "Weekly":
        parsed  = [(w, week_start(w)) for w in all_weeks]
        parsed  = [(w, d) for w, d in parsed if pd.notna(d)]
        latest_ = max(d for _, d in parsed) if parsed else None
        cutoff_ = (latest_ - pd.Timedelta(weeks=8)) if latest_ else None
        avail_w = [w for w, d in parsed if cutoff_ is None or d >= cutoff_] or all_weeks
        st.markdown("**Select Weeks**")
        selected_weeks = st.multiselect("weeks", avail_w,
                                        default=avail_w[-2:] if len(avail_w) >= 2 else avail_w,
                                        format_func=week_label, label_visibility="collapsed")
        # Monthly/Yearly: build aggregated views that include gas_therm and water_gallon
        agg_cols = {"kWh": "sum", "gas_therm": "sum", "water_gallon": "sum",
                    "heating_dd": "sum", "normalized_kWh": "sum"}
        df_view      = df_all.copy()
        period_label = week_label

    elif time_filter == "Monthly":
        df_all["_period"] = df_all["_wstart"].dt.to_period("M").astype(str)
        monthly = (df_all.groupby(["_period", "building"])
                   .agg(kWh=("kWh","sum"), gas_therm=("gas_therm","sum"),
                        water_gallon=("water_gallon","sum"),
                        heating_dd=("heating_dd","sum"), normalized_kWh=("normalized_kWh","sum"))
                   .reset_index().rename(columns={"_period": "week"}))
        all_periods = sorted(monthly["week"].unique())
        def month_label(p):
            try:    return pd.to_datetime(p + "-01").strftime("%B %Y")
            except: return str(p)
        st.markdown("**Select Months**")
        selected_weeks = st.multiselect("months", all_periods,
                                        default=all_periods[-2:] if len(all_periods) >= 2 else all_periods,
                                        format_func=month_label, label_visibility="collapsed")
        df_view      = monthly
        period_label = month_label

    else:  # Yearly
        df_all["_period"] = df_all["_wstart"].dt.year.astype(str)
        yearly = (df_all.groupby(["_period", "building"])
                  .agg(kWh=("kWh","sum"), gas_therm=("gas_therm","sum"),
                       water_gallon=("water_gallon","sum"),
                       heating_dd=("heating_dd","sum"), normalized_kWh=("normalized_kWh","sum"))
                  .reset_index().rename(columns={"_period": "week"}))
        all_periods = sorted(yearly["week"].unique())
        def year_label(p): return str(p)
        st.markdown("**Select Years**")
        selected_weeks = st.multiselect("years", all_periods,
                                        default=all_periods[-2:] if len(all_periods) >= 2 else all_periods,
                                        format_func=year_label, label_visibility="collapsed")
        df_view      = yearly
        period_label = year_label

    st.markdown("---")

    # Tab navigation
    st.markdown("**Section**")
    if role == "Student (Gamified)":
        nav_opts = ["📊 Overview", "⚡ Electricity", "⛽ Gas", "💧 Water", "🏆 Leaderboard", "🔍 Data Integrity"]
    else:
        nav_opts = ["📊 Overview", "⚡ Electricity", "⛽ Gas", "💧 Water", "🔍 Data Integrity"]
    _tab = st.radio("nav", nav_opts, label_visibility="collapsed")
    active_tab = ("Overview"       if "Overview"       in _tab else
                  "Electricity"    if "Electricity"    in _tab else
                  "Gas"            if "Gas"            in _tab else
                  "Water"          if "Water"          in _tab else
                  "Leaderboard"    if "Leaderboard"    in _tab else "DataIntegrity")

    st.markdown("---")
    if time_filter == "Daily":
        st.markdown(
            f'<div style="font-size:0.75rem;color:#6a9cc0;line-height:1.7;">'
            f'{len(all_days)} day(s) in daily_energy.csv<br>'
            f'Source: Pipeline DB (actual dates only)</div>',
            unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div style="font-size:0.75rem;color:#6a9cc0;line-height:1.7;">'
            f'{len(all_weeks)} week(s) in database<br>'
            f'Latest: {week_label(all_weeks[-1]) if all_weeks else "—"}</div>',
            unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# GUARDS & SHARED AGGREGATES
# ══════════════════════════════════════════════════════════════════════════════
if not selected_weeks:
    st.warning("👈  Select at least one period from the sidebar.")
    st.stop()

df_sel = df_view[df_view["week"].isin(selected_weeks)]
if df_sel.empty:
    st.warning("No data for the selected period.")
    st.stop()

sorted_sel  = sorted(selected_weeks)
latest_week = sorted_sel[-1]
prev_week   = sorted_sel[-2] if len(sorted_sel) >= 2 else None

if prev_week is None:
    avail_all = sorted(df_view["week"].unique())
    idx_l     = avail_all.index(latest_week) if latest_week in avail_all else -1
    prev_week = avail_all[idx_l - 1] if idx_l > 0 else None

# Per-building aggregates for current and previous week
def bld_agg(col):
    return df_view.groupby(["week", "building"])[col].sum().reset_index()

by_bld_kwh   = bld_agg("kWh")
by_bld_gas   = bld_agg("gas_therm")
by_bld_water = bld_agg("water_gallon")

campus_cur   = by_bld_kwh[by_bld_kwh["week"] == latest_week]["kWh"].sum()
campus_prev  = by_bld_kwh[by_bld_kwh["week"] == prev_week]["kWh"].sum() if prev_week else 0.0
campus_cost  = campus_cur * ENERGY_RATE
scale        = "MWh" if campus_cur >= 1_000 else "kWh"
pct_change   = (campus_cur - campus_prev) / campus_prev * 100 if campus_prev > 0 else 0.0
cost_diff    = campus_prev * ENERGY_RATE - campus_cost

campus_gas_cur   = by_bld_gas[by_bld_gas["week"] == latest_week]["gas_therm"].sum()
campus_water_cur = by_bld_water[by_bld_water["week"] == latest_week]["water_gallon"].sum()

n_open   = sum(1 for s in BUILDINGS_STATUS.values() if s == "open")
n_review = sum(1 for s in BUILDINGS_STATUS.values() if s == "review")

# ── Utility chart helper (used by Electricity, Gas, Water tabs) ──────────────
def utility_bar_chart(by_bld_df, val_col, color_curr, color_prev, unit_label, height_per_bld=52):
    """
    Horizontal grouped bar chart for any utility across all buildings.
    When 2 periods are shown the bars use clearly distinct colours and a
    labelled legend so the viewer always knows which bar is which week.
    """
    # Distinct muted colour for the prior bar so it doesn't clash with current
    PRIOR_COLOR   = "#93a8c0"   # slate-blue: readable, clearly different from navy/amber/blue
    CURRENT_COLOR = color_curr  # the accent colour passed in by the caller

    if prev_week:
        c_df = by_bld_df[by_bld_df["week"] == latest_week][["building", val_col]].rename(columns={val_col:"c"})
        p_df = by_bld_df[by_bld_df["week"] == prev_week][["building", val_col]].rename(columns={val_col:"p"})
        both = pd.merge(c_df, p_df, on="building", how="outer").fillna(0).sort_values("c", ascending=True)
        fig  = go.Figure()
        fig.add_trace(go.Bar(
            name=period_label(prev_week),
            y=both["building"], x=both["p"].round(2), orientation="h",
            marker_color=PRIOR_COLOR,
            text=[(f"{v:.0f}" if v > 0 else "") for v in both["p"]],
            textposition="outside", textfont=dict(size=11, color="#374151", family="Inter"),
            hovertemplate=f"<b>%{{y}}</b><br>{period_label(prev_week)}: %{{x:,.1f}} {unit_label}<extra></extra>"))
        fig.add_trace(go.Bar(
            name=period_label(latest_week),
            y=both["building"], x=both["c"].round(2), orientation="h",
            marker_color=CURRENT_COLOR,
            text=[(f"{v:.0f}" if v > 0 else "") for v in both["c"]],
            textposition="outside", textfont=dict(size=11, color="#374151", family="Inter"),
            hovertemplate=f"<b>%{{y}}</b><br>{period_label(latest_week)}: %{{x:,.1f}} {unit_label}<extra></extra>"))
        fig.update_layout(**plot_base(height=max(340, len(both) * 64)), barmode="group",
                          bargap=0.2, bargroupgap=0.06,
                          xaxis_title=unit_label, yaxis_title="", showlegend=True,
                          legend=dict(
                              orientation="h", yanchor="bottom", y=1.01,
                              xanchor="right", x=1,
                              font=dict(size=12, family="Inter", color="#374151"),
                              bgcolor="#ffffff",
                              bordercolor="#e2e8f0", borderwidth=1))
        fig.update_yaxes(tickfont=dict(size=12, color="#111827", family="Inter"))
    else:
        ldf = by_bld_df[by_bld_df["week"] == latest_week].sort_values(val_col, ascending=True).copy()
        fig = go.Figure(go.Bar(
            name=period_label(latest_week),
            x=ldf[val_col].round(2), y=ldf["building"], orientation="h",
            marker_color=CURRENT_COLOR,
            text=[(f"{v:.0f}" if v > 0 else "") for v in ldf[val_col]],
            textposition="outside", textfont=dict(size=11, color="#374151", family="Inter"),
            hovertemplate=f"<b>%{{y}}</b><br>%{{x:,.1f}} {unit_label}<extra></extra>"))
        fig.update_layout(**plot_base(height=max(300, len(ldf) * height_per_bld)),
                          xaxis_title=unit_label, yaxis_title="", showlegend=False)
        fig.update_yaxes(tickfont=dict(size=12, color="#111827", family="Inter"))
    return fig


def building_detail_block(by_bld_df, val_col, unit_label, rate, color_curr, currency_unit=None):
    """
    Single-building detail: 3 KPI metrics + comparison cards + trend.
    currency_unit — if set (e.g. 'therm'), show cost using rate.
    """
    bld_list = sorted(
        by_bld_df[by_bld_df["week"].isin(sorted_sel + ([prev_week] if prev_week else []))]
        ["building"].unique()
    )
    sel_bld = st.selectbox("Select a Building", bld_list, key=f"sel_{val_col}")

    bld_status = BUILDINGS_STATUS.get(sel_bld, "ok")
    if bld_status == "open":
        st.markdown(alert(f'⚠️ <b>{sel_bld}</b> — No data received from FTP. '
                          f'Values show as 0 and do not reflect actual consumption. '
                          f'Check Data Integrity tab.'), unsafe_allow_html=True)
    elif bld_status == "review":
        st.markdown(alert(f'⚠️ <b>{sel_bld}</b> — {WINE_NOTE}', "amber"), unsafe_allow_html=True)

    b_cur  = by_bld_df[(by_bld_df["week"] == latest_week) & (by_bld_df["building"] == sel_bld)][val_col].sum()
    b_prev = by_bld_df[(by_bld_df["week"] == prev_week) & (by_bld_df["building"] == sel_bld)][val_col].sum() if prev_week else 0.0
    b_cost = b_cur * rate
    b_pct  = (b_cur - b_prev) / b_prev * 100 if b_prev > 0 else 0.0
    b_cdiff = b_prev * rate - b_cost

    bm1, bm2, bm3 = st.columns(3)
    if prev_week and b_prev > 0:
        bm1.metric(unit_label, fmt_val(b_cur, unit_label.split()[0]),
                   delta=f"{'▲' if b_pct > 0 else '▼'} {abs(b_pct):.1f}% vs prior",
                   delta_color="inverse")
        bm2.metric("Estimated Cost", fmt_cost(b_cost),
                   delta=fmt_cost(b_cdiff) + (" Saved" if b_cdiff >= 0 else " Extra"),
                   delta_color="normal" if b_cdiff >= 0 else "inverse")
        bm3.metric("Prior Period", fmt_val(b_prev, unit_label.split()[0]))
    else:
        bm1.metric(unit_label, fmt_val(b_cur, unit_label.split()[0]))
        bm2.metric("Estimated Cost", fmt_cost(b_cost))
        bm3.metric("Prior Period", "—" if not prev_week else fmt_val(b_prev, unit_label.split()[0]))

    if prev_week and (b_prev > 0 or b_cur > 0):
        st.markdown('<div class="sec-label">Period Comparison</div>', unsafe_allow_html=True)
        improved = b_cur <= b_prev
        chg_col  = C_GREEN if improved else C_RED
        chg_word = f"{'▼ DOWN' if improved else '▲ UP'} {abs(b_pct):.1f}%"
        ca, cb, cc = st.columns([2, 2, 3])
        ca.markdown(cmp_card(period_label(prev_week),
            f'{b_prev:,.1f} <span style="font-size:1rem;color:{C_MUTED};font-weight:500">{unit_label.split()[0]}</span>',
            footnote=f"{fmt_cost(b_prev * rate)} est. cost"), unsafe_allow_html=True)
        cb.markdown(cmp_card(period_label(latest_week),
            f'{b_cur:,.1f} <span style="font-size:1rem;color:{C_MUTED};font-weight:500">{unit_label.split()[0]}</span>',
            footnote=f"{fmt_cost(b_cost)} est. cost", accent=chg_col), unsafe_allow_html=True)
        cc.markdown(cmp_card("Change",
            f'<span style="color:{chg_col}">{chg_word}</span>',
            footnote=("Lower ✓" if improved else "Higher ✗"), accent=chg_col), unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        y_max = max(b_prev, b_cur, 0.001) * 1.38
        fig2  = go.Figure()
        fig2.add_trace(go.Bar(x=[period_label(prev_week)], y=[b_prev],
            marker_color=color_curr, opacity=0.4,
            text=[f"{b_prev:,.1f}"], textposition="outside",
            textfont=dict(size=14, color=PLOT_TEXT, family="Inter"), showlegend=False))
        fig2.add_trace(go.Bar(x=[period_label(latest_week)], y=[b_cur],
            marker_color=chg_col,
            text=[f"{b_cur:,.1f}"], textposition="outside",
            textfont=dict(size=14, color=PLOT_TEXT, family="Inter"), showlegend=False))
        fig2.update_layout(**plot_base(height=290), bargap=0.52)
        fig2.update_xaxes(showgrid=False)
        fig2.update_yaxes(visible=False, range=[0, y_max])
        st.plotly_chart(fig2, use_container_width=True)

    if len(sorted_sel) >= 3:
        st.markdown(f'<div class="sec-label">Trend — All Selected Periods</div>', unsafe_allow_html=True)
        trend_df = (by_bld_df[by_bld_df["week"].isin(sorted_sel) & (by_bld_df["building"] == sel_bld)]
                    .sort_values("week").copy())
        trend_df["label"] = trend_df["week"].apply(period_label)
        vals = trend_df[val_col].values
        c_bars = [C_NAVY] + [C_GREEN if vals[i] < vals[i-1] else C_RED for i in range(1, len(vals))]
        fig_t = go.Figure(go.Bar(x=trend_df["label"], y=trend_df[val_col],
            marker_color=c_bars,
            text=[f"{v:,.1f}" for v in trend_df[val_col]], textposition="outside",
            textfont=dict(size=12, color=PLOT_TEXT, family="Inter"), showlegend=False))
        yt = trend_df[val_col].max() * 1.32 if trend_df[val_col].max() > 0 else 1
        fig_t.update_layout(**plot_base(height=240), bargap=0.3)
        fig_t.update_xaxes(showgrid=False)
        fig_t.update_yaxes(visible=False, range=[0, yt])
        st.plotly_chart(fig_t, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# OVERVIEW TAB
# ══════════════════════════════════════════════════════════════════════════════
if active_tab == "Overview":

    # ── Daily Meter Report (shown when Daily filter is active) ────────────────
    if time_filter == "Daily":
        sel_day      = sorted_sel[-1]
        day_data     = df_daily[df_daily["week"] == sel_day].sort_values("kWh", ascending=False)
        total_kwh_day = day_data["kWh"].sum()

        h_left_d, h_right_d = st.columns([3.2, 1])
        with h_left_d:
            st.markdown('<div class="uni-label">SONOMA STATE UNIVERSITY</div>', unsafe_allow_html=True)
            st.title("Campus Energy Dashboard")
            st.markdown(
                '<p style="font-size:1.1rem;color:#6b7280;margin-top:4px;font-weight:400;line-height:1.6;">'
                'Utility monitoring across campus buildings — electricity, gas, and water.</p>',
                unsafe_allow_html=True)
        with h_right_d:
            rw = period_label(sel_day)
            st.markdown(
                f'<div style="margin-top:28px"><div class="report-window-box">'
                f'<span class="report-window-label">Report Window</span>'
                f'<span class="report-window-value">{rw}</span>'
                f'</div></div>', unsafe_allow_html=True)

        st.markdown(
            '<div class="alert-amber" style="margin-top:12px;">📅  <b>Daily View</b> — '
            'Actual daily totals from the pipeline database. Only real processed dates shown. '
            'Wine Spectator values understated (~4×) due to 75% sensor gaps.</div>',
            unsafe_allow_html=True)

        st.markdown('<div class="sec-label">Daily Campus Summary</div>', unsafe_allow_html=True)
        dk1, dk2, dk3 = st.columns(3)
        dk1.metric("Total Campus kWh", f"{total_kwh_day:,.0f} kWh")
        dk2.metric("Total Campus MWh",  f"{total_kwh_day/1000:.2f} MWh")
        dk3.metric("Est. Electricity Cost", f"${total_kwh_day * ENERGY_RATE:,.0f}")

        st.markdown('<div class="sec-label">Building Meter Reports</div>', unsafe_allow_html=True)
        max_kwh = day_data["kWh"].max() if not day_data.empty else 1

        if len(sorted_sel) == 2:
            # Two-day comparison table
            day_a, day_b = sorted_sel[0], sorted_sel[1]
            da  = df_daily[df_daily["week"] == day_a][["building","kWh"]].rename(columns={"kWh":"kWh_a"})
            db  = df_daily[df_daily["week"] == day_b][["building","kWh"]].rename(columns={"kWh":"kWh_b"})
            cmp = pd.merge(da, db, on="building", how="outer").fillna(0).sort_values("kWh_b", ascending=False)
            tbl_h = (f'<div class="card"><div class="card-title">Day Comparison — '
                     f'{period_label(day_a)}  vs  {period_label(day_b)}</div>'
                     f'<div style="height:8px"></div>'
                     f'<table class="di-table"><thead><tr>')
            for col in ["Building", f"{period_label(day_a)} kWh", f"{period_label(day_b)} kWh", "Δ kWh", "Δ %"]:
                tbl_h += f'<th>{col}</th>'
            tbl_h += '</tr></thead><tbody>'
            for _, row in cmp.iterrows():
                delta = row["kWh_b"] - row["kWh_a"]
                pct   = (delta / row["kWh_a"] * 100) if row["kWh_a"] > 0 else 0.0
                color = "#16a34a" if delta <= 0 else "#dc2626"
                arrow = "▼" if delta <= 0 else "▲"
                tbl_h += (f'<tr><td><b>{row["building"]}</b></td>'
                          f'<td>{row["kWh_a"]:,.0f}</td>'
                          f'<td>{row["kWh_b"]:,.0f}</td>'
                          f'<td style="color:{color};font-weight:600">{arrow} {abs(delta):,.0f}</td>'
                          f'<td style="color:{color};font-weight:600">{arrow} {abs(pct):.1f}%</td></tr>')
            tbl_h += '</tbody></table></div>'
            st.markdown(tbl_h, unsafe_allow_html=True)
        else:
            # Single day (or 3+): building cards in 2-col grid
            bld_list   = day_data.to_dict("records")
            left_col, right_col = st.columns(2)
            for i, row in enumerate(bld_list):
                bld   = row["building"]
                kwh   = row["kWh"]
                pct_w = kwh / max_kwh * 100 if max_kwh > 0 else 0
                bstat = BUILDINGS_STATUS.get(bld, "ok")
                status_icon = "🟢" if bstat == "ok" else "🟡" if bstat == "review" else "🔴"
                card_html = (
                    f'<div class="card" style="margin-bottom:14px;">'
                    f'<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:4px;">'
                    f'<div class="card-title">{status_icon} {bld}</div>'
                    f'<div style="font-size:1.55rem;font-weight:800;color:#1b3a5c;letter-spacing:-0.02em;">'
                    f'{kwh:,.0f} <span style="font-size:0.85rem;color:#6b7280;font-weight:500">kWh</span></div>'
                    f'</div>'
                    f'<div style="font-size:0.78rem;color:#6b7280;margin-bottom:8px;">'
                    f'{kwh/1000:.3f} MWh &nbsp;·&nbsp; Est. cost: ${kwh * ENERGY_RATE:,.0f}</div>'
                    f'<div class="topbld-track"><div class="topbld-fill" style="width:{pct_w:.0f}%;background:#1b3a5c"></div></div>'
                    f'</div>'
                )
                if i % 2 == 0:
                    left_col.markdown(card_html, unsafe_allow_html=True)
                else:
                    right_col.markdown(card_html, unsafe_allow_html=True)

        # Bar chart
        st.markdown('<div class="sec-label">Daily kWh by Building</div>', unsafe_allow_html=True)
        _chart_data = (day_data if len(sorted_sel) == 1 else
                       df_daily[df_daily["week"] == sel_day].sort_values("kWh", ascending=False))
        fig_d = go.Figure(go.Bar(
            x=_chart_data["kWh"].round(0), y=_chart_data["building"], orientation="h",
            marker_color=C_NAVY,
            text=[f"{v:,.0f}" for v in _chart_data["kWh"]],
            textposition="outside",
            textfont=dict(size=11, color="#374151", family="Inter"),
            hovertemplate="<b>%{y}</b><br>%{x:,.0f} kWh<extra></extra>"))
        fig_d.update_layout(
            **plot_base(height=max(280, len(_chart_data) * 52)),
            xaxis_title="kWh", yaxis_title="", showlegend=False)
        fig_d.update_yaxes(tickfont=dict(size=12, color="#111827", family="Inter"))
        st.plotly_chart(fig_d, use_container_width=True)

        st.stop()   # Daily view is self-contained

    # ── Normal (Weekly / Monthly / Yearly) Overview header ────────────────────
    h_left, h_right = st.columns([3.2, 1])
    with h_left:
        st.markdown('<div class="uni-label">SONOMA STATE UNIVERSITY</div>', unsafe_allow_html=True)
        st.title("Campus Energy Dashboard")
        st.markdown(
            '<p style="font-size:1.1rem;color:#6b7280;margin-top:4px;font-weight:400;line-height:1.6;">'
            'Utility monitoring across campus buildings — electricity, gas, and water.</p>',
            unsafe_allow_html=True)
    with h_right:
        rw = build_report_window(sorted_sel, period_label)
        st.markdown(
            f'<div style="margin-top:28px"><div class="report-window-box">'
            f'<span class="report-window-label">Report Window</span>'
            f'<span class="report-window-value">{rw}</span>'
            f'</div></div>', unsafe_allow_html=True)

    # KPI row — two rows of 3 so labels never truncate
    st.markdown('<div class="sec-label">Campus Overview</div>', unsafe_allow_html=True)

    # Row 1: Electricity, Cost, Change vs prior
    k1, k2, k3 = st.columns(3)
    # Check for MBTU anomaly so we can flag the metric
    _gmc_latest = by_bld_kwh[
        (by_bld_kwh["week"] == latest_week) &
        (by_bld_kwh["building"] == "Green Music Center")
    ]["kWh"].sum()
    _gmc_prior = by_bld_kwh[
        (by_bld_kwh["week"] == prev_week) &
        (by_bld_kwh["building"] == "Green Music Center")
    ]["kWh"].sum() if prev_week else 0.0
    _anomaly_present = _gmc_latest > 5_000_000 or _gmc_prior > 5_000_000
    _elec_label = f"Electricity — {scale}" + (" ⚠️" if _anomaly_present else "")

    if prev_week and campus_prev > 0:
        arrow = "▲" if pct_change > 0 else "▼"
        k1.metric(_elec_label, fmt_energy(campus_cur, scale),
                  delta=f"{arrow} {abs(pct_change):.1f}% vs prior period"
                        + (" (see anomaly note below)" if _anomaly_present else ""),
                  delta_color="inverse")
        k2.metric("Estimated Electricity Cost", fmt_cost(campus_cost),
                  delta=fmt_cost(cost_diff) + (" Saved" if cost_diff >= 0 else " Extra"),
                  delta_color="normal" if cost_diff >= 0 else "inverse")
    else:
        k1.metric(_elec_label, fmt_energy(campus_cur, scale))
        k2.metric("Estimated Electricity Cost", fmt_cost(campus_cost),
                  delta=f"@ ${ENERGY_RATE:.2f}/kWh")
    _n_rep = len(by_bld_kwh[by_bld_kwh["week"] == latest_week]["building"].unique())
    k3.metric("Buildings Reporting", f"{_n_rep} active",
              delta=f"{n_open} no data  ·  {n_review} partial")

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # Row 2: Gas, Water, Buildings reporting, Data alerts
    k4, k5, k6 = st.columns(3)
    k4.metric("Natural Gas", fmt_val(campus_gas_cur, "therm"),
              delta=f"Est. cost: {fmt_cost(campus_gas_cur * GAS_RATE)}")
    k5.metric("Water Usage", fmt_val(campus_water_cur, "gallons"),
              delta=f"Est. cost: {fmt_cost(campus_water_cur * WATER_RATE)}")

    _n_reporting = len(by_bld_kwh[by_bld_kwh["week"] == latest_week]["building"].unique())
    _n_total     = len(BUILDINGS_STATUS)
    k6.metric("Buildings Reporting Data",
              f"{_n_reporting} of {_n_total} buildings",
              delta=f"{n_open} with no data · {n_review} partial")

    # ── Anomaly banner: warn when GMC MBTU sensor inflates totals ────────────
    # Threshold: GMC realistic max is ~2,000 MWh/week. Over 5,000 MWh = anomalous.
    GMC_NORMAL_MAX_KWH = 5_000_000   # 5,000 MWh — anything above is the MBTU rate bug
    gmc_cur_kwh = by_bld_kwh[
        (by_bld_kwh["week"] == latest_week) &
        (by_bld_kwh["building"] == "Green Music Center")
    ]["kWh"].sum()
    gmc_prev_kwh = by_bld_kwh[
        (by_bld_kwh["week"] == prev_week) &
        (by_bld_kwh["building"] == "Green Music Center")
    ]["kWh"].sum() if prev_week else 0.0

    if gmc_cur_kwh > GMC_NORMAL_MAX_KWH or gmc_prev_kwh > GMC_NORMAL_MAX_KWH:
        _which = []
        if gmc_prev_kwh > GMC_NORMAL_MAX_KWH:
            _which.append(f"prior period ({gmc_prev_kwh/1e6:.1f}M kWh)")
        if gmc_cur_kwh > GMC_NORMAL_MAX_KWH:
            _which.append(f"current period ({gmc_cur_kwh/1e6:.1f}M kWh)")
        st.markdown(
            f'<div class="alert-amber" style="margin-top:14px;">'
            f'⚠️ <b>Data Anomaly Detected — Green Music Center:</b> The Hot Water BTU meter '
            f'(sensor 234aa956-82d369b2) is reporting unrealistically large values in the '
            f'{" and ".join(_which)}. '
            f'This inflates campus totals and causes extreme % changes. '
            f'The sensor appears to be sending an <b>instantaneous flow rate</b> instead of '
            f'<b>interval consumption</b> — a BMS configuration issue. '
            f'The pipeline stores raw values faithfully; the fix must happen at the BMS level. '
            f'All other buildings and meters are unaffected.'
            f'</div>',
            unsafe_allow_html=True)

    # Main layout
    main_col, side_col = st.columns([1.55, 1])

    with main_col:
        st.markdown('<div class="sec-label">Building Details — Electricity</div>', unsafe_allow_html=True)
        bld_list = sorted(by_bld_kwh[by_bld_kwh["week"].isin(
            sorted_sel + ([prev_week] if prev_week else [])
        )]["building"].unique())
        sel_bld = st.selectbox("Select a Building", bld_list, key="ov_sel")

        bld_status = BUILDINGS_STATUS.get(sel_bld, "ok")
        if bld_status == "open":
            st.markdown(alert(f'⚠️ <b>{sel_bld}</b> — No interval data from FTP. See Data Integrity.'),
                        unsafe_allow_html=True)
        elif bld_status == "review":
            st.markdown(alert(f'⚠️ <b>{sel_bld}</b> — {WINE_NOTE}', "amber"), unsafe_allow_html=True)

        b_cur  = by_bld_kwh[(by_bld_kwh["week"] == latest_week) & (by_bld_kwh["building"] == sel_bld)]["kWh"].sum()
        b_prev = by_bld_kwh[(by_bld_kwh["week"] == prev_week) & (by_bld_kwh["building"] == sel_bld)]["kWh"].sum() if prev_week else 0.0
        b_cost = b_cur * ENERGY_RATE
        b_pct  = (b_cur - b_prev) / b_prev * 100 if b_prev > 0 else 0.0
        b_cdiff = b_prev * ENERGY_RATE - b_cost

        bm1, bm2, bm3 = st.columns(3)
        if prev_week and b_prev > 0:
            bm1.metric(f"Energy ({scale})", fmt_energy(b_cur, scale),
                       delta=f"{'▲' if b_pct > 0 else '▼'} {abs(b_pct):.1f}% vs prior", delta_color="inverse")
            bm2.metric("Estimated Cost", fmt_cost(b_cost),
                       delta=fmt_cost(b_cdiff) + (" Saved" if b_cdiff >= 0 else " Extra"),
                       delta_color="normal" if b_cdiff >= 0 else "inverse")
            bm3.metric("Prior Period", fmt_energy(b_prev, scale))
        else:
            bm1.metric(f"Energy ({scale})", fmt_energy(b_cur, scale))
            bm2.metric("Estimated Cost", fmt_cost(b_cost))
            bm3.metric("Prior Period", "—" if not prev_week else fmt_energy(b_prev, scale))

        if prev_week and (b_prev > 0 or b_cur > 0):
            st.markdown('<div class="sec-label">Period Comparison</div>', unsafe_allow_html=True)
            div = 1000 if scale == "MWh" else 1
            p_v, c_v = b_prev / div, b_cur / div
            improved = b_cur <= b_prev
            chg_col  = C_GREEN if improved else C_RED
            chg_word = f"{'▼ DOWN' if improved else '▲ UP'} {abs(b_pct):.1f}%"
            ca, cb, cc = st.columns([2, 2, 3])
            ca.markdown(cmp_card(period_label(prev_week),
                f'{p_v:,.1f} <span style="font-size:1rem;color:{C_MUTED};font-weight:500">{scale}</span>',
                footnote=f"${b_prev * ENERGY_RATE:,.0f} est. cost"), unsafe_allow_html=True)
            cb.markdown(cmp_card(period_label(latest_week),
                f'{c_v:,.1f} <span style="font-size:1rem;color:{C_MUTED};font-weight:500">{scale}</span>',
                footnote=f"${b_cost:,.0f} est. cost", accent=chg_col), unsafe_allow_html=True)
            cc.markdown(cmp_card("Change",
                f'<span style="color:{chg_col}">{chg_word}</span>',
                footnote="Lower ✓" if improved else "Higher ✗", accent=chg_col), unsafe_allow_html=True)
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            y_max = max(p_v, c_v, 0.001) * 1.38
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(x=[period_label(prev_week)], y=[p_v], marker_color=C_NAVY, opacity=0.45,
                text=[f"{p_v:,.1f}"], textposition="outside",
                textfont=dict(size=14, color=PLOT_TEXT, family="Inter"), showlegend=False))
            fig2.add_trace(go.Bar(x=[period_label(latest_week)], y=[c_v], marker_color=chg_col,
                text=[f"{c_v:,.1f}"], textposition="outside",
                textfont=dict(size=14, color=PLOT_TEXT, family="Inter"), showlegend=False))
            fig2.update_layout(**plot_base(height=290), bargap=0.52)
            fig2.update_xaxes(showgrid=False); fig2.update_yaxes(visible=False, range=[0, y_max])
            st.plotly_chart(fig2, use_container_width=True)

        if len(sorted_sel) >= 3:
            st.markdown('<div class="sec-label">Energy Trend — All Selected Periods</div>', unsafe_allow_html=True)
            trend_df = (by_bld_kwh[by_bld_kwh["week"].isin(sorted_sel) & (by_bld_kwh["building"] == sel_bld)]
                        .sort_values("week").copy())
            trend_df["disp"]  = trend_df["kWh"] / (1000 if scale == "MWh" else 1)
            trend_df["label"] = trend_df["week"].apply(period_label)
            vals   = trend_df["kWh"].values
            c_bars = [C_NAVY] + [C_GREEN if vals[i] < vals[i-1] else C_RED for i in range(1, len(vals))]
            fig_t  = go.Figure(go.Bar(x=trend_df["label"], y=trend_df["disp"], marker_color=c_bars,
                text=[f"{v:,.1f}" for v in trend_df["disp"]], textposition="outside",
                textfont=dict(size=12, color=PLOT_TEXT, family="Inter"), showlegend=False))
            yt = trend_df["disp"].max() * 1.32 if trend_df["disp"].max() > 0 else 1
            fig_t.update_layout(**plot_base(height=240), bargap=0.3)
            fig_t.update_xaxes(showgrid=False); fig_t.update_yaxes(visible=False, range=[0, yt])
            st.plotly_chart(fig_t, use_container_width=True)

        # All buildings comparison
        cmp_ttl = f"All Buildings — {build_report_window(sorted_sel, period_label)}"
        st.markdown(f'<div class="sec-label">{cmp_ttl}</div>', unsafe_allow_html=True)
        st.plotly_chart(utility_bar_chart(by_bld_kwh, "kWh", C_NAVY, C_NAVY, scale),
                        use_container_width=True)

    with side_col:
        # Top buildings (electric)
        top_blds  = by_bld_kwh[by_bld_kwh["week"] == latest_week].sort_values("kWh", ascending=False).head(7)
        max_kwh   = float(top_blds["kWh"].max()) if not top_blds.empty else 1.0
        bars_html = "".join(top_bld_html(str(r["building"]), float(r["kWh"]), max_kwh)
                            for _, r in top_blds.iterrows())
        st.markdown(
            f'<div class="card"><div class="card-title">Top Buildings by Electricity</div>'
            f'<div class="card-sub">Current period — kWh</div>'
            f'{bars_html}</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        # Utility coverage — enlarged
        st.markdown(
            '<div class="card"><div class="card-title" style="font-size:1.35rem;">🔌 Utility Coverage</div>'
            '<div style="font-size:1.05rem;color:#374151;line-height:2.2;margin-top:10px;">'
            '<b>⚡ Electric:</b> Active for 8+ buildings<br>'
            '<b>🌡 Thermal (BTU/kBTU):</b> GMC, Nichols, Ives, Student Center<br>'
            '<b>⛽ Gas (therm):</b> 5 meters registered — '
            '<span style="color:#dc2626;font-weight:600">all missing from FTP</span><br>'
            '<b>💧 Water:</b> 1 meter registered (GMC) — '
            '<span style="color:#dc2626;font-weight:600">all NaN in provided files</span><br>'
            '<b>📊 See Data Integrity tab</b> for full sensor map &amp; data quality monitor.'
            '</div></div>',
            unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ELECTRICITY TAB
# ══════════════════════════════════════════════════════════════════════════════
elif active_tab == "Electricity":

    if time_filter == "Daily":
        sel_day       = sorted_sel[-1]
        day_data      = df_daily[df_daily["week"] == sel_day].sort_values("kWh", ascending=False)
        total_kwh_day = day_data["kWh"].sum()
        max_kwh_d     = day_data["kWh"].max() if not day_data.empty else 1

        h_l, h_r = st.columns([3.2, 1])
        with h_l:
            st.markdown('<div class="uni-label">SONOMA STATE UNIVERSITY</div>', unsafe_allow_html=True)
            st.title("⚡ Electricity")
            st.markdown(
                '<p style="font-size:1.1rem;color:#6b7280;margin-top:4px;line-height:1.6;">'
                'Daily verified electric meter readings by building.</p>',
                unsafe_allow_html=True)
        with h_r:
            st.markdown(
                f'<div style="margin-top:28px"><div class="report-window-box">'
                f'<span class="report-window-label">Report Window</span>'
                f'<span class="report-window-value">{period_label(sel_day)}</span>'
                f'</div></div>', unsafe_allow_html=True)

        st.markdown(
            '<div class="alert-amber">📅 <b>Daily View</b> — '
            'Actual daily totals from the pipeline database. Only real processed dates shown. '
            'Wine Spectator values understated (~4×) due to 75% sensor gaps.</div>',
            unsafe_allow_html=True)

        st.markdown('<div class="sec-label">Daily Electricity Summary</div>', unsafe_allow_html=True)
        ek1, ek2, ek3 = st.columns(3)
        ek1.metric("Total Campus kWh",     f"{total_kwh_day:,.0f} kWh")
        ek2.metric("Total Campus MWh",     f"{total_kwh_day/1000:.2f} MWh")
        ek3.metric("Est. Electricity Cost",f"${total_kwh_day * ENERGY_RATE:,.0f}")

        if len(sorted_sel) == 2:
            day_a, day_b = sorted_sel[0], sorted_sel[1]
            da  = df_daily[df_daily["week"] == day_a][["building","kWh"]].rename(columns={"kWh":"kWh_a"})
            db  = df_daily[df_daily["week"] == day_b][["building","kWh"]].rename(columns={"kWh":"kWh_b"})
            cmp = pd.merge(da, db, on="building", how="outer").fillna(0).sort_values("kWh_b", ascending=False)
            tbl = (f'<div class="card"><div class="card-title">Day Comparison — '
                   f'{period_label(day_a)} vs {period_label(day_b)}</div>'
                   f'<div style="height:8px"></div><table class="di-table"><thead><tr>')
            for col in ["Building", f"{period_label(day_a)} kWh", f"{period_label(day_b)} kWh", "Δ kWh", "Δ %"]:
                tbl += f'<th>{col}</th>'
            tbl += '</tr></thead><tbody>'
            for _, row in cmp.iterrows():
                delta = row["kWh_b"] - row["kWh_a"]
                pct   = (delta / row["kWh_a"] * 100) if row["kWh_a"] > 0 else 0.0
                color = "#16a34a" if delta <= 0 else "#dc2626"
                arrow = "▼" if delta <= 0 else "▲"
                tbl  += (f'<tr><td><b>{row["building"]}</b></td>'
                         f'<td>{row["kWh_a"]:,.0f}</td><td>{row["kWh_b"]:,.0f}</td>'
                         f'<td style="color:{color};font-weight:600">{arrow} {abs(delta):,.0f}</td>'
                         f'<td style="color:{color};font-weight:600">{arrow} {abs(pct):.1f}%</td></tr>')
            tbl += '</tbody></table></div>'
            st.markdown(tbl, unsafe_allow_html=True)
        else:
            st.markdown('<div class="sec-label">Building Meter Reports</div>', unsafe_allow_html=True)
            lc, rc = st.columns(2)
            for i, row in enumerate(day_data.to_dict("records")):
                bld   = row["building"]
                kwh   = row["kWh"]
                pct_w = kwh / max_kwh_d * 100 if max_kwh_d > 0 else 0
                bstat = BUILDINGS_STATUS.get(bld, "ok")
                icon  = "🟢" if bstat == "ok" else "🟡" if bstat == "review" else "🔴"
                card  = (f'<div class="card" style="margin-bottom:14px;">'
                         f'<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:4px;">'
                         f'<div class="card-title">{icon} {bld}</div>'
                         f'<div style="font-size:1.55rem;font-weight:800;color:#1b3a5c;letter-spacing:-0.02em;">'
                         f'{kwh:,.0f} <span style="font-size:0.85rem;color:#6b7280;font-weight:500">kWh</span></div>'
                         f'</div>'
                         f'<div style="font-size:0.78rem;color:#6b7280;margin-bottom:8px;">'
                         f'{kwh/1000:.3f} MWh &nbsp;·&nbsp; Est. cost: ${kwh * ENERGY_RATE:,.0f}</div>'
                         f'<div class="topbld-track"><div class="topbld-fill" style="width:{pct_w:.0f}%;background:#1b3a5c"></div></div>'
                         f'</div>')
                (lc if i % 2 == 0 else rc).markdown(card, unsafe_allow_html=True)

        st.markdown('<div class="sec-label">Daily kWh by Building</div>', unsafe_allow_html=True)
        fig_de = go.Figure(go.Bar(
            x=day_data["kWh"].round(0), y=day_data["building"], orientation="h",
            marker_color=C_NAVY,
            text=[f"{v:,.0f}" for v in day_data["kWh"]],
            textposition="outside",
            textfont=dict(size=11, color="#374151", family="Inter"),
            hovertemplate="<b>%{y}</b><br>%{x:,.0f} kWh<extra></extra>"))
        fig_de.update_layout(
            **plot_base(height=max(280, len(day_data) * 52)),
            xaxis_title="kWh", yaxis_title="", showlegend=False)
        fig_de.update_yaxes(tickfont=dict(size=12, color="#111827", family="Inter"))
        st.plotly_chart(fig_de, use_container_width=True)
        st.stop()

    h_left, h_right = st.columns([3.2, 1])
    with h_left:
        st.markdown('<div class="uni-label">SONOMA STATE UNIVERSITY</div>', unsafe_allow_html=True)
        st.title("⚡ Electricity")
        st.markdown(
            '<p style="font-size:1.1rem;color:#6b7280;margin-top:4px;line-height:1.6;">'
            'Electric meter readings in kWh across all campus buildings. '
            'Thermal (BTU/MBTU) readings are converted to kWh equivalent.</p>',
            unsafe_allow_html=True)
    with h_right:
        rw = build_report_window(sorted_sel, period_label)
        st.markdown(
            f'<div style="margin-top:28px"><div class="report-window-box">'
            f'<span class="report-window-label">Report Window</span>'
            f'<span class="report-window-value">{rw}</span>'
            f'</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="sec-label">Campus Electricity Overview</div>', unsafe_allow_html=True)
    k1, k2, k3 = st.columns(3)
    campus_prev_e = by_bld_kwh[by_bld_kwh["week"] == prev_week]["kWh"].sum() if prev_week else 0.0
    e_pct = (campus_cur - campus_prev_e) / campus_prev_e * 100 if campus_prev_e > 0 else 0.0
    if prev_week and campus_prev_e > 0:
        k1.metric(f"Total Campus Electricity ({scale})", fmt_energy(campus_cur, scale),
                  delta=f"{'▲' if e_pct > 0 else '▼'} {abs(e_pct):.1f}% vs prior", delta_color="inverse")
        k2.metric("Estimated Cost", fmt_cost(campus_cost),
                  delta=fmt_cost(cost_diff) + (" Saved" if cost_diff >= 0 else " Extra"),
                  delta_color="normal" if cost_diff >= 0 else "inverse")
    else:
        k1.metric(f"Total Campus Electricity ({scale})", fmt_energy(campus_cur, scale))
        k2.metric("Estimated Cost", fmt_cost(campus_cost))
    k3.metric("Rate", f"${ENERGY_RATE:.2f}/kWh")

    main_col, side_col = st.columns([1.6, 1])
    with main_col:
        st.markdown('<div class="sec-label">Building Detail</div>', unsafe_allow_html=True)
        building_detail_block(by_bld_kwh, "kWh", "kWh", ENERGY_RATE, C_NAVY)

        st.markdown(f'<div class="sec-label">All Buildings — {build_report_window(sorted_sel, period_label)}</div>', unsafe_allow_html=True)
        st.plotly_chart(utility_bar_chart(by_bld_kwh, "kWh", C_NAVY, C_NAVY, scale), use_container_width=True)

    with side_col:
        top_blds  = by_bld_kwh[by_bld_kwh["week"] == latest_week].sort_values("kWh", ascending=False).head(7)
        max_kwh   = float(top_blds["kWh"].max()) if not top_blds.empty else 1.0
        bars_html = "".join(top_bld_html(str(r["building"]), float(r["kWh"]), max_kwh)
                            for _, r in top_blds.iterrows())
        st.markdown(
            f'<div class="card"><div class="card-title">Top Buildings by Electricity</div>'
            f'<div class="card-sub">Current period</div>{bars_html}</div>',
            unsafe_allow_html=True)
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        st.markdown(
            '<div class="card"><div class="card-title">Conversion notes</div>'
            '<div style="font-size:0.94rem;color:#374151;line-height:1.9;margin-top:8px;">'
            'All BTU/MBTU readings are converted to kWh:<br>'
            '<code style="background:#f1f5f9;padding:2px 6px;border-radius:4px;">BTU × 0.000293071</code><br>'
            '<code style="background:#f1f5f9;padding:2px 6px;border-radius:4px;">MBTU × 293.071</code><br><br>'
            'Raw values are stored faithfully in the DB; conversion happens only when computing kWh totals.'
            '</div></div>',
            unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# GAS TAB
# ══════════════════════════════════════════════════════════════════════════════
elif active_tab == "Gas":

    if time_filter == "Daily":
        st.markdown('<div class="uni-label">SONOMA STATE UNIVERSITY</div>', unsafe_allow_html=True)
        st.title("⛽ Natural Gas")
        st.info("📅 **Daily View** — No daily gas meter data is available. "
                "Gas meters (Boiler Plant, Green Music Center, Schulz Info Center) are currently "
                "reporting 100% missing from FTP. Switch to Weekly / Monthly to see gas data once "
                "BMS begins reporting. Check the 🔍 Data Integrity tab for details.")
        st.stop()

    h_left, h_right = st.columns([3.2, 1])
    with h_left:
        st.markdown('<div class="uni-label">SONOMA STATE UNIVERSITY</div>', unsafe_allow_html=True)
        st.title("⛽ Natural Gas")
        st.markdown(
            '<p style="font-size:1.1rem;color:#6b7280;margin-top:4px;line-height:1.6;">'
            'Natural gas consumption in therms from the gas_usage table. '
            'Meters: Boiler Plant, Green Music Center, Schulz Info Center.</p>',
            unsafe_allow_html=True)
    with h_right:
        rw = build_report_window(sorted_sel, period_label)
        st.markdown(
            f'<div style="margin-top:28px"><div class="report-window-box">'
            f'<span class="report-window-label">Report Window</span>'
            f'<span class="report-window-value">{rw}</span>'
            f'</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="sec-label sec-label-gas">Campus Gas Overview</div>', unsafe_allow_html=True)

    campus_gas_prev = by_bld_gas[by_bld_gas["week"] == prev_week]["gas_therm"].sum() if prev_week else 0.0
    gas_pct = (campus_gas_cur - campus_gas_prev) / campus_gas_prev * 100 if campus_gas_prev > 0 else 0.0
    g1, g2, g3 = st.columns(3)
    if prev_week and campus_gas_prev > 0:
        g1.metric("Total Gas (therm)", fmt_val(campus_gas_cur, "therm"),
                  delta=f"{'▲' if gas_pct > 0 else '▼'} {abs(gas_pct):.1f}% vs prior", delta_color="inverse")
        gas_cost = campus_gas_cur * GAS_RATE; gas_prev_cost = campus_gas_prev * GAS_RATE
        g2.metric("Estimated Cost", fmt_cost(gas_cost),
                  delta=fmt_cost(gas_prev_cost - gas_cost) + (" Saved" if gas_prev_cost >= gas_cost else " Extra"),
                  delta_color="normal" if gas_prev_cost >= gas_cost else "inverse")
    else:
        g1.metric("Total Gas (therm)", fmt_val(campus_gas_cur, "therm"))
        g2.metric("Estimated Cost", fmt_cost(campus_gas_cur * GAS_RATE))
    g3.metric("Rate", f"${GAS_RATE:.2f}/therm")

    if campus_gas_cur == 0 and campus_gas_prev == 0:
        st.info(
            "⛽ No gas meter data in the selected period. "
            "Three gas meters are registered in the system (Boiler Plant, Green Music Center, Schulz Info Center). "
            "They will appear here as soon as the BMS begins reporting readings. "
            "Check the Data Integrity tab for sensor status.", icon="ℹ️")
    else:
        main_col, side_col = st.columns([1.6, 1])
        with main_col:
            st.markdown('<div class="sec-label sec-label-gas">Building Detail</div>', unsafe_allow_html=True)
            building_detail_block(by_bld_gas, "gas_therm", "therm", GAS_RATE, C_AMBER)
            st.markdown('<div class="sec-label sec-label-gas">All Buildings</div>', unsafe_allow_html=True)
            st.plotly_chart(utility_bar_chart(by_bld_gas, "gas_therm", C_AMBER, C_AMBER, "therm"),
                            use_container_width=True)
        with side_col:
            top_gas  = by_bld_gas[by_bld_gas["week"] == latest_week].sort_values("gas_therm", ascending=False).head(7)
            max_gas  = float(top_gas["gas_therm"].max()) if not top_gas.empty else 1.0
            bars_gas = "".join(top_bld_html(str(r["building"]), float(r["gas_therm"]), max_gas, "therm", C_AMBER)
                               for _, r in top_gas.iterrows())
            st.markdown(
                f'<div class="card"><div class="card-title">Top Buildings by Gas</div>'
                f'<div class="card-sub">Current period — therm</div>{bars_gas}</div>',
                unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# WATER TAB
# ══════════════════════════════════════════════════════════════════════════════
elif active_tab == "Water":

    if time_filter == "Daily":
        st.markdown('<div class="uni-label">SONOMA STATE UNIVERSITY</div>', unsafe_allow_html=True)
        st.title("💧 Water")
        st.info("📅 **Daily View** — No daily water meter data is available. "
                "The Green Music Center water meter (234aa782-f7b1eef2) is 100% NaN in all "
                "provided FTP files. Switch to Weekly / Monthly once the BMS begins reporting. "
                "Check the 🔍 Data Integrity tab for details.")
        st.stop()

    h_left, h_right = st.columns([3.2, 1])
    with h_left:
        st.markdown('<div class="uni-label">SONOMA STATE UNIVERSITY</div>', unsafe_allow_html=True)
        st.title("💧 Water")
        st.markdown(
            '<p style="font-size:1.1rem;color:#6b7280;margin-top:4px;line-height:1.6;">'
            'Water consumption in gallons from the water_usage table. '
            'Meter: Green Music Center (234aa782-f7b1eef2).</p>',
            unsafe_allow_html=True)
    with h_right:
        rw = build_report_window(sorted_sel, period_label)
        st.markdown(
            f'<div style="margin-top:28px"><div class="report-window-box">'
            f'<span class="report-window-label">Report Window</span>'
            f'<span class="report-window-value">{rw}</span>'
            f'</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="sec-label sec-label-water">Campus Water Overview</div>', unsafe_allow_html=True)

    campus_water_prev = by_bld_water[by_bld_water["week"] == prev_week]["water_gallon"].sum() if prev_week else 0.0
    water_pct = (campus_water_cur - campus_water_prev) / campus_water_prev * 100 if campus_water_prev > 0 else 0.0
    w1, w2, w3 = st.columns(3)
    if prev_week and campus_water_prev > 0:
        w1.metric("Total Water (gal)", fmt_val(campus_water_cur, "gal"),
                  delta=f"{'▲' if water_pct > 0 else '▼'} {abs(water_pct):.1f}% vs prior", delta_color="inverse")
        wat_cost = campus_water_cur * WATER_RATE; wat_prev_cost = campus_water_prev * WATER_RATE
        w2.metric("Estimated Cost", fmt_cost(wat_cost),
                  delta=fmt_cost(wat_prev_cost - wat_cost) + (" Saved" if wat_prev_cost >= wat_cost else " Extra"),
                  delta_color="normal" if wat_prev_cost >= wat_cost else "inverse")
    else:
        w1.metric("Total Water (gal)", fmt_val(campus_water_cur, "gal"))
        w2.metric("Estimated Cost", fmt_cost(campus_water_cur * WATER_RATE))
    w3.metric("Rate", f"${WATER_RATE * 1000:.2f}/1,000 gal")

    if campus_water_cur == 0 and campus_water_prev == 0:
        st.info(
            "💧 No water meter data in the selected period. "
            "The Green Music Center water meter (234aa782-f7b1eef2) is registered and will appear "
            "here once the BMS begins reporting readings.", icon="ℹ️")
    else:
        main_col, side_col = st.columns([1.6, 1])
        with main_col:
            st.markdown('<div class="sec-label sec-label-water">Building Detail</div>', unsafe_allow_html=True)
            building_detail_block(by_bld_water, "water_gallon", "gallon", WATER_RATE, C_BLUE)
            st.markdown('<div class="sec-label sec-label-water">All Buildings</div>', unsafe_allow_html=True)
            st.plotly_chart(utility_bar_chart(by_bld_water, "water_gallon", C_BLUE, C_BLUE, "gallon"),
                            use_container_width=True)
        with side_col:
            top_wat  = by_bld_water[by_bld_water["week"] == latest_week].sort_values("water_gallon", ascending=False).head(7)
            max_wat  = float(top_wat["water_gallon"].max()) if not top_wat.empty else 1.0
            bars_wat = "".join(top_bld_html(str(r["building"]), float(r["water_gallon"]), max_wat, "gal", C_BLUE)
                               for _, r in top_wat.iterrows())
            st.markdown(
                f'<div class="card"><div class="card-title">Top Buildings by Water</div>'
                f'<div class="card-sub">Current period — gallons</div>{bars_wat}</div>',
                unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# LEADERBOARD TAB  (original logic preserved; electric kWh only)
# ══════════════════════════════════════════════════════════════════════════════
elif active_tab == "Leaderboard":

    if time_filter == "Daily":
        sel_day       = sorted_sel[-1]
        day_data_lb   = df_daily[df_daily["week"] == sel_day].sort_values("kWh", ascending=False)
        st.markdown('<div class="uni-label">SONOMA STATE UNIVERSITY</div>', unsafe_allow_html=True)
        st.title("🏆 Building Energy Leaderboard")
        st.markdown(
            f'<p style="font-size:1.1rem;color:#6b7280;margin-top:4px;line-height:1.6;">'
            f'Daily electricity rankings for <b style="color:#111827">{period_label(sel_day)}</b>. '
            f'Ranked by total kWh consumed.</p>',
            unsafe_allow_html=True)

        if len(sorted_sel) >= 2:
            # Day vs day leaderboard: rank by % improvement
            day_a, day_b = sorted_sel[-2], sorted_sel[-1]
            da  = df_daily[df_daily["week"] == day_a][["building","kWh"]].rename(columns={"kWh":"p"})
            db  = df_daily[df_daily["week"] == day_b][["building","kWh"]].rename(columns={"kWh":"c"})
            lb  = pd.merge(da, db, on="building", how="inner")
            lb  = lb[(lb["p"] > 0) & (lb["c"] > 0)].copy()
            lb["pct"] = (lb["c"] - lb["p"]) / lb["p"] * 100
            lb  = lb.sort_values("pct").reset_index(drop=True)
            medals = {0:"🥇", 1:"🥈", 2:"🥉"}
            rank_cls = {0:"gold", 1:"silver", 2:"bronze"}
            for i, row in lb.iterrows():
                improved  = row["pct"] <= 0
                pct_color = C_GREEN if improved else C_RED
                medal     = medals.get(i, "")
                rank_text = medal if medal else f"#{i+1}"
                rank_c    = rank_cls.get(i, "")
                st.markdown(
                    f'<div class="lb-row">'
                    f'<div class="lb-rank {rank_c}">{rank_text}</div>'
                    f'<div style="flex:1">'
                    f'<div class="lb-name">{row["building"]}</div>'
                    f'<div class="lb-sub">{period_label(day_a)}: {row["p"]:,.0f} kWh &nbsp;→&nbsp; '
                    f'{period_label(day_b)}: {row["c"]:,.0f} kWh</div>'
                    f'</div>'
                    f'<div>'
                    f'<div class="lb-pct" style="color:{pct_color}">'
                    f'{"▼" if improved else "▲"} {abs(row["pct"]):.1f}%</div>'
                    f'<div class="lb-pct-lbl">vs prior day</div>'
                    f'</div></div>',
                    unsafe_allow_html=True)
        else:
            # Single day: rank by absolute kWh (lower = better)
            medals = {0:"🥇", 1:"🥈", 2:"🥉"}
            rank_cls = {0:"gold", 1:"silver", 2:"bronze"}
            ranked = day_data_lb.reset_index(drop=True)
            for i, row in ranked.iterrows():
                medal     = medals.get(i, "")
                rank_text = medal if medal else f"#{i+1}"
                rank_c    = rank_cls.get(i, "")
                pct_w     = row["kWh"] / ranked["kWh"].max() * 100 if ranked["kWh"].max() > 0 else 0
                st.markdown(
                    f'<div class="lb-row">'
                    f'<div class="lb-rank {rank_c}">{rank_text}</div>'
                    f'<div style="flex:1">'
                    f'<div class="lb-name">{row["building"]}</div>'
                    f'<div class="lb-sub">{period_label(sel_day)}</div>'
                    f'</div>'
                    f'<div>'
                    f'<div class="lb-pct" style="color:#1b3a5c">{row["kWh"]:,.0f}</div>'
                    f'<div class="lb-pct-lbl">kWh</div>'
                    f'</div></div>',
                    unsafe_allow_html=True)
            st.markdown(
                '<div style="font-size:0.8rem;color:#9ca3af;margin-top:10px;">'
                '💡 Select two days in the sidebar to see a day-vs-day % change leaderboard.</div>',
                unsafe_allow_html=True)
        st.stop()

    h_left2, h_right2 = st.columns([3.2, 1])
    with h_left2:
        st.markdown('<div class="uni-label">SONOMA STATE UNIVERSITY</div>', unsafe_allow_html=True)
        st.title("Building Energy Leaderboard")
        st.markdown(
            '<p style="font-size:1.1rem;color:#6b7280;margin-top:4px;line-height:1.6;">'
            'Rankings by <b style="color:#111827">% change in electricity (kWh)</b> vs prior period. '
            'Buildings with no data in either period are excluded.</p>',
            unsafe_allow_html=True)

    lb_latest = sorted_sel[-1]
    lb_prev   = sorted_sel[-2] if len(sorted_sel) >= 2 else None
    if lb_prev is None:
        avail2  = sorted(df_view["week"].unique())
        idx2    = avail2.index(lb_latest) if lb_latest in avail2 else -1
        lb_prev = avail2[idx2 - 1] if idx2 > 0 else None

    with h_right2:
        rw2 = (f"{period_label(lb_prev)}  vs  {period_label(lb_latest)}"
               if lb_prev else period_label(lb_latest))
        st.markdown(
            f'<div style="margin-top:28px"><div class="report-window-box">'
            f'<span class="report-window-label">Comparing</span>'
            f'<span class="report-window-value">{rw2}</span>'
            f'</div></div>', unsafe_allow_html=True)

    if lb_prev is None:
        st.info("Only one period of data. Run the pipeline next period to unlock rankings.")
        st.stop()

    by_lb = by_bld_kwh
    c_df  = by_lb[by_lb["week"] == lb_latest][["building","kWh"]].rename(columns={"kWh":"kWh_c"})
    p_df  = by_lb[by_lb["week"] == lb_prev][["building","kWh"]].rename(columns={"kWh":"kWh_p"})
    cmp   = pd.merge(c_df, p_df, on="building", how="outer").fillna(0)
    cmp   = cmp[(cmp["kWh_c"] > 0) | (cmp["kWh_p"] > 0)].copy()

    cmp["delta_kwh"]  = cmp["kWh_p"] - cmp["kWh_c"]
    cmp["delta_pct"]  = cmp.apply(
        lambda r: r["delta_kwh"] / r["kWh_p"] * 100 if r["kWh_p"] > 0 else 0.0, axis=1)
    cmp["cost_saved"] = cmp["delta_kwh"] * ENERGY_RATE

    all_pvt = (by_lb.pivot_table(index="week", columns="building", values="kWh", aggfunc="sum")
               .fillna(0).sort_index())
    streak_map = {}
    for b in all_pvt.columns:
        s, k = all_pvt[b].values, 0
        for i in range(len(s) - 1, 0, -1):
            if s[i] < s[i - 1]: k += 1
            else: break
        streak_map[b] = k
    cmp["streak"] = cmp["building"].map(streak_map).fillna(0).astype(int)

    lb      = cmp.sort_values(["delta_pct","delta_kwh"], ascending=[False, False]).reset_index(drop=True)
    tot_c   = float(cmp["kWh_c"].sum()); tot_p = float(cmp["kWh_p"].sum())
    tot_d   = tot_p - tot_c
    tot_pct = tot_d / tot_p * 100 if tot_p > 0 else 0.0
    n_better = int((cmp["delta_pct"] > 0.5).sum())
    n_worse  = int((cmp["delta_pct"] < -0.5).sum())
    d_col    = C_GREEN if tot_d >= 0 else C_RED

    st.markdown(
        f'<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px;">'
        f'<div style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:7px 14px;font-size:0.86rem;color:#4b5563;font-weight:500;">'
        f'🏫 <b style="color:#111827">{len(lb)}</b> buildings ranked</div>'
        f'<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:7px 14px;font-size:0.86rem;color:#166534;font-weight:600;">'
        f'✅ {n_better} reduced</div>'
        f'<div style="background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:7px 14px;font-size:0.86rem;color:#991b1b;font-weight:600;">'
        f'⚠️ {n_worse} increased</div>'
        f'<div style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:7px 14px;font-size:0.86rem;color:#4b5563;font-weight:500;">'
        f'Campus: <b style="color:{d_col}">{tot_pct:+.1f}%</b></div>'
        f'<div style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:7px 14px;font-size:0.86rem;color:#4b5563;font-weight:500;">'
        f'💰 <b style="color:{d_col}">${abs(tot_d * ENERGY_RATE):,.0f}</b> {"saved" if tot_d >= 0 else "extra"}</div>'
        f'</div>', unsafe_allow_html=True)

    rows_html = ""
    for i, row in lb.iterrows():
        pct      = float(row["delta_pct"])
        eco_kwh  = int(float(row["delta_kwh"]))
        saved    = pct > 0.5; neutral = abs(pct) <= 0.5
        cost_abs = abs(float(row["cost_saved"])); kwh_abs = abs(eco_kwh)
        bld      = str(row["building"])
        p_kwh    = int(float(row["kWh_p"])); c_kwh = int(float(row["kWh_c"]))

        if saved:
            pts_col = C_GREEN; pct_disp = f"+{pct:.1f}%"
            act_str = f"{kwh_abs:,} kWh saved"; cost_str = f"💰 ${cost_abs:,.0f} saved"
        elif neutral:
            pts_col = C_MUTED; pct_disp = "≈ 0%"
            act_str = "No significant change"; cost_str = ""
        else:
            pts_col = C_RED; pct_disp = f"{pct:.1f}%"
            act_str = f"{kwh_abs:,} kWh more used"; cost_str = f"💸 ${cost_abs:,.0f} extra"

        rank_num = i + 1
        rank_cls = "gold" if rank_num == 1 else "silver" if rank_num == 2 else "bronze" if rank_num == 3 else ""
        rd = f"#{rank_num}"

        streak_tag = (f'<span class="streak">🔥 {int(row["streak"])}w streak</span>'
                      if row["streak"] > 0 else "")
        gap_tag = ""
        if bld == "Wine Spectator Learning Ctr":
            gap_tag = ('<span style="font-size:0.68rem;font-weight:700;color:#92400e;background:#fef3c7;'
                       'border-radius:4px;padding:2px 7px;margin-left:7px;">PARTIAL DATA</span>')
        elif BUILDINGS_STATUS.get(bld) == "open":
            gap_tag = ('<span style="font-size:0.68rem;font-weight:700;color:#991b1b;background:#fee2e2;'
                       'border-radius:4px;padding:2px 7px;margin-left:7px;">NO DATA</span>')

        rows_html += (
            '<div class="lb-row">'
            f'<div class="lb-rank {rank_cls}">{rd}</div>'
            '<div style="flex:1;min-width:0">'
            f'<div class="lb-name">{bld}{gap_tag}</div>'
            '<div class="lb-sub">'
            f'<span style="color:{pts_col};font-weight:700">{act_str}</span>'
            + (f' &nbsp;·&nbsp; {cost_str}' if cost_str else '') +
            f'<br><span style="color:#9ca3af;font-size:0.75rem">'
            f'prev {p_kwh:,} kWh → now {c_kwh:,} kWh</span>'
            '</div></div>'
            + streak_tag +
            f'<div style="text-align:right;min-width:88px">'
            f'<div class="lb-pct" style="color:{pts_col}">{pct_disp}</div>'
            f'<div class="lb-pct-lbl">% change</div>'
            f'</div></div>'
        )
    st.markdown(rows_html, unsafe_allow_html=True)

    st.markdown('<div class="sec-label">Highlights</div>', unsafe_allow_html=True)
    saved_df   = lb[lb["delta_pct"] > 0.5]
    wasted_df  = lb[lb["delta_pct"] < -0.5]
    streak_df  = lb[lb["streak"] > 0].sort_values("streak", ascending=False)

    hc1, hc2, hc3 = st.columns(3)

    # Best reducer
    if not saved_df.empty:
        t = saved_df.iloc[0]
        hc1.metric("🥇 Best Reduction", t["building"],
                   f"{float(t['delta_pct']):.1f}%  ·  {int(float(t['delta_kwh'])):,} kWh saved")
    else:
        hc1.metric("🥇 Best Reduction", "—", "No reductions this period")

    # Highest increase — always show someone; fall back to worst-performing if none increased >0.5%
    if not wasted_df.empty:
        w = wasted_df.iloc[-1]   # most negative delta_pct
        pct_v = float(w["delta_pct"])
        extra = abs(float(w["cost_saved"]))
        hc2.metric("⚠️ Highest Increase", w["building"],
                   f"{abs(pct_v):.1f}% more  ·  ${extra:,.0f} extra")
    elif not lb.empty:
        # All buildings reduced — show the one that saved least (closest to 0)
        w = lb.sort_values("delta_pct").iloc[0]  # smallest (least) reduction
        pct_v = float(w["delta_pct"])
        hc2.metric("✅ Closest to Breakeven", w["building"],
                   f"{abs(pct_v):.1f}% change — all buildings reduced 🎉")
    else:
        hc2.metric("⚠️ Highest Increase", "—", "No data to compare")

    # Longest streak
    if not streak_df.empty:
        s = streak_df.iloc[0]
        hc3.metric("🔥 Longest Streak", s["building"],
                   f"{int(s['streak'])} week{'s' if s['streak'] != 1 else ''} of reductions")
    else:
        hc3.metric("🔥 Longest Streak", "—", "Reduce 2+ weeks in a row to earn one")

    GOAL     = 5.0
    progress = min(max(-tot_pct / GOAL * 100, 0.0), 100.0)
    achieved = tot_pct <= -GOAL
    bar_col  = C_GREEN if achieved else C_AMBER
    txt_col  = "#166534" if achieved else "#92400e"
    if achieved:
        status = f"🎉 Goal achieved! Campus is {abs(tot_pct):.1f}% below prior period."
    elif tot_pct < 0:
        status = f"Reduced by {abs(tot_pct):.1f}% — need {GOAL - abs(tot_pct):.1f}% more to reach −{GOAL:.0f}%."
    else:
        status = f"Campus energy up {tot_pct:.1f}% — need to cut {GOAL + tot_pct:.1f}% to reach −{GOAL:.0f}%."

    st.markdown(f"""
<div class="goal-box">
  <div class="goal-lbl">Campus Weekly Reduction Target — {GOAL:.0f}%</div>
  <div class="goal-status" style="color:{txt_col}">{status}</div>
  <div class="prog-bg"><div class="prog-fill" style="width:{progress:.1f}%;background:{bar_col}"></div></div>
  <div style="display:flex;justify-content:space-between;font-size:0.83rem;color:{C_MUTED};margin-top:6px;font-weight:500;">
    <span>{progress:.0f}% of goal reached</span>
    <span>Campus change: {tot_pct:+.1f}% &nbsp;|&nbsp; Target: −{GOAL:.0f}%</span>
  </div>
</div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# DATA INTEGRITY TAB
# ══════════════════════════════════════════════════════════════════════════════
elif active_tab == "DataIntegrity":

    st.markdown('<div class="uni-label">SONOMA STATE UNIVERSITY</div>', unsafe_allow_html=True)
    st.title("🔍 Data Integrity Report")

    # Show current reporting period prominently
    _di_period = build_report_window(sorted_sel, period_label)
    st.markdown(
        f'<div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:10px;'
        f'padding:14px 20px;margin:10px 0 16px 0;display:flex;align-items:center;gap:12px;">'
        f'<span style="font-size:1.5rem;">📅</span>'
        f'<div><div style="font-size:0.75rem;font-weight:700;color:#0369a1;text-transform:uppercase;'
        f'letter-spacing:0.1em;">Reporting Period</div>'
        f'<div style="font-size:1.15rem;font-weight:700;color:#0c4a6e;">{_di_period}</div>'
        f'<div style="font-size:0.82rem;color:#0369a1;margin-top:2px;">'
        f'{len(selected_weeks)} period(s) selected · {time_filter} view</div></div>'
        f'</div>',
        unsafe_allow_html=True)

    st.markdown(
        '<p style="font-size:1.1rem;color:#6b7280;margin-top:4px;line-height:1.6;">'
        'Full sensor registry with building → meter → point ID linkage, verified daily readings '
        'from raw FTP files, gap analysis, unit conversion proof, and deployment notes.</p>',
        unsafe_allow_html=True)

    # ── Summary KPIs ──────────────────────────────────────────────────────────
    st.markdown('<div class="sec-label">Summary</div>', unsafe_allow_html=True)
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Total Sensors",    "37 mapped")
    s2.metric("Active (data)",    "8 sensors",  delta="reporting regularly")
    s3.metric("100% Data Gaps",   "17 sensors", delta="FTP column empty")
    s4.metric("Partial Gaps",     "1 sensor",   delta="Wine Spectator — 75% missing")

    # ── Data Quality Monitor (moved here from Overview) ──────────────────────
    st.markdown('<div class="sec-label" style="font-size:1rem;">📋 Data Quality Monitor</div>',
                unsafe_allow_html=True)
    _dqm_html  = ""
    _ok_blds   = [b for b, s in BUILDINGS_STATUS.items() if s == "ok"]
    _dqm_html += dqm_row(f"{n_open} buildings — no interval data from FTP", "Open", "dqm-open")
    _dqm_html += dqm_row("Wine Spectator Learning Ctr — 75% gaps (24/96 intervals/day)", "Review", "dqm-review")
    for _b in _ok_blds:
        _dqm_html += dqm_row(_b, "OK", "dqm-ok")
    st.markdown(
        f'<div class="card"><div class="card-title" style="font-size:1.25rem;">Data Quality Monitor</div>'
        f'<div class="card-sub" style="font-size:1rem;">Sensor status as of {_di_period}</div>'
        f'{_dqm_html}</div>', unsafe_allow_html=True)

    # ── Building → Meter → Point ID table ─────────────────────────────────────
    st.markdown('<div class="sec-label">Building → Meter → Point ID Registry (all 37 sensors)</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:0.82rem;color:#6b7280;margin-bottom:10px;">'
        'Every meter point ID proven from named column headers in 2024 FTP interval files. '
        'Unit corrections applied: Art Building HHW &amp; Salazar HHW → BTU. '
        'Water meter captured as gallon. '
        'POINT_ID_MAP is the single source of truth in the pipeline.</div>',
        unsafe_allow_html=True)

    tbl = ('<table class="di-table"><thead><tr>'
           '<th>Building</th><th>Point ID</th><th>Meter description (from FTP named CSVs)</th>'
           '<th>DB table</th><th>Unit</th><th>Status</th><th>Notes</th>'
           '</tr></thead><tbody>')
    for bld, sid, util, unit, status, notes in SENSOR_REGISTRY:
        db_table = ("water_usage" if unit == "gallon"
                    else "gas_usage" if unit == "therm"
                    else "energy_usage" if unit not in ("—",) else "—")
        tbl += (f'<tr><td><b>{bld}</b></td>'
                f'<td><code style="background:#f1f5f9;padding:2px 6px;border-radius:4px;font-size:0.78rem">{sid}</code></td>'
                f'<td>{util}</td>'
                f'<td><code style="font-size:0.78rem">{db_table}</code></td>'
                f'<td>{unit}</td>'
                f'<td>{badge_html(status)}</td>'
                f'<td style="color:#6b7280;font-size:0.82rem">{notes}</td></tr>')
    tbl += '</tbody></table>'
    st.markdown(f'<div class="card" style="overflow-x:auto">{tbl}</div>', unsafe_allow_html=True)

    # ── Unit conversion proof ──────────────────────────────────────────────────
    st.markdown('<div class="sec-label">Unit Conversion Proof</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.markdown(
        '<div class="card"><div class="card-title">Conversions applied in pipeline</div>'
        '<div style="font-size:0.97rem;color:#374151;line-height:2;margin-top:8px;">'
        '<code>BTU × 0.000293071 = kWh</code><br>'
        '<code>MBTU × 293.071 = kWh</code><br>'
        '<code>therm × 29.3071 = kWh</code><br>'
        '<code>tonref × 3.51685 = kWh</code><br>'
        '<code>gallon → stored raw (no conversion)</code><br>'
        '<code>therm → stored raw in gas_usage</code>'
        '</div></div>',
        unsafe_allow_html=True)
    c2.markdown(
        '<div class="card"><div class="card-title">Routing to DB tables</div>'
        '<div style="font-size:0.97rem;color:#374151;line-height:2;margin-top:8px;">'
        '<code>Unit = kWh, BTU, MBTU, tonref → energy_usage</code><br>'
        '<code>Unit = therm → gas_usage</code><br>'
        '<code>Unit = gallon → water_usage</code><br><br>'
        '<b>weekly_energy.csv columns:</b><br>'
        '<code>week, building, kWh, gas_therm, water_gallon, heating_dd, normalized_kWh</code>'
        '</div></div>',
        unsafe_allow_html=True)

    # ── Daily readings from daily_energy.csv ────────────────────────────────
    st.markdown('<div class="sec-label">Daily Readings — From Pipeline (daily_energy.csv)</div>',
                unsafe_allow_html=True)
    if df_daily.empty:
        st.info("No daily data yet. Run the pipeline with interval CSV files to populate daily_energy.csv.")
    else:
        rows_v = []
        for _, _dr in df_daily.sort_values(["week","building"]).iterrows():
            rows_v.append({
                "Date":      _dr["week"],
                "Building":  _dr["building"],
                "kWh":       f"{_dr['kWh']:,.1f}",
                "MWh":       f"{_dr['kWh']/1000:.3f}",
                "Est. Cost": f"${_dr['kWh'] * ENERGY_RATE:,.0f}",
            })
        vdf  = pd.DataFrame(rows_v)
        tbl2 = '<table class="di-table"><thead><tr>'
        for col in vdf.columns:
            tbl2 += f'<th>{col}</th>'
        tbl2 += '</tr></thead><tbody>'
        for _, r in vdf.iterrows():
            tbl2 += '<tr>' + ''.join(f'<td>{v}</td>' for v in r.values) + '</tr>'
        tbl2 += '</tbody></table>'
        st.markdown(f'<div class="card">{tbl2}</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div style="font-size:0.9rem;color:#9ca3af;margin-top:8px;line-height:1.6;">'
            f'* {len(all_days)} date(s) in daily_energy.csv — sourced directly from the pipeline DB. '
            'Only dates with actual processed raw CSV files appear here. '
            'Green Music Center kWh includes electric + CHW BTU (÷3,412) + HW kBTU (×0.293071). '
            'Wine Spectator understated ~4× due to 75% sensor gaps.</div>',
            unsafe_allow_html=True)

    # ── Gas & Water status ─────────────────────────────────────────────────────
    st.markdown('<div class="sec-label">Gas & Water — Current Status</div>', unsafe_allow_html=True)
    col_g, col_w = st.columns(2)
    col_g.markdown(
        '<div class="card"><div class="card-title">⛽ Gas Meters (therm)</div>'
        '<div style="font-size:0.97rem;color:#374151;line-height:1.9;margin-top:8px;">'
        '<b>3 gas meters registered in POINT_ID_MAP:</b><br>'
        '&nbsp;&nbsp;• Boiler Plant (234a6e2b) — <span style="color:#dc2626;font-weight:600">100% missing</span><br>'
        '&nbsp;&nbsp;• Green Music Center (234aab84) — <span style="color:#dc2626;font-weight:600">100% missing</span><br>'
        '&nbsp;&nbsp;• Schulz Info Center (206e94b8) — <span style="color:#dc2626;font-weight:600">100% missing</span><br>'
        '<br><b>Pipeline status:</b> Routes correctly to <code>gas_usage</code> table.<br>'
        '<b>Weekly CSV:</b> <code>gas_therm</code> column present, all 0.0 until BMS reports.<br>'
        '<b>App:</b> ⛽ Gas tab shows info message until data arrives.'
        '</div></div>',
        unsafe_allow_html=True)
    col_w.markdown(
        '<div class="card"><div class="card-title">💧 Water Meter</div>'
        '<div style="font-size:0.97rem;color:#374151;line-height:1.9;margin-top:8px;">'
        '<b>1 water meter registered:</b><br>'
        '&nbsp;&nbsp;• Green Music Center Total Water Meter Usage (C)<br>'
        '&nbsp;&nbsp;• Point ID: <code>234aa782-f7b1eef2</code><br>'
        '&nbsp;&nbsp;• Status: <span style="color:#dc2626;font-weight:600">100% NaN in all provided files</span><br>'
        '<br><b>Pipeline status:</b> Routes correctly to <code>water_usage</code> table (gallon).<br>'
        '<b>Weekly CSV:</b> <code>water_gallon</code> column present, all 0.0 until BMS reports.<br>'
        '<b>App:</b> 💧 Water tab shows info message until data arrives.'
        '</div></div>',
        unsafe_allow_html=True)

    # ── Wine Spectator gap detail ──────────────────────────────────────────────
    st.markdown('<div class="sec-label">Wine Spectator Learning Ctr — Gap Detail</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="card">'
        '<div style="font-size:0.86rem;color:#374151;line-height:1.9;">'
        '<b>Why it says "Partial":</b> Each day should have 96 data points (one every 15 minutes). '
        'Wine Spectator only sends <b>24 of 96</b> each day — 72 intervals are missing (75% gap rate).<br>'
        '<b>Verified from raw FTP interval files (Feb 11–14 2026):</b><br>'
        '&nbsp;&nbsp;• Feb 11: <b>3,308 kWh</b> reported (24/96 intervals) → est. actual: ~<b>13,200 kWh</b><br>'
        '&nbsp;&nbsp;• Feb 12: <b>3,189 kWh</b> reported (24/96 intervals) → est. actual: ~<b>12,800 kWh</b><br>'
        '&nbsp;&nbsp;• Feb 13: <b>3,037 kWh</b> reported (24/96 intervals) → est. actual: ~<b>12,100 kWh</b><br>'
        '&nbsp;&nbsp;• Feb 14: <b>1,793 kWh</b> reported (24/96 intervals) → est. actual: ~<b>7,200 kWh</b><br>'
        '<b>Recommendation:</b> Investigate BMS polling configuration for this building.'
        '</div></div>',
        unsafe_allow_html=True)

    # ── Deployment & cron ─────────────────────────────────────────────────────
    st.markdown('<div class="sec-label">Deployment & Daily Updates</div>', unsafe_allow_html=True)
    d1, d2 = st.columns(2)
    d1.markdown(
        '<div class="card"><div class="card-title">🚀 Deployment Options</div>'
        '<div style="font-size:0.97rem;color:#374151;line-height:1.9;margin-top:8px;">'
        '<b>Streamlit Community Cloud (free)</b><br>'
        '&nbsp;&nbsp;1. Push code to GitHub<br>'
        '&nbsp;&nbsp;2. share.streamlit.io → connect repo → deploy<br>'
        '&nbsp;&nbsp;→ Gets a public https:// URL<br><br>'
        '<b>Server (Hostinger / DigitalOcean)</b><br>'
        '&nbsp;&nbsp;1. Create Ubuntu server<br>'
        '&nbsp;&nbsp;2. <code>pip install streamlit plotly pandas</code><br>'
        '&nbsp;&nbsp;3. Run behind nginx reverse proxy<br>'
        '&nbsp;&nbsp;→ Full control, custom domain, cron-compatible'
        '</div></div>',
        unsafe_allow_html=True)
    d2.markdown(
        '<div class="card"><div class="card-title">🔄 Daily Pipeline via Cron</div>'
        '<div style="font-size:0.97rem;color:#374151;line-height:1.9;margin-top:8px;">'
        '<b>Cron entry (daily at 06:00):</b><br>'
        '<code style="background:#f1f5f9;padding:4px 8px;border-radius:4px;display:block;margin:6px 0;">'
        '0 6 * * * /usr/bin/python3 /var/www/html/Energy/master_pipeline_final.py >> /var/www/html/Energy/logs/cron.log 2>&amp;1'
        '</code>'
        'Pipeline pulls new FTP files → normalises → inserts into DB (energy_usage, gas_usage, water_usage) '
        '→ regenerates weekly_energy.csv → app auto-refreshes (TTL=5 min).<br><br>'
        '<b>Add to crontab:</b> <code>crontab -e</code><br>'
        '<b>Test run:</b> <code>python3 master_pipeline_final.py</code>'
        '</div></div>',
        unsafe_allow_html=True)
