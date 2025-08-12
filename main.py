import json, os, base64, uuid
from datetime import datetime
from functools import partial
from core.demo import login_as_demo_and_seed, DEMO_USERNAME

import streamlit as st

from i18n import get_text
from core.config import load_settings, save_settings, get_version
from core.auth import (
    load_users, save_users, add_user, set_user_role, set_user_active,
    set_user_password, delete_user, find_user, verify_password, make_hash, get_user_enc_params
)
from core.storage import (
    load_entries as _load_entries,
    save_entries as _save_entries,
    load_notifications as _load_notes,
    save_notifications as _save_notes,
    backup_entries as _backup_entries,
    rewrap_user_data, wipe_user,
    entries_export, entries_import
)
from core.cycles import get_turnus_mapping, turnus_label
from core.calc import (
    calculate_monthly_saving_and_progress,
    calculate_saldo_over_time,
    get_next_due_text,
)
from core.notify import (
    notify_on_add, notify_on_update, notify_on_delete,
    ensure_monthly_notifications,
)
from ui.topbar import render_topbar
from ui.dialogs import notifications_page, settings_page
from ui.add_page import add_page
from ui.edit_page import edit_page
from ui.charts import saldo_chart
from core.crypto import derive_fernet_key


# -------------------------------
# Settings & i18n
# -------------------------------
settings = load_settings()
LANG = settings.get("language", "de")
CURRENCY = settings.get("currency", "€")
t = lambda key: get_text(LANG, key)

st.set_page_config(page_title=t("app_title"), layout="wide")
st.session_state.setdefault("route", "main")  # "main" | "settings" | "admin_users" | "notifications" | "add" | "edit"

# -------------------------------
# Session helpers
# -------------------------------
def _fkey():
    return st.session_state.get("enc_key")

def current_user():
    return st.session_state.get("user")

def username_or_anon():
    u = current_user()
    return u["username"] if u else "_anon"

def load_entries():
    return _load_entries(username_or_anon(), _fkey())

def save_entries(entries):
    _save_entries(username_or_anon(), entries, _fkey())

def load_notes():
    return _load_notes(username_or_anon(), _fkey())

def save_notes(notes):
    _save_notes(username_or_anon(), notes, _fkey())

def backup_entries(reason: str):
    _backup_entries(username_or_anon(), reason, _fkey())

def append_notes(new_notes):
    if not new_notes:
        return
    notes = load_notes()
    notes.extend(new_notes)
    save_notes(notes)

def get_user_prefs():
    u = current_user()
    if not u:
        return {}
    usr = find_user(u["username"])
    return usr.get("prefs", {}) if usr else {}

def update_user_prefs(updates: dict):
    u = current_user()
    if not u:
        return
    users = load_users()
    for usr in users:
        if usr.get("username") == u["username"]:
            prefs = usr.get("prefs", {})
            prefs.update(updates)
            usr["prefs"] = prefs
            break
    save_users(users)

# -------------------------------
# Login flow
# -------------------------------
def ensure_login():
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("enc_key", None)
    users = load_users()

    # Ersteinrichtung: ersten Admin anlegen
    if not users:
        st.title(t("first_setup"))
        with st.form("bootstrap_admin"):
            username = st.text_input(t("admin_username"))
            pw1 = st.text_input(t("password"), type="password")
            pw2 = st.text_input(t("password_repeat"), type="password")
            ok = st.form_submit_button(t("create_admin"))
        if ok and username and pw1 and pw1 == pw2:
            # add_user sorgt automatisch für enc.salt / enc.iters
            add_user(username, pw1, role="admin")
            st.success(t("admin_created_login"))
            st.rerun()
        return False

    # Bereits eingeloggt
    if st.session_state["user"]:
        return True

    # Login
    st.title(t("login_title"))
    with st.form("login_form"):
        username = st.text_input(t("login_username"))
        pw = st.text_input(t("password"), type="password")
        ok = st.form_submit_button(t("login_submit"))

    if ok:
        u = find_user(username)
        if u and u.get("active") and verify_password(pw, u.get("pw_hash", "")):
            # Letzten Login speichern
            u["last_login"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            uu = load_users()
            for x in uu:
                if x.get("username") == u["username"]:
                    x["last_login"] = u["last_login"]
                    break

            # Verschlüsselungsparameter prüfen / ggf. hinzufügen
            params = get_user_enc_params(u["username"])
            if not params:
                for x in uu:
                    if x.get("username") == u["username"]:
                        x["enc"] = {
                            "salt": base64.b64encode(os.urandom(16)).decode("ascii"),
                            "iters": 200_000,
                        }
                        params = {
                            "salt": base64.b64decode(x["enc"]["salt"]),
                            "iters": 200_000,
                        }
                        break
            save_users(uu)

            # Fernet-Key aus Passwort ableiten
            if params:
                st.session_state["enc_key"] = derive_fernet_key(pw, params["salt"], params["iters"])
            else:
                st.session_state["enc_key"] = None

            st.session_state["user"] = {"username": u["username"], "role": u.get("role", "user")}
            st.rerun()
        else:
            st.error(t("login_failed"))
            # --- Demo-Login ohne Passwort ---
    if st.button(t("login_demo"), type="secondary", use_container_width=True):
        demo_username, fkey = login_as_demo_and_seed()
        st.session_state["user"] = {"username": demo_username, "role": "user"}  # Demo ist normaler user
        st.session_state["enc_key"] = fkey
        st.rerun()
    return False


# -------------------------------
# App bootstrap
# -------------------------------
for _k in ("open_add", "open_edit", "open_settings", "open_notifications"):
    st.session_state.setdefault(_k, False)

if not ensure_login():
    st.stop()

# User-Overrides anwenden
prefs = get_user_prefs()
LANG = prefs.get("language", LANG)
CURRENCY = prefs.get("currency", CURRENCY)
t = lambda key: get_text(LANG, key)
TURNUS_MAPPING = get_turnus_mapping(LANG)
TURNUS_LABELS = list(TURNUS_MAPPING.keys())

st.title(f"📊 {t('app_title')} · v{get_version()}")

# Topbar
try:
    unread = sum(1 for n in load_notes() if not n.get("read"))
except Exception:
    unread = 0
u = current_user()
render_topbar(t, unread, u["username"] if u else None)

# Monatliche Notifications
try:
    ym_now = datetime.now().strftime("%Y-%m")
    if settings.get("last_notif_month") != ym_now:
        ensure_monthly_notifications(load_entries, load_notes, save_notes, LANG, CURRENCY, t)
        settings["last_notif_month"] = ym_now
        save_settings(settings)
except Exception:
    pass

# -------------------------------
# Modal routing
# -------------------------------
# --- Navigation aus Topbar-Buttons (falls du sie setzt) ---
# Beispiel: in render_topbar rufst du set_route("settings") etc. – oder du setzt hier:
if st.session_state.get("open_notifications"):
    st.session_state["open_notifications"] = False
    st.session_state["route"] = "notifications"
if st.session_state.get("open_add"):
    st.session_state["open_add"] = False
    st.session_state["route"] = "add"
if st.session_state.get("open_settings"):
    st.session_state["open_settings"] = False
    st.session_state["route"] = "settings"
if st.session_state.get("open_edit"):
    st.session_state["open_edit"] = False
    st.session_state["route"] = "edit"

# --- ROUTER ---
from ui.dialogs import (
    notifications_page, settings_page
)

route = st.session_state.get("route", "main")

def go_main(): st.session_state["route"] = "main"
def go_settings(): st.session_state["route"] = "settings"
def go_notifications(): st.session_state["route"] = "notifications"
def go_add(): st.session_state["route"] = "add"
def go_edit(): st.session_state["route"] = "edit"

if route == "notifications":
    notifications_page(t, load_notes, save_notes, on_back=go_main)
    st.stop()

elif route == "settings":
    exp = lambda: entries_export(username_or_anon(), _fkey())
    imp = lambda data, replace: entries_import(username_or_anon(), data, replace, _fkey())

    def _verify_self_password(old, pw1, pw2):
        cu = current_user()
        if not cu: return False
        uu = find_user(cu["username"])
        if not uu: return False
        if not (verify_password(old, uu.get("pw_hash","")) and pw1 and pw1 == pw2):
            return False

        # alten Key (aus Session), neuen Key (aus neuem Passwort) berechnen
        params = get_user_enc_params(cu["username"])
        old_fkey = st.session_state.get("enc_key")
        new_fkey = derive_fernet_key(pw1, params["salt"], params["iters"])

        # Passwort-Hash aktualisieren
        set_user_password(cu["username"], pw1)

        # Daten rewrap auf neuen Key
        rewrap_user_data(cu["username"], old_fkey, new_fkey)

        # Session-Key aktualisieren
        st.session_state["enc_key"] = new_fkey
        return True
    
    settings_page(
        t,
        {"de": "Deutsch", "en": "English"},
        get_user_prefs, update_user_prefs,
        exp, imp,
        current_user(),
        _verify_self_password,
        on_back=lambda: st.session_state.update(route="main"),
        # Admin-Callbacks -> Tab „Benutzer“
        admin_add_user=add_user,
        admin_load_users=load_users,
        admin_save_users=save_users,
        admin_set_role=set_user_role,
        admin_set_active=set_user_active,
        admin_set_password=set_user_password,
        admin_delete_user=delete_user,
        admin_wipe_user_data=wipe_user,
    )
    st.stop()

elif route == "add":
    def _on_add(e):
        es = load_entries(); es.append(e); save_entries(es)
        notify_on_add(append_notes, e, CURRENCY, LANG, t)
    add_page(t, CURRENCY, LANG, TURNUS_LABELS, _on_add, on_back=go_main)
    st.stop()

elif route == "edit":
    entry = next((x for x in load_entries() if x.get("id")==st.session_state.get("edit_id")), None)
    if entry:
        def _on_save(updated):
            es = load_entries()
            old = None
            for i, e in enumerate(es):
                if e.get("id")==updated["id"]:
                    old = es[i]; es[i] = updated; break
            save_entries(es)
            if old:
                prefs_local = get_user_prefs()
                notify_on_update(append_notes, old, updated, CURRENCY, LANG, t, prefs_local)
        edit_page(t, CURRENCY, LANG, TURNUS_LABELS, entry, _on_save, on_back=go_main)
        st.stop()
    else:
        go_main()
# -------------------------------
# Haupt-Tabs
# -------------------------------
entries = load_entries()
tab1, tab2 = st.tabs([t("tab_overview"), t("tab_history")])

with tab1:
    st.subheader(t("overview_header"))
    cats = sorted(set(e.get("category", "") for e in entries if e.get("category", "")))
    accs = sorted(set(e.get("konto", "") for e in entries if e.get("konto", "")))
    c1, c2, c3, _ = st.columns([2, 2, 2, 2])
    selected_category = c1.selectbox(t("filter_category"), [t("all")] + cats, key="fcat1")
    selected_konto = c2.selectbox(t("filter_account"), [t("all")] + accs, key="facc1")
    sort_labels = [t("sort_name"), t("sort_due_month"), t("sort_monthly")]
    sort_option = c3.selectbox(t("filter_sort"), sort_labels, key="fsort1")

    def _match(v, sel):
        return sel == t("all") or v == sel

    filtered = [e for e in entries if _match(e.get("category", ""), selected_category)
                and _match(e.get("konto", ""), selected_konto)]

    if sort_option == t("sort_due_month"):
        filtered.sort(key=lambda x: int(x["due_month"]))
    elif sort_option == t("sort_monthly"):
        filtered.sort(key=lambda x: calculate_monthly_saving_and_progress(x, LANG)[0], reverse=True)
    else:
        filtered.sort(key=lambda x: x["name"].lower())

    st.markdown("---")
    total_rate = 0.0
    for e in filtered:
        rate, percent, saved, info = calculate_monthly_saving_and_progress(e, LANG)
        total_rate += rate
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1.5])
        with col1:
            st.markdown(f"**{e['name']}**<br/>({e.get('category', t('uncategorized'))})", unsafe_allow_html=True)
        with col2:
            st.markdown(f"{t('turnus')}: {turnus_label(e, LANG, t('custom_cycle_label'))}")
        with col3:
            nd_text = get_next_due_text(e, LANG)
            start_text = e.get("start_date", "-")
            end_text = e.get("end_date") or "—"
            st.markdown(
                f"{t('next_due')}: **{nd_text}**<br/>"
                f"<small>{t('start')}: {start_text} · {t('end')}: {end_text}</small>",
                unsafe_allow_html=True
            )
        with col4:
            if info:
                st.markdown(f"{t('monthly_save')}: **{rate:.2f} {CURRENCY}** (ab {info})")
                st.progress(0, text=t("not_started"))
            else:
                st.markdown(f"{t('monthly_save')}: **{rate:.2f} {CURRENCY}**")
                if LANG == "de":
                    st.progress(percent, text=f"{percent*100:.1f}% von {e['amount']:.2f} {CURRENCY} gespart ({saved:.2f} {CURRENCY})")
                else:
                    st.progress(percent, text=f"{percent*100:.1f}% of {e['amount']:.2f} {CURRENCY} saved ({saved:.2f} {CURRENCY})")
        with col5:
            b1, b2 = st.columns([0.2, 1])
            with b1:
                if st.button(t("btn_edit"), key=f"edit_{e['id']}"):
                    st.session_state["edit_id"] = e["id"]
                    st.session_state.update(open_edit=True, open_add=False, open_settings=False, open_notifications=False)
                    st.rerun()
            with b2:
                if st.button(t("btn_delete"), key=f"delete_{e['id']}"):
                    es = load_entries()
                    to_del = next((x for x in es if x.get("id") == e["id"]), None)
                    es = [x for x in es if x.get("id") != e["id"]]
                    save_entries(es)
                    if to_del:
                        notify_on_delete(append_notes, to_del, t)
                    st.rerun()

    st.markdown("---")
    s1, s2 = st.columns([2, 2])
    s1.metric(t("monthly_sum_filtered"), f"{total_rate:.2f} {CURRENCY}")
    s2.caption(f"{t('entries_count')}: {len(filtered)}")

with tab2:
    st.subheader(t("history_header"))
    cats2 = sorted(set(e.get("category", "") for e in entries if e.get("category", "")))
    accs2 = sorted(set(e.get("konto", "") for e in entries if e.get("konto", "")))
    c1, c2, _ = st.columns([2, 2, 2])
    sel_cat = c1.selectbox(t("filter_category"), [t("all")] + cats2, key="fcat2")
    sel_acc = c2.selectbox(t("filter_account"), [t("all")] + accs2, key="facc2")

    def _m(v, s):
        return s == t("all") or v == s

    filtered2 = [e for e in entries if _m(e.get("category", ""), sel_cat) and _m(e.get("konto", ""), sel_acc)]
    df = calculate_saldo_over_time(filtered2, LANG)
    saldo_chart(df, LANG, CURRENCY, t("history_header"))