from __future__ import annotations
from typing import Callable, List, Dict
import streamlit as st


def edit_page(
    t: Callable[[str], str],
    currency: str,
    lang: str,
    turnus_labels: List[str],
    entry: Dict,
    on_save: Callable[[dict], None],
    on_back: Callable[[], None],
):
    _section_header_with_back(t("edit_title"), t, on_back, key="edit_top")

    # Vorbelegung
    name0 = entry.get("name", "")
    amount0 = float(entry.get("amount", 0.01) or 0.01)
    konto0 = entry.get("konto", "")
    category0 = entry.get("category", "")
    cycle0 = entry.get("cycle") or ( "Jährlich" if lang=="de" else "Annual" )
    custom_cycle0 = entry.get("custom_cycle")
    due_month0 = int(entry.get("due_month", 1))
    start_str = entry.get("start_date", "2024-01")
    end_str = entry.get("end_date")

    try:
        start_y, start_m = map(int, str(start_str).split("-")[:2])
    except Exception:
        start_y, start_m = 2024, 1

    with st.form(f"edit_form_{entry.get('id','_x')}"):
        name = st.text_input(t("f_name"), value=name0)
        amount = st.number_input(
            t("f_amount").replace("€", currency),
            min_value=0.01,
            value=amount0,
            step=0.01,
            format="%.2f",
        )
        konto_val = st.text_input(t("f_account"), value=konto0)
        category_val = st.text_input(t("f_category"), value=category0)

        # Turnus
        # Fallback: falls cycle0 nicht in Labels -> index 0
        idx = turnus_labels.index(cycle0) if cycle0 in turnus_labels else 0
        cycle = st.selectbox(t("f_cycle"), turnus_labels, index=idx)
        is_custom = _is_custom_label(cycle, lang, t)
        if is_custom:
            default_cm = custom_cycle0 or 12
            custom_cycle = st.number_input(t("f_custom_cycle"), min_value=1, value=int(default_cm), step=1)
        else:
            custom_cycle = None

        # Fälligkeit / Start / Ende
        due_month = st.selectbox(
            t("f_due_month"), list(range(1, 13)),
            index=max(1, min(12, due_month0)) - 1,
            format_func=lambda x: f"{x:02d}",
        )
        start_month = st.selectbox(
            t("f_start_month"), list(range(1, 13)),
            index=max(1, min(12, start_m)) - 1,
            format_func=lambda x: f"{x:02d}",
        )
        start_year = st.number_input(t("f_start_year"), min_value=2020, max_value=2100, value=int(start_y), step=1)

        use_end_date = st.checkbox(t("f_use_end"), value=bool(end_str))
        end_date = None
        if use_end_date:
            try:
                end_y, end_m = map(int, str(end_str).split("-")[:2]) if end_str else (start_y, start_m)
            except Exception:
                end_y, end_m = start_y, start_m
            end_year = st.number_input(t("f_end_year"), min_value=2020, max_value=2100, value=int(end_y), step=1)
            end_month = st.selectbox(
                t("f_end_month"), list(range(1, 13)),
                index=max(1, min(12, end_m)) - 1,
                format_func=lambda x: f"{x:02d}",
            )
            end_date = f"{int(end_year)}-{int(end_month):02d}"

        submitted = st.form_submit_button(t("btn_save"), use_container_width=True)

    if submitted:
        updated = {
            **entry,
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
        on_save(updated)
        st.success(t("saved"))
        on_back()
        st.rerun()

    _bottom_right_back(t, on_back, key="edit_bottom")


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
    return label == t("custom_cycle_label") or label in ("Benutzerdefiniert", "Custom")