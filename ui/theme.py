# ui/theme.py
from __future__ import annotations
import streamlit as st
import plotly.io as pio


def set_plotly_theme(theme: str) -> None:
    """Switch the default Plotly template to match the app theme."""
    pio.templates.default = "plotly_dark" if theme == "dark" else "plotly"


def inject_theme_css(theme: str) -> None:
    """Inject consistent CSS for light, dark and system themes.

    Existing theme styles are replaced and buttons now use the accent color
    for their background to ensure a visible primary action.
    """

    # Remove previously injected theme, if any
    st.markdown(
        "<script>var el=document.getElementById('rp-theme');if(el) el.remove();</script>",
        unsafe_allow_html=True,
    )

    DARK = """
    <style id="rp-theme">
    :root { --bg:#0f1117; --card:#151a23; --fg:#e7e7e7; --muted:#a0a5ac; --border:#2a3140; --accent:#4c8bf5; }
    .stApp { background: var(--bg) !important; color: var(--fg) !important; }
    div[data-testid="stHeader"] { background: var(--card) !important; }
    .stButton>button, .stDownloadButton>button {
      background: var(--accent) !important; color: #fff !important;
      border: 1px solid var(--accent) !important; border-radius: 12px !important;
    }
    .stButton>button:hover, .stDownloadButton>button:hover { filter: brightness(1.1); }
    .stTextInput input, .stNumberInput input, .stTextArea textarea,
    .stDateInput input, .stTimeInput input,
    .stSelectbox div[role="combobox"], .stMultiSelect div[role="combobox"] {
      background: var(--card) !important; color: var(--fg) !important;
      border: 1px solid var(--border) !important; border-radius: 10px !important;
    }
    .stSelectbox label, .stTextInput label, .stNumberInput label, .stTextArea label,
    .stDateInput label, .stTimeInput label, .stMultiSelect label { color: var(--muted) !important; }
    .stCheckbox, .stRadio { color: var(--fg) !important; }
    .stDataFrame, .stTable { color: var(--fg) !important; }
    </style>
    """

    LIGHT = """
    <style id="rp-theme">
    :root { --bg:#ffffff; --card:#ffffff; --fg:#111111; --muted:#5f6368; --border:#e0e3e7; --accent:#316bd8; }
    .stApp { background: var(--bg) !important; color: var(--fg) !important; }
    div[data-testid="stHeader"] { background: var(--card) !important; }
    .stButton>button, .stDownloadButton>button {
      background: var(--accent) !important; color: #fff !important;
      border: 1px solid var(--accent) !important; border-radius: 12px !important;
    }
    .stButton>button:hover, .stDownloadButton>button:hover { filter: brightness(0.9); }
    .stTextInput input, .stNumberInput input, .stTextArea textarea,
    .stDateInput input, .stTimeInput input,
    .stSelectbox div[role="combobox"], .stMultiSelect div[role="combobox"] {
      background: var(--card) !important; color: var(--fg) !important;
      border: 1px solid var(--border) !important; border-radius: 10px !important;
    }
    .stSelectbox label, .stTextInput label, .stNumberInput label, .stTextArea label,
    .stDateInput label, .stTimeInput label, .stMultiSelect label { color: var(--muted) !important; }
    .stCheckbox, .stRadio { color: var(--fg) !important; }
    .stDataFrame, .stTable { color: var(--fg) !important; }
    </style>
    """

    SYSTEM = """
    <style id="rp-theme">
    @media (prefers-color-scheme: dark){
      :root { --bg:#0f1117; --card:#151a23; --fg:#e7e7e7; --muted:#a0a5ac; --border:#2a3140; --accent:#4c8bf5; }
      .stApp { background: var(--bg) !important; color: var(--fg) !important; }
      div[data-testid="stHeader"] { background: var(--card) !important; }
      .stButton>button, .stDownloadButton>button {
        background: var(--accent) !important; color: #fff !important;
        border: 1px solid var(--accent) !important; border-radius: 12px !important;
      }
      .stButton>button:hover, .stDownloadButton>button:hover { filter: brightness(1.1); }
      .stTextInput input, .stNumberInput input, .stTextArea textarea,
      .stDateInput input, .stTimeInput input,
      .stSelectbox div[role="combobox"], .stMultiSelect div[role="combobox"] {
        background: var(--card) !important; color: var(--fg) !important;
        border: 1px solid var(--border) !important; border-radius: 10px !important;
      }
      .stSelectbox label, .stTextInput label, .stNumberInput label, .stTextArea label,
      .stDateInput label, .stTimeInput label, .stMultiSelect label { color: var(--muted) !important; }
      .stCheckbox, .stRadio { color: var(--fg) !important; }
      .stDataFrame, .stTable { color: var(--fg) !important; }
    }
    </style>
    """

    if theme == "dark":
        st.markdown(DARK, unsafe_allow_html=True)
    elif theme == "system":
        st.markdown(SYSTEM, unsafe_allow_html=True)
    else:
        st.markdown(LIGHT, unsafe_allow_html=True)
