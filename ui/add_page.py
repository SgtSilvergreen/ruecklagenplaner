from __future__ import annotations
import uuid
from typing import Callable, List, Optional
import streamlit as st

CUSTOM_ID = "__CUSTOM__"

def add_page(
    t: Callable[[str], str],
    currency: str,
    lang: str,
    turnus_labels: List[str],
    on_add: Callable[[dict], None],
    on_back: Callable[[], None],
    known_accounts: Optional[List[str]] = None,
    known_categories: Optional[List[str]] = None,
) -> None:
    """Render the page for adding a new entry."""

    _section_header_with_back(t("add_title"), t, on_back, key="add_top")

    today = st.session_state.get("_today_cache")
    import datetime as _dt
    if not today:
        today = _dt.datetime.now()
        st.session_state["_today_cache"] = today

    name = st.text_input(t("f_name"))
    amount = st.number_input(t("f_amount").replace("€", currency), min_value=0.01, value=1.00, step=0.10, format="%.2f")

    col_due, col_start_m, col_start_y = st.columns(3)
    with col_due:
        due_month = st.selectbox(t("f_due_month"), list(range(1, 13)), index=today.month - 1, format_func=lambda x: f"{x:02d}")
    with col_start_m:
        start_month = st.selectbox(t("f_start_month"), list(range(1, 13)), index=today.month - 1, format_func=lambda x: f"{x:02d}")
    with col_start_y:
        start_year = st.number_input(t("f_start_year"), min_value=2020, max_value=2100, value=today.year, step=1)

    # ---- Zeile 1: Turnus + (optional) Custom-Monate
    col_cycle, col_custom = st.columns([1.5, 1.5])
    with col_cycle:
        default_idx = _pref_idx(turnus_labels, default_label=t("annual_label"))
        selected_cycle = st.selectbox(t("f_cycle"), turnus_labels, index=default_idx, key="add_cycle")
    with col_custom:
        if _is_custom_label(selected_cycle, lang, t):
            st.number_input(
                t("f_custom_cycle"),
                min_value=1,
                value=st.session_state.get("add_custom_cycle", 12),
                step=1,
                key="add_custom_cycle",
            )

    # ---- Zeile 2: Konto (Dropdown + Custom-Feld)
    col_kto, col_kto_cust = st.columns([1.5, 1.5])
    with col_kto:
        account_options = [a for a in (known_accounts or []) if a] or [t("custom_account_label")]
        selected_account = st.selectbox(t("f_account"), account_options, index=0, key="add_account")
    with col_kto_cust:
        if selected_account == t("custom_account_label"):
            st.text_input(t("f_account") + " " + t("new_value_suffix"), key="add_account_custom")

    # ---- Zeile 3: Kategorie (Dropdown + Custom-Feld)
    col_cat, col_cat_cust = st.columns([1.5, 1.5])
    with col_cat:
        category_options = [c for c in (known_categories or []) if c] or [t("custom_category_label")]
        selected_category = st.selectbox(t("f_category"), category_options, index=0, key="add_category")
    with col_cat_cust:
        if selected_category == t("custom_category_label"):
            st.text_input(t("f_category") + " " + t("new_value_suffix"), key="add_category_custom")

    # ---- Zeile 4: Enddatum (Checkbox + Felder in einer Zeile)
    col_use_end, col_end_year, col_end_month = st.columns([1, 1, 1])
    with col_use_end:
        st.checkbox(t("f_use_end"), key="add_use_end")
    if st.session_state.get("add_use_end"):
        with col_end_year:
            st.number_input(t("f_end_year"), min_value=2020, max_value=2100, value=today.year, step=1, key="add_end_year")
        with col_end_month:
            st.selectbox(t("f_end_month"), list(range(1, 13)), index=today.month - 1,
                        format_func=lambda x: f"{x:02d}", key="add_end_month")

    submitted = st.button(t("btn_add"), use_container_width=True)

    if submitted:
        cycle = st.session_state.get("add_cycle")
        is_custom = _is_custom_label(cycle, lang, t)
        custom_cycle = int(st.session_state.get("add_custom_cycle", 12)) if is_custom else None

        if selected_account == t("custom_account_label"):
            konto = (st.session_state.get("add_account_custom") or "").strip()
        else:
            konto = (selected_account or "").strip()
        if selected_category == t("custom_category_label"):
            category = (st.session_state.get("add_category_custom") or "").strip()
        else:
            category = (selected_category or "").strip()

        end_date = None
        if st.session_state.get("add_use_end"):
            end_year = int(st.session_state.get("add_end_year", today.year))
            end_month = int(st.session_state.get("add_end_month", today.month))
            end_date = f"{end_year}-{end_month:02d}"

        entry = {
            "id": str(uuid.uuid4()),
            "name": name.strip(),
            "amount": float(amount),
            "konto": konto.strip(),
            "category": category.strip(),
            "cycle": cycle,
            "custom_cycle": custom_cycle,
            "due_month": int(due_month),
            "start_date": f"{int(start_year)}-{int(start_month):02d}",
            "end_date": end_date,
        }
        on_add(entry)
        st.success(t("saved"))
        on_back()
        st.rerun()

    _bottom_right_back(t, on_back, key="add_bottom")


# ------- Helper -------
def _section_header_with_back(title: str, t: Callable[[str], str], on_back: Callable[[], None], key: str) -> None:
    """Render a section header with a back button on the right."""
    c1, c2 = st.columns([6, 1])
    with c1:
        st.subheader(title)
    with c2:
        if st.button("⬅️ " + t("back"), key=f"back_top_{key}", use_container_width=True):
            on_back()
            st.rerun()


def _bottom_right_back(t: Callable[[str], str], on_back: Callable[[], None], key: str) -> None:
    """Render a back button aligned to the bottom right."""
    c1, c2 = st.columns([5, 1])
    with c2:
        if st.button("⬅️ " + t("back"), key=f"back_bottom_{key}", use_container_width=True):
            on_back()
            st.rerun()


def _is_custom_label(label: str, lang: str, t: Callable[[str], str]) -> bool:
    """Return True if the cycle label represents a custom value."""
    return label == t("custom_cycle_label") or label in ("Benutzerdefiniert", "Custom")


def _is_custom_account(label: str, lang: str, t: Callable[[str], str]) -> bool:
    """Return True if the account label represents a custom account."""
    return label == t("custom_account_label") or label in ("Neues Konto", "New account")


def _is_custom_category(label: str, lang: str, t: Callable[[str], str]) -> bool:
    """Return True if the category label represents a custom category."""
    return label == t("custom_category_label") or label in ("Neue Kategorie", "New category")


def _pref_idx(labels: List[str], default_label: str) -> int:
    """Return the index of the default label or 0 if not found."""
    try:
        return labels.index(default_label)
    except ValueError:
        return 0 if labels else 0
