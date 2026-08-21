import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
import warnings
import io
import re
import json
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
try:
    from finance_advisor import page_finance
    _FA_AVAILABLE = True
except Exception as _fa_err:
    _FA_AVAILABLE = False
    _FA_ERR = str(_fa_err)

try:
    from mf_module import page_mf_portfolio
    _MF_AVAILABLE = True
except Exception as _mf_err:
    _MF_AVAILABLE = False
    _MF_ERR = str(_mf_err)
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="EQUITEX PRO · Indian Equity Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────
# THEME — "THE LEDGER"
# One deliberate identity, inspired by the Indian passbook/
# ledger book: bond-paper canvas, fountain-pen ink text,
# a seal-green primary ink for actions, and a brass-gold
# reserved for the one signature moment (the verdict seal).
# ─────────────────────────────────────────────
THEMES = {
    "ledger": {
        "label": "📘 The Ledger",
        "--bg-primary":    "#F0F1EA",
        "--bg-secondary":  "#E6E8DF",
        "--bg-card":       "#FFFFFF",
        "--bg-card-hover": "#FAFAF4",
        "--bg-input":      "#FFFFFF",
        "--border":        "#DBDDD1",
        "--border-bright": "#C4C7B7",
        "--text-primary":  "#192623",
        "--text-secondary":"#4C5A55",
        "--text-muted":    "#8B948C",
        "--accent-gold":   "#0E6E58",
        "--accent-gold2":  "#12876A",
        "--accent-amber":  "#A8752E",
        "--accent-blue":   "#2E5C86",
        "--accent-cyan":   "#3E8BA0",
        "--accent-green":  "#1F8A5F",
        "--accent-red":    "#A23B41",
        "--accent-purple": "#6B5B95",
        "--glow-blue":     "rgba(46,92,134,0.08)",
        "--glow-green":    "rgba(31,138,95,0.08)",
        "--glow-red":      "rgba(162,59,65,0.08)",
        "--glow-gold":     "rgba(14,110,88,0.10)",
        "--navbar-bg":     "#152520",
        "--navbar-text":   "#F0F1EA",
        "--score-bg":      "#E6E8DF",
        "--is-light":      "1",
        "--font-display":  "'IBM Plex Sans', sans-serif",
        "--font-mono":     "'IBM Plex Mono', monospace",
        "--font-serif":    "'Fraunces', serif",
    },
}

def inject_theme():
    """Inject the active theme CSS — complete, explicit, no bleed-through."""
    theme_key = st.session_state.get("theme", "ledger")
    t = THEMES.get(theme_key, THEMES["ledger"])
    vars_css = " ".join(f"{k}: {v};" for k, v in t.items() if k.startswith("--"))

    bg      = t["--bg-primary"]
    bgcard  = t["--bg-card"]
    bgsec   = t["--bg-secondary"]
    bginp   = t["--bg-input"]
    border  = t["--border"]
    borderbr= t["--border-bright"]
    tp      = t["--text-primary"]
    ts      = t["--text-secondary"]
    tm      = t["--text-muted"]
    accent  = t["--accent-gold"]
    accent2 = t["--accent-gold2"]
    green   = t["--accent-green"]
    red     = t["--accent-red"]
    glow    = t["--glow-gold"]
    font    = t.get("--font-display", "'Plus Jakarta Sans', sans-serif")

    st.markdown(f"""<style>
    :root {{ {vars_css} }}

    /* ── BASE ── */
    html, body, .stApp, [class*="css"] {{
        background-color: {bg} !important;
        color: {tp} !important;
        font-family: {font} !important;
    }}
    .stApp {{ background-color: {bg} !important; }}
    .main .block-container {{
        background-color: {bg} !important;
        padding-top: 0 !important;
    }}

    /* ── GLOBAL TEXT — explicit, no inherit ── */
    p, h1, h2, h3, h4, h5, h6 {{
        color: {tp} !important;
    }}
    span, li {{ color: {tp}; }}
    label {{ color: {ts} !important; }}
    small, .stCaption, [data-testid="stCaptionContainer"] p {{
        color: {tm} !important;
    }}
    .stMarkdown, .stMarkdown p, .stMarkdown span {{
        color: {tp} !important;
    }}
    code {{ color: {accent} !important; background: {bgsec} !important; }}

    /* ── SIDEBAR ── */
    [data-testid="stSidebar"] {{
        background-color: {bgsec} !important;
        border-right: 1px solid {border} !important;
    }}
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div {{
        color: {ts} !important;
    }}
    [data-testid="collapsedControl"] {{
        background-color: {bgsec} !important;
        border-right: 1px solid {border} !important;
    }}

    /* ── INPUTS ── */
    .stTextInput input,
    .stNumberInput input,
    textarea,
    .stTextArea textarea {{
        background-color: {bginp} !important;
        border: 1px solid {borderbr} !important;
        color: {tp} !important;
        border-radius: 6px !important;
        font-family: {font} !important;
    }}
    .stTextInput input:focus,
    .stNumberInput input:focus,
    textarea:focus {{
        border-color: {accent} !important;
        box-shadow: 0 0 0 2px {glow} !important;
        outline: none !important;
    }}
    [data-baseweb="select"] > div {{
        background-color: {bginp} !important;
        border: 1px solid {borderbr} !important;
        color: {tp} !important;
        border-radius: 6px !important;
    }}
    [data-baseweb="select"] [data-testid="stMarkdownContainer"] p {{
        color: {tp} !important;
    }}
    [data-baseweb="menu"] {{
        background-color: {bgcard} !important;
        border: 1px solid {border} !important;
    }}
    [data-baseweb="option"] {{
        background-color: {bgcard} !important;
        color: {tp} !important;
    }}
    [data-baseweb="option"]:hover {{
        background-color: {bgsec} !important;
    }}

    /* ── BUTTONS ── */
    .stButton > button {{
        background: transparent !important;
        border: 1px solid {borderbr} !important;
        color: {ts} !important;
        border-radius: 6px !important;
        font-family: {font} !important;
        font-size: 12px !important;
        font-weight: 500 !important;
        transition: all 0.15s ease !important;
    }}
    .stButton > button:hover {{
        border-color: {accent} !important;
        color: {accent} !important;
        background: {glow} !important;
    }}
    [data-testid="baseButton-primary"] {{
        background: {accent} !important;
        border-color: {accent} !important;
        color: {bgcard} !important;
        font-weight: 600 !important;
    }}
    [data-testid="baseButton-primary"]:hover {{
        background: {accent2} !important;
        border-color: {accent2} !important;
    }}

    /* ── TABS ── */
    .stTabs [data-baseweb="tab-list"] {{
        background: {bgsec} !important;
        border-bottom: 1px solid {border} !important;
        gap: 0 !important;
        padding: 0 !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        background: transparent !important;
        color: {tm} !important;
        font-size: 11px !important;
        font-weight: 500 !important;
        letter-spacing: 0.6px !important;
        text-transform: uppercase !important;
        padding: 0 16px !important;
        height: 44px !important;
        border-radius: 0 !important;
        border-bottom: 2px solid transparent !important;
        font-family: {font} !important;
    }}
    .stTabs [aria-selected="true"] {{
        color: {accent} !important;
        border-bottom: 2px solid {accent} !important;
        background: transparent !important;
    }}
    .stTabs [data-baseweb="tab-panel"] {{
        background: {bg} !important;
        padding: 20px 4px !important;
        color: {tp} !important;
    }}
    .stTabs [data-baseweb="tab-panel"] p,
    .stTabs [data-baseweb="tab-panel"] span,
    .stTabs [data-baseweb="tab-panel"] label,
    .stTabs [data-baseweb="tab-panel"] div {{
        color: {tp} !important;
    }}

    /* ── EXPANDER ── */
    .stExpander {{
        background-color: {bgcard} !important;
        border: 1px solid {border} !important;
        border-radius: 8px !important;
    }}
    .streamlit-expanderHeader, details summary {{
        background: {bgcard} !important;
        color: {tp} !important;
        border-radius: 8px !important;
        font-family: {font} !important;
    }}
    .streamlit-expanderHeader p,
    .streamlit-expanderHeader span {{
        color: {tp} !important;
    }}
    .streamlit-expanderContent, details[open] > div {{
        background: {bgsec} !important;
        color: {tp} !important;
    }}
    .streamlit-expanderContent p,
    .streamlit-expanderContent span,
    .streamlit-expanderContent label,
    .streamlit-expanderContent div {{
        color: {tp} !important;
    }}

    /* ── RADIO & CHECKBOX ── */
    .stRadio label, .stCheckbox label {{
        color: {tp} !important;
    }}
    .stRadio [data-testid="stMarkdownContainer"] p {{
        color: {tp} !important;
    }}
    [data-testid="stRadio"] > label {{
        color: {ts} !important;
    }}

    /* ── FILE UPLOADER ── */
    [data-testid="stFileUploader"] {{
        background: {bgcard} !important;
        border: 1px dashed {borderbr} !important;
        border-radius: 8px !important;
    }}
    [data-testid="stFileUploader"] p,
    [data-testid="stFileUploader"] span {{
        color: {ts} !important;
    }}
    [data-testid="stFileUploaderDropzone"] {{
        background: {bgsec} !important;
    }}
    [data-testid="stFileUploaderDropzone"] p,
    [data-testid="stFileUploaderDropzone"] span {{
        color: {ts} !important;
    }}

    /* ── ALERTS / SPINNERS ── */
    [data-testid="stAlert"] {{
        background: {bgsec} !important;
        color: {tp} !important;
        border-radius: 6px !important;
    }}
    [data-testid="stAlert"] p {{ color: {tp} !important; }}
    .stSpinner > div {{ border-top-color: {accent} !important; }}
    .stSpinner p {{ color: {ts} !important; }}

    /* ── SLIDER ── */
    [data-testid="stSlider"] [data-baseweb="slider"] div[role="progressbar"] {{
        background: {accent} !important;
    }}
    [data-testid="stSlider"] p {{ color: {ts} !important; }}

    /* ── METRICS ── */
    [data-testid="stMetric"] {{
        background: {bgcard} !important;
        border: 1px solid {border} !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
    }}
    [data-testid="stMetricLabel"] p {{ color: {ts} !important; }}
    [data-testid="stMetricValue"] {{ color: {tp} !important; }}

    /* ── PROGRESS ── */
    .stProgress > div > div {{
        background: {accent} !important;
        border-radius: 4px !important;
    }}
    .stProgress > div {{
        background: {border} !important;
        border-radius: 4px !important;
    }}

    /* ── SCROLLBAR ── */
    ::-webkit-scrollbar {{ width: 5px; height: 5px; }}
    ::-webkit-scrollbar-track {{ background: {bg}; }}
    ::-webkit-scrollbar-thumb {{ background: {borderbr}; border-radius: 3px; }}

    /* ── NUMBER INPUT ARROWS ── */
    .stNumberInput [data-testid="stNumberInputField"] {{
        color: {tp} !important;
    }}
    button[kind="stepper"] {{
        background: {bgsec} !important;
        color: {ts} !important;
        border-color: {border} !important;
    }}
    </style>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# EQUITEX — "THE LEDGER" THEME
# Bond-paper canvas · Ink-navy text · Seal-green primary
# Fonts: Fraunces (serif headlines) + IBM Plex Sans (UI) + IBM Plex Mono (data)
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: var(--font-display, 'Plus Jakarta Sans', sans-serif) !important;
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
    }

    .stApp { background-color: var(--bg-primary) !important; }
    .main .block-container { padding: 0 0 40px 0 !important; max-width: 100% !important; }
    #MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden !important; display: none !important; }

    /* ── SIDEBAR ── */
    [data-testid="stSidebar"] {
        background-color: var(--bg-secondary) !important;
        border-right: 1px solid var(--border) !important;
    }
    [data-testid="stSidebar"] * { color: var(--text-secondary) !important; }
    [data-testid="collapsedControl"] {
        display: flex !important; visibility: visible !important;
        background-color: var(--bg-secondary) !important;
        border-right: 1px solid var(--border) !important;
    }
    [data-testid="collapsedControl"] button,
    [data-testid="collapsedControl"] svg {
        display: block !important; visibility: visible !important;
        color: var(--accent-cyan) !important; fill: var(--accent-cyan) !important;
    }

    /* ── INPUTS ── */
    .stTextInput input, .stSelectbox select, .stNumberInput input {
        background-color: var(--bg-input) !important;
        border: 1px solid var(--border-bright) !important;
        color: var(--text-primary) !important;
        border-radius: 6px !important;
        font-family: 'DM Mono', monospace !important;
        font-size: 13px !important;
    }
    .stTextInput input:focus, .stSelectbox select:focus {
        border-color: var(--accent-gold) !important;
        box-shadow: 0 0 0 3px var(--glow-gold) !important;
    }

    /* ── BUTTONS ── */
    .stButton button {
        background: transparent !important;
        border: 1px solid var(--border-bright) !important;
        color: var(--text-secondary) !important;
        border-radius: 6px !important;
        font-family: 'DM Mono', monospace !important;
        font-size: 11px !important;
        font-weight: 500 !important;
        letter-spacing: 0.8px !important;
        text-transform: uppercase !important;
        transition: all 0.18s ease !important;
    }
    .stButton button:hover {
        border-color: var(--accent-gold) !important;
        color: var(--accent-gold) !important;
        background: var(--glow-gold) !important;
    }
    [data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, var(--accent-gold), var(--accent-gold2)) !important;
        border-color: transparent !important;
        color: var(--bg-primary) !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 16px rgba(201,168,76,0.35) !important;
    }
    [data-testid="baseButton-primary"]:hover {
        background: var(--accent-gold2) !important;
        box-shadow: 0 4px 24px rgba(201,168,76,0.5) !important;
    }

    /* ── TABS ── */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-secondary) !important;
        border-bottom: 1px solid var(--border) !important;
        gap: 0 !important; padding: 0 !important;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: var(--text-muted) !important;
        font-size: 10px !important; font-weight: 500 !important;
        letter-spacing: 1px !important; text-transform: uppercase !important;
        padding: 0 18px !important; height: 44px !important;
        border-radius: 0 !important;
        border-bottom: 2px solid transparent !important;
        font-family: 'DM Mono', monospace !important;
    }
    .stTabs [aria-selected="true"] {
        color: var(--accent-gold) !important;
        border-bottom: 2px solid var(--accent-gold) !important;
        background: transparent !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        background: var(--bg-primary) !important;
        padding: 20px 24px !important;
    }

    /* ── EXPANDER ── */
    .streamlit-expanderHeader {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
        border-radius: 4px !important;
        font-family: var(--font-mono, 'Fira Code', monospace) !important;
        font-size: 12px !important;
    }
    .streamlit-expanderContent {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border) !important;
        border-top: none !important;
    }

    /* ── FILE UPLOADER ── */
    [data-testid="stFileUploader"] {
        background: var(--bg-card) !important;
        border: 1px dashed var(--border-bright) !important;
        border-radius: 6px !important;
    }
    [data-testid="stFileUploader"] * { color: var(--text-secondary) !important; }
    [data-testid="stFileUploaderDropzone"] {
        background: var(--bg-input) !important;
        border: 1px dashed var(--accent-blue) !important;
    }

    /* ── RADIO ── */
    .stRadio [data-testid="stMarkdownContainer"] p { color: var(--text-secondary) !important; }
    .stRadio label { color: var(--text-primary) !important; }

    /* ── SCROLLBAR ── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-primary); }
    ::-webkit-scrollbar-thumb { background: var(--border-bright); border-radius: 3px; }

    /* ── BLOOMBERG TOP BAR ── */
    .bb-topbar {
        background: var(--bg-secondary);
        border-bottom: 1px solid var(--border);
        padding: 0 20px;
        height: 48px;
        display: flex;
        align-items: center;
        gap: 0;
    }
    .bb-logo {
        font-family: 'Fraunces', serif;
        font-size: 22px;
        letter-spacing: 2px;
        color: var(--accent-amber);
        padding-right: 20px;
        border-right: 1px solid var(--border);
        margin-right: 4px;
    }
    .bb-nav-item {
        padding: 0 16px;
        height: 48px;
        display: inline-flex;
        align-items: center;
        font-family: var(--font-mono, 'Fira Code', monospace);
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        color: var(--text-muted);
        cursor: pointer;
        border-bottom: 2px solid transparent;
        transition: all 0.15s ease;
    }
    .bb-nav-item.active {
        color: var(--accent-amber);
        border-bottom: 2px solid var(--accent-amber);
    }

    /* ── TERMINAL CARD ── */
    .t-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 4px;
        overflow: hidden;
        margin-bottom: 12px;
    }
    .t-card-header {
        padding: 10px 16px;
        border-bottom: 1px solid var(--border);
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: var(--bg-secondary);
    }
    .t-card-title {
        font-family: var(--font-mono, 'Fira Code', monospace);
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: var(--text-muted);
    }

    /* ── STAT TILE ── */
    .stat-tile {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 4px;
        padding: 14px 16px;
        position: relative;
        overflow: hidden;
    }
    .stat-tile::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
    }
    .stat-tile.blue::before { background: var(--accent-blue); }
    .stat-tile.green::before { background: var(--accent-green); }
    .stat-tile.red::before { background: var(--accent-red); }
    .stat-tile.amber::before { background: var(--accent-amber); }
    .stat-tile.cyan::before { background: var(--accent-cyan); }
    .stat-label {
        font-family: var(--font-mono, 'Fira Code', monospace);
        font-size: 9px;
        font-weight: 600;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: var(--text-muted);
        margin-bottom: 8px;
    }
    .stat-value {
        font-family: var(--font-mono, 'Fira Code', monospace);
        font-size: 20px;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1.2;
    }
    .stat-value.blue  { color: var(--accent-blue); }
    .stat-value.green { color: var(--accent-green); }
    .stat-value.red   { color: var(--accent-red); }
    .stat-value.amber { color: var(--accent-amber); }
    .stat-value.cyan  { color: var(--accent-cyan); }
    .stat-sub {
        font-size: 10px;
        color: var(--text-muted);
        margin-top: 4px;
        font-family: var(--font-mono, 'Fira Code', monospace);
    }

    /* ── TABLE ── */
    .t-table { width: 100%; border-collapse: collapse; font-size: 12px; }
    .t-table th {
        padding: 8px 14px;
        font-family: var(--font-mono, 'Fira Code', monospace);
        font-size: 9px;
        font-weight: 600;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: var(--text-muted);
        background: var(--bg-secondary);
        border-bottom: 1px solid var(--border);
        text-align: left;
        white-space: nowrap;
    }
    .t-table td {
        padding: 9px 14px;
        border-bottom: 1px solid var(--border);
        color: var(--text-primary);
        font-size: 12px;
        font-family: 'IBM Plex Sans', sans-serif;
    }
    .t-table tr:last-child td { border-bottom: none; }
    .t-table tr:hover td { background: var(--bg-card-hover); }
    .mono { font-family: var(--font-mono, 'Fira Code', monospace) !important; font-size: 12px !important; }

    /* ── BADGES ── */
    .badge {
        display: inline-flex; align-items: center;
        padding: 2px 8px; border-radius: 2px;
        font-family: var(--font-mono, 'Fira Code', monospace);
        font-size: 10px; font-weight: 700; letter-spacing: 0.5px;
    }
    .badge-buy  { background: rgba(0,200,122,0.15); color: var(--accent-green); border: 1px solid rgba(0,200,122,0.3); }
    .badge-hold { background: rgba(255,176,0,0.15);  color: var(--accent-amber); border: 1px solid rgba(255,176,0,0.3); }
    .badge-avoid{ background: rgba(255,59,92,0.12);  color: var(--accent-red);   border: 1px solid rgba(255,59,92,0.3); }

    /* ── SCORE BAR ── */
    .score-bar { display: flex; align-items: center; gap: 8px; }
    .score-track { flex: 1; height: 3px; background: var(--border); border-radius: 2px; overflow: hidden; }
    .score-fill { height: 100%; border-radius: 2px; }
    .score-num { font-family: var(--font-mono, 'Fira Code', monospace); font-size: 11px; color: var(--text-secondary); min-width: 24px; }

    /* ── SIGNAL ROWS ── */
    .sig-row {
        display: flex; align-items: center; padding: 9px 16px; gap: 10px;
        border-bottom: 1px solid var(--border); font-size: 12px;
    }
    .sig-row:last-child { border-bottom: none; }
    .sig-green  { color: var(--accent-green);  font-family: var(--font-mono, 'Fira Code', monospace); font-size: 11px; font-weight: 600; }
    .sig-red    { color: var(--accent-red);    font-family: var(--font-mono, 'Fira Code', monospace); font-size: 11px; font-weight: 600; }
    .sig-amber  { color: var(--accent-amber);  font-family: var(--font-mono, 'Fira Code', monospace); font-size: 11px; font-weight: 600; }
    .sig-cyan   { color: var(--accent-cyan);   font-family: var(--font-mono, 'Fira Code', monospace); font-size: 11px; font-weight: 600; }

    /* ── BLOCKS ── */
    .info-block  { background:rgba(0,144,255,0.08); border-left:3px solid var(--accent-blue); border-radius:0 4px 4px 0; padding:10px 14px; margin:6px 0; font-size:12px; color:var(--text-primary); }
    .warn-block  { background:rgba(255,176,0,0.08); border-left:3px solid var(--accent-amber);border-radius:0 4px 4px 0; padding:10px 14px; margin:6px 0; font-size:12px; color:var(--text-primary); }
    .ok-block    { background:rgba(0,200,122,0.08); border-left:3px solid var(--accent-green); border-radius:0 4px 4px 0; padding:10px 14px; margin:6px 0; font-size:12px; color:var(--text-primary); }
    .danger-block{ background:rgba(255,59,92,0.08); border-left:3px solid var(--accent-red);   border-radius:0 4px 4px 0; padding:10px 14px; margin:6px 0; font-size:12px; color:var(--text-primary); }

    /* ── DIVIDEND SPECIFIC ── */
    .div-badge-consistent { background:rgba(0,200,122,0.12); color:var(--accent-green); border:1px solid rgba(0,200,122,0.3); padding:2px 8px; border-radius:2px; font-family:var(--font-mono,'Fira Code',monospace); font-size:10px; font-weight:700; }
    .div-badge-irregular  { background:rgba(255,176,0,0.12);  color:var(--accent-amber); border:1px solid rgba(255,176,0,0.3); padding:2px 8px; border-radius:2px; font-family:var(--font-mono,'Fira Code',monospace); font-size:10px; font-weight:700; }
    .div-badge-no-div     { background:rgba(255,59,92,0.10);   color:var(--accent-red);   border:1px solid rgba(255,59,92,0.3);  padding:2px 8px; border-radius:2px; font-family:var(--font-mono,'Fira Code',monospace); font-size:10px; font-weight:700; }

    /* ── DIVIDER ── */
    .t-divider { border:none; border-top:1px solid var(--border); margin:12px 0; }

    /* ── UPLOAD MODAL ── */
    .upload-panel {
        background: var(--bg-card);
        border: 1px solid var(--border-bright);
        border-radius: 6px;
        padding: 24px;
        margin-bottom: 20px;
    }

    /* ── GRADE BADGE ── */
    .grade { width:30px; height:30px; border-radius:3px; display:inline-flex; align-items:center; justify-content:center; font-family:var(--font-mono,'Fira Code',monospace); font-size:14px; font-weight:700; }
    .grade-A { background:rgba(0,200,122,0.15); color:var(--accent-green); border:1px solid rgba(0,200,122,0.4); }
    .grade-B { background:rgba(0,144,255,0.15); color:var(--accent-blue); border:1px solid rgba(0,144,255,0.4); }
    .grade-C { background:rgba(255,176,0,0.15); color:var(--accent-amber); border:1px solid rgba(255,176,0,0.4); }
    .grade-D { background:rgba(255,59,92,0.12); color:var(--accent-red); border:1px solid rgba(255,59,92,0.4); }

    /* ── SECTION HEADER ── */
    .sec-hdr {
        font-family: var(--font-mono, 'Fira Code', monospace);
        font-size: 9px; font-weight: 600;
        letter-spacing: 2px; text-transform: uppercase;
        color: var(--text-muted);
        padding: 8px 0 6px;
        border-bottom: 1px solid var(--border);
        margin-bottom: 12px;
    }

    /* ── TICKER STRIP (decorative) ── */
    .ticker-strip {
        background: var(--bg-secondary);
        border-bottom: 1px solid var(--border);
        padding: 4px 0;
        font-family: var(--font-mono, 'Fira Code', monospace);
        font-size: 10px;
        overflow: hidden;
        white-space: nowrap;
    }

    /* ── PAGE TITLE ── */
    .page-hdr {
        padding: 16px 24px 12px;
        border-bottom: 1px solid var(--border);
        background: var(--bg-secondary);
        margin-bottom: 20px;
    }
    .page-title {
        font-family: 'Fraunces', serif;
        font-size: 24px; letter-spacing: 2px;
        color: var(--text-primary);
    }
    .page-subtitle {
        font-family: var(--font-mono, 'Fira Code', monospace);
        font-size: 10px; color: var(--text-muted);
        letter-spacing: 0.5px;
        margin-top: 2px;
    }

    /* ── PROGRESS BAR ── */
    .stProgress > div > div { background: var(--accent-blue) !important; }

    /* ── COMPARE CARD ── */
    .cmp-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 4px;
        overflow: hidden;
    }
    .cmp-hdr {
        padding: 12px 16px;
        border-bottom: 1px solid var(--border);
        background: var(--bg-secondary);
        display: flex; align-items: center; gap: 8px;
    }
    .cmp-name { font-size: 13px; font-weight: 600; color: var(--text-primary); }
    .cstat { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; font-size: 12px; }
    .cstat-label { color: var(--text-muted); font-size: 11px; }
    .cstat-val { font-family: var(--font-mono, 'Fira Code', monospace); font-weight: 600; font-size: 12px; color: var(--text-primary); }

    /* ── NEUTRAL STBUTTON SIDEBAR ── */
    [data-testid="stSidebar"] .stButton button {
        border-color: var(--border-bright) !important;
        color: var(--text-secondary) !important;
    }

    /* ── SENTIMENT TAGS ── */
    .sent-pos { background:rgba(0,200,122,0.12); color:var(--accent-green); border:1px solid rgba(0,200,122,0.3); padding:1px 7px; border-radius:2px; font-family:var(--font-mono,'Fira Code',monospace); font-size:9px; font-weight:700; }
    .sent-neg { background:rgba(255,59,92,0.10); color:var(--accent-red); border:1px solid rgba(255,59,92,0.3); padding:1px 7px; border-radius:2px; font-family:var(--font-mono,'Fira Code',monospace); font-size:9px; font-weight:700; }
    .sent-neu { background:rgba(122,144,168,0.10); color:var(--text-secondary); border:1px solid var(--border); padding:1px 7px; border-radius:2px; font-family:var(--font-mono,'Fira Code',monospace); font-size:9px; font-weight:700; }

    .news-item { padding: 10px 16px; border-bottom: 1px solid var(--border); }
    .news-item:last-child { border-bottom: none; }
    .news-headline { font-size: 12px; color: var(--text-primary); line-height: 1.5; margin-bottom: 4px; }
    .news-meta { display: flex; align-items: center; gap: 8px; font-size: 10px; color: var(--text-muted); }

    /* ── METRIC CARD ── */
    .metric-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-left: 3px solid var(--accent-blue);
        border-radius: 0 4px 4px 0;
        padding: 12px 14px;
        margin-bottom: 8px;
    }
    .metric-label { font-family:var(--font-mono,'Fira Code',monospace); font-size:9px; letter-spacing:1.5px; text-transform:uppercase; color:var(--text-muted); margin-bottom:5px; }
    .metric-val { font-family:var(--font-mono,'Fira Code',monospace); font-size:16px; font-weight:700; color:var(--text-primary); }
    .metric-note { font-size:10px; color:var(--text-muted); margin-top:3px; font-family:var(--font-mono,'Fira Code',monospace); }

    /* ── DIV HISTORY BAR ── */
    .div-bar-row { display:flex; align-items:center; gap:8px; margin-bottom:7px; font-size:11px; }
    .div-bar-year { color:var(--text-muted); width:36px; font-family:var(--font-mono,'Fira Code',monospace); font-size:10px; }
    .div-bar-track { flex:1; height:6px; background:var(--border); border-radius:2px; overflow:hidden; }
    .div-bar-fill { height:100%; border-radius:2px; background:linear-gradient(90deg,#0090ff,#00d4ff); }
    .div-bar-val { font-family:var(--font-mono,'Fira Code',monospace); font-size:10px; color:var(--text-secondary); width:50px; text-align:right; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
PORTFOLIO_COLORS = ["#0090ff","#00c87a","#ffb000","#ff3b5c","#a855f7","#00d4ff","#ff6b35"]

DEFAULT_PORTFOLIO = [
    {"ticker":"RELIANCE.NS","name":"Reliance Industries","qty":10,"buy_price":2400,"invested":24000,"market_value":0,"pnl_broker":0,"sector":"Energy","ltp":0,"market_cap_type":"Large Cap"},
    {"ticker":"TCS.NS","name":"Tata Consultancy Services","qty":5,"buy_price":3500,"invested":17500,"market_value":0,"pnl_broker":0,"sector":"IT","ltp":0,"market_cap_type":"Large Cap"},
    {"ticker":"HDFCBANK.NS","name":"HDFC Bank","qty":15,"buy_price":1500,"invested":22500,"market_value":0,"pnl_broker":0,"sector":"Banking","ltp":0,"market_cap_type":"Large Cap"},
    {"ticker":"INFY.NS","name":"Infosys","qty":12,"buy_price":1400,"invested":16800,"market_value":0,"pnl_broker":0,"sector":"IT","ltp":0,"market_cap_type":"Large Cap"},
    {"ticker":"BAJFINANCE.NS","name":"Bajaj Finance","qty":3,"buy_price":6800,"invested":20400,"market_value":0,"pnl_broker":0,"sector":"NBFC","ltp":0,"market_cap_type":"Large Cap"},
]

POSITIVE_WORDS = ["profit","growth","surge","rally","strong","beat","record","upgrade","buy","bullish","gain","rise","positive","outperform","robust","expansion","acquisition","dividend","win","success"]
NEGATIVE_WORDS = ["loss","decline","fall","crash","weak","miss","downgrade","sell","bearish","drop","negative","underperform","concern","risk","fraud","investigation","penalty","debt","warning","layoff"]

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def safe_get(val, default=None):
    try:
        if val is None or (isinstance(val, float) and np.isnan(val)): return default
        return val
    except: return default

def pct(val):
    if val is None: return "N/A"
    return f"{val*100:.1f}%"

def fmt_cr(val):
    if val is None: return "N/A"
    if abs(val) >= 1e7: return f"₹{val/1e7:.1f}Cr"
    if abs(val) >= 1e5: return f"₹{val/1e5:.1f}L"
    return f"₹{val:.0f}"

def fmt_inr(val):
    if abs(val) >= 1e7: return f"₹{val/1e7:.1f}Cr"
    if abs(val) >= 1e5: return f"₹{val/1e5:.1f}L"
    return f"₹{val:,.0f}"

def score_to_badge_html(score_100):
    if score_100 >= 75: grade, cls = "A", "grade-A"
    elif score_100 >= 60: grade, cls = "B", "grade-B"
    elif score_100 >= 45: grade, cls = "C", "grade-C"
    else: grade, cls = "D", "grade-D"
    return f'<span class="grade {cls}">{grade}</span>'

def score_fill(score_100):
    if score_100 >= 70: return "linear-gradient(90deg,#00c87a,#00d4ff)"
    elif score_100 >= 50: return "linear-gradient(90deg,#0090ff,#00d4ff)"
    elif score_100 >= 35: return "linear-gradient(90deg,#ffb000,#ff6b35)"
    else: return "linear-gradient(90deg,#ff3b5c,#ff6b35)"

def score_bar_html(score_100):
    color = score_fill(score_100)
    return f"""<div class="score-bar">
        <div class="score-track"><div class="score-fill" style="width:{score_100}%;background:{color};"></div></div>
        <div class="score-num">{score_100}</div>
    </div>"""

def decision_badge(decision):
    cls = {"BUY":"badge-buy","HOLD":"badge-hold","AVOID":"badge-avoid"}.get(decision,"badge-hold")
    return f'<span class="badge {cls}">{decision}</span>'

def portfolio_color(idx): return PORTFOLIO_COLORS[idx % len(PORTFOLIO_COLORS)]

# ─────────────────────────────────────────────
# DIVIDEND FUNCTIONS
# ─────────────────────────────────────────────
def fetch_dividend_data(ticker_symbol, qty=0):
    """Fetch 3 years dividend history for a ticker."""
    result = {
        "yield_pct": None,
        "history": {},        # {year: total_dividend_per_share}
        "total_received": 0,  # qty * dividends received
        "consistency": "NO_DIV",
        "consistency_label": "No Dividend",
        "last_dividend": None,
        "forward_annual": None,
    }
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info

        # Dividend yield
        dy = safe_get(info.get("dividendYield"))
        result["yield_pct"] = dy * 100 if dy else None

        # Forward annual dividend
        result["forward_annual"] = safe_get(info.get("dividendRate"))

        # 3-year history
        now = datetime.now()
        start = now - timedelta(days=365*3 + 30)
        dividends = stock.dividends

        if dividends is not None and not dividends.empty:
            # Filter last 3 years
            dividends.index = pd.to_datetime(dividends.index).tz_localize(None)
            three_yr_divs = dividends[dividends.index >= pd.Timestamp(start)]

            if not three_yr_divs.empty:
                for year in [now.year - 2, now.year - 1, now.year]:
                    yr_total = three_yr_divs[three_yr_divs.index.year == year].sum()
                    if yr_total > 0:
                        result["history"][year] = round(yr_total, 2)

                # Total dividends received for user's qty
                result["total_received"] = round(three_yr_divs.sum() * qty, 2)
                result["last_dividend"] = round(float(three_yr_divs.iloc[-1]), 2)

                # Consistency badge
                years_with_div = len([y for y in result["history"].values() if y > 0])
                if years_with_div >= 3:
                    result["consistency"] = "CONSISTENT"
                    result["consistency_label"] = "Consistent Payer"
                elif years_with_div >= 1:
                    result["consistency"] = "IRREGULAR"
                    result["consistency_label"] = "Irregular Payer"
                else:
                    result["consistency"] = "NO_DIV"
                    result["consistency_label"] = "No Dividend"
            else:
                result["consistency"] = "NO_DIV"
                result["consistency_label"] = "No Dividend"
        else:
            result["consistency"] = "NO_DIV"
            result["consistency_label"] = "No Dividend"
    except:
        pass
    return result

def render_dividend_section(div_data):
    """Render the dividend card HTML."""
    badge_cls = {
        "CONSISTENT": "div-badge-consistent",
        "IRREGULAR":  "div-badge-irregular",
        "NO_DIV":     "div-badge-no-div",
    }.get(div_data["consistency"], "div-badge-no-div")

    yield_str = f"{div_data['yield_pct']:.2f}%" if div_data["yield_pct"] else "—"
    last_div_str = f"₹{div_data['last_dividend']}" if div_data["last_dividend"] else "—"
    fwd_str = f"₹{div_data['forward_annual']:.2f}/yr" if div_data["forward_annual"] else "—"
    total_str = fmt_inr(div_data["total_received"]) if div_data["total_received"] > 0 else "—"

    # Build bar chart for 3-year history
    history = div_data.get("history", {})
    max_div = max(history.values()) if history else 1
    now = datetime.now()
    bar_rows = ""
    for yr in [now.year - 2, now.year - 1, now.year]:
        val = history.get(yr, 0)
        width = int(val / max_div * 100) if max_div > 0 and val > 0 else 0
        bar_rows += f"""<div class="div-bar-row">
            <span class="div-bar-year">{yr}</span>
            <div class="div-bar-track"><div class="div-bar-fill" style="width:{width}%;"></div></div>
            <span class="div-bar-val">₹{val:.2f}</span>
        </div>"""

    if not bar_rows:
        bar_rows = '<div style="font-size:11px;color:var(--text-muted);padding:8px 0;">No dividend data available for last 3 years</div>'

    return f"""
    <div class="t-card">
        <div class="t-card-header">
            <div class="t-card-title">💰 DIVIDEND ANALYSIS — 3 YEAR HISTORY</div>
            <span class="{badge_cls}">{div_data['consistency_label'].upper()}</span>
        </div>
        <div style="padding:16px;">
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px;">
                <div>
                    <div class="stat-label">DIVIDEND YIELD</div>
                    <div class="stat-value {'green' if div_data['yield_pct'] and div_data['yield_pct']>2 else 'amber' if div_data['yield_pct'] else ''}">{yield_str}</div>
                </div>
                <div>
                    <div class="stat-label">LAST DIVIDEND</div>
                    <div class="stat-value">{last_div_str}</div>
                </div>
                <div>
                    <div class="stat-label">FWD ANNUAL</div>
                    <div class="stat-value">{fwd_str}</div>
                </div>
                <div>
                    <div class="stat-label">TOTAL RCVD (3Y)</div>
                    <div class="stat-value cyan">{total_str}</div>
                    <div class="stat-sub">based on your qty</div>
                </div>
            </div>
            <div class="sec-hdr">3-YEAR DIVIDEND PER SHARE HISTORY</div>
            {bar_rows}
        </div>
    </div>"""

# ─────────────────────────────────────────────
# TECHNICAL INDICATORS
# ─────────────────────────────────────────────
def compute_indicators(df):
    close, high, low, vol = df["Close"], df["High"], df["Low"], df["Volume"]
    df["SMA20"]  = close.rolling(20).mean()
    df["SMA50"]  = close.rolling(50).mean()
    df["SMA200"] = close.rolling(200).mean()
    delta = close.diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    rs    = gain / loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))
    ema12, ema26 = close.ewm(span=12, adjust=False).mean(), close.ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_Hist"]   = df["MACD"] - df["MACD_Signal"]
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low  - close.shift()).abs()
    df["ATR"] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1).rolling(14).mean()
    sma20, std20 = close.rolling(20).mean(), close.rolling(20).std()
    df["BB_Upper"] = sma20 + 2*std20
    df["BB_Lower"] = sma20 - 2*std20
    df["BB_Mid"]   = sma20
    df["Vol_MA20"] = vol.rolling(20).mean()
    df["Support"]       = low.rolling(60).min()
    df["StrongSupport"] = low.rolling(120).min()
    df["Resistance"]    = high.rolling(60).max()
    return df

# ─────────────────────────────────────────────
# SCORING
# ─────────────────────────────────────────────
def technical_score(df, info):
    score, reasons, warnings_list = 0, [], []
    row   = df.iloc[-1]
    price = row["Close"]
    sma200, sma50, sma20 = row["SMA200"], row["SMA50"], row["SMA20"]
    rsi, macd, macd_s     = row["RSI"], row["MACD"], row["MACD_Signal"]
    atr, support          = row["ATR"], row["Support"]

    if not np.isnan(sma200):
        if price > sma200 * 1.02:
            score += 1; reasons.append("✅ Price comfortably above 200 DMA — strong long-term uptrend")
        elif price > sma200:
            score += 0.5; reasons.append("⚠️ Price slightly above 200 DMA — weak uptrend")
        else:
            warnings_list.append("❌ Price below 200 DMA — long-term downtrend")

    if not np.isnan(sma50) and not np.isnan(sma200):
        if sma50 > sma200:
            score += 0.5; reasons.append("✅ Golden Cross: 50 DMA above 200 DMA — bullish structure")
        else:
            warnings_list.append("❌ Death Cross: 50 DMA below 200 DMA — bearish structure")

    if not np.isnan(rsi):
        if 45 <= rsi <= 65:
            score += 1; reasons.append(f"✅ RSI at {rsi:.0f} — healthy momentum zone (45–65)")
        elif rsi < 35:
            score += 0.5; reasons.append(f"⚠️ RSI oversold at {rsi:.0f} — potential bounce")
        elif rsi > 75:
            warnings_list.append(f"❌ RSI overbought at {rsi:.0f} — avoid chasing")
        else:
            score += 0.3; reasons.append(f"✅ RSI at {rsi:.0f} — neutral zone")

    if not np.isnan(macd) and not np.isnan(macd_s):
        if macd > macd_s:
            score += 1; reasons.append("✅ MACD bullish crossover — positive momentum")
        else:
            warnings_list.append("❌ MACD bearish — negative momentum")

    if not np.isnan(atr) and not np.isnan(support):
        upside   = (row["Resistance"] - price) / price
        downside = (price - support) / price
        if upside > downside * 1.5:
            score += 1; reasons.append(f"✅ Favorable risk-reward: {upside*100:.1f}% upside vs {downside*100:.1f}% downside")
        elif upside > downside:
            score += 0.5; reasons.append(f"⚠️ Moderate risk-reward: {upside*100:.1f}% upside vs {downside*100:.1f}% downside")
        else:
            warnings_list.append(f"❌ Poor risk-reward: only {upside*100:.1f}% upside vs {downside*100:.1f}% downside")

    if not np.isnan(sma20):
        if price > sma20:
            score += 0.5; reasons.append("✅ Price above 20 DMA — short-term bullish")
        else:
            warnings_list.append("❌ Price below 20 DMA — short-term bearish")

    return round(min(score, 5), 1), reasons, warnings_list


def fundamental_score(info):
    score, reasons, warnings_list = 0, [], []
    pe = safe_get(info.get("trailingPE"))
    if pe:
        if pe < 15:    score += 1.5; reasons.append(f"✅ PE {pe:.1f}x — attractively valued (<15x)")
        elif pe < 25:  score += 1.0; reasons.append(f"✅ PE {pe:.1f}x — reasonably valued (15–25x)")
        elif pe < 40:  score += 0.5; reasons.append(f"⚠️ PE {pe:.1f}x — moderately expensive (25–40x)")
        else:          warnings_list.append(f"❌ PE {pe:.1f}x — overvalued (>40x)")

    roe = safe_get(info.get("returnOnEquity"))
    if roe:
        if roe > 0.20: score += 1;   reasons.append(f"✅ ROE {pct(roe)} — excellent capital efficiency (>20%)")
        elif roe>0.12: score += 0.5; reasons.append(f"⚠️ ROE {pct(roe)} — adequate (12–20%)")
        else:          warnings_list.append(f"❌ ROE {pct(roe)} — low (<12%)")

    de = safe_get(info.get("debtToEquity"))
    if de is not None:
        if de < 30:    score += 1;   reasons.append(f"✅ D/E {de:.1f} — low leverage")
        elif de < 100: score += 0.5; reasons.append(f"⚠️ D/E {de:.1f} — moderate leverage")
        else:          warnings_list.append(f"❌ D/E {de:.1f} — high leverage")

    rg = safe_get(info.get("revenueGrowth"))
    if rg:
        if rg > 0.15:  score += 1;   reasons.append(f"✅ Revenue growth {pct(rg)} — strong")
        elif rg > 0.05:score += 0.5; reasons.append(f"⚠️ Revenue growth {pct(rg)} — moderate")
        else:          warnings_list.append(f"❌ Revenue growth {pct(rg)} — slow")

    margin = safe_get(info.get("profitMargins"))
    if margin:
        if margin > 0.15:  score += 0.5; reasons.append(f"✅ Net margin {pct(margin)} — high profitability")
        elif margin > 0.05:score += 0.3; reasons.append(f"⚠️ Net margin {pct(margin)} — thin margins")
        else:              warnings_list.append(f"❌ Net margin {pct(margin)} — very thin margins")

    return round(min(score, 5), 1), reasons, warnings_list


def fetch_screener_data(ticker):
    """Scrape Screener.in for PE, ROE, ROCE, sales growth, D/E, promoter holding."""
    R = {"pe":None,"roe":None,"roce":None,"sales_growth":None,"debt_equity":None,"promoter_pct":None,"ok":False}
    try:
        sym = ticker.replace(".NS","").replace(".BO","").replace("-","")
        for suffix in ["/consolidated/","/standalone/","/"]:
            url = f"https://www.screener.in/company/{sym}{suffix}"
            r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=8)
            if r.status_code == 200: break
        if r.status_code != 200: return R
        t = r.text
        for pat in [r'Stock P/E.*?<span[^>]*>\s*([\d.]+)',r'P/E\s*</td>.*?<td[^>]*>\s*([\d.]+)']:
            m = re.search(pat, t, re.DOTALL|re.I)
            if m:
                try: R["pe"] = float(m.group(1)); break
                except: pass
        m = re.search(r'Return on equity.*?([\d.]+)\s*%', t, re.DOTALL|re.I)
        if m:
            try: R["roe"] = float(m.group(1))/100
            except: pass
        m = re.search(r'ROCE.*?([\d.]+)\s*%', t, re.DOTALL|re.I)
        if m:
            try: R["roce"] = float(m.group(1))/100
            except: pass
        m = re.search(r'Sales growth.*?(\d[\d.]*)\s*%', t, re.DOTALL|re.I)
        if m:
            try: R["sales_growth"] = float(m.group(1))/100
            except: pass
        m = re.search(r'Promoter[s]?\s+(?:holding)?\s*[\W\s]*?([\d.]+)\s*%', t, re.I|re.DOTALL)
        if m:
            try: R["promoter_pct"] = float(m.group(1))
            except: pass
        for pat in [r'Debt to equity.*?<b>\s*([\d.]+)',r'D/E.*?([\d.]+)']:
            m = re.search(pat, t, re.DOTALL|re.I)
            if m:
                try: R["debt_equity"] = float(m.group(1)); break
                except: pass
        R["ok"] = True
    except: pass
    return R


def peer_comparison_score(ticker, info, screener):
    """Compare stock vs sector peers. Returns 0-15 pts."""
    PEERS = {
        "IT":["TCS.NS","INFY.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS"],
        "Banking":["HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","KOTAKBANK.NS","AXISBANK.NS"],
        "Energy":["RELIANCE.NS","ONGC.NS","BPCL.NS","IOC.NS"],
        "Auto":["MARUTI.NS","TATAMOTORS.NS","M&M.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS"],
        "Pharma":["SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS","DIVISLAB.NS"],
        "FMCG":["HINDUNILVR.NS","ITC.NS","NESTLEIND.NS","BRITANNIA.NS","DABUR.NS"],
        "NBFC":["BAJFINANCE.NS","BAJAJFINSV.NS","MUTHOOTFIN.NS","CHOLAFIN.NS"],
    }
    reasons, warnings_list = [], []
    yf_sector = safe_get(info.get("sector"),"")
    peers = []
    for sec, tlist in PEERS.items():
        if ticker in tlist:
            peers = [t for t in tlist if t != ticker][:4]; break
    if not peers:
        ys = yf_sector.lower()
        if any(w in ys for w in ["tech","software","it"]): peers = [t for t in PEERS["IT"] if t!=ticker][:4]
        elif any(w in ys for w in ["bank","financial"]): peers = [t for t in PEERS["Banking"] if t!=ticker][:4]
        elif any(w in ys for w in ["pharma","health"]): peers = [t for t in PEERS["Pharma"] if t!=ticker][:4]
        elif any(w in ys for w in ["auto","vehicle"]): peers = [t for t in PEERS["Auto"] if t!=ticker][:4]
        elif any(w in ys for w in ["fmcg","consumer","food"]): peers = [t for t in PEERS["FMCG"] if t!=ticker][:4]
    if not peers:
        return 8, ["No sector peers found — neutral score applied"], [], []

    peer_pes, peer_roes, peer_sgs = [], [], []
    peer_details = []
    for p in peers:
        try:
            pi = yf.Ticker(p).info
            peer_details.append({"ticker":p,"name":safe_get(pi.get("shortName"),p),
                "pe":safe_get(pi.get("trailingPE")), "roe":safe_get(pi.get("returnOnEquity")),
                "sg":safe_get(pi.get("revenueGrowth")), "r1y":safe_get(pi.get("52WeekChange"))})
            if safe_get(pi.get("trailingPE")): peer_pes.append(pi["trailingPE"])
            if safe_get(pi.get("returnOnEquity")): peer_roes.append(pi["returnOnEquity"])
            if safe_get(pi.get("revenueGrowth")): peer_sgs.append(pi["revenueGrowth"])
        except: pass

    score = 0
    pe_self  = screener.get("pe") or safe_get(info.get("trailingPE"))
    roe_self = screener.get("roe") or safe_get(info.get("returnOnEquity"))
    sg_self  = screener.get("sales_growth") or safe_get(info.get("revenueGrowth"))

    if pe_self and peer_pes:
        med = float(np.median(peer_pes))
        if pe_self < med*0.75: score+=5; reasons.append(f"P/E {pe_self:.1f}x is 25%+ below sector median {med:.1f}x — clear value vs peers")
        elif pe_self < med*0.95: score+=3; reasons.append(f"P/E {pe_self:.1f}x below sector median {med:.1f}x — modest discount")
        elif pe_self <= med*1.1: score+=2; reasons.append(f"P/E {pe_self:.1f}x in-line with sector median {med:.1f}x")
        else: warnings_list.append(f"P/E {pe_self:.1f}x premium to sector median {med:.1f}x — expensive vs peers")
    if roe_self and peer_roes:
        med = float(np.median(peer_roes))
        if roe_self > med*1.35: score+=5; reasons.append(f"ROE {pct(roe_self)} well above sector median {pct(med)} — superior capital efficiency")
        elif roe_self > med*1.1: score+=3; reasons.append(f"ROE {pct(roe_self)} above sector median {pct(med)}")
        elif roe_self >= med*0.85: score+=2; reasons.append(f"ROE {pct(roe_self)} broadly in-line with sector")
        else: warnings_list.append(f"ROE {pct(roe_self)} below sector median {pct(med)}")
    if sg_self is not None and peer_sgs:
        med = float(np.median(peer_sgs))
        if sg_self > med*1.4: score+=5; reasons.append(f"Revenue growth {pct(sg_self)} outpacing sector median {pct(med)} significantly")
        elif sg_self > med*1.1: score+=3; reasons.append(f"Revenue growth {pct(sg_self)} above sector median {pct(med)}")
        elif sg_self >= med*0.7: score+=2; reasons.append(f"Revenue growth {pct(sg_self)} broadly in-line with sector")
        else: warnings_list.append(f"Revenue growth {pct(sg_self)} lagging sector median {pct(med)}")
    if not peer_pes and not peer_roes: score = 8; reasons.append("Limited peer data — neutral assumption")
    return min(round(score,1), 15), reasons, warnings_list, peer_details


def historical_pattern_score(df, info):
    """Score multi-timeframe price history + volatility + drawdown. Returns 0-10 pts."""
    score, reasons, warnings_list = 0, [], []
    close = df["Close"]
    row = df.iloc[-1]

    def r(col):
        v = row.get(col, np.nan)
        return float(v) if not (isinstance(v,float) and np.isnan(v)) else None

    # Add return columns if not present
    if "Return1M" not in df.columns: df["Return1M"] = close.pct_change(21)
    if "Return3M" not in df.columns: df["Return3M"] = close.pct_change(63)
    if "Return6M" not in df.columns: df["Return6M"] = close.pct_change(126)
    if "Volatility" not in df.columns: df["Volatility"] = close.pct_change().rolling(60).std()*np.sqrt(252)
    row = df.iloc[-1]

    r1m = float(df["Return1M"].iloc[-1]) if not np.isnan(df["Return1M"].iloc[-1]) else None
    r3m = float(df["Return3M"].iloc[-1]) if not np.isnan(df["Return3M"].iloc[-1]) else None
    r1y = safe_get(info.get("52WeekChange"))
    vola= float(df["Volatility"].iloc[-1]) if not np.isnan(df["Volatility"].iloc[-1]) else None

    positives = sum(1 for v in [r1m,r3m,r1y] if v is not None and v>0)
    negatives = sum(1 for v in [r1m,r3m,r1y] if v is not None and v<=0)
    if positives >= 3: score+=4; reasons.append(f"All timeframes positive: 1M {(r1m or 0)*100:+.0f}% / 3M {(r3m or 0)*100:+.0f}% / 1Y {(r1y or 0)*100:+.0f}%")
    elif positives >= 2: score+=2; reasons.append(f"Mostly positive across timeframes: 1M {(r1m or 0)*100:+.0f}% / 3M {(r3m or 0)*100:+.0f}%")
    elif negatives >= 3: warnings_list.append(f"All timeframes negative: 1M {(r1m or 0)*100:+.0f}% / 3M {(r3m or 0)*100:+.0f}%")
    else: score+=1; reasons.append("Mixed multi-timeframe signals")

    if vola:
        if vola<0.25: score+=3; reasons.append(f"Low volatility {vola*100:.0f}% — stable, low-risk mover")
        elif vola<0.40: score+=2; reasons.append(f"Moderate volatility {vola*100:.0f}% — acceptable risk")
        elif vola<0.60: score+=1; reasons.append(f"High volatility {vola*100:.0f}% — size carefully")
        else: warnings_list.append(f"Very high volatility {vola*100:.0f}% — speculative profile")

    if len(df)>=252:
        peak = close.rolling(252).max().iloc[-1]
        dd   = (row["Close"]-peak)/peak
        if dd>-0.05: score+=3; reasons.append(f"Near 52w high ({dd*100:.1f}%) — strong trend")
        elif dd>-0.15: score+=2; reasons.append(f"{dd*100:.1f}% from 52w high — healthy pullback")
        elif dd>-0.30: score+=1; reasons.append(f"{dd*100:.1f}% from 52w high — moderate correction")
        else: warnings_list.append(f"{dd*100:.1f}% from 52w high — deep drawdown risk")

    return min(round(score,1),10), reasons, warnings_list


def compute_projection(info, tech_s, fund_s, current_price):
    base_cagr = 10
    pe    = safe_get(info.get("trailingPE"), 25)
    roe   = safe_get(info.get("returnOnEquity"), 0.10)
    rev_g = safe_get(info.get("revenueGrowth"), 0.08)
    if pe < 15:    base_cagr += 4
    elif pe < 25:  base_cagr += 2
    elif pe > 40:  base_cagr -= 4
    if roe > 0.20: base_cagr += 3
    elif roe>0.12: base_cagr += 1
    if rev_g > 0.15: base_cagr += 3
    elif rev_g > 0.05: base_cagr += 1
    elif rev_g < 0:    base_cagr -= 3
    base_cagr += (tech_s - 2.5) * 1.5 + (fund_s - 2.5) * 1.5
    cagr = max(2, min(35, round(base_cagr, 1)))
    proj_3y = current_price * ((1 + cagr/100)**3)
    return cagr, proj_3y


def compute_buy_plan(df, info):
    row   = df.iloc[-1]
    price = float(row["Close"])
    atr   = float(row["ATR"]) if not np.isnan(row["ATR"]) else price * 0.02
    return {
        "current":        round(price, 2),
        "support":        round(float(row["Support"]), 2),
        "strong_support": round(float(row["StrongSupport"]), 2),
        "stop_loss":      round(price - 2*atr, 2),
        "atr":            round(atr, 2),
        "resistance":     round(float(row["Resistance"]), 2),
    }

# ─────────────────────────────────────────────
# SENTIMENT & NEWS
# ─────────────────────────────────────────────
def analyze_sentiment(headlines):
    if not headlines: return 0, "Neutral"
    total = 0
    for h in headlines:
        hl = h.lower()
        total += sum(1 for w in POSITIVE_WORDS if w in hl) - sum(1 for w in NEGATIVE_WORDS if w in hl)
    avg = total / len(headlines)
    if avg >= 1.5:    return avg, "Strongly Positive"
    elif avg >= 0.5:  return avg, "Positive"
    elif avg >= -0.4: return avg, "Neutral"
    elif avg >= -1.5: return avg, "Negative"
    else:             return avg, "Strongly Negative"

def fetch_news(ticker_symbol, company_name):
    headlines = []
    try:
        url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker_symbol}&region=IN&lang=en-IN"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', resp.text)
            titles = [t for t in titles if "Yahoo" not in t and len(t) > 15]
            headlines = titles[:8]
    except: pass
    if not headlines:
        headlines = [
            f"{company_name or ticker_symbol} announces quarterly results",
            f"Analysts review {company_name or ticker_symbol} outlook",
            f"Market update: {ticker_symbol} performance review"
        ]
    return headlines

def generate_commentary(info, df, tech_s, fund_s, total_score, cagr, bp, sent_label):
    price  = df["Close"].iloc[-1]
    name   = safe_get(info.get("longName"), info.get("shortName", "This company"))
    sector = safe_get(info.get("sector"), "N/A")
    pe, roe = safe_get(info.get("trailingPE")), safe_get(info.get("returnOnEquity"))
    decision = "BUY" if total_score >= 8 else ("HOLD" if total_score >= 6 else "AVOID")
    lines = []
    if decision == "BUY":
        lines.append(f"**{name}** presents a compelling investment case at current levels, scoring {total_score}/10 — firmly in the accumulation zone.")
    elif decision == "HOLD":
        lines.append(f"**{name}** shows mixed signals with a score of {total_score}/10. Patient investors can hold; fresh entry should wait for a better setup.")
    else:
        lines.append(f"**{name}** shows weakness across multiple dimensions with a score of {total_score}/10. Capital preservation recommended.")
    rsi = df["RSI"].iloc[-1]
    macd_bull = df["MACD"].iloc[-1] > df["MACD_Signal"].iloc[-1]
    above_200 = price > df["SMA200"].iloc[-1]
    lines.append(f"**Technically**, the stock is {'above' if above_200 else 'below'} its 200 DMA, RSI at {rsi:.0f} ({'healthy' if 40<rsi<70 else 'extended' if rsi>70 else 'oversold'}), MACD {'bullish' if macd_bull else 'bearish'}. Technicals: {tech_s}/5.")
    lines.append(f"**Fundamentally**, {sector} sector with {'PE of '+str(round(pe,1)) if pe else 'PE N/A'}, ROE {pct(roe) if roe else 'N/A'}. Fundamentals: {fund_s}/5.")
    lines.append(f"**3-Year Projection**: Expected blended CAGR ~{cagr}%, implying ₹{bp['current']*((1+cagr/100)**3):.0f} target by {datetime.now().year+3}.")
    lines.append(f"**Sentiment**: {sent_label} based on recent news flow.")
    lines.append(f"**Risk**: Stop loss ₹{bp['stop_loss']} (2× ATR). Staggered entry: 40% at ₹{bp['current']}, 30% at ₹{bp['support']}, 30% at ₹{bp['strong_support']}.")
    return "\n\n".join(lines)

# ─────────────────────────────────────────────
# CHART
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────
# FIBONACCI RETRACEMENT
# ─────────────────────────────────────────────────────────────────
def compute_fibonacci(df):
    """Compute Fibonacci retracement levels from swing high/low in df."""
    high = float(df["High"].max())
    low  = float(df["Low"].min())
    diff = high - low
    return {
        "f0":    high,
        "f236":  high - 0.236 * diff,
        "f382":  high - 0.382 * diff,
        "f500":  high - 0.500 * diff,
        "f618":  high - 0.618 * diff,
        "f786":  high - 0.786 * diff,
        "f1000": low,
        "high":  high,
        "low":   low,
    }

# ─────────────────────────────────────────────────────────────────
# DYNAMIC SUPPORT / RESISTANCE  (pivot-based)
# ─────────────────────────────────────────────────────────────────
def compute_sr_levels(df, n_levels=3):
    """
    Find significant S/R levels by clustering pivot highs/lows.
    Returns dict with lists of support and resistance price levels.
    """
    highs = df["High"].values
    lows  = df["Low"].values
    close = df["Close"].values
    price = close[-1]

    pivot_highs, pivot_lows = [], []
    window = 5
    for i in range(window, len(df) - window):
        if highs[i] == max(highs[i-window:i+window+1]):
            pivot_highs.append(highs[i])
        if lows[i] == min(lows[i-window:i+window+1]):
            pivot_lows.append(lows[i])

    def cluster(levels, tol=0.015):
        if not levels: return []
        levels = sorted(levels)
        clusters = []
        group = [levels[0]]
        for v in levels[1:]:
            if (v - group[-1]) / group[-1] < tol:
                group.append(v)
            else:
                clusters.append(sum(group)/len(group))
                group = [v]
        clusters.append(sum(group)/len(group))
        return clusters

    all_sr = cluster(pivot_highs + pivot_lows)
    supports   = sorted([v for v in all_sr if v < price * 0.999], reverse=True)[:n_levels]
    resistances= sorted([v for v in all_sr if v > price * 1.001])[:n_levels]
    return {"supports": supports, "resistances": resistances}

# ─────────────────────────────────────────────────────────────────
# ENHANCED CHART  (Fibonacci + dynamic S/R + term-aware MAs)
# ─────────────────────────────────────────────────────────────────
def build_chart_enhanced(df, bp, show_fib=True, show_sr=True, term_view="All Indicators"):
    fig = make_subplots(
        rows=3, cols=1, row_heights=[0.60, 0.20, 0.20],
        shared_xaxes=True, vertical_spacing=0.03,
        subplot_titles=("", "Volume", "RSI (14)")
    )

    # ── Candlestick ───────────────────────────────────────────
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        name="Price",
        increasing_line_color="#00c87a", decreasing_line_color="#ff3b5c",
        increasing_fillcolor="#00c87a",  decreasing_fillcolor="#ff3b5c",
    ), row=1, col=1)

    # ── Moving averages by term ───────────────────────────────
    if "Short" in term_view or "All" in term_view:
        fig.add_trace(go.Scatter(x=df.index, y=df["SMA20"],
            name="20 DMA", line=dict(color="#f59e0b", width=1.5, dash="dot")), row=1, col=1)
    if "Mid" in term_view or "All" in term_view:
        fig.add_trace(go.Scatter(x=df.index, y=df["SMA50"],
            name="50 DMA", line=dict(color="#ffb000", width=1.5)), row=1, col=1)
    if "Long" in term_view or "All" in term_view:
        fig.add_trace(go.Scatter(x=df.index, y=df["SMA200"],
            name="200 DMA", line=dict(color="#0090ff", width=2)), row=1, col=1)

    # ── Bollinger Bands ───────────────────────────────────────
    if "All" in term_view or "Short" in term_view:
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_Upper"],
            name="BB Upper", line=dict(color="rgba(128,128,128,0.6)", width=1, dash="dash"), opacity=0.6), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_Lower"],
            name="BB Lower", line=dict(color="rgba(128,128,128,0.6)", width=1, dash="dash"), opacity=0.6,
            fill="tonexty", fillcolor="rgba(61,82,104,0.05)"), row=1, col=1)

    # ── Fibonacci levels ─────────────────────────────────────
    if show_fib:
        fib = compute_fibonacci(df)
        fib_colors = {
            "f0":   ("#c9a84c", "0% — Swing High"),
            "f236": ("#a78bfa", "23.6%"),
            "f382": ("#60a5fa", "38.2%"),
            "f500": ("#34d399", "50.0%"),
            "f618": ("#f97316", "61.8% — Golden"),
            "f786": ("#f43f5e", "78.6%"),
            "f1000":("#6b7280", "100% — Swing Low"),
        }
        for key, (clr, lbl) in fib_colors.items():
            val = fib[key]
            fig.add_hline(
                y=val, line_color=clr, line_dash="dot", line_width=1,
                annotation_text=f"Fib {lbl} ₹{val:,.0f}",
                annotation_font_color=clr, annotation_font_size=9,
                annotation_position="right",
                row=1, col=1
            )

    # ── Dynamic Support / Resistance ─────────────────────────
    if show_sr:
        sr = compute_sr_levels(df)
        for i, sv in enumerate(sr["supports"]):
            fig.add_hline(
                y=sv, line_color="#00c87a", line_dash="dashdot", line_width=1.2,
                annotation_text=f"S{i+1} ₹{sv:,.0f}",
                annotation_font_color="#00c87a", annotation_font_size=9,
                annotation_position="left",
                row=1, col=1
            )
        for i, rv in enumerate(sr["resistances"]):
            fig.add_hline(
                y=rv, line_color="#ff3b5c", line_dash="dashdot", line_width=1.2,
                annotation_text=f"R{i+1} ₹{rv:,.0f}",
                annotation_font_color="#ff3b5c", annotation_font_size=9,
                annotation_position="left",
                row=1, col=1
            )

    # ── Buy plan levels ───────────────────────────────────────
    fig.add_hline(y=bp["support"],   line_color="#ffb000", line_dash="dot",
        annotation_text=f"Support ₹{bp['support']:,.0f}",
        annotation_font_color="#ffb000", annotation_font_size=9, row=1, col=1)
    fig.add_hline(y=bp["stop_loss"], line_color="#ff3b5c", line_dash="dashdot",
        annotation_text=f"Stop Loss ₹{bp['stop_loss']:,.0f}",
        annotation_font_color="#ff3b5c", annotation_font_size=9, row=1, col=1)

    # ── Volume ────────────────────────────────────────────────
    bar_colors = ["#00c87a" if c >= o else "#ff3b5c"
                  for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"],
        name="Volume", marker_color=bar_colors, opacity=0.6), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["Vol_MA20"],
        name="Vol MA20", line=dict(color="#0090ff", width=1)), row=2, col=1)

    # ── RSI ───────────────────────────────────────────────────
    fig.add_trace(go.Scatter(x=df.index, y=df["RSI"],
        name="RSI", line=dict(color="#a855f7", width=1.5)), row=3, col=1)
    fig.add_hline(y=70, line_color="#ff3b5c", line_dash="dot", row=3, col=1)
    fig.add_hline(y=30, line_color="#00c87a", line_dash="dot", row=3, col=1)
    fig.add_hrect(y0=40, y1=60, fillcolor="rgba(0,200,122,0.04)",
        line_width=0, row=3, col=1)

    # ── MACD histogram (replace second subplot if long term) ──
    if "Long" in term_view or "All" in term_view:
        pass  # keep volume as row2

    # ── Layout ───────────────────────────────────────────────
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#7a90a8", family="Fira Code"),
        showlegend=True,
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1e2d3d",
                    borderwidth=1, font=dict(size=10),
                    orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0),
        xaxis_rangeslider_visible=False,
        height=680,
        margin=dict(l=10, r=120, t=40, b=10),
    )
    for i in range(1, 4):
        fig.update_xaxes(gridcolor="rgba(128,128,128,0.15)", showgrid=True, zeroline=False,
                         row=i, col=1, color="rgba(128,128,128,0.6)")
        fig.update_yaxes(gridcolor="rgba(128,128,128,0.15)", showgrid=True, zeroline=False,
                         row=i, col=1, color="rgba(128,128,128,0.6)")
    return fig

def build_chart(df, bp):
    fig = make_subplots(rows=3, cols=1, row_heights=[0.6, 0.2, 0.2],
                        shared_xaxes=True, vertical_spacing=0.03)
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        name="Price", increasing_line_color="#00c87a", decreasing_line_color="#ff3b5c",
        increasing_fillcolor="#00c87a", decreasing_fillcolor="#ff3b5c"
    ), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["SMA50"],  name="50 DMA",  line=dict(color="#ffb000", width=1.5, dash="dot")), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["SMA200"], name="200 DMA", line=dict(color="#0090ff", width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["BB_Upper"], name="BB Upper", line=dict(color="rgba(128,128,128,0.6)", width=1, dash="dash"), opacity=0.6), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["BB_Lower"], name="BB Lower", line=dict(color="rgba(128,128,128,0.6)", width=1, dash="dash"), opacity=0.6, fill="tonexty", fillcolor="rgba(61,82,104,0.05)"), row=1, col=1)
    fig.add_hline(y=bp["support"],   line_color="#ffb000", line_dash="dot",    annotation_text=f"Support ₹{bp['support']}", annotation_font_color="#ffb000", row=1, col=1)
    fig.add_hline(y=bp["stop_loss"], line_color="#ff3b5c", line_dash="dashdot", annotation_text=f"Stop Loss ₹{bp['stop_loss']}", annotation_font_color="#ff3b5c", row=1, col=1)
    bar_colors = ["#00c87a" if c >= o else "#ff3b5c" for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volume", marker_color=bar_colors, opacity=0.6), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["Vol_MA20"], name="Vol MA20", line=dict(color="#0090ff", width=1)), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI", line=dict(color="#a855f7", width=1.5)), row=3, col=1)
    fig.add_hline(y=70, line_color="#ff3b5c", line_dash="dot", row=3, col=1)
    fig.add_hline(y=30, line_color="#00c87a", line_dash="dot", row=3, col=1)
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#7a90a8", family="Fira Code"),
        showlegend=True,
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1e2d3d", borderwidth=1, font=dict(size=10)),
        xaxis_rangeslider_visible=False, height=640,
        margin=dict(l=10, r=10, t=30, b=10)
    )
    for i in range(1, 4):
        fig.update_xaxes(gridcolor="rgba(128,128,128,0.15)", showgrid=True, zeroline=False, row=i, col=1, color="rgba(128,128,128,0.6)")
        fig.update_yaxes(gridcolor="rgba(128,128,128,0.15)", showgrid=True, zeroline=False, row=i, col=1, color="rgba(128,128,128,0.6)")
    return fig

def build_stock_chart(df, buy_price, ticker):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], name="Price", line=dict(color="#0090ff", width=2)))
    fig.add_trace(go.Scatter(x=df.index, y=df["SMA50"],  name="50 DMA",  line=dict(color="#ffb000", width=1, dash="dot")))
    fig.add_trace(go.Scatter(x=df.index, y=df["SMA200"], name="200 DMA", line=dict(color="#00c87a", width=1.5)))
    if buy_price > 0:
        fig.add_hline(y=buy_price, line_color="#a855f7", line_dash="dash", annotation_text=f"Buy ₹{buy_price:.0f}", annotation_font_color="#a855f7")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#7a90a8", family="Fira Code"), height=280,
        margin=dict(l=5, r=5, t=10, b=5), showlegend=True,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
        xaxis=dict(gridcolor="rgba(128,128,128,0.15)", color="rgba(128,128,128,0.6)"),
        yaxis=dict(gridcolor="rgba(128,128,128,0.15)", color="rgba(128,128,128,0.6)")
    )
    return fig

# ─────────────────────────────────────────────
# PORTFOLIO PARSING
# ─────────────────────────────────────────────
KNOWN_MAP = {
    "RELIANCE":"RELIANCE.NS","TCS":"TCS.NS","HDFC BANK":"HDFCBANK.NS",
    "HDFCBANK":"HDFCBANK.NS","INFOSYS":"INFY.NS","INFY":"INFY.NS",
    "WIPRO":"WIPRO.NS","ICICI BANK":"ICICIBANK.NS","SBI":"SBIN.NS",
    "BAJAJ FINANCE":"BAJFINANCE.NS","MARUTI":"MARUTI.NS",
    "TATA MOTORS":"TATAMOTORS.NS","ASIAN PAINTS":"ASIANPAINT.NS",
    "KOTAK":"KOTAKBANK.NS","AXIS BANK":"AXISBANK.NS",
    "HINDUSTAN UNILEVER":"HINDUNILVR.NS","HUL":"HINDUNILVR.NS",
    "NESTLE":"NESTLEIND.NS","ITC":"ITC.NS","BHARTI AIRTEL":"BHARTIARTL.NS",
    "ADANI PORTS":"ADANIPORTS.NS","TITAN":"TITAN.NS","ULTRACEMCO":"ULTRACEMCO.NS",
    "TATA STEEL":"TATASTEEL.NS","ONGC":"ONGC.NS","NTPC":"NTPC.NS",
    "POWERGRID":"POWERGRID.NS","L&T":"LT.NS","COAL INDIA":"COALINDIA.NS",
    "SUN PHARMA":"SUNPHARMA.NS","DIVIS":"DIVISLAB.NS","CIPLA":"CIPLA.NS",
    "DR REDDYS":"DRREDDY.NS","APOLLO HOSPITALS":"APOLLOHOSP.NS",
    "BAJAJ AUTO":"BAJAJ-AUTO.NS","HERO MOTOCORP":"HEROMOTOCO.NS",
    "EICHER MOTORS":"EICHERMOT.NS","TATA CONSUMER":"TATACONSUM.NS",
    "HINDALCO":"HINDALCO.NS","JSW STEEL":"JSWSTEEL.NS",
    "GRASIM":"GRASIM.NS","INDUSIND BANK":"INDUSINDBK.NS",
    "TECH MAHINDRA":"TECHM.NS","HAVELLS":"HAVELLS.NS",
    "PIDILITE":"PIDILITIND.NS","ZOMATO":"ZOMATO.NS","PAYTM":"PAYTM.NS",
    "HCLTECH":"HCLTECH.NS","LTI":"LTIM.NS","MPHASIS":"MPHASIS.NS",
    "TATA POWER":"TATAPOWER.NS","ADANI GREEN":"ADANIGREEN.NS",
    "VEDANTA":"VEDL.NS","SAIL":"SAIL.NS","IRCTC":"IRCTC.NS",
}

def resolve_ticker(name):
    if not name: return None
    nu = name.upper().strip()
    for key, ticker in KNOWN_MAP.items():
        if key in nu: return ticker
    clean = re.sub(r'[^A-Z0-9]', '', re.sub(r'\b(LTD|LIMITED|PVT|PRIVATE|INDIA|INDUSTRIES|CORP|CORPORATION|CO|COMPANY)\b', '', nu).strip())
    return f"{clean}.NS" if clean else None

def parse_master_template(file_bytes, fname):
    """
    Robust parser for master template and common Indian broker formats.
    Handles: formula-only rows, None stock names, comma-formatted numbers,
    ₹ symbols, multi-row headers, blank rows.

    Template columns:
    Stock Name | ISIN | Total Qty | Avg Price | LTP | Invested Value | Market Value | P&L | P&L %
    """
    import traceback as _tb

    def _safe_float(series_row, col):
        """Extract float from pandas Series — handles NaN, strings with commas/₹."""
        if col is None:
            return 0.0
        try:
            val = series_row[col]
            if val is None or (isinstance(val, float) and pd.isna(val)):
                return 0.0
            cleaned = str(val).replace(',', '').replace('₹', '').replace(' ', '').replace('(', '-').replace(')', '')
            return float(cleaned)
        except:
            return 0.0

    def _safe_str(series_row, col):
        if col is None:
            return ""
        try:
            val = series_row[col]
            if val is None or (isinstance(val, float) and pd.isna(val)):
                return ""
            return str(val).strip()
        except:
            return ""

    try:
        fname_lower = fname.lower()
        df_raw = None

        if fname_lower.endswith(".csv"):
            for enc in ["utf-8", "latin-1", "cp1252"]:
                try:
                    df_raw = pd.read_csv(io.BytesIO(file_bytes), encoding=enc)
                    break
                except:
                    continue
        else:
            # Try header at rows 0–3: some broker files have a title row on top
            for hrow in [0, 1, 2, 3]:
                try:
                    df_try = pd.read_excel(io.BytesIO(file_bytes), header=hrow)
                    cols_lower = " ".join(str(c).lower() for c in df_try.columns)
                    if any(kw in cols_lower for kw in ["stock","name","qty","quantity","company","instrument","isin","scrip"]):
                        df_raw = df_try
                        break
                except:
                    continue
            if df_raw is None:
                df_raw = pd.read_excel(io.BytesIO(file_bytes))

        if df_raw is None:
            return None, "File could not be read. Please ensure it is a valid .xlsx or .csv file."

        # Normalise column names
        df_raw.columns = [str(c).strip() for c in df_raw.columns]

        # Drop completely empty rows
        df_raw = df_raw.dropna(how="all").reset_index(drop=True)

        # Values in the name column that indicate junk/header/total rows
        SKIP = {
            "stock name", "total", "grand total", "nan", "none",
            "company", "company name", "instrument", "scrip", "scrip name",
            "stock", "symbol", "name", "#", "sl.no", "sr.no", "s.no",
            "holdings", "holding", "portfolio", ""
        }

        def find_col(keywords):
            for kw in keywords:
                for c in df_raw.columns:
                    if kw.lower() in str(c).lower():
                        return c
            return None

        col_name = find_col(["stock name", "company name", "instrument", "scrip name",
                              "stock", "company", "name", "symbol"])
        col_isin = find_col(["isin"])
        col_qty  = find_col(["total qty", "net qty", "qty", "quantity", "shares",
                              "units", "no. of shares", "no of shares"])
        col_avg  = find_col(["avg price", "average price", "avg buy", "cost price",
                              "purchase price", "avg cost", "average cost", "avg"])
        col_ltp  = find_col(["ltp", "cmp", "last price", "market price",
                              "current price", "close price", "rate"])
        col_inv  = find_col(["invested value", "invested amount", "cost value",
                              "book value", "purchase value", "total cost", "amount invested"])
        col_mkt  = find_col(["market value", "current value", "present value",
                              "ltp value", "mkt value", "market val"])
        col_pnl  = find_col(["p&l", "pnl", "unrealised", "profit loss",
                              "profit & loss", "gain/loss", "gain loss", "p / l"])

        if not col_name:
            return None, (
                "Could not find a 'Stock Name' or 'Company' column.\n\n"
                f"Columns found in your file: {list(df_raw.columns)}\n\n"
                "Please fill in your stock names in the 'Stock Name' column and re-upload."
            )

        portfolio = []
        skipped   = 0

        for _, row in df_raw.iterrows():
            name = _safe_str(row, col_name)

            # Skip blank names, formula residue, totals, headers
            if not name or name.lower() in SKIP:
                skipped += 1
                continue
            # Skip rows that still look like column headers repeated mid-sheet
            if name.lower() in [str(c).lower().strip() for c in df_raw.columns]:
                skipped += 1
                continue

            qty = _safe_float(row, col_qty)
            avg = _safe_float(row, col_avg)
            ltp = _safe_float(row, col_ltp)
            inv = _safe_float(row, col_inv) or round(qty * avg, 2)
            mkt = _safe_float(row, col_mkt) or (round(ltp * qty, 2) if ltp else 0.0)
            pnl = _safe_float(row, col_pnl) or round(mkt - inv, 2)

            # A row with no qty AND no avg AND no invested value is useless
            if qty == 0.0 and avg == 0.0 and inv == 0.0:
                skipped += 1
                continue

            ticker = resolve_ticker(name) or (re.sub(r'[^A-Z0-9]', '', name.upper()) + ".NS")

            qty_int = max(1, int(round(qty))) if qty > 0 else 1

            portfolio.append({
                "ticker":       ticker,
                "name":         name,
                "qty":          qty_int,
                "buy_price":    round(avg, 2),
                "invested":     round(inv, 2),
                "market_value": round(mkt, 2),
                "pnl_broker":   round(pnl, 2),
                "ltp":          round(ltp, 2),
                "sector":       "N/A",
                "market_cap_type": "N/A",
            })

        if not portfolio:
            hint = (
                "The file was read successfully but no stock rows were found.\n\n"
                f"• Columns detected: {list(df_raw.columns)}\n"
                f"• Total rows read: {len(df_raw)}  |  Rows skipped (blank/header): {skipped}\n\n"
                "Most likely cause: The 'Stock Name' column is empty — "
                "please fill in your stock names and Qty / Avg Price, then re-upload."
            )
            return None, hint

        return portfolio, None

    except Exception as e:
        return None, (
            f"Parse error: {str(e)[:300]}\n\n"
            f"Traceback:\n{_tb.format_exc()[-500:]}"
        )

# ─────────────────────────────────────────────
# PORTFOLIO ANALYSIS HELPERS
# ─────────────────────────────────────────────
def holding_decision(r):
    sc = r.get("score_100", 50)
    action = "BUY" if sc >= 70 else ("HOLD" if sc >= 50 else "AVOID")
    color  = {"BUY":"#00c87a","HOLD":"#ffb000","AVOID":"#ff3b5c"}.get(action,"#ffb000")
    return {"action": action, "color": color, "score_100": sc}

def concentration_risk(results):
    alerts = []
    total_val = sum(r.get("market_value", r.get("invested",0)) for r in results)
    if not total_val: return alerts
    sector_map = {}
    for r in results:
        sec = r.get("sector","N/A")
        val = r.get("market_value", r.get("invested",0))
        sector_map[sec] = sector_map.get(sec,0) + val
    for r in results:
        alloc = r.get("market_value", r.get("invested",0)) / total_val * 100
        if alloc > 20:
            alerts.append({"msg": f"{r['name']} is {alloc:.1f}% of portfolio — consider trimming"})
    for sec, val in sector_map.items():
        alloc = val / total_val * 100
        if alloc > 35:
            alerts.append({"msg": f"{sec} sector is {alloc:.1f}% of portfolio — heavily concentrated"})
    return alerts

def analyze_single_portfolio_stock(stock_item):
    ticker    = stock_item.get("ticker","")
    name      = stock_item.get("name", ticker)
    buy_price = stock_item.get("buy_price", 0)
    qty       = stock_item.get("qty", 0)
    invested  = stock_item.get("invested", buy_price * qty)

    result = {
        "ticker":ticker,"name":name,"qty":qty,"buy_price":buy_price,"invested":invested,
        "market_value":stock_item.get("market_value",0),"pnl_broker":stock_item.get("pnl_broker",0),
        "sector":"N/A","market_cap_type":"N/A",
        "score_10":5,"score_100":50,"tech_s":2.5,"fund_s":2.5,
        "tech_reasons":[],"tech_warnings":[],"fund_reasons":[],"fund_warnings":[],
        "cmp":0,"pnl_pct":0,"pnl_abs":0,"decision":"HOLD","decision_color":"#ffb000",
        "pe":None,"roe":None,"de":None,"rev_growth":None,
        "df":None,"info":{},"error":None,"cagr":10,"bp":{},
        "headlines":[],"sent_label":"Neutral","div_data":None,
    }
    try:
        stock  = yf.Ticker(ticker)
        df_raw = stock.history(period="2y")
        info   = stock.info

        if df_raw.empty:
            result["error"] = f"No data for {ticker}"
            return result

        df = compute_indicators(df_raw.copy())
        tech_s, tech_r, tech_w = technical_score(df, info)
        fund_s, fund_r, fund_w = fundamental_score(info)
        score_10  = min(round(tech_s + fund_s), 10)
        score_100 = score_10 * 10

        cmp     = float(df["Close"].iloc[-1])
        pnl_abs = (cmp - buy_price) * qty if buy_price > 0 else 0
        pnl_pct = ((cmp - buy_price) / buy_price * 100) if buy_price > 0 else 0
        decision = "BUY" if score_100 >= 70 else ("HOLD" if score_100 >= 50 else "AVOID")

        cagr, _ = compute_projection(info, tech_s, fund_s, cmp)
        bp      = compute_buy_plan(df, info)
        headlines = fetch_news(ticker, safe_get(info.get("longName"), name))
        _, sent_label = analyze_sentiment(headlines)

        # Fetch dividend data
        div_data = fetch_dividend_data(ticker, qty)

        result.update({
            "sector":       safe_get(info.get("sector"),"N/A"),
            "market_cap_type": "Large Cap" if safe_get(info.get("marketCap"),0)>2e10 else "Mid Cap" if safe_get(info.get("marketCap"),0)>5e9 else "Small Cap",
            "score_10":score_10,"score_100":score_100,
            "tech_s":tech_s,"fund_s":fund_s,
            "tech_reasons":tech_r,"tech_warnings":tech_w,
            "fund_reasons":fund_r,"fund_warnings":fund_w,
            "cmp":cmp,"pnl_pct":pnl_pct,"pnl_abs":pnl_abs,
            "market_value":cmp*qty,"decision":decision,
            "decision_color":{"BUY":"#00c87a","HOLD":"#ffb000","AVOID":"#ff3b5c"}.get(decision,"#ffb000"),
            "pe":safe_get(info.get("trailingPE")),
            "roe":safe_get(info.get("returnOnEquity")),
            "de":safe_get(info.get("debtToEquity")),
            "rev_growth":safe_get(info.get("revenueGrowth")),
            "df":df,"info":info,"cagr":cagr,"bp":bp,
            "headlines":headlines,"sent_label":sent_label,
            "div_data":div_data,
        })
    except Exception as e:
        result["error"] = str(e)[:200]
    return result

def generate_excel_report(results):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        rows = []
        for r in results:
            div = r.get("div_data") or {}
            rows.append({
                "Company":r["name"],"Ticker":r["ticker"],
                "Sector":r.get("sector","N/A"),"Qty":r["qty"],
                "Buy Price":r["buy_price"],"CMP":round(r.get("cmp",0),2),
                "Invested":round(r["invested"],0),"Market Value":round(r.get("market_value",0),0),
                "P&L (₹)":round(r.get("pnl_abs",0),0),"P&L (%)":round(r.get("pnl_pct",0),1),
                "Score":r.get("score_100",0),"Decision":r.get("decision","HOLD"),
                "PE":r.get("pe"),"ROE":pct(r.get("roe")),
                "D/E":r.get("de"),
                "Div Yield %":f"{div.get('yield_pct'):.2f}%" if div.get("yield_pct") else "—",
                "Div Consistency":div.get("consistency_label","—"),
                "Total Div Rcvd (3Y)":div.get("total_received",0),
            })
        pd.DataFrame(rows).to_excel(writer, index=False, sheet_name="Portfolio Analysis")
    output.seek(0)
    return output.getvalue()

# ─────────────────────────────────────────────
# NAV BAR
# ─────────────────────────────────────────────
def render_navbar():
    portfolios = st.session_state.get("portfolios", [])

    # ── Top bar: brand + theme + quick stats ──────────────────
    st.markdown(f"""
    <div style="background:var(--bg-card);border-bottom:1px solid var(--border);
        padding:0 24px;height:56px;display:flex;align-items:center;gap:20px;">
        <div style="font-size:18px;font-weight:700;color:var(--text-primary);
            letter-spacing:0.5px;flex-shrink:0;">
            ◈ EQUITEX PRO
        </div>
        <div style="flex:1;"></div>
        <div style="font-size:11px;color:var(--text-muted);">
            {len(portfolios)} portfolio{'s' if len(portfolios)!=1 else ''} &nbsp;·&nbsp;
            {sum(len(pf.get('stocks',[])) for pf in portfolios)} stocks
        </div>
    </div>""", unsafe_allow_html=True)

    # ── Main navigation + actions row ─────────────────────────
    col_nav, col_actions = st.columns([6, 2])
    with col_nav:
        page = st.radio(
            "nav",
            ["🏠  Dashboard", "📈  Portfolio", "🏦  Wealth", "📊  Budget", "🤖  AI Advisor"],
            horizontal=True, label_visibility="collapsed", key="main_nav"
        )
    with col_actions:
        if st.button("＋ Add Portfolio", key="nav_add_pf", use_container_width=True, type="primary"):
            st.session_state.show_add_portfolio = True
            st.rerun()

    st.markdown('<div style="border-bottom:1px solid var(--border);margin:0 0 20px 0;"></div>', unsafe_allow_html=True)

    # ── Sidebar ───────────────────────────────────────────────
    with st.sidebar:
        st.markdown(f"""
        <div style="padding:16px 12px 14px;border-bottom:1px solid var(--border);">
            <div style="font-size:16px;font-weight:700;color:var(--text-primary);
                letter-spacing:0.5px;margin-bottom:2px;">◈ EQUITEX PRO</div>
            <div style="font-size:10px;color:var(--text-muted);letter-spacing:1px;">
                INDIAN EQUITY TERMINAL</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("""<div style="font-size:10px;font-weight:600;letter-spacing:1.5px;
            color:var(--text-muted);padding:14px 12px 6px;text-transform:uppercase;">
            My Portfolios</div>""", unsafe_allow_html=True)

        active_idx = st.session_state.get("active_portfolio_idx", 0)
        if portfolios:
            pf_names = [pf["name"] for pf in portfolios]
            safe_idx = min(active_idx, len(pf_names)-1)
            selected = st.radio("pf_select", pf_names, index=safe_idx,
                                label_visibility="collapsed", key="sidebar_pf_radio")
            new_idx = pf_names.index(selected)
            if new_idx != active_idx:
                st.session_state.active_portfolio_idx = new_idx
                st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)
            for i, pf in enumerate(portfolios):
                c    = pf.get("color", portfolio_color(i))
                p    = pf.get("pnl_pct", 0)
                pstr = f"+{p:.1f}%" if p >= 0 else f"{p:.1f}%"
                pcol = "var(--accent-green)" if p >= 0 else "var(--accent-red)"
                nstk = len(pf.get("stocks", []))
                st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;
                    padding:4px 12px;margin-bottom:2px;">
                    <div style="width:7px;height:7px;border-radius:50%;
                        background:{c};flex-shrink:0;"></div>
                    <span style="color:var(--text-secondary);flex:1;font-size:12px;">
                        {pf['name'][:16]}</span>
                    <span style="font-size:10px;color:var(--text-muted);">{nstk}stk</span>
                    <span style="font-size:11px;font-weight:600;color:{pcol};">{pstr}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div style="font-size:12px;color:var(--text-muted);
                padding:8px 12px;">No portfolios yet.<br>Click ＋ Add Portfolio to start.</div>""",
                unsafe_allow_html=True)

    return page

# ─────────────────────────────────────────────
# ADD PORTFOLIO MODAL
# ─────────────────────────────────────────────
def render_add_portfolio_modal():
    st.markdown("""
    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:6px;padding:20px 24px;margin-bottom:20px;">
        <div style="font-family:'Fraunces',serif;font-size:22px;font-weight:600;color:var(--accent-gold);margin-bottom:4px;">ADD NEW PORTFOLIO</div>
        <div style="font-family:var(--font-mono,'Fira Code',monospace);font-size:10px;color:var(--text-muted);letter-spacing:0.5px;">
            Upload your master template Excel or create manually. Supports the standard template format.
        </div>
    </div>""", unsafe_allow_html=True)

    c1, c2 = st.columns([3,1])
    with c1:
        pf_name = st.text_input("Portfolio Name *", placeholder="e.g. Long Term Growth, Retirement Fund...", key="new_pf_name")
    with c2:
        color_idx = st.selectbox("Color Tag", range(len(PORTFOLIO_COLORS)),
            format_func=lambda i: ["🔵 Blue","🟢 Green","🟡 Amber","🔴 Red","🟣 Purple","🩵 Cyan","🟠 Orange"][i],
            key="new_pf_color")

    st.markdown("""
    <div class="t-card" style="margin:12px 0;">
        <div class="t-card-header"><div class="t-card-title">📂 UPLOAD BROKER FILE (MASTER TEMPLATE FORMAT)</div></div>
        <div style="padding:12px 16px;">
            <div style="font-family:var(--font-mono,'Fira Code',monospace);font-size:10px;color:var(--text-muted);margin-bottom:8px;">
                Expected columns: <span style="color:#7a90a8;">Stock Name · ISIN · Total Qty · Avg Price · LTP · Invested Value · Market Value · P&L · P&L %</span>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Upload file",
        type=["xlsx","xls","csv"],
        key="new_pf_file",
        label_visibility="collapsed",
        help="Upload Excel/CSV matching master template columns."
    )

    if uploaded:
        st.markdown(f'<div class="ok-block">✅ File ready: <b>{uploaded.name}</b></div>', unsafe_allow_html=True)

    # Download master template button
    master_df = pd.DataFrame(columns=["Stock Name","ISIN","Total Qty","Avg Price","LTP","Invested Value","Market Value","P&L","P&L %"])
    buf = io.BytesIO()
    master_df.to_excel(buf, index=False)
    buf.seek(0)
    st.download_button("⬇ Download Master Template", data=buf.getvalue(),
                       file_name="FinAnalysis_Master_Template.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.markdown("<br>", unsafe_allow_html=True)
    ca, cb, _ = st.columns([1,1,2])
    with ca:
        if st.button("✕ Cancel", key="cancel_add_pf", use_container_width=True):
            st.session_state.show_add_portfolio = False
            for k in ["new_pf_name","new_pf_color","new_pf_file"]: st.session_state.pop(k, None)
            st.rerun()
    with cb:
        if st.button("🚀 Create Portfolio", key="create_pf_btn", use_container_width=True, type="primary"):
            if not pf_name or not pf_name.strip():
                st.error("Please enter a portfolio name.")
                return

            stocks, parse_error = [], None
            if uploaded is not None:
                try:
                    file_bytes = uploaded.read()
                    parsed, err = parse_master_template(file_bytes, uploaded.name)
                    if err:
                        parse_error = err
                    else:
                        stocks = parsed or []
                except Exception as e:
                    parse_error = str(e)

            if parse_error:
                st.error(f"❌ Could not parse file: {parse_error}")
                return

            new_pf = {
                "name": pf_name.strip(),
                "color": PORTFOLIO_COLORS[color_idx],
                "stocks": stocks,
                "results": [],
                "analyzed": False,
                "pnl_pct": 0,
            }
            if "portfolios" not in st.session_state:
                st.session_state.portfolios = []
            if len(st.session_state.portfolios) >= MAX_PORTFOLIOS:
                st.error(f"⚠️ Maximum {MAX_PORTFOLIOS} portfolios reached. Delete one first.")
                return
            st.session_state.portfolios.append(new_pf)
            st.session_state.active_portfolio_idx = len(st.session_state.portfolios) - 1
            st.session_state.show_add_portfolio = False
            for k in ["new_pf_name","new_pf_color","new_pf_file"]: st.session_state.pop(k, None)
            save_portfolios()  # persist to equitex_data.json
            st.success(f"✅ Portfolio '{pf_name}' created with {len(stocks)} stocks!")
            st.rerun()

    st.markdown("---")

# ─────────────────────────────────────────────
# OVERVIEW PAGE
# ─────────────────────────────────────────────
def render_stock_summary_block(portfolios):
    """Aggregate stock stats + per-portfolio comparison + unified holdings table.
    This is the ONE place these numbers are computed and shown — used by the
    Dashboard so the Portfolio tab doesn't have to repeat them."""
    all_results = []
    for pf in portfolios: all_results.extend(pf.get("results",[]))

    total_invested = sum(r.get("invested",0) for r in all_results) or sum(sum(s.get("invested",0) for s in pf.get("stocks",[])) for pf in portfolios)
    total_mkt      = sum(r.get("market_value",0) for r in all_results)
    total_pnl      = total_mkt - total_invested if total_mkt > 0 else sum(sum(s.get("pnl_broker",0) for s in pf.get("stocks",[])) for pf in portfolios)
    total_pnl_pct  = (total_pnl / total_invested * 100) if total_invested > 0 else 0
    total_stocks   = sum(len(pf.get("stocks",[])) for pf in portfolios)
    buy_count      = sum(1 for r in all_results if r.get("decision")=="BUY")
    total_div_rcvd = sum(r.get("div_data",{}).get("total_received",0) for r in all_results if r.get("div_data"))

    c1,c2,c3,c4,c5 = st.columns(5)
    tiles = [
        ("TOTAL INVESTED", fmt_inr(total_invested), f"{total_stocks} stocks", "blue"),
        ("CURRENT VALUE",  fmt_inr(total_mkt) if total_mkt>0 else fmt_inr(total_invested), f"{len(portfolios)} portfolios", "cyan"),
        ("TOTAL P&L",      (f"+{fmt_inr(total_pnl)}" if total_pnl>=0 else fmt_inr(total_pnl)), f"{total_pnl_pct:+.1f}% overall", "green" if total_pnl>=0 else "red"),
        ("BUY SIGNALS",    str(buy_count), f"{buy_count}/{total_stocks} stocks", "green"),
        ("DIV INCOME (3Y)", fmt_inr(total_div_rcvd) if total_div_rcvd>0 else "—", "total dividends rcvd", "amber"),
    ]
    for col,(lbl,val,sub,accent) in zip([c1,c2,c3,c4,c5],tiles):
        with col:
            st.markdown(f"""<div class="stat-tile {accent}">
                <div class="stat-label">{lbl}</div>
                <div class="stat-value {accent}">{val}</div>
                <div class="stat-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if len(portfolios) > 1:
        cmp_cols = st.columns(min(len(portfolios),4))
        for i,(pf,col) in enumerate(zip(portfolios,cmp_cols)):
            with col:
                results = pf.get("results",[])
                pf_inv  = sum(r.get("invested",0) for r in results) or sum(s.get("invested",0) for s in pf.get("stocks",[]))
                pf_mkt  = sum(r.get("market_value",0) for r in results)
                pf_pnl  = pf_mkt - pf_inv if pf_mkt>0 else 0
                pf_pnl_pct = (pf_pnl/pf_inv*100) if pf_inv>0 else 0
                pf_buy  = sum(1 for r in results if r.get("decision")=="BUY")
                pf_hold = sum(1 for r in results if r.get("decision")=="HOLD")
                pf_avoid= sum(1 for r in results if r.get("decision")=="AVOID")
                avg_score = round(np.mean([r.get("score_100",50) for r in results])) if results else "N/A"
                color = pf.get("color",portfolio_color(i))
                pnl_col = "var(--accent-green)" if pf_pnl>=0 else "var(--accent-red)"
                st.markdown(f"""<div class="cmp-card">
                    <div class="cmp-hdr">
                        <div style="width:8px;height:8px;border-radius:50%;background:{color};"></div>
                        <div class="cmp-name">{pf['name']}</div>
                        <div style="margin-left:auto;font-family:var(--font-mono,'IBM Plex Mono',monospace);font-size:9px;color:var(--text-muted);">{len(pf.get('stocks',[]))} STOCKS</div>
                    </div>
                    <div style="padding:12px 16px;">
                        <div class="cstat"><span class="cstat-label">Invested</span><span class="cstat-val">{fmt_inr(pf_inv)}</span></div>
                        <div class="cstat"><span class="cstat-label">Current</span><span class="cstat-val">{fmt_inr(pf_mkt) if pf_mkt>0 else '—'}</span></div>
                        <div class="cstat"><span class="cstat-label">P&L</span><span class="cstat-val" style="color:{pnl_col};">{fmt_inr(pf_pnl)} ({pf_pnl_pct:+.1f}%)</span></div>
                        <div class="cstat"><span class="cstat-label">Avg Score</span><span class="cstat-val">{avg_score}/100</span></div>
                    </div>
                    <div style="display:flex;gap:4px;padding:8px 12px;border-top:1px solid var(--border);">
                        <div style="flex:1;text-align:center;background:var(--glow-green);border:1px solid var(--border);border-radius:2px;padding:3px;font-family:var(--font-mono,'IBM Plex Mono',monospace);font-size:10px;color:var(--accent-green);">B {pf_buy}</div>
                        <div style="flex:1;text-align:center;background:var(--glow-gold);border:1px solid var(--border);border-radius:2px;padding:3px;font-family:var(--font-mono,'IBM Plex Mono',monospace);font-size:10px;color:var(--accent-amber);">H {pf_hold}</div>
                        <div style="flex:1;text-align:center;background:var(--glow-red);border:1px solid var(--border);border-radius:2px;padding:3px;font-family:var(--font-mono,'IBM Plex Mono',monospace);font-size:10px;color:var(--accent-red);">A {pf_avoid}</div>
                    </div>
                </div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    if not all_results:
        st.markdown('<div class="info-block">💡 Go to the Portfolio tab, open a portfolio, and click <b>Analyze Portfolio</b> to see scores and signals here.</div>', unsafe_allow_html=True)
        return

    rows_html = ""
    for pf in portfolios:
        color = pf.get("color","#0090ff")
        for r in pf.get("results",[]):
            pnl_c = "var(--accent-green)" if r.get("pnl_pct",0)>=0 else "var(--accent-red)"
            pnl_s = f"+{r.get('pnl_pct',0):.1f}%" if r.get("pnl_pct",0)>=0 else f"{r.get('pnl_pct',0):.1f}%"
            sc    = r.get("score_100",50)
            div   = r.get("div_data") or {}
            dy    = f"{div.get('yield_pct'):.1f}%" if div.get("yield_pct") else "—"
            div_badge = {
                "CONSISTENT": f'<span class="div-badge-consistent">CONSISTENT</span>',
                "IRREGULAR":  f'<span class="div-badge-irregular">IRREGULAR</span>',
                "NO_DIV":     f'<span class="div-badge-no-div">NO DIV</span>',
            }.get(div.get("consistency","NO_DIV"),'<span class="div-badge-no-div">—</span>')

            rows_html += f"""<tr>
                <td><div style="display:flex;align-items:center;gap:6px;">
                    <div style="width:6px;height:6px;border-radius:50%;background:{color};"></div>
                    <span style="font-family:var(--font-mono,'IBM Plex Mono',monospace);font-size:9px;color:var(--text-muted);">{pf['name'][:10]}</span>
                </div></td>
                <td><div style="font-weight:600;">{r['name'][:22]}</div></td>
                <td class="mono">₹{r.get('cmp',0):,.0f}</td>
                <td class="mono" style="color:{pnl_c};">{pnl_s}</td>
                <td>{score_bar_html(sc)}</td>
                <td class="mono" style="color:{'var(--accent-green)' if (r.get('pe') or 99)<25 else 'var(--accent-amber)'};">{f"{r.get('pe'):.1f}x" if r.get('pe') else '—'}</td>
                <td class="mono">{dy}</td>
                <td>{div_badge}</td>
                <td>{decision_badge(r.get('decision','HOLD'))}</td>
            </tr>"""

    st.markdown(f"""<div class="t-card">
        <div class="t-card-header"><div class="t-card-title">ALL STOCKS — UNIFIED VIEW</div></div>
        <table class="t-table"><thead><tr>
            <th>Portfolio</th><th>Company</th><th>CMP</th><th>P&L</th>
            <th>Score</th><th>P/E</th><th>Div Yield</th><th>Div</th><th>Signal</th>
        </tr></thead><tbody>{rows_html}</tbody></table>
    </div>""", unsafe_allow_html=True)


def page_overview():
    """Portfolio workspace — holdings management per portfolio.
    Aggregate totals live on the Dashboard now, not here, so nothing is shown twice."""
    portfolios = st.session_state.get("portfolios",[])

    col_t, col_a = st.columns([4,1])
    with col_t:
        st.markdown(f"""
        <div style="padding:0 0 16px;">
            <div style="font-family:'Fraunces',serif;font-size:24px;font-weight:600;color:var(--text-primary);">YOUR PORTFOLIOS</div>
            <div style="font-family:var(--font-mono,'IBM Plex Mono',monospace);font-size:10px;color:var(--text-muted);margin-top:2px;">
                {len(portfolios)} PORTFOLIO{'S' if len(portfolios)!=1 else ''} · LAST UPDATED {datetime.now().strftime('%d %b %Y %H:%M')}
            </div>
        </div>""", unsafe_allow_html=True)
    with col_a:
        if st.button("⟳ Re-analyze All", key="reanalyze_all"):
            for pf in portfolios:
                pf["analyzed"] = False
                pf["results"]  = []
            st.rerun()

    if not portfolios:
        st.markdown("""
        <div style="text-align:center;padding:80px 20px;">
            <div style="font-family:'Fraunces',serif;font-size:48px;font-weight:600;color:var(--text-muted);margin-bottom:12px;">NO PORTFOLIOS</div>
            <div style="font-family:var(--font-mono,'IBM Plex Mono',monospace);font-size:11px;color:var(--text-muted);">Click ＋ Add Portfolio to get started</div>
        </div>""", unsafe_allow_html=True)
        return

    if len(portfolios) == 1:
        render_portfolio_tab(portfolios[0], 0)
        return

    tab_labels = [f"💼 {pf['name'].upper()}" for pf in portfolios]
    tabs = st.tabs(tab_labels)
    for i,(pf,tab) in enumerate(zip(portfolios, tabs)):
        with tab:
            render_portfolio_tab(pf, i)

# ─────────────────────────────────────────────
# PORTFOLIO TAB
# ─────────────────────────────────────────────
def render_portfolio_tab(pf, pf_idx):
    stocks  = pf.get("stocks",[])
    results = pf.get("results",[])
    color   = pf.get("color", portfolio_color(pf_idx))

    col_info, col_btns = st.columns([3,2])
    with col_info:
        total_inv     = sum(s.get("invested",0) for s in stocks)
        total_pnl_broker = sum(s.get("pnl_broker",0) for s in stocks)
        pnl_col = "#00c87a" if total_pnl_broker >= 0 else "#ff3b5c"
        st.markdown(f"""<div style="padding:0 0 12px;font-family:'DM Mono',monospace;font-size:11px;color:var(--text-secondary);">
            {len(stocks)} STOCKS &nbsp;·&nbsp; INVESTED: <span style="color:var(--text-primary);">₹{total_inv:,.0f}</span>
            &nbsp;·&nbsp; P&L: <span style="color:{pnl_col};">₹{total_pnl_broker:+,.0f}</span>
        </div>""", unsafe_allow_html=True)
    with col_btns:
        bc1,bc2,bc3,bc4 = st.columns(4)
        with bc1:
            if st.button("＋ Stock", key=f"add_stock_{pf_idx}"):
                st.session_state[f"show_add_stock_{pf_idx}"] = True
        with bc2:
            if st.button("⊡ Sample", key=f"sample_{pf_idx}"):
                pf["stocks"] = DEFAULT_PORTFOLIO.copy()
                pf["results"] = []; pf["analyzed"] = False
                save_portfolios()
                st.rerun()
        with bc3:
            if st.button("⊘ Clear", key=f"clear_{pf_idx}"):
                pf["stocks"] = []; pf["results"] = []; pf["analyzed"] = False
                save_portfolios()
                st.rerun()
        with bc4:
            if st.button("🗑 Delete", key=f"del_pf_{pf_idx}", type="secondary"):
                st.session_state[f"confirm_del_{pf_idx}"] = True

    # Delete confirmation
    if st.session_state.get(f"confirm_del_{pf_idx}"):
        st.markdown(f'<div class="warn-block">⚠️ Delete portfolio <b>{pf.get("name","")}</b>? This cannot be undone.</div>', unsafe_allow_html=True)
        dc1, dc2, _ = st.columns([1,1,3])
        with dc1:
            if st.button("✅ Yes, delete", key=f"yes_del_{pf_idx}", type="primary"):
                portfolios = st.session_state.get("portfolios", [])
                portfolios.pop(pf_idx)
                st.session_state.portfolios = portfolios
                st.session_state.active_portfolio_idx = max(0, pf_idx - 1)
                st.session_state.pop(f"confirm_del_{pf_idx}", None)
                save_portfolios()
                st.rerun()
        with dc2:
            if st.button("✗ Cancel", key=f"no_del_{pf_idx}"):
                st.session_state.pop(f"confirm_del_{pf_idx}", None)
                st.rerun()

    if st.session_state.get(f"show_add_stock_{pf_idx}"):
        with st.expander("＋ ADD STOCK MANUALLY", expanded=True):
            ac1,ac2,ac3,ac4,ac5 = st.columns([2,2,1,1,1])
            with ac1: new_tick = st.text_input("Ticker (.NS)", placeholder="RELIANCE.NS", key=f"nt_{pf_idx}")
            with ac2: new_nm   = st.text_input("Name", placeholder="Reliance Industries", key=f"nn_{pf_idx}")
            with ac3: new_qt   = st.number_input("Qty", min_value=1, value=10, key=f"nq_{pf_idx}")
            with ac4: new_pr   = st.number_input("Avg Price ₹", min_value=1.0, value=100.0, key=f"np_{pf_idx}")
            with ac5:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Add", key=f"do_add_{pf_idx}"):
                    if new_tick:
                        inv = new_qt * new_pr
                        pf["stocks"].append({
                            "ticker":new_tick.strip().upper(),"name":new_nm or new_tick,
                            "qty":new_qt,"buy_price":new_pr,"invested":inv,
                            "market_value":0,"pnl_broker":0,"sector":"N/A","ltp":0,"market_cap_type":"N/A",
                        })
                        pf["results"] = []; pf["analyzed"] = False
                        st.session_state[f"show_add_stock_{pf_idx}"] = False
                        save_portfolios()
                        st.rerun()

    if not stocks:
        st.markdown('<div class="warn-block">No stocks in this portfolio. Click ＋ Stock or ⊡ Sample to get started.</div>', unsafe_allow_html=True)
        return

    rows_html = ""
    for s in stocks:
        pnl_b = s.get("pnl_broker",0)
        pc = "#00c87a" if pnl_b >= 0 else "#ff3b5c"
        rows_html += f"""<tr>
            <td><div style="font-weight:600;">{s['name'][:25]}</div></td>
            <td class="mono" style="color:var(--text-muted);">{s['ticker']}</td>
            <td class="mono">{s['qty']}</td>
            <td class="mono">₹{s['buy_price']:,.1f}</td>
            <td class="mono">₹{s.get('invested',0):,.0f}</td>
            <td class="mono" style="color:{pc};">₹{pnl_b:+,.0f}</td>
        </tr>"""

    st.markdown(f"""<div class="t-card">
        <div class="t-card-header">
            <div class="t-card-title">
                <span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:{color};margin-right:8px;"></span>
                {pf['name'].upper()} — {len(stocks)} HOLDINGS
            </div>
        </div>
        <table class="t-table"><thead><tr>
            <th>Company</th><th>Ticker</th><th>Qty</th><th>Avg Price</th><th>Invested</th><th>Broker P&L</th>
        </tr></thead><tbody>{rows_html}</tbody></table>
    </div>""", unsafe_allow_html=True)

    if not pf.get("analyzed") or not results:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            '<div class="info-block">📡 This will fetch live price data from NSE/BSE for each stock. '
            'Allow 5–10 seconds per stock.</div>',
            unsafe_allow_html=True
        )
        if st.button(f"🔍 Analyze {pf['name']} Portfolio", key=f"analyze_{pf_idx}", use_container_width=True, type="primary"):
            total    = len(stocks)
            progress = st.progress(0, text=f"Starting analysis — 0 / {total} stocks...")
            status   = st.empty()
            analyzed = []

            # Run sequentially — avoids Streamlit thread-safety crash
            # (st.progress cannot be called from ThreadPoolExecutor threads)
            for i, item in enumerate(stocks):
                status.markdown(
                    f'<div class="info-block">🔄 Analyzing <b>{item.get("name", item["ticker"])}</b> '
                    f'({i+1}/{total})…</div>',
                    unsafe_allow_html=True
                )
                result = analyze_single_portfolio_stock(item)
                analyzed.append(result)
                progress.progress((i + 1) / total, text=f"Done {i+1} / {total} stocks")

            progress.empty()
            status.empty()
            pf["results"]  = analyzed
            pf["analyzed"] = True
            pf_inv = sum(r.get("invested", 0) for r in analyzed)
            pf_mkt = sum(r.get("market_value", 0) for r in analyzed)
            if pf_inv > 0 and pf_mkt > 0:
                pf["pnl_pct"] = (pf_mkt - pf_inv) / pf_inv * 100
            st.rerun()
    else:
        render_portfolio_results(results, pf, pf_idx)

# ─────────────────────────────────────────────
# PORTFOLIO RESULTS
# ─────────────────────────────────────────────
def render_portfolio_results(results, pf, pf_idx):
    if not results: return
    color = pf.get("color", portfolio_color(pf_idx))

    total_inv  = sum(r.get("invested",0) for r in results)
    total_mkt  = sum(r.get("market_value",0) for r in results)
    total_pnl  = total_mkt - total_inv
    total_pnl_pct = (total_pnl / total_inv * 100) if total_inv > 0 else 0
    buy_c  = sum(1 for r in results if r.get("decision")=="BUY")
    hold_c = sum(1 for r in results if r.get("decision")=="HOLD")
    avoid_c= sum(1 for r in results if r.get("decision")=="AVOID")
    avg_score = round(np.mean([r.get("score_100",50) for r in results]))
    total_div = sum(r.get("div_data",{}).get("total_received",0) for r in results if r.get("div_data"))

    c1,c2,c3,c4,c5 = st.columns(5)
    summary = [
        ("INVESTED",     fmt_inr(total_inv),  f"{len(results)} holdings", "blue"),
        ("CURRENT VALUE",fmt_inr(total_mkt),  "live prices",              "cyan"),
        ("TOTAL P&L",    (f"+{fmt_inr(total_pnl)}" if total_pnl>=0 else fmt_inr(total_pnl)), f"{total_pnl_pct:+.1f}%", "green" if total_pnl>=0 else "red"),
        ("AVG SCORE",    f"{avg_score}/100",   "portfolio quality",        "blue"),
        ("DIV INCOME 3Y",fmt_inr(total_div) if total_div>0 else "—", f"{buy_c}B·{hold_c}H·{avoid_c}A", "amber"),
    ]
    for col,(lbl,val,sub,accent) in zip([c1,c2,c3,c4,c5],summary):
        with col:
            st.markdown(f"""<div class="stat-tile {accent}">
                <div class="stat-label">{lbl}</div>
                <div class="stat-value {accent}">{val}</div>
                <div class="stat-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_table, col_side = st.columns([3,1])

    with col_table:
        # Table header
        st.markdown(f"""<div class="t-card">
            <div class="t-card-header">
                <div class="t-card-title">
                    <span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:{color};margin-right:8px;"></span>
                    HOLDINGS — SORTED BY SCORE
                </div>
                <div style="font-family:'DM Mono',monospace;font-size:9px;color:#2e4060;">CLICK ◆ TO OPEN IN ANALYZER</div>
            </div>
        </div>""", unsafe_allow_html=True)

        sorted_results = sorted(results, key=lambda x: -x.get("score_100",0))
        for row_idx, r in enumerate(sorted_results):
            pnl_pct  = r.get("pnl_pct",0)
            pnl_str  = f"+{pnl_pct:.1f}%" if pnl_pct>=0 else f"{pnl_pct:.1f}%"
            pnl_col  = "#3ecf8e" if pnl_pct>=0 else "#e05252"
            sc       = r.get("score_100",50)
            dec      = r.get("decision","HOLD")
            dec_col  = {"BUY":"#3ecf8e","HOLD":"#c9a84c","AVOID":"#e05252"}.get(dec,"#c9a84c")
            div      = r.get("div_data") or {}
            dy       = f"{div.get('yield_pct'):.1f}%" if div.get("yield_pct") else "—"
            roe_val  = r.get("roe")
            roe_str  = pct(roe_val) if roe_val else "—"
            roe_col  = "#3ecf8e" if (roe_val or 0)>0.15 else ("#c9a84c" if roe_val else "#2e4060")
            fill     = score_fill(sc)
            ticker   = r.get("ticker","")
            # Unique key: portfolio index + row index (avoid ticker dots causing key issues)
            btn_key  = f"az_btn_{pf_idx}_{row_idx}"

            row_c1, row_c2 = st.columns([6, 1])
            with row_c1:
                st.markdown(f"""<div style="background:linear-gradient(145deg,#111827,#0d1220);border:1px solid #1e2d46;
                    border-radius:8px;padding:10px 16px;margin-bottom:6px;display:flex;align-items:center;gap:16px;">
                  <div style="width:36px;height:36px;background:linear-gradient(135deg,#1a2338,#2e4060);border-radius:6px;
                    display:flex;align-items:center;justify-content:center;font-family:'DM Mono',monospace;
                    font-size:11px;font-weight:700;color:#a8b8cc;flex-shrink:0;">{ticker.replace('.NS','').replace('.BO','')[:4]}</div>
                  <div style="flex:1;min-width:0;">
                    <div style="font-size:13px;font-weight:600;color:#e2e8f0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{r['name'][:26]}</div>
                    <div style="font-family:'DM Mono',monospace;font-size:9px;color:#5a7090;">{r.get('sector','N/A')} · {ticker}</div>
                  </div>
                  <div style="text-align:right;flex-shrink:0;">
                    <div style="font-family:'DM Mono',monospace;font-size:13px;font-weight:600;color:#e2e8f0;">₹{r.get('cmp',0):,.0f}</div>
                    <div style="font-family:'DM Mono',monospace;font-size:11px;color:{pnl_col};">{pnl_str}</div>
                  </div>
                  <div style="flex-shrink:0;width:80px;">
                    <div style="height:4px;background:#1e2d46;border-radius:2px;overflow:hidden;margin-bottom:3px;">
                      <div style="width:{sc}%;height:100%;background:{fill};border-radius:2px;"></div>
                    </div>
                    <div style="font-family:'DM Mono',monospace;font-size:10px;color:#a8b8cc;">{sc}/100</div>
                  </div>
                  <div style="flex-shrink:0;text-align:center;">
                    <div style="font-family:'DM Mono',monospace;font-size:9px;color:#5a7090;">ROE</div>
                    <div style="font-family:'DM Mono',monospace;font-size:11px;font-weight:600;color:{roe_col};">{roe_str}</div>
                  </div>
                  <div style="flex-shrink:0;text-align:center;">
                    <div style="font-family:'DM Mono',monospace;font-size:9px;color:#5a7090;">DIV</div>
                    <div style="font-family:'DM Mono',monospace;font-size:11px;color:#a8b8cc;">{dy}</div>
                  </div>
                  <span style="background:{dec_col};color:#080b12;font-family:'DM Mono',monospace;font-size:9px;
                    font-weight:700;padding:3px 8px;border-radius:4px;flex-shrink:0;">{dec}</span>
                </div>""", unsafe_allow_html=True)
            with row_c2:
                if st.button("◆ Analyze", key=btn_key, use_container_width=True):
                    existing = dict(r)
                    existing["company_name"] = r.get("name", ticker)
                    existing["dec_col"]  = dec_col
                    existing["tech_r"]   = r.get("tech_reasons", [])
                    existing["tech_w"]   = r.get("tech_warnings", [])
                    existing["fund_r"]   = r.get("fund_reasons", [])
                    existing["fund_w"]   = r.get("fund_warnings", [])
                    existing["price"]    = r.get("cmp", 0)
                    existing["proj_3y"]  = r.get("cmp", 0) * ((1 + r.get("cagr", 10) / 100) ** 3)
                    if r.get("df") is not None and not r["df"].empty:
                        try:
                            existing["commentary"] = generate_commentary(
                                r.get("info", {}), r["df"], r.get("tech_s", 0), r.get("fund_s", 0),
                                r.get("score_100", 50) / 10, r.get("cagr", 10),
                                r.get("bp", {}), r.get("sent_label", "Neutral")
                            )
                        except Exception:
                            existing["commentary"] = "Commentary unavailable."
                    else:
                        existing["commentary"] = "Re-run analysis for full commentary."
                    st.session_state.az_ticker = ticker
                    st.session_state.az_period = "2y"
                    st.session_state.az_result = existing
                    st.session_state.main_nav  = "🔍  Analyzer"
                    st.rerun()

        alerts = concentration_risk(results)
        if alerts:
            for a in alerts:
                st.markdown(f'<div class="warn-block">⚠️ {a["msg"]}</div>', unsafe_allow_html=True)

    with col_side:
        # Sector donut
        sector_map = {}
        for r in results:
            sec = r.get("sector","N/A")
            val = r.get("market_value", r.get("invested",0))
            sector_map[sec] = sector_map.get(sec,0) + val
        total_val = sum(sector_map.values()) or 1
        sec_colors = ["#0090ff","#00c87a","#ffb000","#ff3b5c","#a855f7","#00d4ff"]
        legend_html, conic_parts, running = "", [], 0
        for j,(sec,val) in enumerate(sorted(sector_map.items(), key=lambda x:-x[1])[:5]):
            pct_val = val/total_val*100
            c = sec_colors[j%len(sec_colors)]
            conic_parts.append(f"{c} {running:.0f}deg {running+pct_val*3.6:.0f}deg")
            running += pct_val*3.6
            legend_html += f"""<div style="display:flex;align-items:center;gap:6px;margin-bottom:5px;font-size:10px;">
                <div style="width:7px;height:7px;border-radius:1px;background:{c};flex-shrink:0;"></div>
                <span style="color:#7a90a8;flex:1;">{sec[:14]}</span>
                <span style="font-family:var(--font-mono,'Fira Code',monospace);font-size:9px;color:var(--text-muted);">{pct_val:.0f}%</span>
            </div>"""
        conic = ",".join(conic_parts)

        st.markdown(f"""<div class="t-card">
            <div class="t-card-header"><div class="t-card-title">SECTOR ALLOCATION</div></div>
            <div style="padding:16px;text-align:center;">
                <div style="width:90px;height:90px;border-radius:50%;background:conic-gradient({conic});margin:0 auto 12px;position:relative;">
                    <div style="position:absolute;width:52px;height:52px;background:#131920;border-radius:50%;top:50%;left:50%;transform:translate(-50%,-50%);display:flex;align-items:center;justify-content:center;flex-direction:column;">
                        <div style="font-family:var(--font-mono,'Fira Code',monospace);font-size:12px;font-weight:700;color:#e8edf2;">{len(results)}</div>
                        <div style="font-size:8px;color:var(--text-muted);">stks</div>
                    </div>
                </div>
                {legend_html}
            </div>
        </div>""", unsafe_allow_html=True)

        # Key signals
        avg_pe  = np.mean([r.get("pe") for r in results if r.get("pe")]) if any(r.get("pe") for r in results) else None
        avg_roe = np.mean([r.get("roe") for r in results if r.get("roe")]) if any(r.get("roe") for r in results) else None
        div_payers = sum(1 for r in results if r.get("div_data",{}).get("consistency")!="NO_DIV")
        consistent_payers = sum(1 for r in results if r.get("div_data",{}).get("consistency")=="CONSISTENT")

        st.markdown(f"""<div class="t-card">
            <div class="t-card-header"><div class="t-card-title">KEY SIGNALS</div></div>
            <div>
                <div class="sig-row"><span>📊</span><span style="flex:1;font-size:11px;color:#7a90a8;">Avg Score</span><span class="{'sig-green' if avg_score>=60 else 'sig-amber'}">{avg_score}/100</span></div>
                <div class="sig-row"><span>🏦</span><span style="flex:1;font-size:11px;color:#7a90a8;">Avg ROE</span><span class="{'sig-green' if avg_roe and avg_roe>0.15 else 'sig-amber'}">{pct(avg_roe) if avg_roe else '—'}</span></div>
                <div class="sig-row"><span>💰</span><span style="flex:1;font-size:11px;color:#7a90a8;">Avg P/E</span><span class="{'sig-green' if avg_pe and avg_pe<25 else 'sig-amber' if avg_pe and avg_pe<40 else 'sig-red'}">{f'{avg_pe:.1f}x' if avg_pe else '—'}</span></div>
                <div class="sig-row"><span>✅</span><span style="flex:1;font-size:11px;color:#7a90a8;">BUY Signals</span><span class="sig-green">{buy_c}/{len(results)}</span></div>
                <div class="sig-row"><span>💸</span><span style="flex:1;font-size:11px;color:#7a90a8;">Div Payers</span><span class="sig-cyan">{div_payers}/{len(results)}</span></div>
                <div class="sig-row"><span>🔁</span><span style="flex:1;font-size:11px;color:#7a90a8;">Consistent</span><span class="sig-green">{consistent_payers}/{len(results)}</span></div>
            </div>
        </div>""", unsafe_allow_html=True)

    # Export
    st.markdown("<br>", unsafe_allow_html=True)
    ec1,ec2,ec3 = st.columns([1,1,2])
    with ec1:
        excel_data = generate_excel_report(results)
        st.download_button("⬇ Export Excel", data=excel_data,
                           file_name=f"{pf['name']}_analysis.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)
    with ec2:
        if st.button("🔬 Deep Dive", key=f"deep_{pf_idx}", use_container_width=True):
            st.session_state[f"show_deep_{pf_idx}"] = not st.session_state.get(f"show_deep_{pf_idx}", False)
            st.rerun()

    if st.session_state.get(f"show_deep_{pf_idx}"):
        st.markdown('<div class="sec-hdr" style="margin-top:16px;">DEEP STOCK ANALYSIS</div>', unsafe_allow_html=True)
        for r in sorted(results, key=lambda x: -x.get("score_100",0)):
            render_deep_stock(r)

# ─────────────────────────────────────────────
# DEEP DIVE STOCK CARD
# ─────────────────────────────────────────────
def render_deep_stock(r):
    sc = r.get("score_100",50)
    dec = r.get("decision","HOLD")
    dec_col = {"BUY":"#00c87a","HOLD":"#ffb000","AVOID":"#ff3b5c"}.get(dec,"#ffb000")

    with st.expander(f"{'▲' if dec=='BUY' else '►' if dec=='HOLD' else '▼'} {r['name']} — {sc}/100 — {dec}", expanded=False):
        pnl_pct = r.get("pnl_pct",0)
        pnl_str = f"+{pnl_pct:.1f}%" if pnl_pct>=0 else f"{pnl_pct:.1f}%"
        pnl_col = "#00c87a" if pnl_pct>=0 else "#ff3b5c"
        grade   = score_to_badge_html(sc)

        st.markdown(f"""<div style="background:var(--bg-card);border:1px solid var(--border);border-radius:4px;padding:16px 20px;margin-bottom:16px;display:flex;align-items:center;gap:16px;">
            <div style="width:44px;height:44px;background:linear-gradient(135deg,#0090ff,#00d4ff);border-radius:4px;
                display:flex;align-items:center;justify-content:center;font-family:var(--font-mono,'Fira Code',monospace);font-size:14px;font-weight:700;color:white;">
                {r['ticker'][:2]}
            </div>
            <div style="flex:1;">
                <div style="font-family:var(--font-mono,'Fira Code',monospace);font-size:10px;color:#0090ff;letter-spacing:1px;">{r['ticker']}</div>
                <div style="font-size:16px;font-weight:700;color:#e8edf2;">{r['name']}</div>
                <div style="font-size:10px;color:var(--text-muted);">{r.get('sector','N/A')} · {r.get('market_cap_type','N/A')}</div>
            </div>
            <div style="display:flex;align-items:center;gap:20px;">
                <div>
                    <div style="font-family:var(--font-mono,'Fira Code',monospace);font-size:9px;color:var(--text-muted);letter-spacing:1px;">SCORE</div>
                    <div style="display:flex;align-items:center;gap:8px;">{grade}<span style="font-family:var(--font-mono,'Fira Code',monospace);font-size:22px;font-weight:700;color:#e8edf2;">{sc}<span style="font-size:12px;color:var(--text-muted);">/100</span></span></div>
                </div>
                <div style="text-align:right;">
                    <div style="font-family:var(--font-mono,'Fira Code',monospace);font-size:9px;color:var(--text-muted);">CMP</div>
                    <div style="font-family:var(--font-mono,'Fira Code',monospace);font-size:20px;font-weight:700;color:#e8edf2;">₹{r.get('cmp',0):,.0f}</div>
                    <div style="font-family:var(--font-mono,'Fira Code',monospace);font-size:11px;color:{pnl_col};">{pnl_str} from buy</div>
                </div>
                <span style="background:{dec_col};color:white;font-family:var(--font-mono,'Fira Code',monospace);font-size:11px;font-weight:700;padding:6px 14px;border-radius:2px;letter-spacing:1px;">{dec}</span>
            </div>
        </div>""", unsafe_allow_html=True)

        # Metrics
        mc1,mc2,mc3,mc4 = st.columns(4)
        metrics = [
            ("P/E RATIO",  f"{r.get('pe'):.1f}x" if r.get('pe') else "N/A"),
            ("ROE",        pct(r.get('roe')) if r.get('roe') else "N/A"),
            ("D/E RATIO",  f"{r.get('de'):.1f}" if r.get('de') is not None else "N/A"),
            ("REV GROWTH", pct(r.get('rev_growth')) if r.get('rev_growth') else "N/A"),
        ]
        for col,(lbl,val) in zip([mc1,mc2,mc3,mc4],metrics):
            with col:
                st.markdown(f"""<div class="metric-card">
                    <div class="metric-label">{lbl}</div>
                    <div class="metric-val">{val}</div>
                </div>""", unsafe_allow_html=True)

        # Dividend section
        div_data = r.get("div_data")
        if div_data:
            st.markdown(render_dividend_section(div_data), unsafe_allow_html=True)

        # Chart
        if r.get("df") is not None and not r["df"].empty:
            st.plotly_chart(build_stock_chart(r["df"], r["buy_price"], r["ticker"]), use_container_width=True)

        # Scorecard
        tc1,tc2 = st.columns(2)
        with tc1:
            st.markdown(f'<div class="sec-hdr">TECHNICAL SCORE: {r.get("tech_s",0)}/5</div>', unsafe_allow_html=True)
            for reason in r.get("tech_reasons",[])[:4]:
                st.markdown(f'<div class="ok-block">{reason}</div>', unsafe_allow_html=True)
            for warn in r.get("tech_warnings",[])[:3]:
                st.markdown(f'<div class="danger-block">{warn}</div>', unsafe_allow_html=True)
        with tc2:
            st.markdown(f'<div class="sec-hdr">FUNDAMENTAL SCORE: {r.get("fund_s",0)}/5</div>', unsafe_allow_html=True)
            for reason in r.get("fund_reasons",[])[:4]:
                st.markdown(f'<div class="ok-block">{reason}</div>', unsafe_allow_html=True)
            for warn in r.get("fund_warnings",[])[:3]:
                st.markdown(f'<div class="danger-block">{warn}</div>', unsafe_allow_html=True)

        # News
        headlines = r.get("headlines",[])
        if headlines:
            st.markdown('<div class="sec-hdr" style="margin-top:12px;">LATEST NEWS</div>', unsafe_allow_html=True)
            st.markdown('<div class="t-card">', unsafe_allow_html=True)
            for h in headlines[:4]:
                hl = h.lower()
                pos_c = sum(1 for w in POSITIVE_WORDS if w in hl)
                neg_c = sum(1 for w in NEGATIVE_WORDS if w in hl)
                if pos_c > neg_c: sent_html = '<span class="sent-pos">POSITIVE</span>'
                elif neg_c > pos_c: sent_html = '<span class="sent-neg">NEGATIVE</span>'
                else: sent_html = '<span class="sent-neu">NEUTRAL</span>'
                st.markdown(f"""<div class="news-item">
                    <div class="news-headline">{h[:120]}</div>
                    <div class="news-meta">{sent_html}</div>
                </div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# STOCK ANALYZER PAGE
# ─────────────────────────────────────────────
def page_analyzer():
    st.markdown("""
    <div style="padding:0 0 16px;">
        <div style="font-family:'Fraunces',serif;font-size:24px;font-weight:600;color:var(--text-primary);">STOCK DEEP DIVE</div>
        <div style="font-family:var(--font-mono,'Fira Code',monospace);font-size:10px;color:var(--text-muted);margin-top:2px;">
            FULL TECHNICAL + FUNDAMENTAL + DIVIDEND ANALYSIS FOR ANY NSE/BSE STOCK
        </div>
    </div>""", unsafe_allow_html=True)

    # ── Persistent state so switching tabs doesn't wipe the result ──
    if "az_ticker"  not in st.session_state: st.session_state.az_ticker  = ""
    if "az_period"  not in st.session_state: st.session_state.az_period  = "3y"
    if "az_result"  not in st.session_state: st.session_state.az_result  = None

    c1,c2,c3 = st.columns([3,1,1])
    with c1:
        ticker_input = st.text_input(
            "Ticker",
            value=st.session_state.az_ticker,
            placeholder="e.g. RELIANCE.NS, TCS.NS, HDFCBANK.NS",
            label_visibility="collapsed",
            key="analyzer_ticker"
        )
    with c2:
        period = st.selectbox("Period", [
            "3mo","6mo","1y","2y","3y","5y"
        ], index=2, label_visibility="collapsed", key="analyzer_period_sel")
    with c3:
        do_analyze = st.button("🔍 Analyze", use_container_width=True, key="do_analyze")

    # Only re-fetch when the user explicitly clicks Analyze
    if do_analyze and ticker_input.strip():
        st.session_state.az_ticker = ticker_input.strip().upper()
        st.session_state.az_period = period
        st.session_state.az_result = None   # clear stale result

        with st.spinner(f"Fetching {st.session_state.az_ticker}…"):
            try:
                stock  = yf.Ticker(st.session_state.az_ticker)
                df_raw = stock.history(period=period)
                info   = stock.info
            except Exception as e:
                st.markdown(f'<div class="danger-block">❌ Could not fetch data: {str(e)[:200]}</div>', unsafe_allow_html=True)
                return

        if df_raw.empty:
            st.markdown(f'<div class="warn-block">⚠️ No data for "{st.session_state.az_ticker}". Try with .NS suffix (e.g. RELIANCE.NS)</div>', unsafe_allow_html=True)
            return

        df          = compute_indicators(df_raw.copy())
        tech_s, tech_r, tech_w = technical_score(df, info)
        fund_s, fund_r, fund_w = fundamental_score(info)
        # ── NEW: Additional sources ──
        screener    = fetch_screener_data(st.session_state.az_ticker)
        peer_s, peer_r, peer_w, peer_details = peer_comparison_score(st.session_state.az_ticker, info, screener)
        hist_s, hist_r, hist_w = historical_pattern_score(df, info)
        promoter_pct= screener.get("promoter_pct") or (safe_get(info.get("heldPercentInsiders"),0)*100)
        prom_s = 12 if (promoter_pct or 0)>=55 else (9 if (promoter_pct or 0)>=40 else (5 if (promoter_pct or 0)>=25 else 3))
        inst_pct = safe_get(info.get("heldPercentInstitutions"),0)*100
        fii_s  = 8 if inst_pct>=30 else (5 if inst_pct>=15 else 2)
        # ── Composite: tech/5→20, fund/5→25, prom→15, fii→15, peer→15, hist→10 = 100 ──
        score_100 = min(100, int(
            (tech_s/5)*20 + (fund_s/5)*25 + prom_s + fii_s + peer_s + hist_s
        ))
        total_score  = round(score_100/10, 1)
        decision    = "BUY" if score_100 >= 72 else ("HOLD" if score_100 >= 48 else "AVOID")
        dec_col     = {"BUY":"#00c87a","HOLD":"#ffb000","AVOID":"#ff3b5c"}.get(decision,"#ffb000")
        price       = df["Close"].iloc[-1]
        cagr, proj_3y = compute_projection(info, tech_s, fund_s, price)
        bp          = compute_buy_plan(df, info)
        company_name= safe_get(info.get("longName"), st.session_state.az_ticker)
        headlines   = fetch_news(st.session_state.az_ticker, company_name)
        _, sent_label = analyze_sentiment(headlines)
        commentary  = generate_commentary(info, df, tech_s, fund_s, total_score, cagr, bp, sent_label)
        div_data    = fetch_dividend_data(st.session_state.az_ticker)

        st.session_state.az_chart_period = period
        st.session_state.az_result = {
            "df":df, "info":info, "tech_s":tech_s, "tech_r":tech_r, "tech_w":tech_w,
            "fund_s":fund_s, "fund_r":fund_r, "fund_w":fund_w,
            "screener":screener, "peer_s":peer_s, "peer_r":peer_r, "peer_w":peer_w,
            "peer_details":peer_details, "hist_s":hist_s, "hist_r":hist_r, "hist_w":hist_w,
            "prom_s":prom_s, "fii_s":fii_s, "promoter_pct":promoter_pct, "inst_pct":inst_pct,
            "total_score":total_score, "score_100":score_100,
            "decision":decision, "dec_col":dec_col, "price":price,
            "cagr":cagr, "proj_3y":proj_3y, "bp":bp,
            "company_name":company_name, "headlines":headlines,
            "sent_label":sent_label, "commentary":commentary, "div_data":div_data,
        }

    # ── Render stored result (survives tab switches) ──
    R = st.session_state.az_result

    # If result came from portfolio but has no usable data, clear it so user can re-fetch
    if R is not None and (R.get("df") is None or R.get("error")):
        err = R.get("error","")
        st.markdown(f'<div class="warn-block">⚠️ No data available for <b>{st.session_state.az_ticker}</b>{(": " + err) if err else ""}. Click <b>Analyze</b> to fetch fresh data, or check the ticker symbol.</div>', unsafe_allow_html=True)
        st.session_state.az_result = None
        return

    if R is None:
        st.markdown("""
        <div style="text-align:center;padding:80px 20px;">
            <div style="font-family:'Fraunces',serif;font-size:48px;font-weight:600;letter-spacing:4px;color:#1e2d46;margin-bottom:12px;">ENTER A TICKER</div>
            <div style="font-family:'DM Mono',monospace;font-size:11px;color:#5a7090;">
                RELIANCE.NS · TCS.NS · HDFCBANK.NS · INFY.NS · BAJFINANCE.NS
            </div>
            <div style="font-family:'DM Mono',monospace;font-size:10px;color:#2e4060;margin-top:8px;">
                or click ◆ Analyze on any stock in the Overview tab
            </div>
        </div>""", unsafe_allow_html=True)
        return

    # unpack — safe for both fresh Analyzer results AND portfolio-sourced results
    df           = R.get("df");          info        = R.get("info", {})
    tech_s       = R.get("tech_s", 0);  tech_r      = R.get("tech_r") or R.get("tech_reasons", []);  tech_w = R.get("tech_w") or R.get("tech_warnings", [])
    fund_s       = R.get("fund_s", 0);  fund_r      = R.get("fund_r") or R.get("fund_reasons", []);  fund_w = R.get("fund_w") or R.get("fund_warnings", [])
    total_score  = R.get("total_score", R.get("score_10", 5))
    score_100    = R.get("score_100", 50)
    decision     = R.get("decision", "HOLD")
    dec_col      = R.get("dec_col", {"BUY":"#3ecf8e","HOLD":"#c9a84c","AVOID":"#e05252"}.get(decision,"#c9a84c"))
    price        = R.get("price") or R.get("cmp", 0)
    cagr         = R.get("cagr", 10)
    proj_3y      = R.get("proj_3y", price * ((1 + cagr/100)**3) if price else 0)
    bp           = R.get("bp", {})
    company_name = R.get("company_name") or R.get("name", st.session_state.az_ticker)
    headlines    = R.get("headlines", [])
    sent_label   = R.get("sent_label", "Neutral")
    commentary   = R.get("commentary", "")
    div_data     = R.get("div_data")
    ticker       = st.session_state.az_ticker

    grade = score_to_badge_html(score_100)

    # Hero header
    st.markdown(f"""<div style="background:var(--bg-card);border:1px solid var(--border);border-radius:4px;padding:18px 24px;margin-bottom:20px;display:flex;align-items:center;gap:16px;">
        <div style="width:52px;height:52px;background:linear-gradient(135deg,#0090ff,#00d4ff);border-radius:4px;
            display:flex;align-items:center;justify-content:center;font-family:var(--font-mono,'Fira Code',monospace);font-size:18px;font-weight:700;color:white;">
            {safe_get(info.get('symbol'),ticker)[:2]}
        </div>
        <div style="flex:1;">
            <div style="font-family:var(--font-mono,'Fira Code',monospace);font-size:10px;color:#0090ff;letter-spacing:2px;">{safe_get(info.get('symbol'),ticker)} · {safe_get(info.get('exchange'),'NSE')}</div>
            <div style="font-size:20px;font-weight:700;color:#e8edf2;">{company_name}</div>
            <div style="font-family:var(--font-mono,'Fira Code',monospace);font-size:9px;color:var(--text-muted);">{safe_get(info.get('sector'),'N/A')} · {safe_get(info.get('industry'),'N/A')}</div>
        </div>
        <div style="display:flex;align-items:center;gap:24px;">
            <div>
                <div style="font-family:var(--font-mono,'Fira Code',monospace);font-size:9px;color:var(--text-muted);letter-spacing:1.5px;">SCORE</div>
                <div style="display:flex;align-items:center;gap:8px;margin-top:4px;">{grade}
                    <span style="font-family:var(--font-mono,'Fira Code',monospace);font-size:26px;font-weight:700;color:#e8edf2;">{score_100}<span style="font-size:13px;color:var(--text-muted);">/100</span></span>
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-family:var(--font-mono,'Fira Code',monospace);font-size:9px;color:var(--text-muted);letter-spacing:1.5px;">LAST PRICE</div>
                <div style="font-family:var(--font-mono,'Fira Code',monospace);font-size:28px;font-weight:700;color:#e8edf2;margin-top:4px;">₹{price:,.2f}</div>
            </div>
            <span style="background:{dec_col};color:white;font-family:var(--font-mono,'Fira Code',monospace);font-size:13px;font-weight:700;padding:10px 20px;border-radius:2px;letter-spacing:1.5px;">{decision}</span>
        </div>
    </div>""", unsafe_allow_html=True)

    # Metric row
    pe    = safe_get(info.get("trailingPE"))
    roe   = safe_get(info.get("returnOnEquity"))
    de    = safe_get(info.get("debtToEquity"))
    rev_g = safe_get(info.get("revenueGrowth"))
    mktcap= safe_get(info.get("marketCap"))

    m1,m2,m3,m4,m5 = st.columns(5)
    for col,(lbl,val,note) in zip([m1,m2,m3,m4,m5],[
        ("P/E RATIO",   f"{pe:.1f}x" if pe else "N/A",          "lower = cheaper"),
        ("ROE",          pct(roe) if roe else "N/A",              "higher = better"),
        ("D/E RATIO",    f"{de:.1f}" if de is not None else "N/A", "lower = safer"),
        ("REV GROWTH",   pct(rev_g) if rev_g else "N/A",          "YoY"),
        ("MARKET CAP",   fmt_cr(mktcap) if mktcap else "N/A",     "total valuation"),
    ]):
        with col:
            st.markdown(f"""<div class="stat-tile blue">
                <div class="stat-label">{lbl}</div>
                <div class="stat-value" style="font-size:16px;">{val}</div>
                <div class="stat-sub">{note}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab1,tab2,tab3,tab4,tab5,tab6,tab7 = st.tabs(["📈 Chart","◈ 7-Source Score","⊕ Peer Compare","💰 Dividends","📍 Buy Plan","📰 News","🧠 Analysis"])

    with tab1:
        if df is None or df.empty:
            st.markdown('<div class="warn-block">⚠️ No price data available for this ticker.</div>', unsafe_allow_html=True)
        else:
            # ── Chart controls ────────────────────────────────
            cc1,cc2,cc3,cc4 = st.columns([2,2,2,2])
            with cc1:
                chart_tf = st.selectbox("Timeframe", [
                    "1mo","3mo","6mo","1y","2y","3y","5y"
                ], index=["1mo","3mo","6mo","1y","2y","3y","5y"].index(
                    st.session_state.get("az_chart_period","1y") if st.session_state.get("az_chart_period","1y") in ["1mo","3mo","6mo","1y","2y","3y","5y"] else "1y"
                ), key="chart_tf")
            with cc2:
                term_view = st.selectbox("View", [
                    "All Indicators","Short Term (3mo)","Mid Term (1y)","Long Term (3y+)"
                ], key="chart_term")
            with cc3:
                show_fib = st.checkbox("📐 Fibonacci", value=True, key="chart_fib")
            with cc4:
                show_sr  = st.checkbox("🎯 Support/Resistance", value=True, key="chart_sr")

            # Re-slice df by selected timeframe
            import datetime as _dt2
            tf_days = {"1mo":30,"3mo":90,"6mo":180,"1y":365,"2y":730,"3y":1095,"5y":1825}
            days_back = tf_days.get(chart_tf, 365)
            df_view = df.iloc[-min(days_back, len(df)):]

            # Build enhanced chart
            st.plotly_chart(
                build_chart_enhanced(df_view, bp, show_fib=show_fib, show_sr=show_sr, term_view=term_view),
                use_container_width=True
            )

            # ── Term-specific interpretation ──────────────────
            row = df.iloc[-1]
            if "Short" in term_view:
                st.markdown('<div class="sec-hdr">SHORT TERM SIGNALS (Days to Weeks)</div>', unsafe_allow_html=True)
                sc1,sc2,sc3,sc4 = st.columns(4)
                with sc1:
                    ab20 = row["Close"] > row["SMA20"]
                    c = "green" if ab20 else "red"
                    st.markdown(f'<div class="stat-tile {c}"><div class="stat-label">20 DMA</div><div class="stat-value {c}">{"ABOVE ▲" if ab20 else "BELOW ▼"}</div></div>', unsafe_allow_html=True)
                with sc2:
                    rsi_v = row["RSI"]
                    rsig = "HEALTHY" if 40<rsi_v<65 else ("OVERBOUGHT" if rsi_v>=65 else "OVERSOLD")
                    rc = "green" if rsig=="HEALTHY" else ("red" if rsig=="OVERBOUGHT" else "amber")
                    st.markdown(f'<div class="stat-tile {rc}"><div class="stat-label">RSI (14)</div><div class="stat-value {rc}">{rsi_v:.1f} — {rsig}</div></div>', unsafe_allow_html=True)
                with sc3:
                    mb = row["MACD"] > row["MACD_Signal"]
                    c = "green" if mb else "red"
                    st.markdown(f'<div class="stat-tile {c}"><div class="stat-label">MACD</div><div class="stat-value {c}">{"BULLISH ▲" if mb else "BEARISH ▼"}</div></div>', unsafe_allow_html=True)
                with sc4:
                    bp_pos = (price - row["BB_Lower"]) / (row["BB_Upper"] - row["BB_Lower"]) * 100 if (row["BB_Upper"] - row["BB_Lower"]) != 0 else 50
                    st.markdown(f'<div class="stat-tile blue"><div class="stat-label">BB POSITION</div><div class="stat-value">{bp_pos:.0f}%</div><div class="stat-sub">0%=lower · 100%=upper</div></div>', unsafe_allow_html=True)
            elif "Mid" in term_view:
                st.markdown('<div class="sec-hdr">MID TERM SIGNALS (Weeks to Months)</div>', unsafe_allow_html=True)
                sc1,sc2,sc3,sc4 = st.columns(4)
                with sc1:
                    ab50 = row["Close"] > row["SMA50"]
                    c = "green" if ab50 else "red"
                    st.markdown(f'<div class="stat-tile {c}"><div class="stat-label">50 DMA</div><div class="stat-value {c}">{"ABOVE ▲" if ab50 else "BELOW ▼"}</div></div>', unsafe_allow_html=True)
                with sc2:
                    rsi_v = row["RSI"]
                    rsig = "HEALTHY" if 40<rsi_v<65 else ("OVERBOUGHT" if rsi_v>=65 else "OVERSOLD")
                    rc = "green" if rsig=="HEALTHY" else ("red" if rsig=="OVERBOUGHT" else "amber")
                    st.markdown(f'<div class="stat-tile {rc}"><div class="stat-label">RSI (14)</div><div class="stat-value {rc}">{rsi_v:.1f} — {rsig}</div></div>', unsafe_allow_html=True)
                with sc3:
                    golden = row["SMA50"] > row["SMA200"] if not (np.isnan(row["SMA50"]) or np.isnan(row["SMA200"])) else False
                    c = "green" if golden else "red"
                    st.markdown(f'<div class="stat-tile {c}"><div class="stat-label">50/200 CROSS</div><div class="stat-value {c}">{"GOLDEN ▲" if golden else "DEATH ▼"}</div></div>', unsafe_allow_html=True)
                with sc4:
                    st.markdown(f'<div class="stat-tile blue"><div class="stat-label">SUPPORT</div><div class="stat-value">₹{bp["support"]:,.0f}</div><div class="stat-sub">60-day low</div></div>', unsafe_allow_html=True)
            else:  # Long term or All
                st.markdown('<div class="sec-hdr">LONG TERM SIGNALS (Months to Years)</div>', unsafe_allow_html=True)
                sc1,sc2,sc3,sc4 = st.columns(4)
                with sc1:
                    ab200 = row["Close"] > row["SMA200"] if not np.isnan(row["SMA200"]) else False
                    c = "green" if ab200 else "red"
                    st.markdown(f'<div class="stat-tile {c}"><div class="stat-label">200 DMA</div><div class="stat-value {c}">{"ABOVE ▲" if ab200 else "BELOW ▼"}</div></div>', unsafe_allow_html=True)
                with sc2:
                    rsi_v = row["RSI"]
                    rsig = "HEALTHY" if 40<rsi_v<65 else ("OVERBOUGHT" if rsi_v>=65 else "OVERSOLD")
                    rc = "green" if rsig=="HEALTHY" else ("red" if rsig=="OVERBOUGHT" else "amber")
                    st.markdown(f'<div class="stat-tile {rc}"><div class="stat-label">RSI (14)</div><div class="stat-value {rc}">{rsi_v:.1f} — {rsig}</div></div>', unsafe_allow_html=True)
                with sc3:
                    st.markdown(f'<div class="stat-tile blue"><div class="stat-label">STRONG SUPPORT</div><div class="stat-value">₹{bp["strong_support"]:,.0f}</div><div class="stat-sub">120-day low</div></div>', unsafe_allow_html=True)
                with sc4:
                    st.markdown(f'<div class="stat-tile blue"><div class="stat-label">RESISTANCE</div><div class="stat-value">₹{bp["resistance"]:,.0f}</div><div class="stat-sub">60-day high</div></div>', unsafe_allow_html=True)

            # ── Fibonacci table ───────────────────────────────
            if show_fib:
                st.markdown('<div class="sec-hdr" style="margin-top:12px;">📐 FIBONACCI RETRACEMENT LEVELS</div>', unsafe_allow_html=True)
                fib = compute_fibonacci(df_view)
                f1,f2,f3,f4,f5,f6 = st.columns(6)
                for col,(lbl,val,desc) in zip([f1,f2,f3,f4,f5,f6], [
                    ("0%",    fib["f0"],    "Swing High"),
                    ("23.6%", fib["f236"],  "Weak retracement"),
                    ("38.2%", fib["f382"],  "Moderate support"),
                    ("50%",   fib["f500"],  "Midpoint"),
                    ("61.8%", fib["f618"],  "Golden ratio"),
                    ("100%",  fib["f1000"], "Swing Low"),
                ]):
                    is_near = abs(price - val) / price < 0.015  # within 1.5%
                    border = "border-left:3px solid #c9a84c;" if is_near else ""
                    col.markdown(
                        '<div style="background:var(--bg-card);border:1px solid var(--border);' + border +
                        'border-radius:6px;padding:10px 12px;margin-bottom:4px;">' +
                        '<div style="font-size:9px;color:var(--accent-gold);font-family:DM Mono,monospace;letter-spacing:1px;">' + lbl + (" ★" if is_near else "") + '</div>' +
                        '<div style="font-size:14px;font-weight:700;color:var(--text-primary);">₹' + f"{val:,.0f}" + '</div>' +
                        '<div style="font-size:9px;color:var(--text-muted);">' + desc + '</div></div>',
                        unsafe_allow_html=True
                    )

    with tab2:
        screener   = R.get("screener",{})
        peer_s     = R.get("peer_s",0);  peer_r = R.get("peer_r",[]); peer_w = R.get("peer_w",[])
        hist_s     = R.get("hist_s",0);  hist_r = R.get("hist_r",[]); hist_w = R.get("hist_w",[])
        prom_s     = R.get("prom_s",0);  fii_s  = R.get("fii_s",0)
        prom_pct   = R.get("promoter_pct",0); inst   = R.get("inst_pct",0)
        t20  = int((tech_s/5)*20);  f25 = int((fund_s/5)*25)
        st.markdown(f'<div class="sec-hdr">7-SOURCE COMPOSITE SCORE: {score_100}/100 — {decision}</div>', unsafe_allow_html=True)
        sources = [
            ("NSE/BSE Technical",  t20,  20, "#4a9eff",  tech_r,  tech_w),
            ("Screener Fundamental",f25, 25, "#3ecf8e",  fund_r,  fund_w),
            ("Promoter Holding",   prom_s,15,"#c9a84c",  [f"Promoter: {prom_pct:.1f}%" if prom_pct else "Data unavailable"],[]),
            ("FII / DII Inst.",    fii_s, 15,"#2dd4bf",  [f"Institutional: {inst:.1f}%" if inst else "Data unavailable"],[]),
            ("Peer Comparison",    peer_s,15,"#a78bfa",  peer_r,  peer_w),
            ("Historical Patterns",hist_s,10,"#f59e0b",  hist_r,  hist_w),
        ]
        col_list = st.columns(3)
        for i,(name,sc,mx,clr,pos,neg) in enumerate(sources):
            with col_list[i%3]:
                pct_fill = int(sc/mx*100)
                pos_html = "".join(f'<div style="font-size:10px;color:#a8b8cc;padding:2px 0;border-bottom:1px solid #1e2d46;">▸ {p[:55]}</div>' for p in pos[:2])
                neg_html = "".join(f'<div style="font-size:10px;color:#f07070;padding:2px 0;border-bottom:1px solid #1e2d46;">▾ {n[:55]}</div>' for n in neg[:2])
                st.markdown(f"""<div style="background:linear-gradient(145deg,#111827,#0d1220);border:1px solid #1e2d46;
                    border-radius:8px;padding:14px 16px;margin-bottom:12px;">
                  <div style="font-family:'DM Mono',monospace;font-size:9px;letter-spacing:2px;color:#5a7090;margin-bottom:6px;">{name.upper()}</div>
                  <div style="font-family:'Fraunces',serif;font-size:32px;font-weight:700;color:{clr};line-height:1;">{sc:.0f}<span style="font-size:12px;color:#2e4060;">/{mx}</span></div>
                  <div style="height:4px;background:#1e2d46;border-radius:2px;margin:8px 0 10px;overflow:hidden;">
                    <div style="width:{pct_fill}%;height:100%;background:{clr};border-radius:2px;"></div>
                  </div>
                  {pos_html}{neg_html}
                </div>""", unsafe_allow_html=True)

        if screener.get("ok"):
            st.markdown('<div class="sec-hdr" style="margin-top:4px;">SCREENER.IN DATA</div>', unsafe_allow_html=True)
            s1,s2,s3,s4,s5 = st.columns(5)
            for col,(lbl,val) in zip([s1,s2,s3,s4,s5],[
                ("PE",f"{screener.get('pe'):.1f}x" if screener.get("pe") else "—"),
                ("ROE",f"{screener.get('roe')*100:.1f}%" if screener.get("roe") else "—"),
                ("ROCE",f"{screener.get('roce')*100:.1f}%" if screener.get("roce") else "—"),
                ("SALES GR",f"{screener.get('sales_growth')*100:.1f}%" if screener.get("sales_growth") else "—"),
                ("PROMOTER",f"{screener.get('promoter_pct'):.1f}%" if screener.get("promoter_pct") else "—"),
            ]):
                with col:
                    st.markdown(f'<div class="metric-card"><div class="metric-label">{lbl}</div><div class="metric-val">{val}</div></div>', unsafe_allow_html=True)

    with tab3:
        peer_details = R.get("peer_details",[])
        st.markdown(f'<div class="sec-hdr">SECTOR PEER COMPARISON — Score {peer_s:.0f}/15</div>', unsafe_allow_html=True)
        if peer_details:
            self_pe  = R.get("screener",{}).get("pe") or safe_get(info.get("trailingPE"))
            self_roe = R.get("screener",{}).get("roe") or safe_get(info.get("returnOnEquity"))
            self_sg  = safe_get(info.get("revenueGrowth"))
            rows_html = f"""<tr style="background:rgba(201,168,76,0.06);border-left:3px solid #c9a84c;">
              <td style="padding:10px 16px;font-weight:600;color:#e8c96e;">{company_name[:22]} ★</td>
              <td style="padding:10px 16px;font-family:'DM Mono',monospace;color:#e8c96e;">{f"{self_pe:.1f}x" if self_pe else "—"}</td>
              <td style="padding:10px 16px;font-family:'DM Mono',monospace;color:#e8c96e;">{pct(self_roe) if self_roe else "—"}</td>
              <td style="padding:10px 16px;font-family:'DM Mono',monospace;color:#e8c96e;">{pct(self_sg) if self_sg is not None else "—"}</td>
            </tr>"""
            for p in peer_details:
                r1y_c = "#3ecf8e" if (p.get("r1y") or 0)>=0 else "#e05252"
                rows_html += f"""<tr>
                  <td style="padding:10px 16px;color:#a8b8cc;">{p.get("name",p["ticker"])[:22]}</td>
                  <td style="padding:10px 16px;font-family:'DM Mono',monospace;">{f"{p['pe']:.1f}x" if p.get("pe") else "—"}</td>
                  <td style="padding:10px 16px;font-family:'DM Mono',monospace;">{pct(p.get("roe")) if p.get("roe") else "—"}</td>
                  <td style="padding:10px 16px;font-family:'DM Mono',monospace;color:{r1y_c};">{f"{(p.get('r1y') or 0)*100:+.0f}%" }</td>
                </tr>"""
            st.markdown(f"""<div class="t-card">
              <table style="width:100%;border-collapse:collapse;font-size:12px;">
                <thead><tr style="background:#0d1220;border-bottom:1px solid #1e2d46;">
                  <th style="padding:9px 16px;font-family:'DM Mono',monospace;font-size:9px;letter-spacing:2px;color:#2e4060;text-align:left;">COMPANY</th>
                  <th style="padding:9px 16px;font-family:'DM Mono',monospace;font-size:9px;letter-spacing:2px;color:#2e4060;text-align:left;">P/E</th>
                  <th style="padding:9px 16px;font-family:'DM Mono',monospace;font-size:9px;letter-spacing:2px;color:#2e4060;text-align:left;">ROE</th>
                  <th style="padding:9px 16px;font-family:'DM Mono',monospace;font-size:9px;letter-spacing:2px;color:#2e4060;text-align:left;">1Y RETURN</th>
                </tr></thead><tbody>{rows_html}</tbody>
              </table>
            </div>""", unsafe_allow_html=True)
            for item in peer_r: st.markdown(f'<div class="ok-block">◆ {item}</div>', unsafe_allow_html=True)
            for item in peer_w: st.markdown(f'<div class="danger-block">◈ {item}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="warn-block">No peer data available for this ticker.</div>', unsafe_allow_html=True)

    with tab4:
        st.markdown(render_dividend_section(div_data), unsafe_allow_html=True)

    with tab5:
        bp_c1,bp_c2 = st.columns(2)
        with bp_c1:
            st.markdown('<div class="sec-hdr">STAGGERED ENTRY PLAN</div>', unsafe_allow_html=True)
            for lbl,ep,note,clr in [
                ("TRANCHE 1 — 40%", f"₹{bp['current']:,.2f}", "Current price", "#0090ff"),
                ("TRANCHE 2 — 30%", f"₹{bp['support']:,.2f}", "Buy at support on dip", "#ffb000"),
                ("TRANCHE 3 — 30%", f"₹{bp['strong_support']:,.2f}", "Deep dip / strong support", "#ff3b5c"),
            ]:
                st.markdown(f"""<div class="metric-card" style="border-left-color:{clr};">
                    <div class="metric-label">{lbl}</div>
                    <div class="metric-val" style="color:{clr};">{ep}</div>
                    <div class="metric-note">{note}</div>
                </div>""", unsafe_allow_html=True)
            st.markdown(f'<div class="warn-block">⚠️ STOP LOSS: ₹{bp["stop_loss"]} (2× ATR of ₹{bp["atr"]})</div>', unsafe_allow_html=True)
        with bp_c2:
            st.markdown('<div class="sec-hdr">3-YEAR PROJECTION</div>', unsafe_allow_html=True)
            st.markdown(f"""<div class="t-card">
                <div style="padding:20px;">
                    <div class="stat-label">EXPECTED CAGR</div>
                    <div style="font-family:var(--font-mono,'Fira Code',monospace);font-size:44px;font-weight:700;color:#0090ff;margin:8px 0;">{cagr}%</div>
                    <div class="stat-sub">Conservatively blended estimate</div>
                    <hr class="t-divider">
                    <div style="display:flex;justify-content:space-between;align-items:flex-end;">
                        <div>
                            <div class="stat-label">CURRENT PRICE</div>
                            <div style="font-family:var(--font-mono,'Fira Code',monospace);font-size:18px;color:#e8edf2;">₹{price:,.2f}</div>
                        </div>
                        <div style="text-align:right;">
                            <div class="stat-label">3Y TARGET</div>
                            <div style="font-family:var(--font-mono,'Fira Code',monospace);font-size:26px;font-weight:700;color:#00c87a;">₹{proj_3y:,.0f}</div>
                            <div class="stat-sub">by {datetime.now().year+3}</div>
                        </div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

    with tab6:
        sent_col = "#3ecf8e" if "Positive" in sent_label else ("#e05252" if "Negative" in sent_label else "#c9a84c")
        st.markdown(f"""<div class="stat-tile" style="border-top-color:{sent_col};margin-bottom:16px;">
            <div class="stat-label">OVERALL SENTIMENT</div>
            <div style="font-size:20px;font-weight:700;color:{sent_col};margin-top:8px;">{sent_label.upper()}</div>
            <div class="stat-sub">Based on recent news flow analysis</div>
        </div>""", unsafe_allow_html=True)
        st.markdown('<div class="t-card">', unsafe_allow_html=True)
        for h in headlines:
            hl = h.lower()
            pc = sum(1 for w in POSITIVE_WORDS if w in hl)
            nc = sum(1 for w in NEGATIVE_WORDS if w in hl)
            if pc > nc: st_html = '<span class="sent-pos">POSITIVE</span>'
            elif nc > pc: st_html = '<span class="sent-neg">NEGATIVE</span>'
            else: st_html = '<span class="sent-neu">NEUTRAL</span>'
            st.markdown(f"""<div class="news-item">
                <div class="news-headline">{h}</div>
                <div class="news-meta">{st_html}</div>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab7:
        st.markdown('<div class="sec-hdr">EXPERT ANALYSIS</div>', unsafe_allow_html=True)
        safe_commentary = (commentary or "Analysis not available.").replace(chr(10), "<br>")
        st.markdown(f'<div class="info-block" style="font-size:13px;line-height:1.8;">{safe_commentary}</div>', unsafe_allow_html=True)
        desc = safe_get(info.get("longBusinessSummary"))
        if desc:
            st.markdown('<div class="sec-hdr" style="margin-top:20px;">COMPANY OVERVIEW</div>', unsafe_allow_html=True)
            safe_desc = desc[:2000].replace("<", "&lt;").replace(">", "&gt;")
            st.markdown(f'<div class="info-block" style="font-size:12px;line-height:1.7;color:#a8b8cc;">{safe_desc}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# COMPARE PAGE
# ─────────────────────────────────────────────
def page_compare():
    st.markdown("""
    <div style="padding:0 0 16px;">
        <div style="font-family:'Fraunces',serif;font-size:24px;font-weight:600;color:var(--text-primary);">PORTFOLIO COMPARISON</div>
        <div style="font-family:var(--font-mono,'Fira Code',monospace);font-size:10px;color:var(--text-muted);">SIDE-BY-SIDE PERFORMANCE & QUALITY METRICS</div>
    </div>""", unsafe_allow_html=True)

    portfolios = st.session_state.get("portfolios",[])
    if not portfolios:
        st.markdown('<div class="warn-block">No portfolios yet. Add a portfolio first.</div>', unsafe_allow_html=True)
        return

    cols = st.columns(min(len(portfolios),3))
    best_pnl = max((pf.get("pnl_pct",0) for pf in portfolios), default=0)

    for i,(pf,col) in enumerate(zip(portfolios,cols)):
        with col:
            results = pf.get("results",[])
            stocks  = pf.get("stocks",[])
            pf_inv  = sum(r.get("invested",0) for r in results) or sum(s.get("invested",0) for s in stocks)
            pf_mkt  = sum(r.get("market_value",0) for r in results)
            pf_pnl  = pf_mkt - pf_inv if pf_mkt > 0 else 0
            pf_pnl_pct = (pf_pnl/pf_inv*100) if pf_inv>0 else 0
            buy_c   = sum(1 for r in results if r.get("decision")=="BUY")
            hold_c  = sum(1 for r in results if r.get("decision")=="HOLD")
            avoid_c = sum(1 for r in results if r.get("decision")=="AVOID")
            avg_score = round(np.mean([r.get("score_100",50) for r in results])) if results else "—"
            avg_roe   = np.mean([r.get("roe") for r in results if r.get("roe")]) if any(r.get("roe") for r in results) else None
            total_div = sum(r.get("div_data",{}).get("total_received",0) for r in results if r.get("div_data"))
            color   = pf.get("color",portfolio_color(i))
            pnl_col = "#00c87a" if pf_pnl>=0 else "#ff3b5c"
            is_best = pf_pnl_pct >= best_pnl and pf_pnl_pct > 0
            border  = f"border:1px solid {color};" if is_best else ""

            st.markdown(f"""<div class="cmp-card" style="{border}">
                <div class="cmp-hdr" style="{'background:rgba(0,200,122,0.06);' if is_best else ''}">
                    <div style="width:9px;height:9px;border-radius:50%;background:{color};"></div>
                    <div class="cmp-name">{pf['name']}</div>
                    {'<div style="background:rgba(0,200,122,0.15);color:#00c87a;font-family:\'Fira Code\',monospace;font-size:9px;font-weight:700;padding:2px 7px;border-radius:2px;margin-left:auto;">🏆 BEST</div>' if is_best else f'<div style="margin-left:auto;font-family:\'Fira Code\',monospace;font-size:9px;color:var(--text-muted);">{len(stocks)} STKS</div>'}
                </div>
                <div style="padding:12px 16px;">
                    <div class="cstat"><span class="cstat-label">Invested</span><span class="cstat-val">₹{pf_inv:,.0f}</span></div>
                    <div class="cstat"><span class="cstat-label">Current Value</span><span class="cstat-val">₹{pf_mkt:,.0f}</span></div>
                    <div class="cstat"><span class="cstat-label">P&L</span><span class="cstat-val" style="color:{pnl_col};">₹{pf_pnl:+,.0f} ({pf_pnl_pct:+.1f}%)</span></div>
                    <div class="cstat"><span class="cstat-label">Avg Score</span><span class="cstat-val">{avg_score}/100</span></div>
                    <div class="cstat"><span class="cstat-label">Avg ROE</span><span class="cstat-val">{pct(avg_roe) if avg_roe else '—'}</span></div>
                    <div class="cstat"><span class="cstat-label">Div Income 3Y</span><span class="cstat-val" style="color:#ffb000;">{fmt_inr(total_div) if total_div>0 else '—'}</span></div>
                </div>
                <div style="display:flex;gap:4px;padding:8px 12px;border-top:1px solid #1e2d3d;">
                    <div style="flex:1;text-align:center;background:rgba(0,200,122,0.08);border:1px solid rgba(0,200,122,0.2);border-radius:2px;padding:4px;font-family:var(--font-mono,'Fira Code',monospace);font-size:10px;color:#00c87a;">B {buy_c}</div>
                    <div style="flex:1;text-align:center;background:rgba(255,176,0,0.08);border:1px solid rgba(255,176,0,0.2);border-radius:2px;padding:4px;font-family:var(--font-mono,'Fira Code',monospace);font-size:10px;color:#ffb000;">H {hold_c}</div>
                    <div style="flex:1;text-align:center;background:rgba(255,59,92,0.08);border:1px solid rgba(255,59,92,0.2);border-radius:2px;padding:4px;font-family:var(--font-mono,'Fira Code',monospace);font-size:10px;color:#ff3b5c;">A {avoid_c}</div>
                </div>
            </div>""", unsafe_allow_html=True)

    # Unified table
    all_res = [(pf,r) for pf in portfolios for r in pf.get("results",[])]
    if all_res:
        st.markdown("<br>", unsafe_allow_html=True)
        rows_html = ""
        for pf,r in sorted(all_res, key=lambda x:-x[1].get("score_100",0)):
            color   = pf.get("color","#0090ff")
            pnl_pct = r.get("pnl_pct",0)
            pnl_s   = f"+{pnl_pct:.1f}%" if pnl_pct>=0 else f"{pnl_pct:.1f}%"
            pnl_col = "#00c87a" if pnl_pct>=0 else "#ff3b5c"
            sc      = r.get("score_100",50)
            div     = r.get("div_data") or {}
            dy      = f"{div.get('yield_pct'):.1f}%" if div.get("yield_pct") else "—"
            rows_html += f"""<tr>
                <td><div style="display:flex;align-items:center;gap:6px;">
                    <div style="width:6px;height:6px;border-radius:50%;background:{color};"></div>
                    <span style="font-family:var(--font-mono,'Fira Code',monospace);font-size:9px;color:var(--text-muted);">{pf['name'][:12]}</span>
                </div></td>
                <td><div style="font-weight:600;">{r['name'][:20]}</div></td>
                <td class="mono">₹{r.get('cmp',0):,.0f}</td>
                <td class="mono" style="color:{pnl_col};">{pnl_s}</td>
                <td>{score_bar_html(sc)}</td>
                <td class="mono">{pct(r.get('roe')) if r.get('roe') else '—'}</td>
                <td class="mono">{f"{r.get('pe'):.1f}x" if r.get('pe') else '—'}</td>
                <td class="mono">{dy}</td>
                <td>{decision_badge(r.get('decision','HOLD'))}</td>
            </tr>"""

        st.markdown(f"""<div class="t-card">
            <div class="t-card-header"><div class="t-card-title">ALL STOCKS — UNIFIED VIEW ({len(all_res)} stocks)</div></div>
            <table class="t-table"><thead><tr>
                <th>Portfolio</th><th>Company</th><th>CMP</th><th>P&L</th>
                <th>Score</th><th>ROE</th><th>P/E</th><th>Div Yield</th><th>Signal</th>
            </tr></thead><tbody>{rows_html}</tbody></table>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="info-block">💡 Analyze your portfolios first to see the unified comparison view.</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD — unified overview of everything
# ═══════════════════════════════════════════════════════════════════
def page_dashboard():
    """Single-page overview: stocks + MF + wealth + budget snapshot."""
    from datetime import datetime as _dt

    st.markdown(f"""<div style="padding:0 0 20px;">
        <div style="font-family:var(--font-serif,'Fraunces',serif);font-size:24px;font-weight:600;color:var(--text-primary);">Dashboard</div>
        <div style="font-size:12px;color:var(--text-muted);margin-top:2px;">
            {_dt.now().strftime('%d %B %Y')} · Complete financial snapshot</div>
    </div>""", unsafe_allow_html=True)

    portfolios = st.session_state.get("portfolios", [])

    # ── Row 1: Key numbers ────────────────────────────────────
    all_results   = [r for pf in portfolios for r in pf.get("results", [])]
    total_invested= sum(r.get("invested",0) for r in all_results) or \
                    sum(s.get("invested",0) for pf in portfolios for s in pf.get("stocks",[]))
    total_mkt     = sum(r.get("market_value",0) for r in all_results) or total_invested
    total_pnl     = total_mkt - total_invested
    total_stocks  = sum(len(pf.get("stocks",[])) for pf in portfolios)
    pnl_pct       = (total_pnl/total_invested*100) if total_invested>0 else 0

    # MF totals
    mf_invested = mf_value = mf_sip = 0
    try:
        from mf_module import all_funds, get_store as _mgs
        mff = all_funds(_mgs())
        mf_invested = sum(float(f.get("invested",0) or 0) for f in mff)
        mf_value    = sum(float(f.get("current_value",0) or f.get("invested",0) or 0) for f in mff)
        mf_sip      = sum(float(f.get("sip",0) or 0) for f in mff)
    except Exception:
        pass

    # Wealth totals from finance profile
    wealth_total = loan_total = 0
    try:
        from finance_advisor import get_profile as _gp
        fp = _gp()
        wealth_total = (
            float(fp.get("epf_balance",0) or 0) +
            float(fp.get("nps_balance",0) or 0) +
            sum(float(f.get("amount",0) or 0) for f in fp.get("fd_list",[])) +
            sum(float(g.get("grams",0) or 0)*max(1,float(g.get("rate",7500) or 7500)) for g in fp.get("gold_list",[])) +
            sum(float(r.get("current",0) or 0) for r in fp.get("re_list",[]))
        )
        loan_total = sum(float(l.get("outstanding",0) or 0) for l in fp.get("loan_list",[]))
    except Exception:
        pass

    # Budget snapshot
    budget_income = budget_exp = budget_sav = 0
    try:
        from finance_advisor import get_month_budget, current_month_key, _budget_summary
        bgt = get_month_budget(current_month_key())
        budget_income, budget_exp, budget_sav, _, _, _ = _budget_summary(bgt)
    except Exception:
        pass

    family_nw = total_mkt + mf_value + wealth_total - loan_total
    pnl_color = "var(--accent-green)" if total_pnl >= 0 else "var(--accent-red)"

    # ── Net worth banner ──────────────────────────────────────
    st.markdown(f"""<div style="background:var(--bg-card);border:1px solid var(--border);
        border-left:4px solid var(--accent-gold);border-radius:10px;
        padding:20px 24px;margin-bottom:20px;
        display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
        <div>
            <div style="font-size:13px;color:var(--text-muted);font-weight:500;
                letter-spacing:0.5px;margin-bottom:4px;">TOTAL FAMILY NET WORTH</div>
            <div style="font-family:var(--font-serif,'Fraunces',serif);font-size:36px;font-weight:700;color:var(--text-primary);">
                {fmt_inr(family_nw)}</div>
            <div style="font-size:12px;color:var(--text-muted);margin-top:4px;">
                Stocks + MF + Wealth − Loans</div>
        </div>
        <div style="display:flex;gap:24px;flex-wrap:wrap;">
            <div style="text-align:center;">
                <div style="font-size:10px;color:var(--text-muted);margin-bottom:3px;">STOCKS</div>
                <div style="font-family:var(--font-mono,'IBM Plex Mono',monospace);font-size:18px;font-weight:600;color:var(--text-primary);">{fmt_inr(total_mkt)}</div>
                <div style="font-family:var(--font-mono,'IBM Plex Mono',monospace);font-size:11px;color:{pnl_color};">{total_pnl:+,.0f}</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:10px;color:var(--text-muted);margin-bottom:3px;">MF</div>
                <div style="font-family:var(--font-mono,'IBM Plex Mono',monospace);font-size:18px;font-weight:600;color:var(--text-primary);">{fmt_inr(mf_value)}</div>
                <div style="font-family:var(--font-mono,'IBM Plex Mono',monospace);font-size:11px;color:var(--accent-blue);">SIP {fmt_inr(mf_sip)}/mo</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:10px;color:var(--text-muted);margin-bottom:3px;">WEALTH</div>
                <div style="font-family:var(--font-mono,'IBM Plex Mono',monospace);font-size:18px;font-weight:600;color:var(--text-primary);">{fmt_inr(wealth_total)}</div>
                <div style="font-family:var(--font-mono,'IBM Plex Mono',monospace);font-size:11px;color:var(--accent-red);">Loans {fmt_inr(loan_total)}</div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── 3 non-stock summary cards (stocks get full detail below) ──
    c1,c2,c3 = st.columns(3)
    cards = [
        ("MF Value",  fmt_inr(mf_value),   f"Invested {fmt_inr(mf_invested)}", "var(--accent-blue)"),
        ("This Month Income",  fmt_inr(budget_income), f"Exp {fmt_inr(budget_exp)} · Sav {fmt_inr(budget_sav)}", "var(--accent-green)"),
        ("Loans Outstanding",  fmt_inr(loan_total),  f"Wealth {fmt_inr(wealth_total)}", "var(--accent-red)"),
    ]
    for col,(lbl,val,sub,ac) in zip([c1,c2,c3], cards):
        with col:
            st.markdown(f"""<div style="background:var(--bg-card);border:1px solid var(--border);
                border-top:3px solid {ac};border-radius:8px;padding:14px 16px;margin-bottom:16px;">
                <div style="font-size:10px;font-weight:600;letter-spacing:1px;
                    color:var(--text-muted);margin-bottom:6px;">{lbl}</div>
                <div style="font-family:var(--font-mono,'IBM Plex Mono',monospace);font-size:20px;font-weight:700;color:{ac};margin-bottom:3px;">{val}</div>
                <div style="font-size:11px;color:var(--text-muted);">{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Stocks — the one place these numbers live ─────────────
    st.markdown('<div style="font-size:13px;font-weight:600;color:var(--text-primary);margin-bottom:10px;">Stock Portfolios</div>', unsafe_allow_html=True)
    if portfolios:
        render_stock_summary_block(portfolios)
    else:
        st.markdown("""<div style="background:var(--bg-card);border:1px solid var(--border);
            border-radius:8px;padding:24px;text-align:center;margin-bottom:16px;">
            <div style="font-size:14px;color:var(--text-muted);margin-bottom:8px;">No portfolios yet</div>
            <div style="font-size:12px;color:var(--text-muted);">Go to Portfolio tab → Add Portfolio to get started</div>
        </div>""", unsafe_allow_html=True)

    # ── Budget progress bar ───────────────────────────────────
    if budget_income > 0:
        st.markdown('<br>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:13px;font-weight:600;color:var(--text-primary);margin-bottom:10px;">This Month\'s Budget</div>', unsafe_allow_html=True)
        exp_pct = min(100, round(budget_exp/budget_income*100))
        sav_pct = min(100, round(budget_sav/budget_income*100))
        for label, pct_val, color in [
            ("Expenses", exp_pct, "var(--accent-red)"),
            ("Savings",  sav_pct, "var(--accent-green)"),
        ]:
            st.markdown(f"""<div style="margin-bottom:10px;">
                <div style="display:flex;justify-content:space-between;font-size:12px;
                    color:var(--text-secondary);margin-bottom:4px;">
                    <span>{label}</span><span style="font-weight:600;">{pct_val}%</span>
                </div>
                <div style="height:6px;background:var(--border);border-radius:3px;overflow:hidden;">
                    <div style="width:{pct_val}%;height:100%;background:{color};border-radius:3px;"></div>
                </div>
            </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# PAGE: PORTFOLIO — Stocks + MF in one place
# ═══════════════════════════════════════════════════════════════════
def page_portfolio():
    """Stocks & Mutual Funds — both in sub-tabs."""
    st.markdown("""<div style="padding:0 0 16px;">
        <div style="font-family:var(--font-serif,'Fraunces',serif);font-size:22px;font-weight:600;color:var(--text-primary);">Portfolio</div>
        <div style="font-size:12px;color:var(--text-muted);margin-top:2px;">
            Stocks · Mutual Funds · Analysis · Compare</div>
    </div>""", unsafe_allow_html=True)

    sub = st.tabs(["📈 Stocks", "💼 Mutual Funds", "🔍 Analyzer", "⚖️ Compare"])

    with sub[0]:
        # Stocks — existing page_overview logic
        page_overview()

    with sub[1]:
        # MF — existing mf_module
        if _MF_AVAILABLE:
            try:
                page_mf_portfolio()
            except Exception:
                import traceback
                st.error(f"MF module error: {traceback.format_exc()[:300]}")
        else:
            st.warning(f"MF Portfolio module not loaded: {_MF_ERR}")
            st.info("Make sure `mf_module.py` is in the same folder as this file.")

    with sub[2]:
        # Deep stock analyzer
        try:
            page_analyzer()
        except Exception:
            import traceback
            st.error(f"Analyzer error: {traceback.format_exc()[:300]}")

    with sub[3]:
        # Compare portfolios
        try:
            page_compare()
        except Exception:
            import traceback
            st.error(f"Compare error: {traceback.format_exc()[:300]}")


# ═══════════════════════════════════════════════════════════════════
# PAGE: WEALTH — Assets, EPF, NPS, Gold, Property, FDs, Loans, Goals, Projections
# ═══════════════════════════════════════════════════════════════════
def page_wealth():
    """All wealth / investment data from the Finance module — minus Budget."""
    st.markdown("""<div style="padding:0 0 16px;">
        <div style="font-family:var(--font-serif,'Fraunces',serif);font-size:22px;font-weight:600;color:var(--text-primary);">Wealth</div>
        <div style="font-size:12px;color:var(--text-muted);margin-top:2px;">
            Assets · EPF/NPS · Gold · Property · FDs · Loans · Goals · Projections</div>
    </div>""", unsafe_allow_html=True)

    from finance_advisor import (
        fa_load, get_profile, render_profile_section,
        render_assets_section, render_liabilities_section,
        render_goals_section, render_projections_section,
        render_template_import_inner, fa_save
    )
    import json as _json

    if not st.session_state.get("fa_loaded"):
        fa_load()

    p = get_profile()

    # ── Header / backup bar ───────────────────────────────────
    hc1, hc2 = st.columns([3, 2])
    with hc1:
        if p.get("self_name"):
            st.markdown(f"""<div style="background:var(--bg-card);border:1px solid var(--border);
                border-radius:8px;padding:8px 14px;margin-bottom:16px;font-size:12px;">
                <span style="color:var(--accent-green);font-weight:600;">✅ {p.get('self_name')}</span>
                {"  +  <span style='color:var(--accent-gold);font-weight:600;'>" + p.get('spouse_name','') + "</span>" if p.get('include_spouse') and p.get('spouse_name') else ""}
                <span style="color:var(--text-muted);margin-left:8px;">profile loaded</span>
            </div>""", unsafe_allow_html=True)
    with hc2:
        if p.get("self_name"):
            import datetime as _dt2
            profile_json = _json.dumps(p, indent=2, default=str)
            fname = f"equitex_{p.get('self_name','profile').replace(' ','_')}_{_dt2.date.today()}.json"
            st.download_button("⬇ Backup profile", data=profile_json,
                file_name=fname, mime="application/json", key="wealth_dl_backup")

    # ── Import / restore ──────────────────────────────────────
    with st.expander("📂 Import / Restore profile", expanded=not p.get("self_name")):
        rt1, rt2 = st.tabs(["🔄 Restore JSON", "📥 Import Excel template"])
        with rt1:
            bk = st.file_uploader("Upload JSON backup", type=["json"],
                key="wealth_backup_upload", label_visibility="collapsed")
            if bk:
                try:
                    restored = _json.loads(bk.read().decode("utf-8"))
                    if isinstance(restored, dict) and restored.get("self_name"):
                        st.session_state.fa_profile = restored
                        st.session_state.fa_loaded  = True
                        fa_save()
                        st.success(f"✅ Restored {restored.get('self_name')}")
                        st.rerun()
                    else:
                        st.error("Doesn't look like an EQUITEX backup.")
                except Exception as e:
                    st.error(f"Could not read backup: {e}")
        with rt2:
            render_template_import_inner()

    # ── Sub-tabs ──────────────────────────────────────────────
    wtabs = st.tabs(["👤 Profile", "🏦 Assets", "💳 Loans", "🎯 Goals", "📈 Projections"])
    with wtabs[0]: render_profile_section()
    with wtabs[1]: render_assets_section()
    with wtabs[2]: render_liabilities_section()
    with wtabs[3]: render_goals_section()
    with wtabs[4]: render_projections_section()


# ═══════════════════════════════════════════════════════════════════
# PAGE: BUDGET — Monthly budget + Family dashboard
# ═══════════════════════════════════════════════════════════════════
def page_budget_tab():
    """Monthly budget & family financial dashboard."""
    st.markdown("""<div style="padding:0 0 16px;">
        <div style="font-family:var(--font-serif,'Fraunces',serif);font-size:22px;font-weight:600;color:var(--text-primary);">Budget</div>
        <div style="font-size:12px;color:var(--text-muted);margin-top:2px;">
            Monthly budgets · Family dashboard · Income & expense tracking</div>
    </div>""", unsafe_allow_html=True)

    from finance_advisor import (
        fa_load, render_budget_section, render_family_dashboard
    )
    if not st.session_state.get("fa_loaded"):
        fa_load()

    btabs = st.tabs(["📊 Monthly Budget", "👨‍👩‍👧 Family Dashboard"])
    with btabs[0]: render_budget_section()
    with btabs[1]: render_family_dashboard()


# ═══════════════════════════════════════════════════════════════════
# PAGE: AI ADVISOR — analyse stocks, MF, wealth, or all
# ═══════════════════════════════════════════════════════════════════
def page_ai_advisor():
    """AI advisor with context selector — stocks, MF, wealth, or full picture."""
    st.markdown("""<div style="padding:0 0 16px;">
        <div style="font-size:22px;font-weight:600;color:var(--text-primary);">AI Advisor</div>
        <div style="font-size:12px;color:var(--text-muted);margin-top:2px;">
            Powered by Llama 3.3 via Groq · Analyse your stocks, MF, wealth or full portfolio</div>
    </div>""", unsafe_allow_html=True)

    # ── Context selector ──────────────────────────────────────
    st.markdown("""<div style="font-size:12px;font-weight:600;color:var(--text-secondary);
        margin-bottom:8px;">What should the AI analyse?</div>""", unsafe_allow_html=True)

    context_opts = {
        "📈 Stock portfolios only":   "stocks",
        "💼 Mutual funds only":       "mf",
        "🏦 Wealth & assets only":    "wealth",
        "📊 Budget & cashflow only":  "budget",
        "🔍 Everything (full picture)": "all",
    }
    chosen_ctx = st.radio(
        "context", list(context_opts.keys()),
        horizontal=True, label_visibility="collapsed", key="ai_context_sel"
    )
    ctx_key = context_opts[chosen_ctx]

    st.markdown('<div style="border-bottom:1px solid var(--border);margin:12px 0 16px;"></div>',
                unsafe_allow_html=True)

    # ── Build context string based on selection ───────────────
    from finance_advisor import (
        fa_load, get_profile, build_financial_context,
        render_ai_advisor_section
    )
    if not st.session_state.get("fa_loaded"):
        fa_load()

    # Inject context key so the AI advisor section knows what to use
    st.session_state["ai_context_key"] = ctx_key

    # Augment context with stock data if needed
    portfolios = st.session_state.get("portfolios", [])
    if ctx_key in ("stocks", "all") and portfolios:
        all_results = [r for pf in portfolios for r in pf.get("results", [])]
        if all_results:
            total_inv = sum(r.get("invested",0) for r in all_results)
            total_mkt = sum(r.get("market_value",0) for r in all_results)
            buy_c  = sum(1 for r in all_results if r.get("decision")=="BUY")
            hold_c = sum(1 for r in all_results if r.get("decision")=="HOLD")
            avoid_c= sum(1 for r in all_results if r.get("decision")=="AVOID")
            stock_ctx = f"""
STOCK PORTFOLIO SUMMARY:
- Total invested: ₹{total_inv:,.0f}
- Current value: ₹{total_mkt:,.0f}
- P&L: ₹{total_mkt-total_inv:+,.0f} ({(total_mkt-total_inv)/max(1,total_inv)*100:+.1f}%)
- Signals: BUY {buy_c} · HOLD {hold_c} · AVOID {avoid_c}
- Top holdings: {", ".join(r['name'][:20] for r in sorted(all_results,key=lambda x:-x.get('market_value',0))[:5])}
"""
            st.session_state["ai_stock_context"] = stock_ctx
        else:
            st.info("💡 Analyse your stock portfolios first (Portfolio tab) to include stock signals in the AI context.")

    # MF context
    if ctx_key in ("mf", "all"):
        try:
            from mf_module import all_funds, get_store as _mgs
            mff = all_funds(_mgs())
            if mff:
                mv  = sum(float(f.get("current_value",0) or f.get("invested",0) or 0) for f in mff)
                mi  = sum(float(f.get("invested",0) or 0) for f in mff)
                ms  = sum(float(f.get("sip",0) or 0) for f in mff)
                st.session_state["ai_mf_context"] = f"""
MUTUAL FUND SUMMARY:
- Total MF value: ₹{mv:,.0f} (invested ₹{mi:,.0f})
- Monthly SIP: ₹{ms:,.0f}
- Funds: {", ".join(f.get("name","?")[:25] for f in mff[:5])}
"""
        except Exception:
            pass

    # Run the existing AI advisor (it reads groq key & builds finance context)
    render_ai_advisor_section()


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
# PORTFOLIO PERSISTENCE — equitex_data.json
# ─────────────────────────────────────────────
MAX_PORTFOLIOS = 5

def _strip_for_storage(portfolios):
    """Return a JSON-safe copy — no DataFrames, no yfinance info dicts."""
    safe = []
    for pf in portfolios:
        safe.append({
            "name":     pf.get("name", "Portfolio"),
            "color":    pf.get("color", "#4a9eff"),
            "stocks":   pf.get("stocks", []),
            "analyzed": False,
            "results":  [],
            "pnl_pct":  pf.get("pnl_pct", 0),
        })
    return safe

def save_portfolios():
    """Write current portfolios to unified equitex_data.json."""
    from equitex_store import save_portfolios as _store_save
    data = _strip_for_storage(st.session_state.get("portfolios", []))
    _store_save(data)

def render_storage_restore():
    """Load portfolios from unified equitex_data.json on first run."""
    if st.session_state.get("_restored"):
        return
    # First run of this session — load from disk
    try:
        from equitex_store import get_portfolios
        saved = get_portfolios()
        if saved:
            st.session_state.portfolios = saved[:MAX_PORTFOLIOS]
    except Exception as e:
        st.warning(f"Could not load portfolios: {e}")
    st.session_state._restored = True


def main():
    defaults = {
        "portfolios": [], "active_portfolio_idx": 0,
        "show_add_portfolio": False, "main_nav": "🏠  Dashboard",
        "theme": "ledger",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    inject_theme()
    render_storage_restore()

    try:
        page = render_navbar()

        if st.session_state.get("show_add_portfolio"):
            render_add_portfolio_modal()
            return

        def _safe_run(fn, label):
            try:
                fn()
            except Exception:
                import traceback
                st.markdown(f'<div class="danger-block">❌ Error in {label}:<br><pre style="font-size:11px;">{traceback.format_exc()[:600]}</pre></div>',
                            unsafe_allow_html=True)

        if "Dashboard" in page:
            _safe_run(page_dashboard, "Dashboard")

        elif "Portfolio" in page:
            _safe_run(page_portfolio, "Portfolio")

        elif "Wealth" in page:
            if _FA_AVAILABLE:
                _safe_run(page_wealth, "Wealth")
            else:
                st.error(f"Finance module could not load: {_FA_ERR}")

        elif "Budget" in page:
            if _FA_AVAILABLE:
                _safe_run(page_budget_tab, "Budget")
            else:
                st.error(f"Finance module could not load: {_FA_ERR}")

        elif "AI Advisor" in page:
            _safe_run(page_ai_advisor, "AI Advisor")

    except Exception:
        import traceback
        st.markdown(f'<div class="danger-block">❌ Critical error: {traceback.format_exc()[:400]}</div>',
                    unsafe_allow_html=True)


if __name__ == "__main__":
    main()
