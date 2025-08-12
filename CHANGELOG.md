# Changelog
All changes to this project are recorded in this document.
Format based on “Keep a Changelog,” versioning according to SemVer.

## [Unreleased]

## [0.4.0] - 2025-08-08
### Added
- Dialogs for **Add Entry** & **Edit Entry** (centered via `st.dialog`, with sidebar fallback).
- **Settings**: Language, currency, export/import (JSON), and “Danger Zone” (delete all data).
- **Notifications**: Dialog & file handling (base implementation).  
  - Prepared monthly generator + event-based notifications as a patch.
- **Overview**: Monthly total for filtered entries, cycle label, next due date including year.
- **Safe writes** for JSON (`.tmp` + `os.replace`).

### Changed
- Improved calculations (more robust `custom_cycle` fallback, more efficient pre-parsing in history view).
- UI: Top action bar (Add Entry on the left, notifications/settings on the right).
- Data/cache files are now **excluded** from the repository by default (updated `.gitignore`).

### Fixed
- Duplicate widget keys, indentation errors, f-strings.
- Edge cases for start/due dates.
- `months_before` is now properly considered.

### Security
- `data/*.json` (settings, notifications, entries) are no longer versioned.


## [0.5.0] - 2025-08-12
### Added
- **Demo login**:  
  - Available directly on the login screen, accessible without a password.  
  - Automatically creates a demo user with sample entries.  
  - Data is encrypted using the same mechanism as for regular users.  
  - Ideal for presentations and quick testing.
- **Import templates**:  
  - New templates for German (`templates/de/entries_template.json`) and English (`templates/en/entries_template.json`).  
  - Download buttons available directly in the “General” settings tab under Import.
- **Automatic reset** of demo data on every demo login to ensure a fresh test environment.

### Changed
- Settings dialog redesigned: clear separation between language/currency, notification settings, and user management.
- User management moved to its own “Admin 🔒” tab instead of being part of the General tab.
- Import section expanded with direct download links for templates.

### Fixed
- UI layout issues in the settings dialog (width, alignment, tabs) resolved.
- Back button improved (now available both in the top right and bottom right).
- Fixed errors for `wipe_user` calls and missing imports (`datetime`, `add_page`).

### Security
- User and entry data is now stored encrypted (PBKDF2 + Fernet).
