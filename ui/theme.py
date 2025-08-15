# ui/theme.py
from __future__ import annotations

import re
from pathlib import Path

import plotly.io as pio
import streamlit as st


def set_plotly_theme(theme: str) -> None:
    """Switch the default Plotly template to match the app theme."""
    pio.templates.default = "plotly_dark" if theme == "dark" else "plotly"


def set_streamlit_theme(theme: str) -> None:
    """Update Streamlit's theme setting and trigger a rerun."""
    cfg_path = Path(__file__).resolve().parent.parent / ".streamlit" / "config.toml"
    text = cfg_path.read_text(encoding="utf-8")
    if "base" in text:
        text = re.sub(r'base\s*=\s*"(light|dark)"', f'base = "{theme}"', text)
    elif "[theme]" in text:
        text = text.replace("[theme]", f"[theme]\nbase = \"{theme}\"")
    else:
        text += f"\n[theme]\nbase = \"{theme}\""
    cfg_path.write_text(text, encoding="utf-8")
    set_plotly_theme(theme)