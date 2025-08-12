from __future__ import annotations
import uuid
from typing import Callable, List
import streamlit as st


def add_page(
    t: Callable[[str], str],
    currency: str,
    lang: str,
    turnus_labels: List[str],
    on_add: Callable[[dict], None],
    on_back: Callable[[], None],
):
    _section_header_with_back(t("add_title"), t, on_back, key="add_top")

    today = st.session_state.get("_today_cache")
    # Fallback, falls kein Cache gesetzt ist
    import datetime as _dt
    if not today:
        today = _dt.datetime.now()
        st.session_state["_today_cache"] = today

    with st.form("add_form_page"):
        name = st.text_input(t("f_name"))
        amount = st.number_input(
            t("f_amount").replace("€", currency),
            min_value=0.01,
            value=0.01,
            step=0.01,
            format="%.2f",
        )
        konto_val = st.text_input(t("f_account"))
        category_val = st.text_input(t("f_category"))

        # Turnus
        cycle = st.selectbox(t("f_cycle"), turnus_labels, index=_pref_idx(turnus_labels, default_label=_annual_label(lang)))
        is_custom = _is_custom_label(cycle, lang, t)
        custom_cycle = None
        if is_custom:
            custom_cycle = st.number_input(t("f_custom_cycle"), min_value=1, value=12, step=1)

        # Fälligkeit / Start / Ende
        due_month = st.selectbox(
            t("f_due_month"), list(range(1, 13)),
            index=today.month - 1,
            format_func=lambda x: f"{x:02d}",
        )
        start_month = st.selectbox(
            t("f_start_month"), list(range(1, 13)),
            index=today.month - 1,
            format_func=lambda x: f"{x:02d}",
        )
        start_year = st.number_input(t("f_start_year"), min_value=2020, max_value=2100, value=today.year, step=1)

        use_end_date = st.checkbox(t("f_use_end"))
        end_date = None
        if use_end_date:
            end_month = st.selectbox(
                t("f_end_month"), list(range(1, 13)),
                index=today.month - 1,
                format_func=lambda x: f"{x:02d}",
            )
            end_year = st.number_input(t("f_end_year"), min_value=2020, max_value=2100, value=today.year, step=1)
            end_date = f"{int(end_year)}-{int(end_month):02d}"

        submitted = st.form_submit_button(t("btn_add"), use_container_width=True)

    if submitted:
        entry = {
            "id": str(uuid.uuid4()),
            "name": name.strip(),
            "amount": float(amount),
            "konto": konto_val.strip(),
            "category": category_val.strip(),
            "cycle": cycle,
            "custom_cycle": int(custom_cycle) if (is_custom and custom_cycle) else None,
            "due_month": int(due_month),
            "start_date": f"{int(start_year)}-{int(start_month):02d}",
            "end_date": end_date,
        }
        on_add(entry)
        st.success(t("saved"))
        on_back()
        st.rerun()

    _bottom_right_back(t, on_back, key="add_bottom")


# ------- kleine UI-Helper (entkoppelt, keine Abhängigkeit zu dialogs.py) -------
def _section_header_with_back(title: str, t, on_back, key: str):
    c1, c2 = st.columns([6, 1])
    with c1:
        st.subheader(title)
    with c2:
        if st.button("⬅️ " + t("back"), key=f"back_top_{key}", use_container_width=True):
            on_back()
            st.rerun()

def _bottom_right_back(t, on_back, key: str):
    c1, c2 = st.columns([5, 1])
    with c2:
        if st.button("⬅️ " + t("back"), key=f"back_bottom_{key}", use_container_width=True):
            on_back()
            st.rerun()

def _is_custom_label(label: str, lang: str, t) -> bool:
    # robust: akzeptiert i18n-Label und Fallbacks
    return label == t("custom_cycle_label") or label in ("Benutzerdefiniert", "Custom")

def _annual_label(lang: str) -> str:
    return "Jährlich" if lang == "de" else "Annual"

def _pref_idx(labels: List[str], default_label: str) -> int:
    try:
        return labels.index(default_label)
    except ValueError:
        return 0 if labels else 0