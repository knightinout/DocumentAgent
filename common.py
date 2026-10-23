"""Shared UI helpers and styling for DocumentAgent's multipage Streamlit app."""

import uuid
from pathlib import Path

import streamlit as st

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}

# ── Design tokens ────────────────────────────────────────────────────────────
INK = "#0f172a"
MUTED = "#64748b"
BORDER = "#e2e8f0"
SURFACE = "#f8fafc"
ACCENT = "#4f46e5"
ACCENT_DARK = "#4338ca"
CLOUD_COLOR = "#0ea5e9"
LOCAL_COLOR = "#16a34a"

_DRAWER_WIDTH = "220px"
_HEADER_HEIGHT = "56px"


def init_session() -> None:
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())


def inject_theme() -> None:
    """Global styling — YouTube-style drawer + header."""
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body,
        [class*="css"]:not([data-testid="stIconMaterial"]),
        [data-testid="stAppViewContainer"] *:not([data-testid="stIconMaterial"]) {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}

        /* ── Hide default Streamlit chrome ──────────────────────────── */
        #MainMenu, footer, [data-testid="stMainMenu"],
        button[data-testid="stBaseButton-header"],
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="stSidebar"] button[aria-label*="Close"],
        [data-testid="stSidebar"] button[aria-label*="collapse"],
        [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"],
        [data-testid="stExpandSidebarButton"],
        button[data-testid="stExpandSidebarButton"] {{
            display: none !important;
        }}

        /* ── Fixed header bar ──────────────────────────────────────── */
        header[data-testid="stHeader"] {{
            background: #ffffff !important;
            border-bottom: 1px solid {BORDER};
            height: {_HEADER_HEIGHT} !important;
            z-index: 999;
        }}

        .da-header {{
            position: fixed; top: 0; left: 0; right: 0;
            height: {_HEADER_HEIGHT};
            background: #ffffff;
            border-bottom: 1px solid {BORDER};
            display: flex; align-items: center;
            padding: 0 16px;
            z-index: 1000;
            gap: 12px;
        }}
        .da-header-burger {{
            width: 40px; height: 40px;
            border: none; background: transparent;
            border-radius: 50%;
            cursor: pointer;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.4rem; color: {INK};
            transition: background 0.15s ease;
            flex-shrink: 0;
        }}
        .da-header-burger:hover {{ background: #f1f5f9; }}
        .da-header-logo {{
            display: flex; align-items: center; gap: 8px;
            text-decoration: none !important; cursor: pointer;
        }}
        .da-header-logo-icon {{
            width: 32px; height: 32px;
            background: {ACCENT};
            border-radius: 8px;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.1rem; color: white; font-weight: 800;
        }}
        .da-header-logo-text {{
            font-size: 1.05rem; font-weight: 800;
            color: {INK}; letter-spacing: -0.02em;
        }}

        /* ── Header nav links (Cloud / Local) ─────────────────────── */
        .da-header-nav {{
            display: flex; align-items: center; gap: 4px;
            margin-left: 16px;
        }}
        .da-header-nav a {{
            display: flex; align-items: center; gap: 6px;
            padding: 6px 14px; border-radius: 8px;
            font-size: 0.88rem; font-weight: 600;
            color: {MUTED}; text-decoration: none !important;
            transition: background 0.15s ease, color 0.15s ease;
        }}
        .da-header-nav a:hover {{
            background: #f1f5f9; color: {INK};
        }}
        .da-header-nav a.active {{
            background: #f1f5f9; color: {INK}; font-weight: 700;
        }}

        /* ── Dark mode toggle ─────────────────────────────────────── */
        .da-header-spacer {{ flex: 1; }}
        .da-theme-toggle {{
            width: 42px; height: 42px;
            border: 1px solid {BORDER};
            background: {SURFACE};
            border-radius: 10px; cursor: pointer;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.2rem; color: {INK};
            transition: background 0.15s ease, border-color 0.15s ease;
            flex-shrink: 0; margin-right: 12px;
        }}
        .da-theme-toggle:hover {{ background: #e2e8f0; }}

        /* ══════════════════════════════════════════════════════════
           DARK THEME — comprehensive override
           ══════════════════════════════════════════════════════════ */

        /* ── Header ────────────────────────────────────────────── */
        [data-da-theme="dark"] .da-header,
        [data-da-theme="dark"] header[data-testid="stHeader"] {{
            background: #1e1e2e !important;
            border-bottom-color: #313244 !important;
        }}
        [data-da-theme="dark"] .da-header-burger {{ color: #cdd6f4; }}
        [data-da-theme="dark"] .da-header-burger:hover {{ background: #313244; }}
        [data-da-theme="dark"] .da-header-logo-text {{ color: #cdd6f4; }}
        [data-da-theme="dark"] .da-header-nav a {{ color: #a6adc8; }}
        [data-da-theme="dark"] .da-header-nav a:hover {{ background: #313244; color: #cdd6f4; }}
        [data-da-theme="dark"] .da-header-nav a.active {{ background: #313244; color: #cdd6f4; }}
        [data-da-theme="dark"] .da-theme-toggle {{
            background: #313244; border-color: #45475a; color: #cdd6f4;
        }}
        [data-da-theme="dark"] .da-theme-toggle:hover {{ background: #45475a; }}

        /* ── Sidebar — all text + backgrounds ─────────────────── */
        [data-da-theme="dark"] [data-testid="stSidebar"] {{
            background: #1e1e2e !important;
            border-right-color: #313244 !important;
        }}
        [data-da-theme="dark"] [data-testid="stSidebar"] hr {{
            border-color: #313244 !important;
        }}
        [data-da-theme="dark"] [data-testid="stSidebar"] p,
        [data-da-theme="dark"] [data-testid="stSidebar"] span,
        [data-da-theme="dark"] [data-testid="stSidebar"] label,
        [data-da-theme="dark"] [data-testid="stSidebar"] div,
        [data-da-theme="dark"] [data-testid="stSidebar"] small {{
            color: #cdd6f4 !important;
        }}
        [data-da-theme="dark"] [data-testid="stSidebar"] strong {{
            color: #e4e8f7 !important;
        }}
        [data-da-theme="dark"] [data-testid="stSidebar"] [data-testid="stCaptionContainer"],
        [data-da-theme="dark"] [data-testid="stSidebar"] [data-testid="stCaptionContainer"] * {{
            color: #a6adc8 !important;
        }}
        [data-da-theme="dark"] [data-testid="stSidebarNav"] a {{
            color: #cdd6f4 !important;
        }}
        [data-da-theme="dark"] [data-testid="stSidebarNav"] a p {{
            color: #cdd6f4 !important;
        }}
        [data-da-theme="dark"] [data-testid="stSidebarNav"] a:hover {{
            background: #313244 !important;
        }}
        [data-da-theme="dark"] [data-testid="stSidebarNav"] a[aria-current="page"] {{
            background: #313244 !important;
            color: #ffffff !important;
        }}
        [data-da-theme="dark"] [data-testid="stSidebarNav"] a[aria-current="page"] p {{
            color: #ffffff !important;
        }}
        /* Sidebar inputs */
        [data-da-theme="dark"] [data-testid="stSidebar"] input,
        [data-da-theme="dark"] [data-testid="stSidebar"] select,
        [data-da-theme="dark"] [data-testid="stSidebar"] textarea {{
            background: #313244 !important; color: #cdd6f4 !important;
            border-color: #45475a !important;
        }}
        [data-da-theme="dark"] [data-testid="stSidebar"] button {{
            background: #313244 !important; color: #cdd6f4 !important;
            border-color: #45475a !important;
        }}
        [data-da-theme="dark"] [data-testid="stSidebar"] button:hover {{
            background: #45475a !important;
        }}

        /* ── Main content area ─────────────────────────────────── */
        [data-da-theme="dark"] [data-testid="stAppViewContainer"] {{
            background: #181825 !important;
        }}
        [data-da-theme="dark"] [data-testid="stMainBlockContainer"] {{
            color: #cdd6f4;
        }}
        /* All text in main area */
        [data-da-theme="dark"] [data-testid="stAppViewContainer"] p,
        [data-da-theme="dark"] [data-testid="stAppViewContainer"] span,
        [data-da-theme="dark"] [data-testid="stAppViewContainer"] label,
        [data-da-theme="dark"] [data-testid="stAppViewContainer"] div,
        [data-da-theme="dark"] [data-testid="stAppViewContainer"] small {{
            color: #cdd6f4;
        }}
        [data-da-theme="dark"] [data-testid="stAppViewContainer"] h1,
        [data-da-theme="dark"] [data-testid="stAppViewContainer"] h2,
        [data-da-theme="dark"] [data-testid="stAppViewContainer"] h3 {{
            color: #cdd6f4 !important;
        }}
        [data-da-theme="dark"] [data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"],
        [data-da-theme="dark"] [data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"] * {{
            color: #a6adc8 !important;
        }}

        /* ── Buttons ───────────────────────────────────────────── */
        [data-da-theme="dark"] div.stButton > button,
        [data-da-theme="dark"] div.stDownloadButton > button {{
            background: #313244 !important; border-color: #45475a !important; color: #cdd6f4 !important;
        }}
        [data-da-theme="dark"] div.stButton > button:hover,
        [data-da-theme="dark"] div.stDownloadButton > button:hover {{
            background: #45475a !important; border-color: #585b70 !important;
        }}
        [data-da-theme="dark"] div.stButton > button[kind="primary"] {{
            background: {ACCENT} !important; border-color: {ACCENT} !important; color: #ffffff !important;
        }}
        [data-da-theme="dark"] div.stButton > button[kind="primary"]:hover {{
            background: {ACCENT_DARK} !important; border-color: {ACCENT_DARK} !important;
        }}

        /* ── Inputs, selects, radio, file uploader ─────────────── */
        [data-da-theme="dark"] [data-testid="stAppViewContainer"] input,
        [data-da-theme="dark"] [data-testid="stAppViewContainer"] select,
        [data-da-theme="dark"] [data-testid="stAppViewContainer"] textarea {{
            background: #313244 !important; color: #cdd6f4 !important;
            border-color: #45475a !important;
        }}
        [data-da-theme="dark"] [data-testid="stFileUploader"] {{
            border-color: #45475a !important;
        }}
        [data-da-theme="dark"] [data-testid="stFileUploader"] section {{
            background: #1e1e2e !important; color: #cdd6f4 !important;
        }}
        [data-da-theme="dark"] [data-testid="stFileUploader"] section * {{
            color: #cdd6f4 !important;
        }}
        [data-da-theme="dark"] [data-testid="stFileUploader"] button {{
            background: #313244 !important; color: #cdd6f4 !important;
            border-color: #45475a !important;
        }}
        [data-da-theme="dark"] [data-baseweb] {{
            background: #313244 !important; color: #cdd6f4 !important;
        }}
        [data-da-theme="dark"] [data-baseweb] * {{
            color: #cdd6f4 !important;
        }}
        /* Radio buttons */
        [data-da-theme="dark"] [role="radiogroup"] label,
        [data-da-theme="dark"] [role="radiogroup"] p {{
            color: #cdd6f4 !important;
        }}
        /* Selectbox */
        [data-da-theme="dark"] [data-testid="stSelectbox"] div,
        [data-da-theme="dark"] [data-testid="stSelectbox"] span {{
            color: #cdd6f4 !important;
        }}
        /* Toggle switch */
        [data-da-theme="dark"] [data-testid="stAppViewContainer"] [role="switch"] + span,
        [data-da-theme="dark"] [data-testid="stSidebar"] [role="switch"] + span {{
            color: #cdd6f4 !important;
        }}

        /* ── Custom component classes (dark) ───────────────────── */
        [data-da-theme="dark"] .da-hero h1 {{ color: #cdd6f4; }}
        [data-da-theme="dark"] .da-hero p {{ color: #a6adc8; }}
        [data-da-theme="dark"] .da-mode-card {{
            background: #1e1e2e; border-color: #313244;
        }}
        [data-da-theme="dark"] .da-mode-card:hover {{
            box-shadow: 0 12px 24px rgba(0,0,0,0.3);
        }}
        [data-da-theme="dark"] .da-mode-card h3 {{ color: #cdd6f4; }}
        [data-da-theme="dark"] .da-mode-card p {{ color: #a6adc8; }}
        [data-da-theme="dark"] .da-mode-tag {{ background: #313244; color: #bac2de; }}
        [data-da-theme="dark"] .da-card {{ background: #1e1e2e; border-color: #313244; }}
        [data-da-theme="dark"] .da-howto h3 {{ color: #cdd6f4; }}
        [data-da-theme="dark"] .da-step-text {{ color: #bac2de; }}
        [data-da-theme="dark"] .da-step-sub {{ color: #7f849c; }}
        [data-da-theme="dark"] .da-banner {{ border-color: #313244; }}
        [data-da-theme="dark"] .da-banner-local {{ background: #1e1e2e; color: #89b4fa; border-color: #313244; }}
        [data-da-theme="dark"] .da-banner-cloud {{ background: #1e1e2e; color: #a6e3a1; border-color: #313244; }}
        [data-da-theme="dark"] .da-banner-preview {{ background: #1e1e2e; color: #f9e2af; border-color: #313244; }}
        [data-da-theme="dark"] .da-badge-privacy {{ background: #1e1e2e; color: #a6e3a1; border-color: #313244; }}
        [data-da-theme="dark"] .da-badge-local {{ background: #1e1e2e; color: #89b4fa; border-color: #313244; }}
        [data-da-theme="dark"] .da-chip {{ background: #313244; color: #bac2de; border-color: #45475a; }}
        [data-da-theme="dark"] .da-label {{ color: #a6adc8; }}
        [data-da-theme="dark"] div.st-key-da_result_scroll {{
            background: #1e1e2e; border-color: #313244; color: #cdd6f4;
        }}
        [data-da-theme="dark"] div[data-testid="stPageLink"] a {{
            background: #cdd6f4;
        }}
        [data-da-theme="dark"] div[data-testid="stPageLink"] a:hover {{ background: #bac2de; }}
        [data-da-theme="dark"] div[data-testid="stPageLink"] a p {{ color: #1e1e2e !important; }}

        /* Success/error/info/warning message boxes */
        [data-da-theme="dark"] [data-testid="stAlert"] {{
            background: #313244 !important; color: #cdd6f4 !important;
            border-color: #45475a !important;
        }}
        [data-da-theme="dark"] [data-testid="stAlert"] * {{
            color: #cdd6f4 !important;
        }}
        /* Streamlit notification toasts */
        [data-da-theme="dark"] [data-testid="stNotification"] {{
            background: #313244 !important; color: #cdd6f4 !important;
        }}

        /* ── Sidebar / Drawer ──────────────────────────────────────── */
        [data-testid="stSidebar"] {{
            background: #ffffff !important;
            border-right: 1px solid {BORDER};
            top: {_HEADER_HEIGHT} !important;
            height: calc(100vh - {_HEADER_HEIGHT}) !important;
            z-index: 998 !important;
            width: {_DRAWER_WIDTH} !important;
            min-width: {_DRAWER_WIDTH} !important;
            max-width: {_DRAWER_WIDTH} !important;
            transition: transform 0.2s cubic-bezier(0.4,0,0.2,1) !important;
            transform: none !important;
        }}

        /* Hidden state */
        [data-testid="stSidebar"][data-da-drawer="closed"] {{
            transform: translateX(-100%) !important;
        }}

        [data-testid="stSidebarContent"] {{
            padding-top: 0.25rem !important;
        }}
        [data-testid="stSidebarHeader"] {{
            padding: 0 !important;
            min-height: 0 !important;
        }}

        /* ── Nav links ──────────────────────────────────────────────── */
        [data-testid="stSidebarNav"] {{
            padding: 0 8px;
        }}
        [data-testid="stSidebarNav"] li {{
            margin-bottom: 2px;
        }}
        [data-testid="stSidebarNav"] a {{
            font-weight: 600 !important;
            border-radius: 10px !important;
            padding: 0.55rem 0.85rem !important;
            transition: background 0.15s ease;
            display: flex !important; align-items: center !important;
            gap: 12px !important;
            white-space: nowrap;
            overflow: hidden;
        }}
        [data-testid="stSidebarNav"] a:hover {{
            background: #f1f5f9 !important;
        }}
        [data-testid="stSidebarNav"] a[aria-current="page"] {{
            background: #f1f5f9 !important;
            color: {INK} !important;
            font-weight: 700 !important;
        }}
        [data-testid="stSidebarNav"] a[aria-current="page"] p {{
            color: {INK} !important; font-weight: 700 !important;
        }}

        /* Icon spans in nav links */
        [data-testid="stSidebarNav"] a span:first-child {{
            font-size: 1.25rem; flex-shrink: 0;
            width: 24px; text-align: center;
        }}

        /* ── Main content offset ───────────────────────────────────── */
        [data-testid="stAppViewContainer"] {{
            background: #ffffff;
            margin-top: {_HEADER_HEIGHT};
        }}
        [data-testid="stMainBlockContainer"] {{
            padding-top: 1.5rem; max-width: 1180px;
            padding-left: 2rem; padding-right: 2rem;
        }}

        /* ── Buttons ───────────────────────────────────────────────── */
        div.stButton > button, div.stDownloadButton > button {{
            border-radius: 10px; font-weight: 600; border: 1px solid #e2e8f0;
        }}
        div.stButton > button[kind="primary"] {{
            background: {ACCENT}; border-color: {ACCENT};
        }}
        div.stButton > button[kind="primary"]:hover {{
            background: {ACCENT_DARK}; border-color: {ACCENT_DARK};
        }}

        /* ── Reusable component classes ─────────────────────────────── */
        .da-topline {{ font-size: 0.78rem; font-weight: 700; text-transform: uppercase;
            letter-spacing: 0.1em; color: {ACCENT}; margin-bottom: 0.5rem; }}

        .da-hero {{ margin-top: 0.75rem; }}
        .da-hero h1 {{ font-size: 2.4rem; font-weight: 800; margin: 0 0 0.4rem 0;
            letter-spacing: -0.03em; color: {INK}; }}
        .da-hero p {{ font-size: 1.08rem; color: {MUTED}; max-width: 640px; margin: 0 0 1rem 0; }}

        .da-badges {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 1.25rem; }}
        .da-badge {{ display: inline-flex; align-items: center; gap: 5px; font-size: 0.78rem;
            font-weight: 600; padding: 4px 12px; border-radius: 999px; }}
        .da-badge-privacy {{ background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }}
        .da-badge-local {{ background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }}

        .da-banner {{ padding: 12px 18px; border-radius: 12px; margin-bottom: 1.5rem;
            font-size: 0.92rem; font-weight: 500; border: 1px solid transparent; }}
        .da-banner-local {{ background: #eff6ff; color: #1e40af; border-color: #bfdbfe; }}
        .da-banner-preview {{ background: #fffbeb; color: #92400e; border-color: #fde68a; }}
        .da-banner-cloud {{ background: #ecfdf5; color: #065f46; border-color: #a7f3d0; }}

        .da-card {{ background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px;
            padding: 1.5rem 1.7rem; box-shadow: 0 1px 2px rgba(15,23,42,0.04); }}

        .da-howto h3 {{ font-size: 0.95rem; font-weight: 700; margin: 0 0 0.9rem 0; color: #1e293b; }}
        .da-steps {{ display: flex; gap: 2rem; flex-wrap: wrap; }}
        .da-step {{ display: flex; align-items: flex-start; gap: 10px; min-width: 220px; }}
        .da-step-num {{ width: 26px; height: 26px; border-radius: 50%; background: {ACCENT};
            color: white; font-size: 0.78rem; font-weight: 700; display: flex;
            align-items: center; justify-content: center; flex-shrink: 0; margin-top: 1px; }}
        .da-step-text {{ font-size: 0.87rem; color: #475569; line-height: 1.45; }}
        .da-step-sub {{ color: #94a3b8; }}

        .da-label {{ font-size: 0.75rem; font-weight: 700; text-transform: uppercase;
            letter-spacing: 0.08em; color: {MUTED}; margin-bottom: 0.5rem; }}

        .da-chips {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 0.85rem; }}
        .da-chip {{ background: #f1f5f9; color: #334155; font-size: 0.78rem; font-weight: 600;
            padding: 4px 11px; border-radius: 999px; border: 1px solid #e2e8f0; }}

        div.st-key-da_result_scroll {{ border: 1px solid #e2e8f0; border-radius: 12px;
            background: #ffffff; max-height: 640px; overflow-y: auto; overflow-x: hidden;
            padding: 1rem 1.2rem; line-height: 1.65; }}
        div.st-key-da_result_scroll p, div.st-key-da_result_scroll li,
        div.st-key-da_result_scroll h1, div.st-key-da_result_scroll h2,
        div.st-key-da_result_scroll h3, div.st-key-da_result_scroll h4 {{
            overflow-wrap: anywhere; word-break: break-word; white-space: normal;
        }}
        div.st-key-da_result_scroll pre, div.st-key-da_result_scroll code {{
            white-space: pre-wrap; overflow-wrap: anywhere; word-break: break-word;
        }}
        div.st-key-da_result_scroll table {{ display: block; overflow-x: auto; max-width: 100%; }}
        div.st-key-da_result_scroll img {{ max-width: 100%; height: auto; }}

        /* ── Mode selector cards on the home page ───────────────────── */
        .da-mode-card {{ display: block; border: 1px solid #e2e8f0; border-radius: 18px;
            padding: 1.8rem 1.8rem 1.6rem; height: 100%; text-decoration: none !important;
            transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease; }}
        .da-mode-card:hover {{ transform: translateY(-3px);
            box-shadow: 0 12px 24px rgba(15,23,42,0.08); }}
        .da-mode-cloud {{ border-top: 4px solid #0ea5e9; }}
        .da-mode-local {{ border-top: 4px solid #16a34a; }}
        .da-mode-icon {{ font-size: 1.8rem; margin-bottom: 0.6rem; display: block; }}
        .da-mode-card h3 {{ font-size: 1.15rem; font-weight: 700; margin: 0 0 0.4rem 0; color: {INK}; }}
        .da-mode-card p {{ font-size: 0.9rem; color: {MUTED}; line-height: 1.5; margin: 0 0 0.9rem 0; }}
        .da-mode-tags {{ display: flex; gap: 6px; flex-wrap: wrap; }}
        .da-mode-tag {{ font-size: 0.72rem; font-weight: 600; color: #475569; background: #f1f5f9;
            border-radius: 999px; padding: 2px 9px; }}
        div[data-testid="stPageLink"] {{ margin-top: -0.7rem; margin-bottom: 1.5rem; }}
        div[data-testid="stPageLink"] a {{
            display: flex; align-items: center; justify-content: center;
            background: {INK}; padding: 11px 16px; border-radius: 0 0 14px 14px;
            text-decoration: none !important;
        }}
        div[data-testid="stPageLink"] a:hover {{ background: #1e293b; }}
        div[data-testid="stPageLink"] a p {{
            color: #ffffff !important; margin: 0; font-weight: 700; font-size: 0.9rem;
        }}

        /* Sidebar section headings & dividers */
        [data-testid="stSidebar"] hr {{
            margin: 0.6rem 0; border-color: {BORDER};
        }}

        /* ── Chat UI — document strip ─────────────────────────────── */
        .da-doc-strip {{
            display: flex; gap: 12px; flex-wrap: wrap;
            padding: 8px 0; margin-bottom: 1rem;
        }}
        .da-doc-card {{
            border: 1px solid {BORDER}; border-radius: 10px;
            padding: 8px; text-align: center; width: 120px;
            background: {SURFACE};
        }}
        .da-doc-card img {{ border-radius: 6px; max-height: 80px; }}
        .da-doc-card-name {{
            font-size: 0.72rem; font-weight: 600;
            color: {MUTED}; margin-top: 4px;
            overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
        }}
        [data-da-theme="dark"] .da-doc-card {{
            background: #1e1e2e; border-color: #313244;
        }}
        [data-da-theme="dark"] .da-doc-card-name {{ color: #bac2de; }}

        /* ── Attach expander styling ──────────────────────────────── */

        /* ── Copy / Download action buttons in chat ───────────────── */
        div[data-testid="stHorizontalBlock"] button[data-testid*="copy_"],
        div[data-testid="stHorizontalBlock"] button[data-testid*="dl_"] {{
            font-size: 0.75rem !important;
            padding: 4px 10px !important;
            border-radius: 8px !important;
            min-height: 0 !important;
            height: auto !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_header() -> None:
    """Render the fixed YouTube-style header bar with hamburger, logo, and nav."""
    st.markdown(
        f"""
        <div class="da-header" id="da-header">
            <button class="da-header-burger" id="da-burger" title="Menu" aria-label="Toggle sidebar">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/>
                </svg>
            </button>
            <a class="da-header-logo" href="/" target="_self">
                <div class="da-header-logo-icon">D</div>
                <span class="da-header-logo-text">DocumentAgent</span>
            </a>
            <nav class="da-header-nav">
                <a href="/cloud" target="_self" id="da-nav-cloud">☁️ Cloud</a>
                <a href="/local" target="_self" id="da-nav-local">🖥️ Local</a>
            </nav>
            <div class="da-header-spacer"></div>
            <button class="da-theme-toggle" id="da-theme-toggle" title="Toggle dark mode" aria-label="Toggle dark mode">
                <span id="da-theme-icon">🌙</span>
            </button>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.html(
        """
        <script>
        (function() {
            var STORAGE_KEY = 'da_drawer_state';
            var doc = window.parent.document;

            function getState() {
                try { return window.parent.localStorage.getItem(STORAGE_KEY) || 'open'; }
                catch(e) { return 'open'; }
            }
            function setState(s) {
                try { window.parent.localStorage.setItem(STORAGE_KEY, s); } catch(e) {}
            }
            function apply(state) {
                var sb = doc.querySelector('[data-testid="stSidebar"]');
                if (!sb) return;
                sb.setAttribute('data-da-drawer', state);
            }

            function tryApply() { apply(getState()); }
            tryApply();
            var iv = setInterval(function() {
                if (doc.querySelector('[data-testid="stSidebar"]')) {
                    tryApply(); clearInterval(iv);
                }
            }, 100);

            new MutationObserver(function() {
                var sb = doc.querySelector('[data-testid="stSidebar"]');
                if (sb && sb.getAttribute('data-da-drawer') !== getState()) {
                    apply(getState());
                }
            }).observe(doc.body, { childList: true, subtree: true });

            // Highlight active header nav link
            var path = window.parent.location.pathname;
            var links = doc.querySelectorAll('.da-header-nav a');
            links.forEach(function(a) {
                if (path === new URL(a.href).pathname) a.classList.add('active');
            });

            // Theme toggle
            var THEME_KEY = 'da_theme';
            function getTheme() {
                try { return window.parent.localStorage.getItem(THEME_KEY) || 'light'; }
                catch(e) { return 'light'; }
            }
            function setTheme(t) {
                try { window.parent.localStorage.setItem(THEME_KEY, t); } catch(e) {}
            }
            function applyTheme(theme) {
                doc.documentElement.setAttribute('data-da-theme', theme);
                var icon = doc.getElementById('da-theme-icon');
                if (icon) icon.textContent = theme === 'dark' ? '☀️' : '🌙';
            }
            applyTheme(getTheme());

            // Bind clicks (once)
            if (!doc._daBurgerBound) {
                doc._daBurgerBound = true;
                doc.addEventListener('click', function(e) {
                    var burger = e.target.closest('#da-burger');
                    if (burger) {
                        e.preventDefault();
                        e.stopPropagation();
                        var next = getState() === 'open' ? 'closed' : 'open';
                        setState(next);
                        apply(next);
                        return;
                    }
                    var toggle = e.target.closest('#da-theme-toggle');
                    if (toggle) {
                        e.preventDefault();
                        e.stopPropagation();
                        var nextTheme = getTheme() === 'light' ? 'dark' : 'light';
                        setTheme(nextTheme);
                        applyTheme(nextTheme);
                    }
                }, true);
            }
        })();
        </script>
        """,
        unsafe_allow_javascript=True,
    )


def sidebar_base() -> None:
    """Render the common sidebar section that appears on every page."""
    with st.sidebar:
        st.divider()


def page_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="da-hero">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_sample_files() -> list[str]:
    samples_dir = Path("samples")
    if not samples_dir.is_dir():
        return []
    return [
        f.name
        for f in sorted(samples_dir.iterdir())
        if f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]


def render_pdf_first_page(path: str) -> bytes | None:
    """Return PNG bytes for the first page of a PDF (for preview only)."""
    try:
        import fitz
        doc = fitz.open(path)
        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
        img = pix.tobytes("png")
        doc.close()
        return img
    except Exception:
        return None


def document_source_picker(key_prefix: str):
    """Renders the upload/sample picker shared by both extraction pages.

    Returns (doc_bytes, suffix, filename) or (None, None, None) if nothing
    is selected yet.
    """
    sample_files = get_sample_files()

    if sample_files:
        input_mode = st.radio(
            "Document source",
            options=["Upload", "Use sample"],
            horizontal=True,
            key=f"{key_prefix}_input_mode",
        )
    else:
        input_mode = "Upload"

    if input_mode == "Upload":
        uploaded_file = st.file_uploader(
            "Drop your document here",
            type=["pdf", "png", "jpg", "jpeg"],
            label_visibility="collapsed",
            key=f"{key_prefix}_uploader",
        )
        if uploaded_file is None:
            return None, None, None
        return uploaded_file.read(), Path(uploaded_file.name).suffix.lower(), uploaded_file.name

    chosen_sample = st.selectbox(
        "Select a sample document", options=sample_files, key=f"{key_prefix}_sample"
    )
    if not chosen_sample:
        return None, None, None
    sample_path = Path("samples") / chosen_sample
    if not sample_path.exists():
        return None, None, None
    return sample_path.read_bytes(), sample_path.suffix.lower(), sample_path.name


def render_result(
    *,
    success_msg: str,
    chips_html: str,
    markdown: str,
    doc_bytes: bytes,
    suffix: str,
    doc_filename: str,
    pdf_preview: bytes | None,
    download_filename: str,
) -> None:
    st.success(success_msg)

    col_doc, col_result = st.columns([1, 1], gap="large")

    with col_doc:
        st.markdown('<div class="da-label">Document</div>', unsafe_allow_html=True)
        if suffix in {".jpg", ".jpeg", ".png"}:
            st.image(doc_bytes, caption=doc_filename, use_container_width=True)
        elif suffix == ".pdf" and pdf_preview:
            st.image(pdf_preview, caption=f"{doc_filename} — page 1", use_container_width=True)
        else:
            st.info("Preview not available for this file type.")

    with col_result:
        st.markdown('<div class="da-label">Extracted Text</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="da-chips">{chips_html}</div>', unsafe_allow_html=True)
        st.download_button(
            label="Download .md",
            data=markdown,
            file_name=download_filename,
            mime="text/markdown",
        )
        with st.container(key="da_result_scroll"):
            st.markdown(markdown)
