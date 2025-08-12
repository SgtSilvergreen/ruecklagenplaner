# Internationalization (i18n) bundle for Ruecklagenplaner
# Keep UI strings and month names here to keep the main app lean.
# You can extend languages by adding new keys to I18N and MONTHS.

from typing import Dict

MONTHS: Dict[str, list] = {
    "de": [
        "", "Januar", "Februar", "März", "April", "Mai", "Juni",
        "Juli", "August", "September", "Oktober", "November", "Dezember",
    ],
    "en": [
        "", "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ],
}

# Cycle labels per language (label -> months)
CYCLES: Dict[str, Dict[str, int | None]] = {
    "de": {
        "Vierteljährlich": 3,
        "Halbjährlich": 6,
        "Jährlich": 12,
        "Benutzerdefiniert": None,
    },
    "en": {
        "Quarterly": 3,
        "Semiannual": 6,
        "Annual": 12,
        "Custom": None,
    }
}

# Optional: label mapping from German -> English for display helpers
TURNUS_LABELS_EN = {
    "Vierteljährlich": "Quarterly",
    "Halbjährlich": "Semiannual",
    "Jährlich": "Annual",
    "Benutzerdefiniert": "Custom",
}

I18N: Dict[str, Dict[str, str]] = {
    "de": {

        # App / Tabs
        "app_title": "Rücklagenplaner",
        "tab_overview": "Übersicht",
        "tab_history": "Kontoverlauf",

        # Topbar / Buttons
        "btn_add_entry": "Eintrag hinzufügen",
        "btn_edit": "✏️",
        "btn_delete": "❌",
        "btn_save": "Speichern",
        "btn_add": "Hinzufügen",
        "logout": "Logout",

        # Filters / Sorting
        "filter_category": "Kategorie",
        "filter_account": "Konto",
        "filter_sort": "Sortierung",
        "sort_name": "Name",
        "sort_due_month": "Fälligkeitsmonat",
        "sort_monthly": "Monatlicher Beitrag",
        "all": "Alle",

        # Overview / History
        "overview_header": "🗂 Übersicht der Rücklagen",
        "history_header": "💰 Kontostand-Verlauf mit Abbuchungen",
        "turnus": "Turnus",
        "next_due": "Nächste Fälligkeit",
        "start": "Start",
        "end": "Ende",
        "monthly_save": "Monatlich zurücklegen",
        "not_started": "Noch nicht gestartet",
        "monthly_sum_filtered": "Monatliche Summe (gefiltert)",
        "entries_count": "Einträge",
        "uncategorized": "Unkategorisiert",

        # Dialog titles
        "edit_title": "✏️ Eintrag bearbeiten",
        "add_title": "➕ Neuen Eintrag hinzufügen",
        "notifications_title": "🔔 Benachrichtigungen",
        "settings": "Einstellungen",

        # Forms (Entry)
        "f_name": "Bezeichnung",
        "f_amount": "Betrag (€)",
        "f_account": "Konto",
        "f_category": "Kategorie",
        "f_cycle": "Turnus",
        "f_custom_cycle": "Benutzerdefinierter Turnus (Monate)",
        "f_due_month": "Fälligkeitsmonat",
        "f_start_month": "Startmonat",
        "f_start_year": "Startjahr",
        "f_use_end": "Enddatum setzen?",
        "f_end_month": "Endmonat",
        "f_end_year": "Endjahr",

        # Settings (General/Profile/Admin)
        "general": "Allgemein",
        "profile": "Profil",
        "admin_tab": "Admin 🔒",
        "language": "Sprache",
        "currency": "Währungssymbol",
        "notifications": "Benachrichtigungen",
        "notif_monthly_due_label": "Fälligkeiten monatlich prüfen",
        "notif_rate_label": "Rate geändert",
        "notif_due_label": "Fälligkeit geändert",
        "notif_amount_label": "Betrag geändert",
        "notif_cycle_label": "Turnus geändert",
        "export": "Export",
        "download_entries": "Einträge herunterladen",
        "import": "Import",
        "replace_existing": "Bestehende Daten ersetzen",
        "import_btn": "Importieren",
        "danger_zone": "Gefahrenbereich",
        "confirm_wipe": "Ich verstehe, dass diese Aktion nicht rückgängig gemacht werden kann.",
        "wipe_btn": "Ausgewählten Benutzer-Datensatz löschen",
        "select_user": "Benutzer auswählen",
        "last_login": "Letzter Login",
        "role": "Rolle",
        "active": "Aktiv",
        "new_password_optional": "Neues Passwort (optional)",
        "actions": "Aktionen",
        "save": "Speichern",
        "delete": "Löschen",
        "create_user": "Neuen Benutzer anlegen",
        "new_username": "Benutzername",
        "create": "Anlegen",
        "user_created": "Benutzer angelegt.",
        "user_exists": "Benutzer existiert bereits.",
        "at_least_one_admin": "Mindestens ein Admin muss verbleiben",
        "cannot_delete_self": "Du kannst dich nicht selbst löschen",
        "open_user_mgmt": "Benutzerverwaltung öffnen",
        "user_mgmt_title": "👥 Benutzerverwaltung",
        "back": "Zurück",
        "users_tab": "Benutzerverwaltung",
        "language_currency": "Sprache & Währung",
        "notification_settings": "Benachrichtigungseinstellungen",
        "users_list": "Benutzerliste",

        # Profile (password)
        "current_password": "Aktuelles Passwort",
        "new_password": "Neues Passwort",
        "repeat_new_password": "Neues Passwort (wiederholen)",
        "change": "Ändern",
        "password_changed": "Passwort geändert.",
        "check_inputs": "Bitte Eingaben prüfen.",

        # Notifications dialog
        "notifications": "Benachrichtigungen",
        "notifications_title": "🔔 Benachrichtigungen",
        "no_notifications": "Keine Benachrichtigungen.",
        "mark_all_read": "Alle als gelesen",

        # Auth / Login / Setup
        "first_setup": "Ersteinrichtung",
        "admin_username": "Admin-Benutzername",
        "password": "Passwort",
        "password_repeat": "Passwort wiederholen",
        "create_admin": "Admin anlegen",
        "admin_created_login": "Admin angelegt. Bitte einloggen.",
        "login_title": "Anmeldung",
        "login_username": "Benutzername",
        "login_submit": "Anmelden",
        "login_failed": "Benutzer inaktiv oder Passwort falsch.",
        "login_demo": "🔎 Demo ansehen (ohne Passwort)",

        # Misc
        "saved": "Gespeichert.",
        "import_ok": "Import erfolgreich.",
        "import_err": "Import fehlgeschlagen – ungültiges JSON.",
        "wiped": "Alle Daten gelöscht.",
        "no_data_for_filter": "Keine Daten für den gewählten Filter.",
        "own_value": "Eigene Eingabe",
        "enter_value": "Wert eingeben",
        "custom_cycle_label": "Benutzerdefiniert",
        "change": "Ändern",
        "select_user": "Benutzer auswählen",

        # Notification templates
        "notif_new_entry": "Neuer Eintrag: {name}. Monatsrate: {rate}. Betrag: {amount}. Nächste Fälligkeit: {due}.",
        "notif_rate_changed": "Monatsrate geändert für {name}: {old} → {new}.",
        "notif_due_changed": "Fälligkeit geändert für {name}: {old} → {new}.",
        "notif_amount_changed": "Betrag geändert für {name}: {old} → {new}.",
        "notif_cycle_changed": "Turnus geändert für {name}: {old} → {new}.",
        "notif_deleted": "Eintrag gelöscht: {name}.",
        "notif_due_this_month": "Fälligkeit diesen Monat für {name}: {amount} fällig ({due}). Aktuelle Monatsrate: {rate}.",
    },
    "en": {
        # App / Tabs
        "app_title": "Savings Planner",
        "tab_overview": "Overview",
        "tab_history": "Balance over time",

        # Topbar / Buttons
        "btn_add_entry": "Add entry",
        "btn_edit": "✏️",
        "btn_delete": "❌",
        "btn_save": "Save",
        "btn_add": "Add",
        "logout": "Logout",

        # Filters / Sorting
        "filter_category": "Category",
        "filter_account": "Account",
        "filter_sort": "Sorting",
        "sort_name": "Name",
        "sort_due_month": "Due month",
        "sort_monthly": "Monthly contribution",
        "all": "All",

        # Overview / History
        "overview_header": "🗂 Reserve overview",
        "history_header": "💰 Balance with debits",
        "turnus": "Cycle",
        "next_due": "Next due",
        "start": "Start",
        "end": "End",
        "monthly_save": "Save per month",
        "not_started": "Not started yet",
        "monthly_sum_filtered": "Monthly total (filtered)",
        "entries_count": "Entries",
        "uncategorized": "Uncategorized",

        # Dialog titles
        "edit_title": "✏️ Edit entry",
        "add_title": "➕ Add new entry",
        "notifications_title": "🔔 Notifications",
        "settings": "Settings",

        # Forms (Entry)
        "f_name": "Name",
        "f_amount": "Amount (€)",
        "f_account": "Account",
        "f_category": "Category",
        "f_cycle": "Cycle",
        "f_custom_cycle": "Custom cycle (months)",
        "f_due_month": "Due month",
        "f_start_month": "Start month",
        "f_start_year": "Start year",
        "f_use_end": "Set end date?",
        "f_end_month": "End month",
        "f_end_year": "End year",

        # Settings (General/Profile/Admin)
        "general": "General",
        "profile": "Profile",
        "admin_tab": "Admin 🔒",
        "language": "Language",
        "currency": "Currency symbol",
        "notifications": "Notifications",
        "notif_monthly_due_label": "Check due items monthly",
        "notif_rate_label": "Rate changed",
        "notif_due_label": "Due date changed",
        "notif_amount_label": "Amount changed",
        "notif_cycle_label": "Cycle changed",
        "export": "Export",
        "download_entries": "Download entries",
        "import": "Import",
        "replace_existing": "Replace existing data",
        "import_btn": "Import",
        "danger_zone": "Danger zone",
        "confirm_wipe": "I understand this action cannot be undone.",
        "wipe_btn": "Delete selected user's dataset",
        "select_user": "Select user",
        "last_login": "Last login",
        "role": "Role",
        "active": "Active",
        "new_password_optional": "New password (optional)",
        "actions": "Actions",
        "save": "Save",
        "delete": "Delete",
        "create_user": "Create new user",
        "new_username": "Username",
        "create": "Create",
        "user_created": "User created.",
        "user_exists": "User already exists.",
        "actions": "Actions",
        "at_least_one_admin": "At least one admin must remain",
        "cannot_delete_self": "You cannot delete yourself",
        "open_user_mgmt": "Open user management",
        "user_mgmt_title": "👥 User management",
        "back": "Back",
        "users_tab": "User management",
        "language_currency": "Language & currency",
        "notification_settings": "Notification settings",
        "users_list": "Users list",

        # Profile (password)
        "current_password": "Current password",
        "new_password": "New password",
        "repeat_new_password": "Repeat new password",
        "change": "Change",
        "password_changed": "Password changed.",
        "check_inputs": "Please check your inputs.",

        # Notifications dialog
        "notifications": "Notifications",
        "notifications_title": "🔔 Notifications",
        "no_notifications": "No notifications.",
        "mark_all_read": "Mark all as read",

        # Auth / Login / Setup
        "first_setup": "First setup",
        "admin_username": "Admin username",
        "password": "Password",
        "password_repeat": "Repeat password",
        "create_admin": "Create admin",
        "admin_created_login": "Admin created. Please log in.",
        "login_title": "Login",
        "login_username": "Username",
        "login_submit": "Sign in",
        "login_failed": "User inactive or wrong password.",
        "login_demo": "🔎 Try demo (no password)",

        # Misc
        "saved": "Saved.",
        "import_ok": "Import successful.",
        "import_err": "Import failed – invalid JSON.",
        "wiped": "All data deleted.",
        "no_data_for_filter": "No data for the selected filter.",
        "own_value": "Custom input",
        "enter_value": "Enter value",
        "custom_cycle_label": "Custom",
        "change": "Change",
        "select_user": "Select user",

        # Notification templates
        "notif_new_entry": "New entry: {name}. Monthly rate: {rate}. Amount: {amount}. Next due: {due}.",
        "notif_rate_changed": "Monthly rate changed for {name}: {old} → {new}.",
        "notif_due_changed": "Due date changed for {name}: {old} → {new}.",
        "notif_amount_changed": "Amount changed for {name}: {old} → {new}.",
        "notif_cycle_changed": "Cycle changed for {name}: {old} → {new}.",
        "notif_deleted": "Entry deleted: {name}.",
        "notif_due_this_month": "Due this month for {name}: {amount} due ({due}). Current monthly rate: {rate}.",
    },
}

def get_text(lang: str, key: str) -> str:
    """Return localized text for `key` in language `lang`. Fallback to German and the key itself."""
    return I18N.get(lang, I18N["de"]).get(key, key)

__all__ = [
    "MONTHS",
    "I18N",
    "CYCLES",
    "TURNUS_LABELS_EN",
    "get_text",
]