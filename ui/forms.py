import uuid
import streamlit as st

def render_edit_form(entry: dict, t, currency: str, lang: str, turnus_labels: list, key_suffix: str):
    with st.form(key=f"edit_form_{key_suffix}"):
        name = st.text_input(t("f_name"), value=entry.get("name", ""), key=f"edit_name_{key_suffix}")
        amount = st.number_input(t("f_amount").replace("€", currency), min_value=0.01, value=float(entry.get("amount", 0.01)), step=0.01, format="%.2f", key=f"edit_amount_{key_suffix}")
        konto_val = st.text_input(t("f_account"), value=entry.get("konto", ""), key=f"edit_konto_{key_suffix}")
        category_val = st.text_input(t("f_category"), value=entry.get("category", ""), key=f"edit_category_{key_suffix}")

        current_cycle = entry.get("cycle", turnus_labels[0])
        cycle_idx = turnus_labels.index(current_cycle) if current_cycle in turnus_labels else 0
        cycle = st.selectbox(t("f_cycle"), turnus_labels, index=cycle_idx, key=f"edit_cycle_{key_suffix}")

        custom_label = t("custom_cycle_label")
        if cycle == custom_label:
            default_cm = entry.get("custom_cycle") or 12
            custom_cycle = st.number_input(t("f_custom_cycle"), min_value=1, value=int(default_cm), key=f"edit_custom_cycle_{key_suffix}")
        else:
            custom_cycle = None

        due_month = st.selectbox(t("f_due_month"), list(range(1, 13)), format_func=lambda x: f"{x:02d}", index=int(entry.get("due_month", 1)) - 1, key=f"edit_due_month_{key_suffix}")

        start_str = entry.get("start_date", "2024-01")
        try:
            start_y, start_m = map(int, str(start_str).split("-")[:2])
        except Exception:
            start_y, start_m = 2024, 1
        start_month = st.selectbox(t("f_start_month"), list(range(1, 13)), format_func=lambda x: f"{x:02d}", index=start_m - 1, key=f"edit_start_month_{key_suffix}")
        start_year = st.number_input(t("f_start_year"), min_value=2020, max_value=2100, value=int(start_y), key=f"edit_start_year_{key_suffix}")

        use_end_date = st.checkbox(t("f_use_end"), value=bool(entry.get("end_date")), key=f"edit_use_end_date_{key_suffix}")
        end_date = None
        if use_end_date:
            end_str = entry.get("end_date", f"{start_y}-{start_m:02d}")
            try:
                end_y, end_m = map(int, str(end_str).split("-")[:2])
            except Exception:
                end_y, end_m = start_y, start_m
            end_year = st.number_input(t("f_end_year"), min_value=2020, max_value=2100, value=int(end_y), key=f"edit_end_year_{key_suffix}")
            end_month = st.selectbox(t("f_end_month"), list(range(1, 13)), format_func=lambda x: f"{x:02d}", index=end_m - 1, key=f"edit_end_month_{key_suffix}")
            end_date = f"{int(end_year)}-{int(end_month):02d}"

        submitted = st.form_submit_button(t("btn_save"), use_container_width=True)

    updated = {
        **entry,
        "name": name,
        "amount": float(amount),
        "konto": konto_val,
        "category": category_val,
        "cycle": cycle,
        "custom_cycle": int(custom_cycle) if (cycle == custom_label and custom_cycle) else None,
        "due_month": int(due_month),
        "start_date": f"{int(start_year)}-{int(start_month):02d}",
        "end_date": end_date
    }
    return submitted, updated

def render_add_form(t, currency: str, turnus_labels: list, key_suffix: str):
    from datetime import datetime
    today = datetime.today()
    with st.form(key=f"add_form_{key_suffix}"):
        name = st.text_input(t("f_name"), key=f"new_name_{key_suffix}")
        amount = st.number_input(t("f_amount").replace("€", currency), min_value=0.01, value=0.01, step=0.01, format="%.2f", key=f"new_amount_{key_suffix}")
        konto_val = st.text_input(t("f_account"), key=f"new_konto_{key_suffix}")
        category_val = st.text_input(t("f_category"), key=f"new_category_{key_suffix}")

        default_idx = next((i for i, (lbl) in enumerate(turnus_labels) if lbl.lower().startswith(("jähr","annual","year"))), 0)
        cycle = st.selectbox(t("f_cycle"), turnus_labels, index=default_idx, key=f"new_cycle_{key_suffix}")

        custom_label = t("custom_cycle_label")
        if cycle == custom_label:
            custom_cycle = st.number_input(t("f_custom_cycle"), min_value=1, value=12, key=f"new_custom_cycle_{key_suffix}")
        else:
            custom_cycle = None

        due_month = st.selectbox(t("f_due_month"), list(range(1, 13)), format_func=lambda x: f"{x:02d}", index=today.month - 1, key=f"new_due_month_{key_suffix}")
        start_month = st.selectbox(t("f_start_month"), list(range(1, 13)), format_func=lambda x: f"{x:02d}", index=today.month - 1, key=f"new_start_month_{key_suffix}")
        start_year = st.number_input(t("f_start_year"), min_value=2020, max_value=2100, value=today.year, key=f"new_start_year_{key_suffix}")

        use_end_date = st.checkbox(t("f_use_end"), key=f"new_use_end_date_{key_suffix}")
        end_date = None
        if use_end_date:
            end_month = st.selectbox(t("f_end_month"), list(range(1, 13)), format_func=lambda x: f"{x:02d}", index=today.month - 1, key=f"new_end_month_{key_suffix}")
            end_year = st.number_input(t("f_end_year"), min_value=2020, max_value=2100, value=today.year, key=f"new_end_year_{key_suffix}")
            end_date = f"{int(end_year)}-{int(end_month):02d}"

        submitted = st.form_submit_button(t("btn_add"), use_container_width=True)

    entry = {
        "id": str(uuid.uuid4()),
        "name": name,
        "amount": float(amount),
        "konto": konto_val,
        "category": category_val,
        "cycle": cycle,
        "custom_cycle": int(custom_cycle) if (cycle == t("custom_cycle_label") and custom_cycle) else None,
        "due_month": int(due_month),
        "start_date": f"{int(start_year)}-{int(start_month):02d}",
        "end_date": end_date
    }
    return submitted, entry
