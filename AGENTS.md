# AGENTS.md

## Overview
The **Rücklagenplaner** is a Streamlit-based financial planning application designed to track recurring expenses, savings goals, and contractual obligations.  
The project is structured into logical modules ("agents") that handle data management, calculations, notifications, and the user interface.

---

## Agents

### 1. **Authentication Agent**
**Purpose:** Handles user login, password verification, encryption key management, and initial admin setup.  
**Key Files:**
- `core/auth.py`
- `main.py` (`ensure_login()`)

**Responsibilities:**
- Store and manage user accounts in `users.json`.
- Hash and verify passwords.
- Create Fernet encryption keys for secure data handling.
- Provide demo mode login.

---

### 2. **Data Agent**
**Purpose:** Handles persistent storage and retrieval of user data, including savings entries, settings, and events.  
**Key Files:**
- `core/data.py`

**Responsibilities:**
- Load and save JSON data safely (temporary write + replace).
- Maintain user-specific datasets.
- Validate entry structure before saving.

---

### 3. **Calculation Agent**
**Purpose:** Provides all financial and date-based calculations for the application.  
**Key Files:**
- `core/calc.py`
- `core/cycles.py`

**Responsibilities:**
- Determine next due dates for recurring entries.
- Calculate monthly saving rates, progress, and remaining time.
- Simulate account balance over time.
- Support custom payment cycles.

---

### 4. **Notification Agent**
**Purpose:** Monitors upcoming events and generates notifications.  
**Key Files:**
- `core/notify.py`

**Responsibilities:**
- Evaluate entries for due dates or special triggers.
- Store and manage notification events.
- Provide data for notification UI.

---

### 5. **UI Agent**
**Purpose:** Handles all user interface rendering in Streamlit.  
**Key Files:**
- `ui/dialogs.py`
- `ui/pages/` (if present)

**Responsibilities:**
- Render dialogs (e.g., add/edit entries, settings, notifications).
- Provide dropdowns, forms, and tables for user input.
- Support responsive layout for mobile and desktop.
- Handle theming (light/dark) and language switching.

---

### 6. **Theme & Config Agent**
**Purpose:** Manages appearance and app configuration.
**Key Files:**
- `.streamlit/config.toml`
- `main.py` (`inject_theme_css()`)

**Responsibilities:**
- Store Streamlit theme preferences.
- Inject custom CSS for styling.
- Support theme switching from within the app.

---

### 7. **Configuration Agent**
**Purpose:** Provides global paths and persistent settings.
**Key Files:**
- `core/config.py`

**Responsibilities:**
- Ensure data directories exist.
- Load and save application settings and version information.
- Offer configuration data to other agents.

**Interactions:**
- Used by Storage, Localization, and Theme & Config Agents.

---

### 8. **Cryptography Agent**
**Purpose:** Supplies encryption utilities for secure data handling.
**Key Files:**
- `core/crypto.py`

**Responsibilities:**
- Derive keys from passwords.
- Encrypt and decrypt byte streams.
- Wrap and unwrap keys for storage.

**Interactions:**
- Collaborates with Authentication and Storage Agents to protect user data.

---

### 9. **Storage Agent**
**Purpose:** Handles low-level persistence and backup management.
**Key Files:**
- `core/storage.py`

**Responsibilities:**
- Read and write user entries and notifications (optionally encrypted).
- Manage backups and data import/export.

**Interactions:**
- Uses Configuration and Cryptography Agents; provides data for Data and Notification Agents.

---

### 10. **Rule Evaluation Agent**
**Purpose:** Defines notification rule logic.
**Key Files:**
- `core/notify_rules.py`

**Responsibilities:**
- Provide default notification rules and parameters.

**Interactions:**
- Consumed by the Notification Agent to evaluate upcoming events.

---

### 11. **Utilities Agent**
**Purpose:** Collects shared helper functions.
**Key Files:**
- `core/utils.py`

**Responsibilities:**
- Offer miscellaneous helpers for date handling and other tasks.

**Interactions:**
- General support module used across agents.

---

### 12. **Localization Agent**
**Purpose:** Manages translations and localized labels.
**Key Files:**
- `i18n.py`

**Responsibilities:**
- Store language packs and month names.
- Expose translation dictionaries to the UI and configuration modules.

**Interactions:**
- Works with UI and Configuration Agents for language switching.

---

## Data Files
- **`users.json`** – Stores user accounts, roles, encryption params, and last login.
- **`entries.json`** – Stores financial entries per user.
- **`notifications.json`** – Stores triggered notifications.

---

## Orchestration
The `main.py` file imports all agents and coordinates:
1. **Configuration loading** (Configuration Agent)
2. **Login process** (Authentication & Cryptography Agents)
3. **Data loading** (Data & Storage Agents)
4. **Localization setup** (Localization Agent)
5. **UI rendering** (UI Agent)
6. **Calculations & notifications** (Calculation, Notification & Rule Evaluation Agents)
7. **Theme injection** (Theme & Config Agent)
