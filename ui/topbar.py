import streamlit as st
from typing import Callable


def render_topbar(t: Callable[[str], str], unread_count: int, username: str | None) -> None:
    """Render the application top bar with navigation buttons."""

    st.markdown(
        """
    <style>
    div.stButton > button { padding: 0.28rem 0.55rem; border-radius: 10px; }
    </style>
    """,
        unsafe_allow_html=True,
    )

    topbar = st.container()
    with topbar:
        left, right = st.columns([7, 5])
        with left:
            if st.button(f"➕ {t('btn_add_entry')}", key="btn_add_top"):
                st.session_state.update(open_add=True, open_notifications=False, open_settings=False, open_edit=False)
                st.rerun()
        with right:
            c1, c2, c3 = st.columns(3, gap="small")
            with c1:
                notif_label = t("notifications_title").replace("🔔 ", "").strip()
                if unread_count:
                    notif_label = f"{notif_label} ({unread_count})"
                if st.button(f"🔔 {notif_label}", key="btn_notif_top", use_container_width=True):
                    st.session_state.update(open_notifications=True, open_add=False, open_settings=False, open_edit=False)
                    st.rerun()
            with c2:
                if st.button(f"⚙️ {t('settings')}", key="btn_settings_top", use_container_width=True):
                    st.session_state.update(open_settings=True, open_notifications=False, open_add=False, open_edit=False)
                    st.rerun()
            with c3:
                logout_label = f"🚪 {t('logout')}" + (f" ({username})" if username else "")
                if st.button(logout_label, key="btn_logout_top", use_container_width=True):
                    st.session_state.clear()
                    st.rerun()
