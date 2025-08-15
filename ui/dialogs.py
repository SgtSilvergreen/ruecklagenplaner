# ui/dialogs.py
from __future__ import annotations
import json, streamlit as st
from datetime import datetime

from typing import Callable, Optional, Dict, List
from ui.theme import set_streamlit_theme



# =========================
# Notifications (als Seite)
# =========================
def notifications_page(
    t,
    load_notes_fn: Callable[[], list],
    save_notes_fn: Callable[[list], None],
    on_back: Callable[[], None],
):
    _page_title_with_back(t("notifications_title"), t, on_back)
    notes = load_notes_fn()
    if not notes:
        st.info(t("no_notifications"))
    else:
        for n in notes:
            ts = n.get("effective_month") or n.get("created_at", "")
            txt = n.get("text") or n.get("type", "event")
            st.write(f"• {ts}: {txt}")
        if st.button(t("mark_all_read")):
            for n in notes:
                n["read"] = True
            save_notes_fn(notes)
            st.success(t("saved"))


# ==========================================
# Settings (Allgemein / Profil / Benutzer)
# ==========================================
def settings_page(
    t,
    lang_display_map: Dict[str, str],
    prefs_getter: Callable[[], dict],
    prefs_updater: Callable[[dict], None],
    entries_exporter: Optional[Callable[[], List[dict]]] = None,
    entries_importer: Optional[Callable[[List[dict], bool], bool]] = None,
    current_user_ctx: Optional[dict] = None,
    verify_self_password: Optional[Callable[[str, str, str], bool]] = None,
    on_back: Optional[Callable[[], None]] = None,
    # Admin-Callbacks für den Tab „Benutzer“
    admin_add_user: Optional[Callable[[str, str, str], None]] = None,
    admin_load_users: Optional[Callable[[], List[dict]]] = None,
    admin_save_users: Optional[Callable[[List[dict]], None]] = None,
    admin_set_role: Optional[Callable[[str, str], None]] = None,
    admin_set_active: Optional[Callable[[str, bool], None]] = None,
    admin_set_password: Optional[Callable[[str, str], None]] = None,
    admin_delete_user: Optional[Callable[[str, str], None]] = None,
    admin_wipe_user_data: Optional[Callable[[str], None]] = None,
):
    # Seiten-Titel (ohne Back, der Back ist im Bereich "Sprache & Währung" und unten)
    st.title("⚙️ " + t("settings"))

    is_admin = bool(current_user_ctx and current_user_ctx.get("role") == "admin")
    admin_ready = all([
        admin_add_user, admin_load_users, admin_save_users,
        admin_set_role, admin_set_active, admin_set_password,
        admin_delete_user, admin_wipe_user_data
    ])

    if is_admin and admin_ready:
        tab_gen, tab_prof, tab_users = st.tabs([t("general"), t("profile"), t("users_tab")])
    else:
        tab_gen, tab_prof = st.tabs([t("general"), t("profile")])
        tab_users = None

    # --- Tab: Allgemein ---
    with tab_gen:
        prefs = prefs_getter()

        # 1) Sprache & Währung — mit Back oben rechts
        _section_header_with_back(t("language_currency"), t, on_back, key="lang_curr")
        with st.form("settings_lang_currency"):
            new_lang = st.selectbox(
                t("language"),
                ["de", "en"],
                index=["de", "en"].index(prefs.get("language", "de")),
                format_func=lambda x: lang_display_map[x]
            )
            new_currency = st.text_input(t("currency"), value=prefs.get("currency", "€"))

            if st.form_submit_button(t("btn_save"), use_container_width=True):
                prefs_updater({
                    "language": new_lang,
                    "currency": new_currency,
                })
                st.success(t("saved"))
                st.rerun()

        st.markdown("---")

        cur_theme = prefs.get("theme", "light")  # default

        theme_labels = {
            "light": t("theme_light"),
            "dark": t("theme_dark"),
            "system": t("theme_system"),
        }
        theme_values = list(theme_labels.keys())
        theme_display = [theme_labels[v] for v in theme_values]

        try:
            idx = theme_values.index(cur_theme)
        except ValueError:
            idx = 0

        sel = st.selectbox(t("theme"), theme_display, index=idx, key="ui_theme")
        new_theme = theme_values[theme_display.index(sel)]

        if new_theme != cur_theme:
            prefs_updater({"theme": new_theme})
            st.toast(t("saved"), icon="✅")
            set_streamlit_theme(new_theme)

        st.markdown("---")

        # 2) Benachrichtigungseinstellungen — separat
        st.subheader(t("notification_settings"))
        with st.form("settings_notifications"):
            notif_monthly = st.checkbox(t("notif_monthly_due_label"), value=prefs.get("notif_monthly_due", True))
            colA, colB, colC, colD = st.columns(4)
            with colA: notif_rate = st.checkbox(t("notif_rate_label"), value=prefs.get("notif_event_rate", True))
            with colB: notif_due = st.checkbox(t("notif_due_label"), value=prefs.get("notif_event_due", True))
            with colC: notif_amount = st.checkbox(t("notif_amount_label"), value=prefs.get("notif_event_amount", True))
            with colD: notif_cycle = st.checkbox(t("notif_cycle_label"), value=prefs.get("notif_event_cycle", True))

            if st.form_submit_button(t("btn_save"), use_container_width=True):
                prefs_updater({
                    "notif_monthly_due": notif_monthly,
                    "notif_event_rate": notif_rate,
                    "notif_event_due": notif_due,
                    "notif_event_amount": notif_amount,
                    "notif_event_cycle": notif_cycle,
                })
                st.success(t("saved"))

        st.markdown("---")

        # Export / Import
        if entries_exporter:
            st.subheader(t("export"))
            st.download_button(
                t("download_entries"),
                data=json.dumps(entries_exporter(), ensure_ascii=False, indent=2).encode("utf-8"),
                file_name="entries_backup.json",
                mime="application/json",
            )

        if entries_importer:
            st.subheader(t("import"))
            with st.form("settings_import_form_user"):
                file = st.file_uploader("JSON", type=["json"])
                replace = st.checkbox(t("replace_existing"))
                if st.form_submit_button(t("import_btn")) and file is not None:
                    try:
                        data = json.load(file)
                        ok = entries_importer(data, bool(replace))
                        if ok:
                            st.success(t("import_ok"))
                        else:
                            st.error(t("import_err"))
                    except Exception:
                        st.error(t("import_err"))

        # Unterer Zurück-Button (unten rechts, gut sichtbar)
        _bottom_right_back(t, on_back, key="settings_bottom")

    # --- Tab: Profil ---
    with tab_prof:
        _section_header_with_back(t("profile"), t, on_back, key="profle_top")
        if verify_self_password:
            with st.form("change_pw_self"):
                old = st.text_input(t("current_password"), type="password")
                pw1 = st.text_input(t("new_password"), type="password")
                pw2 = st.text_input(t("repeat_new_password"), type="password")
                if st.form_submit_button(t("change")):
                    if verify_self_password(old, pw1, pw2):
                        st.success(t("password_changed"))
                    else:
                        st.error(t("check_inputs"))
        else:
            st.info(t("password_change_unavailable"))

        _bottom_right_back(t, on_back, key="profil_bottom")

    # --- Tab: Benutzer (nur Admin) ---
    if tab_users is not None:
        with tab_users:
            _render_user_management(
                t,
                current_user_ctx,
                lambda: st.session_state.update(route="main"),
                admin_add_user, admin_load_users, admin_save_users,
                admin_set_role, admin_set_active, admin_set_password,
                admin_delete_user, admin_wipe_user_data
            )
            _bottom_right_back(t, on_back, key="usermanagement_bottom")


# ====================================
# Benutzerverwaltung (Tab-Inhalt)
# ====================================
def _render_user_management(
    t,
    current_user_ctx: dict,
    on_back: Callable[[], None],
    admin_add_user: Callable[[str, str, str], None],
    admin_load_users: Callable[[], List[dict]],
    admin_save_users: Callable[[List[dict]], None],
    admin_set_role: Callable[[str, str], None],
    admin_set_active: Callable[[str, bool], None],
    admin_set_password: Callable[[str, str], None],
    admin_delete_user: Callable[[str, str], None],
    admin_wipe_user_data: Callable[[str], None],   
    ):
    # 1) Benutzer anlegen – ohne Expander
    _section_header_with_back(t("create_user"), t, on_back, key="create_user_top")
    with st.form("admin_create_user"):
        new_username = st.text_input(t("new_username"))
        role = st.selectbox(t("role"), ["user", "admin"], index=0)
        pw1 = st.text_input(t("new_password"), type="password")
        pw2 = st.text_input(t("repeat_new_password"), type="password")
        create_ok = st.form_submit_button(t("create"))
    if create_ok:
        try:
            if not new_username or not pw1 or pw1 != pw2:
                raise ValueError(t("check_inputs"))
            admin_add_user(new_username, pw1, role)
            users = admin_load_users()
            for u in users:
                if u.get("username") == new_username:
                    u["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    break
            admin_save_users(users)
            st.success(t("user_created"))
        except Exception as ex:
            st.error(str(ex))

    st.markdown("---")

    # 2) Liste
    st.subheader(t("users_list"))
    st.markdown('<div class="userlist">', unsafe_allow_html=True)

    hdr = st.columns([2.2, 1.4, 1.1, 2.8, 2.5])
    hdr[0].markdown(f"**{t('login_username')}**")
    hdr[1].markdown(f"**{t('role')}**")
    hdr[2].markdown(f"**{t('active')}**")
    hdr[3].markdown(f"**{t('new_password_optional')}**")
    hdr[4].markdown(f"**{t('actions')}**")

    users = admin_load_users()
    for usr in users:
        row = st.container(border=True)
        with row:
            c1, c2, c3, c4, c5 = st.columns([2.2, 1.4, 1.1, 2.8, 2.5], gap="small")
            with c1:
                st.markdown(f"**{usr.get('username')}**")
                st.caption(f"{t('last_login')}: {usr.get('last_login') or '—'}")
            with c2:
                role_sel = st.selectbox(
                    t("role"), ["user", "admin"],
                    index=(0 if usr.get("role") != "admin" else 1),
                    key=f"role_{usr['username']}",
                    label_visibility="collapsed",
                )
            with c3:
                active_chk = st.checkbox(
                    t("active"),
                    value=bool(usr.get("active", True)),
                    key=f"act_{usr['username']}",
                    label_visibility="collapsed",
                )
            with c4:
                pw_new = st.text_input(
                    t("new_password_optional"),
                    type="password",
                    key=f"pw_{usr['username']}",
                    label_visibility="collapsed",
                )
            with c5:
                b1, b2 = st.columns(2, gap="small")
                with b1:
                    if st.button("💾 " + t("save"), key=f"save_{usr['username']}", use_container_width=True):
                        try:
                            # Schutz: letzter Admin darf nicht degradiert werden
                            if usr.get("role") == "admin" and role_sel != "admin":
                                others = [u for u in users if u.get("role") == "admin" and u.get("username") != usr.get("username")]
                                if not others:
                                    raise ValueError(t("at_least_one_admin"))
                            admin_set_role(usr["username"], role_sel)
                            admin_set_active(usr["username"], active_chk)
                            if pw_new:
                                admin_set_password(usr["username"], pw_new)
                            st.success(t("saved"))
                        except Exception as ex:
                            st.error(str(ex))
                with b2:
                    if st.button("🗑️ " + t("delete"), key=f"del_{usr['username']}", use_container_width=True):
                        try:
                            admin_delete_user(current_user_ctx["username"], usr["username"])
                            st.success(t("saved"))
                        except Exception as ex:
                            st.error(str(ex))

    st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    st.subheader(t("danger_zone"))
    users_all = [u.get("username") for u in admin_load_users()]
    me = current_user_ctx
    default_idx = users_all.index(me["username"]) if (me and me["username"] in users_all) else 0
    with st.form("settings_wipe_admin"):
        sel_user = st.selectbox(t("select_user"), users_all, index=default_idx)
        confirm = st.checkbox(t("confirm_wipe"))
        wipe_btn = st.form_submit_button(t("wipe_btn"))
        if wipe_btn:
            try:
                if not confirm:
                    raise ValueError(t("please_confirm"))
                admin_wipe_user_data(sel_user)
                st.success(t("wiped"))
            except Exception as ex:
                st.error(str(ex))


# =========================
# UI‑Hilfsfunktionen
# =========================
def _page_title_with_back(title: str, t, on_back: Optional[Callable[[], None]]):
    c1, c2 = st.columns([6, 1])
    with c1:
        st.title(title)
    with c2:
        if on_back and st.button("⬅️ " + t("back"), key=f"back_top_{title}", use_container_width=True):
            on_back()
            st.rerun()

def _section_header_with_back(title: str, t, on_back: Optional[Callable[[], None]], key: str):
    c1, c2 = st.columns([6, 1])
    with c1:
        st.subheader(title)
    with c2:
        if on_back and st.button("⬅️ " + t("back"), key=f"back_top_{key}", use_container_width=True):
            on_back()
            st.rerun()

def _bottom_right_back(t, on_back: Optional[Callable[[], None]], key: str):
    c1, c2 = st.columns([5, 1])
    with c2:
        if on_back and st.button("⬅️ " + t("back"), key=f"back_bottom_{key}", use_container_width=True):
            on_back()
            st.rerun()