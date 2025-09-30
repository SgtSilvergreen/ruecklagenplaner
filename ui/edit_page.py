from __future__ import annotations
from typing import Callable, List, Dict, Optional, cast
import streamlit as st

def edit_page(
    t: Callable[[str], str],
    currency: str,
    lang: str,
    turnus_labels: List[str],
    entry: Dict,
    on_save: Callable[[dict], None],
    on_back: Callable[[], None],
    known_accounts: Optional[List[str]] = None,
    known_categories: Optional[List[str]] = None,
):
    _section_header_with_back(t("edit_title"), t, on_back, key="edit_top")

    # --- Vorbelegung
    eid = entry.get("id", "_x")
    name0 = entry.get("name", "")
    amount0 = float(entry.get("amount", 0.01) or 0.01)
    konto0 = (entry.get("konto") or "").strip()
    category0 = (entry.get("category") or "").strip()
    cycle0 = entry.get("cycle") or ("Jährlich" if lang == "de" else "Annual")
    custom_cycle0 = entry.get("custom_cycle")
    due_month0 = int(entry.get("due_month", 1))
    start_str = entry.get("start_date", "2024-01")
    end_str = entry.get("end_date")

    try:
        start_y, start_m = map(int, str(start_str).split("-")[:2])
    except Exception:
        start_y, start_m = 2024, 1

    name_input = st.text_input(t("f_name"), value=name0)
    name = str(name_input)
    amount = st.number_input(
        t("f_amount").replace("€", currency),
        min_value=0.01, value=amount0, step=0.01, format="%.2f",
    )
    col_due, col_start_m, col_start_y = st.columns(3)
    with col_due:
        due_month = st.selectbox(
            t("f_due_month"), list(range(1, 13)),
            index=max(1, min(12, due_month0)) - 1,
            format_func=lambda x: f"{x:02d}",
        )
    with col_start_m:
        start_month = st.selectbox(
            t("f_start_month"), list(range(1, 13)),
            index=max(1, min(12, start_m)) - 1,
            format_func=lambda x: f"{x:02d}",
        )
    with col_start_y:
        start_year = st.number_input(t("f_start_year"), min_value=2020, max_value=2100, value=int(start_y), step=1)

    # ---- Zeile 1: Turnus + (optional) Custom-Monate
    col_cycle, col_custom = st.columns([1.5, 1.5])
    with col_cycle:
        idx = turnus_labels.index(cycle0) if cycle0 in turnus_labels else 0
        selected_cycle = cast(str, st.selectbox(t("f_cycle"), turnus_labels, index=idx, key=f"edit_cycle_{eid}"))
    with col_custom:
        if _is_custom_label(selected_cycle, lang, t):
            st.number_input(
                t("f_custom_cycle"),
                min_value=1,
                value=int(custom_cycle0 or 12),
                step=1,
                key=f"edit_custom_cycle_{eid}",
            )

    # ---- Zeile 2: Konto (Dropdown + Custom-Feld)
    col_kto, col_kto_cust = st.columns([1.5, 1.5])
    with col_kto:
        custom_account_label = t("custom_account_label")
        base_accounts = [a for a in (known_accounts or []) if a]
        # Duplizierte Custom-Labels vermeiden, Custom vorne einsortieren:
        options_accounts = [custom_account_label] + [a for a in base_accounts if a != custom_account_label]
        # Vorbelegung: wenn konto0 in Optionen -> wählen, sonst Custom
        acc_index = options_accounts.index(konto0) if konto0 in options_accounts else 0
        selected_account = cast(str, st.selectbox(t("f_account"), options_accounts, index=acc_index, key=f"edit_account_{eid}"))
    with col_kto_cust:
        if selected_account == custom_account_label:
            st.text_input(t("f_account") + " " + t("new_value_suffix"), value=(konto0 if konto0 not in options_accounts else ""), key=f"edit_account_custom_{eid}")

    # ---- Zeile 3: Kategorie (Dropdown + Custom-Feld)
    col_cat, col_cat_cust = st.columns([1.5, 1.5])
    with col_cat:
        custom_category_label = t("custom_category_label")
        base_categories = [c for c in (known_categories or []) if c]
        options_categories = [custom_category_label] + [c for c in base_categories if c != custom_category_label]
        cat_index = options_categories.index(category0) if category0 in options_categories else 0
        selected_category = cast(str, st.selectbox(t("f_category"), options_categories, index=cat_index, key=f"edit_category_{eid}"))
    with col_cat_cust:
        if selected_category == custom_category_label:
            st.text_input(t("f_category") + " " + t("new_value_suffix"), value=(category0 if category0 not in options_categories else ""), key=f"edit_category_custom_{eid}")

    # ---- Zeile 4: Enddatum (Checkbox + Felder)
    col_use_end, col_end_year, col_end_month = st.columns([1, 1, 1])
    with col_use_end:
        default_use_end = bool(end_str)
        st.checkbox(t("f_use_end"), value=default_use_end, key=f"edit_use_end_{eid}")
    if st.session_state.get(f"edit_use_end_{eid}"):
        try:
            end_y0, end_m0 = map(int, str(end_str).split("-")[:2]) if end_str else (start_y, start_m)
        except Exception:
            end_y0, end_m0 = start_y, start_m
        with col_end_year:
            st.number_input(
                t("f_end_year"), min_value=2020, max_value=2100,
                value=int(end_y0), step=1, key=f"edit_end_year_{eid}"
            )
        with col_end_month:
            st.selectbox(
                t("f_end_month"), list(range(1, 13)),
                index=max(1, min(12, end_m0)) - 1,
                format_func=lambda x: f"{x:02d}",
                key=f"edit_end_month_{eid}",
            )    

    submitted = st.button(t("btn_save"), use_container_width=True)

    if submitted:
        # Turnus
        cycle = st.session_state.get(f"edit_cycle_{eid}", selected_cycle)
        is_custom = _is_custom_label(cycle, lang, t)
        custom_cycle = int(st.session_state.get(f"edit_custom_cycle_{eid}", custom_cycle0 or 12)) if is_custom else None

        # Konto final
        if selected_account == custom_account_label:
            konto_val = (st.session_state.get(f"edit_account_custom_{eid}") or "").strip()
        else:
            konto_val = (selected_account or "").strip()

        # Kategorie final
        if selected_category == custom_category_label:
            category_val = (st.session_state.get(f"edit_category_custom_{eid}") or "").strip()
        else:
            category_val = (selected_category or "").strip()

        # Enddatum final
        if st.session_state.get(f"edit_use_end_{eid}"):
            end_year = int(st.session_state.get(f"edit_end_year_{eid}", start_y))
            end_month = int(st.session_state.get(f"edit_end_month_{eid}", start_m))
            end_date = f"{end_year}-{end_month:02d}"
        else:
            end_date = None

        updated = {
            **entry,
            "name": name.strip(),
            "amount": float(amount),
            "konto": konto_val,
            "category": category_val,
            "cycle": cycle,
            "custom_cycle": custom_cycle,
            "due_month": int(due_month),
            "start_date": f"{int(start_year)}-{int(start_month):02d}",
            "end_date": end_date,
        }
        on_save(updated)
        st.success(t("saved"))
        on_back()
        st.rerun()

    _bottom_right_back(t, on_back, key="edit_bottom")


# ------- Helper -------
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

def _is_custom_label(label: Optional[str], lang: str, t) -> bool:
    # robust gegen i18n
    if label is None:
        return False
    try:
        return label == t("custom_cycle_label") or label in ("Benutzerdefiniert", "Custom")
    except Exception:
        return label in ("Benutzerdefiniert", "Custom")
    
