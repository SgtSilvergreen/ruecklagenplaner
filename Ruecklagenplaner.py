import streamlit as st
import os
import json
import uuid
import pandas as pd
from datetime import datetime
from i18n import MONTHS, I18N, TURNUS_LABELS_EN, get_text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "entries.json")
SETTINGS_FILE = os.path.join(BASE_DIR, "data", "settings.json")
NOTIFY_FILE = os.path.join(BASE_DIR, "data", "notifications.json")
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
VERSION_FILE = os.path.join(BASE_DIR, "VERSION")

def get_version():
    try:
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "0.0.0"

try:
    ym_now = datetime.now().strftime("%Y-%m")
    if settings.get("last_notif_month") != ym_now:
        ensure_monthly_notifications()
        settings["last_notif_month"] = ym_now
        save_settings(settings)
except Exception:
    pass

TURNUS_MAPPING = {
    "Vierteljährlich": 3,
    "Halbjährlich": 6,
    "Jährlich": 12,
    "Benutzerdefiniert": None,
}

def load_entries():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_entries(entries):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)

def add_entry(entry):
    entries = load_entries()
    entries.append(entry)
    save_entries(entries)
    try:
        notify_on_add(entry)
    except Exception:
        pass

def delete_entry(entry_id):
    entries = load_entries()
    to_del = next((e for e in entries if e.get("id") == entry_id), None)
    entries = [e for e in entries if e.get("id") != entry_id]
    save_entries(entries)
    try:
        if to_del:
            notify_on_delete(to_del)
    except Exception:
        pass


def update_entry(entry_id, new_data):
    entries = load_entries()
    old = None
    for i, e in enumerate(entries):
        if e.get("id") == entry_id:
            old = e
            entries[i] = new_data
            break
    save_entries(entries)
    try:
        if old:
            notify_on_update(old, new_data)
    except Exception:
        pass


def load_settings():
    default = {"language": "de", "currency": "€"}
    if not os.path.exists(SETTINGS_FILE):
        return default
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {**default, **data}
    except Exception:
        return default

def save_settings(settings: dict):
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    tmp = SETTINGS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)
    os.replace(tmp, SETTINGS_FILE)

def load_notifications():
    if not os.path.exists(NOTIFY_FILE):
        return []
    try:
        with open(NOTIFY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_notifications(notes: list):
    os.makedirs(os.path.dirname(NOTIFY_FILE), exist_ok=True)
    tmp = NOTIFY_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)
    os.replace(tmp, NOTIFY_FILE)

settings = load_settings()
LANG = settings.get("language", "de")
CURRENCY = settings.get("currency", "€")

def t(key: str) -> str:
    return get_text(LANG, key)

def _safe_cycle_months(entry):
    if entry.get("cycle") == "Benutzerdefiniert":
        cm = entry.get("custom_cycle")
    else:
        cm = TURNUS_MAPPING.get(entry.get("cycle"))
    try:
        cm = int(cm)
    except Exception:
        cm = 0
    return cm if cm and cm > 0 else 12

def calculate_monthly_saving_and_progress(entry):
    today = datetime.now().replace(day=1)
    contract_start = datetime.strptime(entry["start_date"], "%Y-%m")
    due_month = int(entry["due_month"])
    cycle = _safe_cycle_months(entry)
    amount = float(entry["amount"])
    first_due = datetime(year=contract_start.year, month=due_month, day=1)
    if first_due < contract_start:
        first_due = datetime(year=contract_start.year + 1, month=due_month, day=1)
    if today < contract_start:
        return 0.0, 0.0, 0.0, contract_start.strftime("%m.%Y")
    if contract_start.year == first_due.year and contract_start.month == first_due.month:
        months_total = cycle
        cycle_start = contract_start
        next_due = first_due
    else:
        months_total = (first_due.year - contract_start.year) * 12 + (first_due.month - contract_start.month)
        cycle_start = contract_start
        next_due = first_due
    while today >= next_due:
        cycle_start = next_due
        next_due = next_due + pd.DateOffset(months=cycle)
        months_total = cycle
    months_saved = (today.year - cycle_start.year) * 12 + (today.month - cycle_start.month)
    months_saved = max(0, min(months_saved, months_total))
    rate = amount / months_total if months_total and months_total > 0 else 0.0
    saved = rate * months_saved
    percent = (saved / amount) if amount > 0 else 0.0
    return rate, percent, saved, None

def calculate_saldo_over_time(entries, months_before=36, months_after=36):
    if not entries:
        return pd.DataFrame(columns=["month", "saldo"])
    earliest_start = min(datetime.strptime(e["start_date"], "%Y-%m") for e in entries)
    today = datetime.now().replace(day=1)
    base_start = min(today, earliest_start)
    start_candidate = base_start - pd.DateOffset(months=months_before)
    start_date = earliest_start if start_candidate < earliest_start else start_candidate
    end_date = today + pd.DateOffset(months=months_after)
    months = pd.date_range(start=start_date, end=end_date, freq="MS")
    saldo = {}
    account = 0.0
    pre = []
    for entry in entries:
        eid = entry["id"]
        start_dt = datetime.strptime(entry["start_date"], "%Y-%m")
        end_dt = datetime.strptime(entry["end_date"], "%Y-%m") if entry.get("end_date") else months[-1]
        amount = float(entry["amount"])
        cycle_months = _safe_cycle_months(entry)
        due_month = int(entry["due_month"])
        first_due = datetime(year=start_dt.year, month=due_month, day=1)
        if first_due < start_dt:
            first_due = datetime(year=start_dt.year + 1, month=due_month, day=1)
        if start_dt.year == first_due.year and start_dt.month == first_due.month:
            first_due = first_due + pd.DateOffset(months=cycle_months)
            months_left = cycle_months
        else:
            months_left = (first_due.year - start_dt.year) * 12 + (first_due.month - start_dt.month)
        initial_rate = amount / months_left if months_left and months_left > 0 else amount
        pre.append({
            "id": eid,
            "start": start_dt,
            "end": end_dt,
            "amount": amount,
            "cycle_months": cycle_months,
            "next_due": first_due,
            "rate": initial_rate,
            "first_cycle": True,
        })
    for month in months:
        key = month.strftime("%Y-%m")
        monthly_plus = 0.0
        monthly_minus = 0.0
        for pe in pre:
            if month < pe["start"] or month > pe["end"]:
                continue
            next_due = pe["next_due"]
            rate = pe["rate"]
            if pe["first_cycle"]:
                if month < next_due:
                    monthly_plus += rate
                elif month.year == next_due.year and month.month == next_due.month:
                    monthly_minus += pe["amount"]
                    pe["next_due"] = next_due + pd.DateOffset(months=pe["cycle_months"])
                    pe["rate"] = pe["amount"] / pe["cycle_months"] if pe["cycle_months"] > 0 else pe["amount"]
                    pe["first_cycle"] = False
                    monthly_plus += pe["rate"]
            else:
                if month.year == next_due.year and month.month == next_due.month:
                    monthly_minus += pe["amount"]
                    pe["next_due"] = next_due + pd.DateOffset(months=pe["cycle_months"])
                    pe["rate"] = pe["amount"] / pe["cycle_months"] if pe["cycle_months"] > 0 else pe["amount"]
                    monthly_plus += pe["rate"]
                elif month > pe["start"] and month < next_due:
                    monthly_plus += rate
        account += monthly_plus
        account -= monthly_minus
        saldo[key] = account
    df_saldo = pd.DataFrame([{"month": k, "saldo": v} for k, v in saldo.items()])
    return df_saldo

def turnus_label(entry: dict) -> str:
    if entry.get("cycle") == "Benutzerdefiniert":
        n = int(entry.get("custom_cycle") or 0)
        if LANG == "de":
            return f"Benutzerdefiniert ({n} Mon.)" if n else "Benutzerdefiniert"
        else:
            return f"Custom ({n} mo)" if n else "Custom"
    months = TURNUS_MAPPING.get(entry.get("cycle"))
    if LANG == "de":
        return f"{entry.get('cycle')} ({months} Mon.)" if months else entry.get('cycle', '-')
    label_map = TURNUS_LABELS_EN
    return f"{label_map.get(entry.get('cycle'), entry.get('cycle', '-'))} ({months} mo)" if months else label_map.get(entry.get('cycle'), '-')

def get_next_due_date(entry: dict):
    today = datetime.now().replace(day=1)
    contract_start = datetime.strptime(entry["start_date"], "%Y-%m")
    cycle_months = _safe_cycle_months(entry)
    due_month = int(entry["due_month"])
    end = datetime.strptime(entry["end_date"], "%Y-%m") if entry.get("end_date") else None
    first_due = datetime(year=contract_start.year, month=due_month, day=1)
    if first_due < contract_start:
        first_due = datetime(year=contract_start.year + 1, month=due_month, day=1)
    if contract_start.year == first_due.year and contract_start.month == first_due.month:
        first_due = first_due + pd.DateOffset(months=cycle_months)
    next_due = first_due
    while next_due < today:
        next_due = next_due + pd.DateOffset(months=cycle_months)
        if end and next_due > end:
            return None
    if end and next_due > end:
        return None
    return next_due

def get_next_due_text(entry: dict) -> str:
    nd = get_next_due_date(entry)
    if not nd:
        return "—"
    return f"{MONTHS[LANG][nd.month]} {nd.year}"

def _append_notifications(new_notes: list):
    if not new_notes:
        return
    notes = load_notifications()
    notes.extend(new_notes)
    save_notifications(notes)

def _monthly_rate(entry: dict) -> float:
    amt = float(entry.get("amount", 0) or 0)
    cm = _safe_cycle_months(entry)
    return amt / cm if cm > 0 else 0.0

def notify_on_add(entry: dict):
    try:
        txt = t("notif_new_entry").format(
            name=entry.get("name", ""),
            rate=f"{_monthly_rate(entry):.2f} {CURRENCY}",
            amount=f"{float(entry.get('amount',0)):.2f} {CURRENCY}",
            due=get_next_due_text(entry),
        )
        _append_notifications([{
            "entry_id": entry.get("id"),
            "type": "new_entry",
            "effective_month": datetime.now().strftime("%Y-%m"),
            "text": txt,
            "read": False,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }])
    except Exception:
        pass

def notify_on_update(old: dict, new: dict):
    try:
        notes = []
        r_old, r_new = _monthly_rate(old), _monthly_rate(new)
        if abs(r_old - r_new) > 1e-6:
            notes.append({
                "entry_id": new.get("id"),
                "type": "rate_changed",
                "effective_month": datetime.now().strftime("%Y-%m"),
                "text": t("notif_rate_changed").format(
                    name=new.get("name",""),
                    old=f"{r_old:.2f} {CURRENCY}",
                    new=f"{r_new:.2f} {CURRENCY}",
                ),
                "read": False,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
        nd_old, nd_new = get_next_due_text(old), get_next_due_text(new)
        if nd_old != nd_new:
            notes.append({
                "entry_id": new.get("id"),
                "type": "due_changed",
                "effective_month": datetime.now().strftime("%Y-%m"),
                "text": t("notif_due_changed").format(
                    name=new.get("name",""),
                    old=nd_old, new=nd_new
                ),
                "read": False,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
        amt_old, amt_new = float(old.get("amount",0) or 0), float(new.get("amount",0) or 0)
        if abs(amt_old - amt_new) > 1e-6:
            notes.append({
                "entry_id": new.get("id"),
                "type": "amount_changed",
                "effective_month": datetime.now().strftime("%Y-%m"),
                "text": t("notif_amount_changed").format(
                    name=new.get("name",""),
                    old=f"{amt_old:.2f} {CURRENCY}",
                    new=f"{amt_new:.2f} {CURRENCY}",
                ),
                "read": False,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
        if (old.get("cycle"), old.get("custom_cycle")) != (new.get("cycle"), new.get("custom_cycle")):
            notes.append({
                "entry_id": new.get("id"),
                "type": "cycle_changed",
                "effective_month": datetime.now().strftime("%Y-%m"),
                "text": t("notif_cycle_changed").format(
                    name=new.get("name",""),
                    old=turnus_label(old),
                    new=turnus_label(new),
                ),
                "read": False,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
        _append_notifications(notes)
    except Exception:
        pass

def notify_on_delete(entry: dict):
    try:
        _append_notifications([{
            "entry_id": entry.get("id"),
            "type": "entry_deleted",
            "effective_month": datetime.now().strftime("%Y-%m"),
            "text": t("notif_deleted").format(name=entry.get("name","")),
            "read": False,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }])
    except Exception:
        pass

def ensure_monthly_notifications():
    notes = load_notifications()
    existing = {(n.get("entry_id"), n.get("effective_month"), n.get("type")) for n in notes}
    now = datetime.now().replace(day=1)
    ym = now.strftime("%Y-%m")
    new = []
    for e in load_entries():
        nd = get_next_due_date(e)
        if nd and nd.year == now.year and nd.month == now.month:
            key = (e["id"], ym, "due")
            if key not in existing:
                txt = t("notif_due_this_month").format(
                    name=e.get("name",""),
                    amount=f"{float(e.get('amount',0)):.2f} {CURRENCY}",
                    due=f"{MONTHS[LANG][nd.month]} {nd.year}",
                    rate=f"{_monthly_rate(e):.2f} {CURRENCY}",
                )
                new.append({
                    "entry_id": e["id"],
                    "type": "due",
                    "effective_month": ym,
                    "text": txt,
                    "read": False,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
    if new:
        save_notifications(notes + new)

def render_edit_form(entry: dict, key_suffix, turnus_mapping: dict):
    with st.form(key=f"edit_form_{key_suffix}"):
        name = st.text_input(t("f_name"), value=entry.get("name", ""), key=f"edit_name_{key_suffix}")
        amount = st.number_input(t("f_amount").replace("€", CURRENCY), min_value=0.01, value=float(entry.get("amount", 0.01)), step=0.01, format="%.2f", key=f"edit_amount_{key_suffix}")
        konto_val = st.text_input(t("f_account"), value=entry.get("konto", ""), key=f"edit_konto_{key_suffix}")
        category_val = st.text_input(t("f_category"), value=entry.get("category", ""), key=f"edit_category_{key_suffix}")
        cycles = list(turnus_mapping.keys())
        current_cycle = entry.get("cycle", cycles[0])
        cycle_idx = cycles.index(current_cycle) if current_cycle in cycles else 0
        cycle = st.selectbox(t("f_cycle"), cycles, index=cycle_idx, key=f"edit_cycle_{key_suffix}")
        if cycle == "Benutzerdefiniert":
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
    updated = {**entry, "name": name, "amount": float(amount), "konto": konto_val, "category": category_val, "cycle": cycle, "custom_cycle": int(custom_cycle) if (cycle == "Benutzerdefiniert" and custom_cycle) else None, "due_month": int(due_month), "start_date": f"{int(start_year)}-{int(start_month):02d}", "end_date": end_date}
    return submitted, updated

def render_add_form(key_suffix, turnus_mapping: dict):
    today = datetime.today()
    with st.form(key=f"add_form_{key_suffix}"):
        name = st.text_input(t("f_name"), key=f"new_name_{key_suffix}")
        amount = st.number_input(t("f_amount").replace("€", CURRENCY), min_value=0.01, value=0.01, step=0.01, format="%.2f", key=f"new_amount_{key_suffix}")
        konto_val = st.text_input(t("f_account"), key=f"new_konto_{key_suffix}")
        category_val = st.text_input(t("f_category"), key=f"new_category_{key_suffix}")
        cycles = list(turnus_mapping.keys())
        cycle = st.selectbox(t("f_cycle"), cycles, index=cycles.index("Jährlich") if "Jährlich" in cycles else 0, key=f"new_cycle_{key_suffix}")
        if cycle == "Benutzerdefiniert":
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
    entry = {"name": name, "amount": float(amount), "konto": konto_val, "category": category_val, "cycle": cycle, "custom_cycle": int(custom_cycle) if (cycle == "Benutzerdefiniert" and custom_cycle) else None, "due_month": int(due_month), "start_date": f"{int(start_year)}-{int(start_month):02d}", "end_date": end_date}
    return submitted, entry

HAS_DIALOG = hasattr(st, "dialog")

if HAS_DIALOG:
    @st.dialog(t("edit_title"))
    def show_edit_dialog(entry):
        submitted, updated = render_edit_form(entry, key_suffix=entry["id"], turnus_mapping=TURNUS_MAPPING)
        if submitted:
            update_entry(entry["id"], updated)
            st.success(t("saved"))
            st.session_state["open_edit"] = False
            st.session_state["edit_id"] = None
            st.rerun()
else:
    def show_edit_dialog(entry):
        with st.sidebar:
            submitted, updated = render_edit_form(entry, key_suffix=entry["id"], turnus_mapping=TURNUS_MAPPING)
        if submitted:
            update_entry(entry["id"], updated)
            st.sidebar.success(t("saved"))
            st.session_state["open_edit"] = False
            st.session_state["edit_id"] = None
            st.rerun()

if HAS_DIALOG:
    @st.dialog(t("add_title"))
    def show_add_dialog():
        submitted, new_entry = render_add_form("new", TURNUS_MAPPING)
        if submitted:
            new_entry["id"] = str(uuid.uuid4())
            add_entry(new_entry)
            st.success(t("saved"))
            st.session_state["open_add"] = False
            st.rerun()
else:
    def show_add_dialog():
        with st.sidebar:
            submitted, new_entry = render_add_form("new", TURNUS_MAPPING)
        if submitted:
            new_entry["id"] = str(uuid.uuid4())
            add_entry(new_entry)
            st.sidebar.success(t("saved"))
            st.session_state["open_add"] = False
            st.rerun()

if HAS_DIALOG:
    @st.dialog("🔔 Benachrichtigungen" if (settings.get("language", "de") == "de") else "🔔 Notifications")
    def show_notifications_dialog():
        notes = load_notifications()
        if not notes:
            st.info("Keine Benachrichtigungen." if (settings.get("language", "de") == "de") else "No notifications.")
            if st.button("OK"):
                st.session_state["open_notifications"] = False
                st.rerun()
        else:
            for n in notes:
                prefix = "•"
                ts = n.get("effective_month") or n.get("created_at", "")
                txt = n.get("text") or n.get("type", "event")
                st.write(f"{prefix} {ts}: {txt}")
            if st.button("Alle als gelesen" if (settings.get("language", "de") == "de") else "Mark all as read"):
                for n in notes:
                    n["read"] = True
                save_notifications(notes)
                st.session_state["open_notifications"] = False
                st.rerun()
else:
    def show_notifications_dialog():
        with st.sidebar:
            notes = load_notifications()
            if not notes:
                st.info("Keine Benachrichtigungen." if (settings.get("language", "de") == "de") else "No notifications.")
            else:
                for n in notes:
                    prefix = "•"
                    ts = n.get("effective_month") or n.get("created_at", "")
                    txt = n.get("text") or n.get("type", "event")
                    st.write(f"{prefix} {ts}: {txt}")
                if st.button("Alle als gelesen" if (settings.get("language", "de") == "de") else "Mark all as read"):
                    for n in notes:
                        n["read"] = True
                    save_notifications(notes)
                    st.session_state["open_notifications"] = False
                    st.rerun()

if HAS_DIALOG:
    @st.dialog(t("settings"))
    def show_settings_dialog():
        with st.form("settings_lang_curr"):
            lang_display = {"de": "Deutsch", "en": "English"}
            new_lang = st.selectbox(t("language"), ["de", "en"], index=["de", "en"].index(LANG), format_func=lambda x: lang_display[x])
            new_currency = st.text_input(t("currency"), value=CURRENCY)
            submitted = st.form_submit_button(t("btn_save"), use_container_width=True)
            if submitted:
                settings.update({"language": new_lang, "currency": new_currency})
                save_settings(settings)
                st.success(t("saved"))
                st.rerun()
        st.markdown("---")
        st.subheader(t("export"))
        entries_export = load_entries()
        def _download_bytes(obj) -> bytes:
            return json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
        st.download_button(t("download_entries"), data=_download_bytes(entries_export), file_name="entries_backup.json", mime="application/json")
        st.subheader(t("import"))
        with st.form("settings_import_form"):
            file = st.file_uploader("JSON", type=["json"])
            replace = st.checkbox(t("replace_existing"))
            submit_imp = st.form_submit_button(t("import_btn"))
            if submit_imp and file is not None:
                try:
                    data = json.load(file)
                    if not isinstance(data, list):
                        raise ValueError("expected list")
                    for e in data:
                        if not e.get("id"):
                            e["id"] = str(uuid.uuid4())
                    if replace:
                        save_entries(data)
                    else:
                        current = load_entries()
                        ids = {e.get("id") for e in current}
                        merged = current + [e for e in data if e.get("id") not in ids]
                        save_entries(merged)
                    st.success(t("import_ok"))
                    st.rerun()
                except Exception:
                    st.error(t("import_err"))
        st.markdown("---")
        st.subheader("Gefahrenbereich" if LANG == "de" else "Danger zone")
        with st.form("settings_wipe"):
            confirm = st.checkbox("Ich verstehe, dass diese Aktion nicht rückgängig gemacht werden kann." if LANG == "de" else "I understand this action cannot be undone.")
            wipe = st.form_submit_button("Alle Daten löschen" if LANG == "de" else "Delete all data")
            if wipe and confirm:
                save_entries([])
                st.success("Alle Daten gelöscht." if LANG == "de" else "All data deleted.")
                st.rerun()
else:
    def show_settings_dialog():
        with st.sidebar:
            with st.form("settings_lang_curr"):
                lang_display = {"de": "Deutsch", "en": "English"}
                new_lang = st.selectbox(t("language"), ["de", "en"], index=["de", "en"].index(LANG), format_func=lambda x: lang_display[x])
                new_currency = st.text_input(t("currency"), value=CURRENCY)
                submitted = st.form_submit_button(t("btn_save"))
                if submitted:
                    settings.update({"language": new_lang, "currency": new_currency})
                    save_settings(settings)
                    st.success(t("saved"))
                    st.rerun()
            st.markdown("---")
            entries_export = load_entries()
            def _download_bytes(obj) -> bytes:
                return json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
            st.download_button(t("download_entries"), data=_download_bytes(entries_export), file_name="entries_backup.json", mime="application/json")
            with st.form("settings_import_form"):
                file = st.file_uploader("JSON", type=["json"])
                replace = st.checkbox(t("replace_existing"))
                submit_imp = st.form_submit_button(t("import_btn"))
                if submit_imp and file is not None:
                    try:
                        data = json.load(file)
                        if not isinstance(data, list):
                            raise ValueError("expected list")
                        for e in data:
                            if not e.get("id"):
                                e["id"] = str(uuid.uuid4())
                        if replace:
                            save_entries(data)
                        else:
                            current = load_entries()
                            ids = {e.get("id") for e in current}
                            merged = current + [e for e in data if e.get("id") not in ids]
                            save_entries(merged)
                        st.success(t("import_ok"))
                        st.rerun()
                    except Exception:
                        st.error(t("import_err"))
            st.markdown("---")
            with st.form("settings_wipe"):
                confirm = st.checkbox("Ich verstehe, dass diese Aktion nicht rückgängig gemacht werden kann." if LANG == "de" else "I understand this action cannot be undone.")
                wipe = st.form_submit_button("Alle Daten löschen" if LANG == "de" else "Delete all data")
                if wipe and confirm:
                    save_entries([])
                    st.success("Alle Daten gelöscht." if LANG == "de" else "All data deleted.")
                    st.rerun()

entries = load_entries()

st.set_page_config(page_title=t("app_title"), layout="wide")
st.title(f"📊 {t('app_title')} · v{get_version()}")

actions = st.container()
with actions:
    left, right = st.columns([8, 4])
    with left:
        if st.button(t("btn_add_entry"), key="open_add_btn_main"):
            st.session_state["open_add"] = True
            st.session_state["open_notifications"] = False
            st.session_state["open_settings"] = False
            st.session_state["open_edit"] = False
            st.rerun()
    with right:
        c1, c2 = st.columns([1, 1], gap="small")
        with c1:
            try:
                _unread = sum(1 for n in load_notifications() if not n.get("read"))
            except Exception:
                _unread = 0
            notif_label = "Benachrichtigungen" if LANG == "de" else "Notifications"
            if _unread:
                notif_label += f" ({_unread})"
            if st.button(f"🔔 {notif_label}", key="open_notif_btn"):
                st.session_state["open_notifications"] = True
                st.session_state["open_add"] = False
                st.session_state["open_settings"] = False
                st.session_state["open_edit"] = False
                st.rerun()
        with c2:
            settings_label = "Einstellungen" if LANG == "de" else "Settings"
            if st.button(f"⚙️ {settings_label}", key="open_settings_btn"):
                st.session_state["open_settings"] = True
                st.session_state["open_notifications"] = False
                st.session_state["open_add"] = False
                st.session_state["open_edit"] = False
                st.rerun()

if st.session_state.get("open_notifications"):
    show_notifications_dialog()
elif st.session_state.get("open_add"):
    show_add_dialog()
elif st.session_state.get("open_settings"):
    show_settings_dialog()

tab1, tab2 = st.tabs([t("tab_overview"), t("tab_history")])

with tab1:
    st.subheader(t("overview_header"))
    all_categories = sorted(set(e.get("category", "") for e in entries if e.get("category", "")))
    all_konten = sorted(set(e.get("konto", "") for e in entries if e.get("konto", "")))
    c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
    with c1:
        selected_category = st.selectbox(t("filter_category"), ["Alle"] + all_categories if LANG == "de" else ["All"] + all_categories, key="filter_category_tab1")
    with c2:
        selected_konto = st.selectbox(t("filter_account"), ["Alle"] + all_konten if LANG == "de" else ["All"] + all_konten, key="filter_konto_tab1")
    with c3:
        sort_labels = [t("sort_name"), t("sort_due_month"), t("sort_monthly")]
        sort_option = st.selectbox(t("filter_sort"), sort_labels, key="sort_option_tab1")
    with c4:
        pass
    def _match(value, selected):
        if LANG == "de":
            return selected == "Alle" or value == selected
        else:
            return selected == "All" or value == selected
    filtered_entries = [e for e in entries if _match(e.get("category", ""), selected_category) and _match(e.get("konto", ""), selected_konto)]
    if sort_option == t("sort_due_month"):
        filtered_entries.sort(key=lambda x: int(x["due_month"]))
    elif sort_option == t("sort_monthly"):
        filtered_entries.sort(key=lambda x: calculate_monthly_saving_and_progress(x)[0], reverse=True)
    else:
        filtered_entries.sort(key=lambda x: x["name"].lower())
    st.markdown("---")
    total_rate = 0.0
    for e in filtered_entries:
        rate, percent, saved, info = calculate_monthly_saving_and_progress(e)
        total_rate += rate
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1.5])
        with col1:
            cat_txt = e.get('category', 'Unkategorisiert' if LANG == 'de' else 'Uncategorized')
            st.markdown(f"**{e['name']}**<br/>({cat_txt})", unsafe_allow_html=True)
        with col2:
            st.markdown(f"{t('turnus')}: {turnus_label(e)}")
        with col3:
            nd_text = get_next_due_text(e)
            start_text = e.get('start_date', '-')
            end_text = e.get('end_date') or '—'
            st.markdown(f"{t('next_due')}: **{nd_text}**<br/><small>{t('start')}: {start_text} · {t('end')}: {end_text}</small>", unsafe_allow_html=True)
        with col4:
            if info:
                st.markdown(f"{t('monthly_save')}: **{rate:.2f} {CURRENCY}** (ab {info})")
                st.progress(0, text=t("not_started"))
            else:
                st.markdown(f"{t('monthly_save')}: **{rate:.2f} {CURRENCY}**")
                st.progress(percent, text=f"{percent*100:.1f}% von {e['amount']:.2f} {CURRENCY} gespart ({saved:.2f} {CURRENCY})" if LANG == "de" else f"{percent*100:.1f}% of {e['amount']:.2f} {CURRENCY} saved ({saved:.2f} {CURRENCY})")
        with col5:
            b1, b2 = st.columns([0.2, 1])
            with b1:
                if st.button(t("btn_edit"), key=f"edit_{e['id']}"):
                    st.session_state["edit_id"] = e["id"]
                    st.session_state["open_edit"] = True
                    st.session_state["open_add"] = False
                    st.session_state["open_settings"] = False
                    st.session_state["open_notifications"] = False
                    st.rerun()
            with b2:
                if st.button(t("btn_delete"), key=f"delete_{e['id']}"):
                    delete_entry(e["id"])
                    st.rerun()
    st.markdown("---")
    s1, s2 = st.columns([2, 2])
    with s1:
        st.metric(t("monthly_sum_filtered"), f"{total_rate:.2f} {CURRENCY}")
    with s2:
        st.caption(f"{t('entries_count')}: {len(filtered_entries)}")
    if st.session_state.get("open_edit"):
        edit_id = st.session_state.get("edit_id")
        entry = next((x for x in entries if x["id"] == edit_id), None)
        if entry:
            show_edit_dialog(entry)
        else:
            st.session_state["open_edit"] = False
            st.session_state["edit_id"] = None
            st.rerun()

with tab2:
    st.subheader(t("history_header"))
    all_categories_t2 = sorted(set(e.get("category", "") for e in entries if e.get("category", "")))
    all_konten_t2 = sorted(set(e.get("konto", "") for e in entries if e.get("konto", "")))
    c1, c2, c3 = st.columns([2, 2, 2])
    with c1:
        selected_category = st.selectbox(t("filter_category"), ["Alle"] + all_categories_t2 if LANG == "de" else ["All"] + all_categories_t2, key="filter_category_tab2")
    with c2:
        selected_konto = st.selectbox(t("filter_account"), ["Alle"] + all_konten_t2 if LANG == "de" else ["All"] + all_konten_t2, key="filter_konto_tab2")
    with c3:
        pass
    filtered_entries_tab2 = [e for e in entries if _match(e.get("category", ""), selected_category) and _match(e.get("konto", ""), selected_konto)]
    df_saldo = calculate_saldo_over_time(filtered_entries_tab2)
    if df_saldo.empty:
        st.info("Keine Daten für den gewählten Filter." if LANG == "de" else "No data for the selected filter.")
    else:
        df_saldo["Monatsname"] = df_saldo["month"].apply(lambda x: f"{MONTHS[LANG][int(x.split('-')[1])]} {x.split('-')[0]}")
        import plotly.express as px
        fig_saldo = px.line(
            df_saldo,
            x="month",
            y="saldo",
            markers=True,
            labels={"saldo": f"Kontostand ({CURRENCY})" if LANG == "de" else f"Balance ({CURRENCY})"},
            title=t("history_header"),
            hover_name="Monatsname",
            hover_data={"saldo": ":.2f", "month": False},
        )
        fig_saldo.update_traces(hovertemplate="<b>%{customdata[0]}</b><br>" + f"{CURRENCY} " + "%{y:.2f}<extra></extra>", customdata=df_saldo[["Monatsname"]].values)
        fig_saldo.update_layout(autosize=True, height=600, margin=dict(l=40, r=40, t=80, b=40), yaxis=dict(autorange=True, fixedrange=False), xaxis=dict(autorange=True, fixedrange=False))
        st.plotly_chart(fig_saldo, use_container_width=True, config={"scrollZoom": True})
