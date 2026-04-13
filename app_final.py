"""
SSU Campus Energy Dashboard — app_final.py
Clean, accurate, simple. Data verified against weekly_energy.csv (pipeline output).
Week: Feb 2–8, 2026 | 8 buildings | Campus total: 203,758 kWh
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import streamlit.components.v1 as components

st.set_page_config(
    page_title="SSU Campus Energy Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── JS: replace sidebar toggle ligature text with clean arrow symbols ─────────
components.html("""
<script>
(function() {
    function fixArrows() {
        var doc;
        try { doc = window.parent.document; } catch(e) { return; }
        if (!doc) return;

        // ◀  collapse button (sidebar open)
        doc.querySelectorAll(
            'button[data-testid="baseButton-headerNoPadding"]'
        ).forEach(function(btn) {
            if (btn.getAttribute('data-arrow-fixed')) return;
            var icon = btn.querySelector('[data-testid="stIconMaterial"]');
            if (icon && icon.textContent.indexOf('keyboard') !== -1) {
                icon.textContent = '◀';
                icon.style.fontFamily = 'Arial,Helvetica,sans-serif';
                icon.style.fontSize   = '1.15rem';
                icon.style.color      = '#c8d9ea';
                btn.setAttribute('data-arrow-fixed', '1');
            }
        });

        // ▶  expand button (sidebar collapsed)
        var ctrl = doc.querySelector('[data-testid="collapsedControl"]');
        if (ctrl) {
            var btn = ctrl.querySelector('button');
            if (btn && !btn.getAttribute('data-arrow-fixed')) {
                var icon = btn.querySelector('[data-testid="stIconMaterial"]');
                if (icon && icon.textContent.indexOf('keyboard') !== -1) {
                    icon.textContent = '▶';
                    icon.style.fontFamily = 'Arial,Helvetica,sans-serif';
                    icon.style.fontSize   = '1.15rem';
                    icon.style.color      = '#c8d9ea';
                    btn.setAttribute('data-arrow-fixed', '1');
                }
            }
        }
    }

    fixArrows();
    // Re-run on every DOM mutation (Streamlit rerenders reset the DOM)
    var observer = new MutationObserver(fixArrows);
    observer.observe(
        window.parent.document.documentElement,
        {childList: true, subtree: true}
    );
})();
</script>
""", height=0, scrolling=False)

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

/* ── Sidebar toggle ── */
[data-testid="collapsedControl"] { background-color: #1b3a5c !important; border-right: 2px solid #2a5180 !important; }
/* Hide ligature text but keep element dimensions (visibility:hidden not font-size:0) */
button[data-testid="baseButton-headerNoPadding"] [data-testid="stIconMaterial"],
[data-testid="collapsedControl"] button [data-testid="stIconMaterial"] {
    visibility: hidden !important;
}
/* Arrow pseudo-elements: MUST be position:absolute centered — display:block gets clipped */
button[data-testid="baseButton-headerNoPadding"] {
    position: relative !important;
    overflow: visible !important;
}
button[data-testid="baseButton-headerNoPadding"]::after {
    content: "◀" !important;
    position: absolute !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;
    font-size: 1.1rem !important;
    font-family: Arial, Helvetica, sans-serif !important;
    color: #c8d9ea !important;
    line-height: 1 !important;
    pointer-events: none !important;
}
[data-testid="collapsedControl"] button {
    position: relative !important;
    overflow: visible !important;
}
[data-testid="collapsedControl"] button::after {
    content: "▶" !important;
    position: absolute !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;
    font-size: 1.1rem !important;
    font-family: Arial, Helvetica, sans-serif !important;
    color: #c8d9ea !important;
    line-height: 1 !important;
    pointer-events: none !important;
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
    ("Green Music Center",          "234ab131-e413ba29", "Electric", "kWh",   "OK",     "Active — primary electric meter, ~85 kWh per reading"),
    ("Green Music Center",          "1f98265e-39835c84", "Thermal",  "BTU",   "OK",     "Active — chilled water cooling loop"),
    ("Green Music Center",          "234aa956-82d369b2", "Thermal",  "kBTU",  "OK",     "Active — heating hot water loop"),
    ("Green Music Center",          "234aab84-c656a0e0", "Gas",      "therm", "Missing","No data received"),
    ("Green Music Center",          "234aa782-f7b1eef2", "Water",    "gallon","Missing","No data received"),
    ("Nichols Hall",                "234e3ee2-f6fcea18", "Thermal",  "BTU",   "OK",     "Active — heating hot water loop, ~20,000 kWh/day"),
    ("Nichols Hall",                "234e3ee2-b06b6c8c", "Thermal",  "BTU",   "OK",     "Active — chilled water cooling loop, reporting zero"),
    ("Nichols Hall",                "234e40da-635bc7c1", "Electric", "kWh",   "OK",     "Active — reporting zero, meter may be offline"),
    ("Physical Education",          "206db469-c986212b", "Electric", "kWh",   "OK",     "Active — consistent readings, ~11 kWh per reading"),
    ("Rachel Carson Hall",          "1f98265e-cbf77175", "Electric", "kWh",   "Missing","No data received"),
    ("Rachel Carson Hall",          "234aa121-a983880d", "Thermal",  "BTU",   "OK",     "Active — chilled water cooling loop, minor daily gaps"),
    ("Rachel Carson Hall",          "234aa43b-a73abf5e", "Thermal",  "BTU",   "OK",     "Active — heating hot water loop, reporting zero"),
    ("Ives Hall",                   "234e3195-7d72fbdc", "Thermal",  "BTU",   "OK",     "Active — heating hot water loop, 950–1,243 kWh/day"),
    ("Ives Hall",                   "234e3195-c20a1a8e", "Thermal",  "BTU",   "OK",     "Active — chilled water cooling loop, reporting zero"),
    ("Ives Hall",                   "206d9425-f3361ab6", "Electric", "kWh",   "OK",     "Active — reporting zero, meter may be offline"),
    ("Student Center",              "234e5dff-8d8eb031", "Thermal",  "BTU",   "OK",     "Active — heating hot water loop, variable output"),
    ("Student Center",              "234e5dff-6fe20abd", "Thermal",  "BTU",   "OK",     "Active — chilled water cooling loop"),
    ("Student Center",              "20c9aa07-acd1558a", "Electric", "kWh",   "OK",     "Active — reporting zero, meter may be offline"),
    ("Wine Spectator Learning Ctr", "250ea73e-3b55a6cf", "Electric", "kWh",   "Review", "Only 25% of expected readings received — kWh understated ~4×"),
    ("Art Building",                "1f97c82e-36e60525", "Thermal",  "BTU",   "Missing","No data received"),
    ("Art Building",                "1f97c82e-d1a92673", "Thermal",  "BTU",   "Missing","No data received"),
    ("Boiler Plant",                "234a6e2b-318cf13d", "Gas",      "therm", "Missing","No data received"),
    ("Darwin Hall",                 "267e6fd0-93d67a62", "Electric", "kWh",   "Missing","No data received"),
    ("ETC",                         "1f97c82e-dd011464", "Electric", "kWh",   "Missing","No data received"),
    ("Salazar Hall",                "20c9b2e1-d7263cf1", "Electric", "kWh",   "Missing","No data received"),
    ("Salazar Hall",                "234e4c64-930d1fd6", "Electric", "kWh",   "Missing","No data received"),
    ("Salazar Hall",                "20c9b4d5-5ea6aa0b", "Thermal",  "BTU",   "Missing","No data received"),
    ("Schulz Info Center",          "1f97c82e-c34c4f2e", "Electric", "kWh",   "Missing","No data received"),
    ("Schulz Info Center",          "1f97c82e-525ca261", "Thermal",  "BTU",   "Missing","No data received"),
    ("Schulz Info Center",          "206e94b8-3b05cb50", "Gas",      "therm", "Missing","No data received"),
    ("Stevenson Hall",              "251810ce-f429b841", "Electric", "kWh",   "Missing","No data received"),
    ("Stevenson Hall",              "267fcb62-ed42e3b3", "Thermal",  "BTU",   "Missing","No data received"),
    ("Student Health Center",       "234e61c5-021da430", "Thermal",  "BTU",   "OK",     "Active — chilled water cooling loop, reporting zero"),
    ("Student Health Center",       "234e61c5-83f6cf71", "Thermal",  "BTU",   "OK",     "Active — chilled water cooling loop, reporting zero"),
    ("Campus Misc",                 "214981c7-dd0b1593", "Electric", "kWh",   "PGE",    "PG&E utility account meter"),
    ("Campus Misc",                 "214981c7-5530731e", "Electric", "kWh",   "PGE",    "PG&E utility account meter"),
    ("Campus Misc",                 "214981c7-63077e46", "Electric", "kWh",   "PGE",    "PG&E utility account meter"),
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
        '<div style="margin:0 auto 10px;">'
        '<img src="data:image/png;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/4gHYSUNDX1BST0ZJTEUAAQEAAAHIAAAAAAQwAABtbnRyUkdCIFhZWiAH4AABAAEAAAAAAABhY3NwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAA9tYAAQAAAADTLQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAlkZXNjAAAA8AAAACRyWFlaAAABFAAAABRnWFlaAAABKAAAABRiWFlaAAABPAAAABR3dHB0AAABUAAAABRyVFJDAAABZAAAAChnVFJDAAABZAAAAChiVFJDAAABZAAAAChjcHJ0AAABjAAAADxtbHVjAAAAAAAAAAEAAAAMZW5VUwAAAAgAAAAcAHMAUgBHAEJYWVogAAAAAAAAb6IAADj1AAADkFhZWiAAAAAAAABimQAAt4UAABjaWFlaIAAAAAAAACSgAAAPhAAAts9YWVogAAAAAAAA9tYAAQAAAADTLXBhcmEAAAAAAAQAAAACZmYAAPKnAAANWQAAE9AAAApbAAAAAAAAAABtbHVjAAAAAAAAAAEAAAAMZW5VUwAAACAAAAAcAEcAbwBvAGcAbABlACAASQBuAGMALgAgADIAMAAxADb/2wBDAAUDBAQEAwUEBAQFBQUGBwwIBwcHBw8LCwkMEQ8SEhEPERETFhwXExQaFRERGCEYGh0dHx8fExciJCIeJBweHx7/2wBDAQUFBQcGBw4ICA4eFBEUHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh7/wAARCAJYAlgDASIAAhEBAxEB/8QAHQABAAMBAAMBAQAAAAAAAAAAAAYHCAkDBAUBAv/EAFkQAAECBAIECQcHBwkGBQQDAAABAgMEBQYHEQgSIdIXGDFBUVZxlJUTIjdSVGGBFDKEkaGxtBUWI0J1gpIzOGJydLKzwdFDU3Oio8IkNDVj8CU2V5ODw+H/xAAbAQEAAgMBAQAAAAAAAAAAAAAABAUBAgMGB//EAEERAAIBAgEHCAkEAQMDBQAAAAABAgMEEQUSEyExUnEVMjNBUZGxwQYUFjRCYXKB0SJTofDhI0PxJILCREVikrL/2gAMAwEAAhEDEQA/ANlgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA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AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD/9k=" '
        'style="height:84px;width:auto;object-fit:contain;" '
        'alt="Sonoma State University"/></div>'
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
            default=[],
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
            default=[],
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
            default=[],
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
# SELECTION-DEPENDENT VARIABLES  (only computed when a period is chosen)
# ══════════════════════════════════════════════════════════════════════════════
if selected_weeks:
    if len(selected_weeks) > 4:
        st.warning("Maximum 4 periods can be selected at once. Showing the most recent 4.")
        selected_weeks = sorted(selected_weeks)[-4:]

    sorted_sel        = sorted(selected_weeks)
    latest_week       = sorted_sel[-1]
    df_sel            = df_view[df_view["week"].isin(sorted_sel)]
    by_bld            = df_view.groupby(["week","building"])["kWh"].sum().reset_index()
    campus_cur        = by_bld[by_bld["week"] == latest_week]["kWh"].sum()
    campus_cost       = campus_cur * ENERGY_RATE
    scale             = "MWh" if campus_cur >= 1_000 else "kWh"
    campus_total_sel  = by_bld[by_bld["week"].isin(sorted_sel)]["kWh"].sum()
    campus_total_cost = campus_total_sel * ENERGY_RATE
    prev_week         = sorted_sel[-2] if len(sorted_sel) >= 2 else None
    campus_prev       = by_bld[by_bld["week"] == prev_week]["kWh"].sum() if prev_week else None
    pct_change        = ((campus_cur - campus_prev) / campus_prev * 100) if campus_prev else None
    n_missing         = sum(1 for s in BUILDINGS_STATUS.values() if s == "open")
else:
    sorted_sel        = []
    latest_week       = None
    by_bld            = pd.DataFrame(columns=["week", "building", "kWh"])
    campus_total_sel  = 0.0
    campus_total_cost = 0.0
    prev_week         = None
    campus_prev       = None
    pct_change        = None
    n_missing         = 0




# ══════════════════════════════════════════════════════════════════════════════
# OVERVIEW TAB
# ══════════════════════════════════════════════════════════════════════════════
if active_tab == "Overview":

    # ── Header (always visible) ──────────────────────────────────────────────
    st.markdown('<div style="margin-bottom:12px;"><img src="data:image/png;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/4gHYSUNDX1BST0ZJTEUAAQEAAAHIAAAAAAQwAABtbnRyUkdCIFhZWiAH4AABAAEAAAAAAABhY3NwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAA9tYAAQAAAADTLQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAlkZXNjAAAA8AAAACRyWFlaAAABFAAAABRnWFlaAAABKAAAABRiWFlaAAABPAAAABR3dHB0AAABUAAAABRyVFJDAAABZAAAAChnVFJDAAABZAAAAChiVFJDAAABZAAAAChjcHJ0AAABjAAAADxtbHVjAAAAAAAAAAEAAAAMZW5VUwAAAAgAAAAcAHMAUgBHAEJYWVogAAAAAAAAb6IAADj1AAADkFhZWiAAAAAAAABimQAAt4UAABjaWFlaIAAAAAAAACSgAAAPhAAAts9YWVogAAAAAAAA9tYAAQAAAADTLXBhcmEAAAAAAAQAAAACZmYAAPKnAAANWQAAE9AAAApbAAAAAAAAAABtbHVjAAAAAAAAAAEAAAAMZW5VUwAAACAAAAAcAEcAbwBvAGcAbABlACAASQBuAGMALgAgADIAMAAxADb/2wBDAAUDBAQEAwUEBAQFBQUGBwwIBwcHBw8LCwkMEQ8SEhEPERETFhwXExQaFRERGCEYGh0dHx8fExciJCIeJBweHx7/2wBDAQUFBQcGBw4ICA4eFBEUHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh7/wAARCAJYAlgDASIAAhEBAxEB/8QAHQABAAMBAAMBAQAAAAAAAAAAAAYHCAkDBAUBAv/EAFkQAAECBAIECQcHBwkGBQQDAAABAgMEBQYHEQgSIdIXGDFBUVZxlJUTIjdSVGGBFDKEkaGxtBUWI0J1gpIzOGJydLKzwdFDU3Oio8IkNDVj8CU2V5ODw+H/xAAbAQEAAgMBAQAAAAAAAAAAAAAABAUBAgMGB//EAEERAAIBAgEHCAkEAQMDBQAAAAABAgMEEQUSEyExUnEVMjNBUZGxwQYUFjRCYXKB0SJTofDhI0PxJILCREVikrL/2gAMAwEAAhEDEQA/ANlgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA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AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD/9k=" style="height:110px;width:auto;object-fit:contain;mix-blend-mode:multiply;" alt="Sonoma State University"/></div>', unsafe_allow_html=True)
    st.title("Campus Energy Dashboard")
    st.markdown(
        '<p style="font-size:1.05rem;color:#6b7280;margin-top:2px;line-height:1.5;">'
        'Daily energy use (electricity + thermal) across campus buildings — sourced from FTP interval meters.</p>',
        unsafe_allow_html=True)

    # ── All-Time Energy Consumption (always visible) ─────────────────────────
    st.markdown('<div class="sec-label">Campus Energy — All Time</div>', unsafe_allow_html=True)

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

    at1, at2, _at_spacer = st.columns(3)
    at1.metric("Total Energy Consumed — All Time", fmt_kwh(_at_total_kwh))
    at2.metric(f"Total Energy Cost — All Time (@ ${ENERGY_RATE}/kWh)", fmt_cost(_at_total_cost))

    y_at_max = _at_monthly["_mwh"].max() * 1.4 if not _at_monthly.empty else 1
    fig_at = go.Figure(go.Bar(
        x=_at_monthly["_label"],
        y=_at_monthly["_mwh"],
        marker_color=C_NAVY,
        text=[f"{v:.1f}" for v in _at_monthly["_mwh"]],
        textposition="outside",
        textfont=dict(size=11, color="#374151", family="Inter"),
        hovertemplate="<b>%{x}</b><br>%{y:.1f} MWh  ·  $%{customdata:,.0f}<extra></extra>",
        customdata=_at_monthly["kWh"] * ENERGY_RATE,
    ))
    fig_at.update_layout(
        **plot_base(height=360),
        bargap=0.35,
        yaxis_title="MWh",
    )
    fig_at.update_xaxes(tickangle=-45, tickfont=dict(size=11, family="Inter", color=PLOT_TEXT))
    fig_at.update_yaxes(range=[0, y_at_max])
    st.plotly_chart(fig_at, use_container_width=True)

    # ── Nothing selected — show prompt and stop ──────────────────────────────
    if not selected_weeks:
        st.markdown(
            '<div class="alert-blue" style="margin-top:4px;">'
            '👈  Select a time period from the sidebar to see detailed building breakdowns.</div>',
            unsafe_allow_html=True)

    else:
        # ── Report window banner ─────────────────────────────────────────────
        _rw_rows = "".join(
            f'<div style="display:flex;justify-content:space-between;align-items:baseline;'
            f'border-bottom:1px solid #f1f5f9;padding:5px 0;last-child:border:none;">'
            f'<span style="font-size:0.72rem;font-weight:700;color:#9ca3af;text-transform:uppercase;'
            f'letter-spacing:0.08em;margin-right:16px;">Period {i+1}</span>'
            f'<span style="font-size:0.95rem;font-weight:700;color:#111827;">'
            f'{period_label(w)}</span></div>'
            for i, w in enumerate(sorted_sel)
        )
        st.markdown(
            f'<div style="display:flex;justify-content:flex-end;margin-bottom:12px;">'
            f'<div class="rw-box" style="text-align:left;min-width:280px;">'
            f'<span class="rw-label" style="display:block;margin-bottom:8px;">Report Window</span>'
            f'{_rw_rows}</div></div>',
            unsafe_allow_html=True)

        # ── Missing data notice ──────────────────────────────────────────────
        missing_blds = [b for b, s in BUILDINGS_STATUS.items() if s not in ("ok", "review")]
        if missing_blds:
            st.markdown(
                f'<div class="alert-amber">⚠️ <b>Missing Data:</b> '
                f'{", ".join(sorted(missing_blds))} have no FTP sensor data. '
                f'See the Data Integrity tab for details.</div>',
                unsafe_allow_html=True)

        # ── Campus KPIs ──────────────────────────────────────────────────────
        st.markdown('<div class="sec-label">Campus Overview</div>', unsafe_allow_html=True)
        k1, k2, k3 = st.columns(3)
        k1_label = (f"Total Campus Energy — {period_label(sorted_sel[0])}"
                    if len(sorted_sel) == 1
                    else f"Total Campus Energy — {len(sorted_sel)} periods combined")
        k1.metric(k1_label, fmt_kwh(campus_total_sel))
        k2.metric(f"Estimated Energy Cost  (@ ${ENERGY_RATE}/kWh equiv)",
                  fmt_cost(campus_total_cost))
        k3.metric("Periods Selected", f"{len(sorted_sel)} selected")
        k3.markdown(
            '<div style="font-family:Inter,sans-serif;font-size:0.82rem;font-weight:600;'
            'color:#9ca3af;margin-top:2px;">(maximum 4 to select)</div>',
            unsafe_allow_html=True)

        # ════════════════════════════════════════════════════════════════════
        # SECTION 1 — All Buildings (selected timeframe)
        # ════════════════════════════════════════════════════════════════════
        max_periods = 4
        chart_weeks = sorted_sel[-max_periods:]
        n_periods   = len(chart_weeks)
        chart_title = (f"All Buildings — {period_label(chart_weeks[0])}"
                       if n_periods == 1
                       else f"All Buildings — {period_label(chart_weeks[0])} to {period_label(chart_weeks[-1])}")
        if n_periods == max_periods:
            chart_title += f" (max {max_periods} shown)"
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
                textfont=dict(size=11, color="#374151", family="Inter"),
                hovertemplate="<b>%{y}</b><br>%{x:.1f} MWh<extra></extra>",
            ))
            fig_all.update_layout(
                **plot_base(height=max(300, len(ldf) * 56)),
                xaxis_title="MWh", yaxis_title="", showlegend=False)
            fig_all.update_yaxes(tickfont=dict(size=12, color="#111827", family="Inter"))
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
                    textfont=dict(size=10, color="#374151", family="Inter"),
                    hovertemplate=f"<b>%{{y}}</b><br>{period_label(wk)}: %{{x:.1f}} MWh<extra></extra>",
                ))
            fig_all.update_layout(
                **plot_base(height=max(340, len(all_blds_sorted) * 70)),
                barmode="group", bargap=0.15, bargroupgap=0.05,
                xaxis_title="MWh", yaxis_title="", showlegend=True,
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1,
                    font=dict(size=12, family="Inter", color=PLOT_TEXT),
                    bgcolor="#ffffff", bordercolor="#e2e8f0", borderwidth=1),
            )
            fig_all.update_yaxes(tickfont=dict(size=12, color="#111827", family="Inter"))
            st.plotly_chart(fig_all, use_container_width=True)

        # ════════════════════════════════════════════════════════════════════
        # SECTION 2 — Building Detail + Trend
        # ════════════════════════════════════════════════════════════════════
        st.markdown('<div class="sec-label">Building Detail</div>', unsafe_allow_html=True)

        bld_kwh_latest = (by_bld[by_bld["week"] == latest_week]
                          .sort_values("kWh", ascending=False)[["building", "kWh"]])
        bld_order   = bld_kwh_latest["building"].tolist()
        bld_kwh_lkp = bld_kwh_latest.set_index("building")["kWh"].to_dict()

        sel_bld = st.selectbox(
            "Select a building (sorted highest to lowest kWh)",
            bld_order, index=0,
            format_func=lambda b: f"{b}  —  {fmt_kwh(bld_kwh_lkp.get(b, 0))}",
            label_visibility="visible")

        if BUILDINGS_STATUS.get(sel_bld, "ok") == "review":
            st.markdown(
                f'<div class="alert-amber">⚠️ <b>{sel_bld}</b> — '
                f'Only 24 of 96 daily 15-minute intervals received (75% missing). '
                f'The kWh shown is understated by approximately 4×.</div>',
                unsafe_allow_html=True)

        b_cur  = bld_kwh_lkp.get(sel_bld, 0.0)
        b_cost = b_cur * ENERGY_RATE
        bm1, bm2 = st.columns(2)
        bm1.metric(f"Energy — {period_label(latest_week)}", fmt_kwh(b_cur))
        bm2.metric(f"Estimated Cost  (@ ${ENERGY_RATE}/kWh)", fmt_cost(b_cost))

        bld_trend = (by_bld[
            (by_bld["building"] == sel_bld) &
            (by_bld["week"].isin(sorted_sel))
        ].sort_values("week").copy())
        if len(bld_trend) >= 1:
            bld_trend["label"] = bld_trend["week"].apply(period_label)
            bld_trend["disp"]  = bld_trend["kWh"] / 1000
            st.markdown(
                f'<div class="sec-label">{sel_bld} — Trend ({time_filter})</div>',
                unsafe_allow_html=True)
            vals_t   = bld_trend["kWh"].values
            colors_t = [C_NAVY] + [
                C_GREEN if vals_t[i] < vals_t[i - 1] else C_RED
                for i in range(1, len(vals_t))
            ]
            fig_trend = go.Figure(go.Bar(
                x=bld_trend["label"], y=bld_trend["disp"],
                marker_color=colors_t,
                text=[f"{v:.1f} MWh" for v in bld_trend["disp"]],
                textposition="outside",
                textfont=dict(size=12, color=PLOT_TEXT, family="Inter"),
                hovertemplate="<b>%{x}</b><br>%{y:.1f} MWh<extra></extra>",
                showlegend=False,
            ))
            yt = bld_trend["disp"].max() * 1.3 if not bld_trend.empty else 1
            fig_trend.update_layout(**plot_base(height=260), bargap=0.45, yaxis_title="MWh")
            fig_trend.update_yaxes(range=[0, yt])
            st.plotly_chart(fig_trend, use_container_width=True)

        # ════════════════════════════════════════════════════════════════════
        # SECTION 3 — Total Campus Energy — All Selected Periods
        # ════════════════════════════════════════════════════════════════════
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
            textfont=dict(size=13, color=PLOT_TEXT, family="Inter"),
            hovertemplate="<b>%{x}</b><br>%{y:.1f} MWh<br>$%{customdata:,.0f}<extra></extra>",
            customdata=campus_by_week["kWh"] * ENERGY_RATE,
        ))
        y_max = campus_by_week["disp"].max() * 1.3 if not campus_by_week.empty else 1
        fig_campus.update_layout(**plot_base(height=280), bargap=0.45, yaxis_title="MWh")
        fig_campus.update_yaxes(range=[0, y_max])
        st.plotly_chart(fig_campus, use_container_width=True)






# ══════════════════════════════════════════════════════════════════════════════
# LEADERBOARD TAB
# ══════════════════════════════════════════════════════════════════════════════
elif active_tab == "Leaderboard":

    if not selected_weeks:
        st.markdown('<div style="margin-bottom:12px;"><img src="data:image/png;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/4gHYSUNDX1BST0ZJTEUAAQEAAAHIAAAAAAQwAABtbnRyUkdCIFhZWiAH4AABAAEAAAAAAABhY3NwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAA9tYAAQAAAADTLQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAlkZXNjAAAA8AAAACRyWFlaAAABFAAAABRnWFlaAAABKAAAABRiWFlaAAABPAAAABR3dHB0AAABUAAAABRyVFJDAAABZAAAAChnVFJDAAABZAAAAChiVFJDAAABZAAAAChjcHJ0AAABjAAAADxtbHVjAAAAAAAAAAEAAAAMZW5VUwAAAAgAAAAcAHMAUgBHAEJYWVogAAAAAAAAb6IAADj1AAADkFhZWiAAAAAAAABimQAAt4UAABjaWFlaIAAAAAAAACSgAAAPhAAAts9YWVogAAAAAAAA9tYAAQAAAADTLXBhcmEAAAAAAAQAAAACZmYAAPKnAAANWQAAE9AAAApbAAAAAAAAAABtbHVjAAAAAAAAAAEAAAAMZW5VUwAAACAAAAAcAEcAbwBvAGcAbABlACAASQBuAGMALgAgADIAMAAxADb/2wBDAAUDBAQEAwUEBAQFBQUGBwwIBwcHBw8LCwkMEQ8SEhEPERETFhwXExQaFRERGCEYGh0dHx8fExciJCIeJBweHx7/2wBDAQUFBQcGBw4ICA4eFBEUHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh7/wAARCAJYAlgDASIAAhEBAxEB/8QAHQABAAMBAAMBAQAAAAAAAAAAAAYHCAkDBAUBAv/EAFkQAAECBAIECQcHBwkGBQQDAAABAgMEBQYHEQgSIdIXGDFBUVZxlJUTIjdSVGGBFDKEkaGxtBUWI0J1gpIzOGJydLKzwdFDU3Oio8IkNDVj8CU2V5ODw+H/xAAbAQEAAgMBAQAAAAAAAAAAAAAABAUBAgMGB//EAEERAAIBAgEHCAkEAQMDBQAAAAABAgMEEQUSEyExUnEVMjNBUZGxwQYUFjRCYXKB0SJTofDhI0PxJILCREVikrL/2gAMAwEAAhEDEQA/ANlgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA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AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD/9k=" style="height:110px;width:auto;object-fit:contain;mix-blend-mode:multiply;" alt="Sonoma State University"/></div>', unsafe_allow_html=True)
        st.title("Building Energy Leaderboard")
        st.markdown(
            '<div class="alert-blue" style="margin-top:8px;">'
            '👈  Select at least two periods from the sidebar to unlock leaderboard rankings.</div>',
            unsafe_allow_html=True)
        st.stop()

    hcol_l2, hcol_r2 = st.columns([3, 1])
    with hcol_l2:
        st.markdown('<div style="margin-bottom:12px;"><img src="data:image/png;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/4gHYSUNDX1BST0ZJTEUAAQEAAAHIAAAAAAQwAABtbnRyUkdCIFhZWiAH4AABAAEAAAAAAABhY3NwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAA9tYAAQAAAADTLQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAlkZXNjAAAA8AAAACRyWFlaAAABFAAAABRnWFlaAAABKAAAABRiWFlaAAABPAAAABR3dHB0AAABUAAAABRyVFJDAAABZAAAAChnVFJDAAABZAAAAChiVFJDAAABZAAAAChjcHJ0AAABjAAAADxtbHVjAAAAAAAAAAEAAAAMZW5VUwAAAAgAAAAcAHMAUgBHAEJYWVogAAAAAAAAb6IAADj1AAADkFhZWiAAAAAAAABimQAAt4UAABjaWFlaIAAAAAAAACSgAAAPhAAAts9YWVogAAAAAAAA9tYAAQAAAADTLXBhcmEAAAAAAAQAAAACZmYAAPKnAAANWQAAE9AAAApbAAAAAAAAAABtbHVjAAAAAAAAAAEAAAAMZW5VUwAAACAAAAAcAEcAbwBvAGcAbABlACAASQBuAGMALgAgADIAMAAxADb/2wBDAAUDBAQEAwUEBAQFBQUGBwwIBwcHBw8LCwkMEQ8SEhEPERETFhwXExQaFRERGCEYGh0dHx8fExciJCIeJBweHx7/2wBDAQUFBQcGBw4ICA4eFBEUHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh7/wAARCAJYAlgDASIAAhEBAxEB/8QAHQABAAMBAAMBAQAAAAAAAAAAAAYHCAkDBAUBAv/EAFkQAAECBAIECQcHBwkGBQQDAAABAgMEBQYHEQgSIdIXGDFBUVZxlJUTIjdSVGGBFDKEkaGxtBUWI0J1gpIzOGJydLKzwdFDU3Oio8IkNDVj8CU2V5ODw+H/xAAbAQEAAgMBAQAAAAAAAAAAAAAABAUBAgMGB//EAEERAAIBAgEHCAkEAQMDBQAAAAABAgMEEQUSEyExUnEVMjNBUZGxwQYUFjRCYXKB0SJTofDhI0PxJILCREVikrL/2gAMAwEAAhEDEQA/ANlgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA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AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD/9k=" style="height:110px;width:auto;object-fit:contain;mix-blend-mode:multiply;" alt="Sonoma State University"/></div>', unsafe_allow_html=True)
        st.title("Building Energy Leaderboard")
        st.markdown(
            '<p style="font-size:1.05rem;color:#6b7280;margin-top:2px;line-height:1.5;">'
            'Ranked by <b style="color:#111827">% reduction</b> compared to the prior selected week.</p>',
            unsafe_allow_html=True)

    lb_latest = sorted_sel[-1]
    lb_prev   = sorted_sel[-2] if len(sorted_sel) >= 2 else None

    with hcol_r2:
        if lb_prev:
            cmp_str = f"{period_label(lb_prev)}  vs  {period_label(lb_latest)}"
        else:
            cmp_str = period_label(lb_latest)
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
            f'{period_label(lb_prev)}: {p_kwh} → {period_label(lb_latest)}: {c_kwh}</span>'
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

    st.markdown('<div style="margin-bottom:12px;"><img src="data:image/png;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/4gHYSUNDX1BST0ZJTEUAAQEAAAHIAAAAAAQwAABtbnRyUkdCIFhZWiAH4AABAAEAAAAAAABhY3NwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAA9tYAAQAAAADTLQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAlkZXNjAAAA8AAAACRyWFlaAAABFAAAABRnWFlaAAABKAAAABRiWFlaAAABPAAAABR3dHB0AAABUAAAABRyVFJDAAABZAAAAChnVFJDAAABZAAAAChiVFJDAAABZAAAAChjcHJ0AAABjAAAADxtbHVjAAAAAAAAAAEAAAAMZW5VUwAAAAgAAAAcAHMAUgBHAEJYWVogAAAAAAAAb6IAADj1AAADkFhZWiAAAAAAAABimQAAt4UAABjaWFlaIAAAAAAAACSgAAAPhAAAts9YWVogAAAAAAAA9tYAAQAAAADTLXBhcmEAAAAAAAQAAAACZmYAAPKnAAANWQAAE9AAAApbAAAAAAAAAABtbHVjAAAAAAAAAAEAAAAMZW5VUwAAACAAAAAcAEcAbwBvAGcAbABlACAASQBuAGMALgAgADIAMAAxADb/2wBDAAUDBAQEAwUEBAQFBQUGBwwIBwcHBw8LCwkMEQ8SEhEPERETFhwXExQaFRERGCEYGh0dHx8fExciJCIeJBweHx7/2wBDAQUFBQcGBw4ICA4eFBEUHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh7/wAARCAJYAlgDASIAAhEBAxEB/8QAHQABAAMBAAMBAQAAAAAAAAAAAAYHCAkDBAUBAv/EAFkQAAECBAIECQcHBwkGBQQDAAABAgMEBQYHEQgSIdIXGDFBUVZxlJUTIjdSVGGBFDKEkaGxtBUWI0J1gpIzOGJydLKzwdFDU3Oio8IkNDVj8CU2V5ODw+H/xAAbAQEAAgMBAQAAAAAAAAAAAAAABAUBAgMGB//EAEERAAIBAgEHCAkEAQMDBQAAAAABAgMEEQUSEyExUnEVMjNBUZGxwQYUFjRCYXKB0SJTofDhI0PxJILCREVikrL/2gAMAwEAAhEDEQA/ANlgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA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AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD/9k=" style="height:110px;width:auto;object-fit:contain;mix-blend-mode:multiply;" alt="Sonoma State University"/></div>', unsafe_allow_html=True)
    st.title("Data Integrity Report")
    st.markdown(
        '<p style="font-size:1.05rem;color:#6b7280;margin-top:2px;line-height:1.5;">'
        'Full sensor registry, verified data, gap analysis, and deployment notes.</p>',
        unsafe_allow_html=True)

    # Load raw CSV — derive earliest / latest from all weeks
    _di_raw = pd.read_csv(WEEKLY_CSV)
    _di_raw["week"] = _di_raw["week"].astype(str).str.strip()
    _di_weeks_sorted = sorted(_di_raw["week"].unique())
    _di_earliest = _di_weeks_sorted[0]
    _di_latest   = _di_weeks_sorted[-1]
    wdf = _di_raw[_di_raw["week"] == _di_latest].sort_values("kWh", ascending=False)

    # ── Derive per-building status dynamically from SENSOR_REGISTRY ──────────
    from collections import defaultdict as _dd
    _bld_sensor_statuses = _dd(list)
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

    # ── SECTION 1: Building Data Status Chart ────────────────────────────────
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
    # Text for bars with fill > 0 (shown inside the coloured bar)
    _texts_inside = [
        f'{d["label"]}  ({d["ok"]}/{d["total"]} meters active)' if d["fill"] > 0 else ''
        for d in _bld_chart_data
    ]
    # Text for zero-fill bars (shown outside, right of the grey track)
    _texts_outside = [
        f'{d["label"]}  ({d["ok"]}/{d["total"]} meters active)' if d["fill"] == 0 else ''
        for d in _bld_chart_data
    ]
    # Colour for outside labels matches status colour
    _outside_font_cols = [d["color"] if d["fill"] == 0 else 'rgba(0,0,0,0)' for d in _bld_chart_data]

    fig_status = go.Figure()
    # Grey background track
    fig_status.add_trace(go.Bar(
        y=_blds_c, x=[1.0] * len(_bld_chart_data), orientation="h",
        marker_color="#f1f5f9", marker_line_width=0,
        showlegend=False, hoverinfo="skip",
    ))
    # Coloured fill bar (inside text for partial/active)
    fig_status.add_trace(go.Bar(
        y=_blds_c, x=_fills_c, orientation="h",
        marker_color=_cols_c, marker_line_width=0,
        text=_texts_inside, textposition="inside", insidetextanchor="start",
        textfont=dict(size=12, color="#ffffff", family="Inter"),
        hovertemplate="<b>%{y}</b><br>%{customdata}<extra></extra>",
        customdata=[f'{d["label"]}  ({d["ok"]}/{d["total"]} meters active)' for d in _bld_chart_data],
        showlegend=False,
    ))
    # Outside labels for zero-fill (No Data) bars — tiny offset so they sit just right of axis
    fig_status.add_trace(go.Bar(
        y=_blds_c, x=[0.01 if d["fill"] == 0 else 0 for d in _bld_chart_data], orientation="h",
        marker_color='rgba(0,0,0,0)', marker_line_width=0,
        text=_texts_outside, textposition="outside",
        textfont=dict(size=11, family="Inter"),
        texttemplate='<span style="color:%{marker.color}">%{text}</span>',
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

    # ── SECTION 2: Data Summary ───────────────────────────────────────────────
    st.markdown('<div class="sec-label">Data Summary</div>', unsafe_allow_html=True)

    def _parse_wk_start(w):
        try:    return pd.to_datetime(str(w).split("/")[0].strip())
        except: return None
    def _parse_wk_end(w):
        try:
            parts = str(w).split("/")
            return pd.to_datetime(parts[1].strip()) if len(parts) > 1 else pd.to_datetime(parts[0].strip())
        except: return None

    _start_dt  = _parse_wk_start(_di_earliest)
    _end_dt    = _parse_wk_end(_di_latest)
    _start_str = _start_dt.strftime("%B %d, %Y") if _start_dt else _di_earliest
    _end_str   = _end_dt.strftime("%B %d, %Y")   if _end_dt   else _di_latest

    import datetime as _dtime
    _now_str = _dtime.datetime.now().strftime("%B %d, %Y  —  %I:%M %p")

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
        f'<div style="margin:4px 0 18px;"><span style="font-size:1.05rem;font-weight:700;color:#16a34a;font-family:Inter,sans-serif;">'
        f'{_n_active} fully active</span>'
        f'<span style="font-size:1.05rem;font-weight:700;color:#d97706;font-family:Inter,sans-serif;margin-left:10px;">'
        f'+ {_n_partial} partial</span></div>'
        f'<div style="line-height:1;"><span style="{_lbl_style}">Buildings with No Data</span></div>'
        f'<div style="margin:4px 0 18px;"><span style="font-size:1.05rem;font-weight:700;color:#dc2626;font-family:Inter,sans-serif;">'
        f'{_n_nodata} buildings</span></div>'
        f'<div style="line-height:1;"><span style="{_lbl_style}">Partial Data Note</span></div>'
        f'<div style="margin:4px 0 0;"><span style="font-size:0.9rem;font-weight:500;color:#78350f;font-family:Inter,sans-serif;">'
        f'{_partial_note}</span></div>'
        f'</div>', unsafe_allow_html=True)

    # ── SECTION 3: Verified Data Table ───────────────────────────────────────
    st.markdown(
        f'<div class="sec-label">Verified Data — {week_label(_di_latest)}</div>',
        unsafe_allow_html=True)

    v_tbl = ('<table class="di-table"><thead><tr>'
             '<th>Building</th><th>kWh</th><th>MWh</th><th>Est. Energy Cost @ $0.15/kWh equiv</th><th>Status</th>'
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
        f'<div style="font-size:0.85rem;color:#9ca3af;margin-top:8px;margin-bottom:4px;">'
        f'Showing most recent week: {week_label(_di_latest)}. '
        f'kWh includes both electric meters and thermal energy sensors (heating &amp; cooling loops) '
        f'converted to kWh. Gas and water meters currently have no data available.'
        f'</div>', unsafe_allow_html=True)

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
        '<span style="display:inline-block;background:#e8eef5;color:#1b3a5c;font-weight:600;'
        'padding:2px 12px;border-radius:6px;font-family:Inter,sans-serif;">BTU × 0.000293071 = kWh</span><br>'
        '<span style="display:inline-block;background:#e8eef5;color:#1b3a5c;font-weight:600;'
        'padding:2px 12px;border-radius:6px;font-family:Inter,sans-serif;">kBTU × 0.293071 = kWh</span><br>'
        '<span style="display:inline-block;background:#e8eef5;color:#1b3a5c;font-weight:600;'
        'padding:2px 12px;border-radius:6px;font-family:Inter,sans-serif;">therm × 29.3071 = kWh</span><br>'
        '<span style="display:inline-block;background:#e8eef5;color:#1b3a5c;font-weight:600;'
        'padding:2px 12px;border-radius:6px;font-family:Inter,sans-serif;">kWh → kWh direct</span><br>'
        '<span style="display:inline-block;background:#e8eef5;color:#1b3a5c;font-weight:600;'
        'padding:2px 12px;border-radius:6px;font-family:Inter,sans-serif;">Water (gallon) → stored as-is, no conversion</span>'
        '</div></div>', unsafe_allow_html=True)

    # Pipeline info
    st.markdown('<div class="sec-label">Pipeline</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="card">'
        '<div style="font-size:0.95rem;color:#374151;line-height:1.9;">'
        '<b>Schedule:</b> Daily, 6 AM (cron job)<br>'
        '<b>DB:</b> 193.203.166.234 | u209446640_SSUEnergy'
        '</div></div>', unsafe_allow_html=True)
