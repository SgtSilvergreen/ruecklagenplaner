# Changelog
Alle Änderungen an diesem Projekt werden in diesem Dokument festgehalten.
Format angelehnt an „Keep a Changelog“, Versionierung nach SemVer.

## [Unreleased]

## [0.4.0] - 2025-08-08
### Added
- Dialoge für **Eintrag hinzufügen** & **Bearbeiten** (zentriert via `st.dialog`, Fallback Sidebar).
- **Einstellungen**: Sprache, Währung, Export/Import (JSON), „Gefahrenbereich“ (Daten löschen).
- **Benachrichtigungen**: Dialog & Datei-Handling (Grundlage). Monatlicher Generator + eventbasierte Meldungen als Patch vorbereitet.
- **Übersicht**: Monats-Summe der gefilterten Einträge, Turnus-Label, nächste Fälligkeit inkl. Jahr.
- **Sichere Writes** für JSON (`.tmp` + `os.replace`).

### Changed
- Verbesserte Berechnungen (robuster `custom_cycle`-Fallback, effizienteres Pre-Parsing in Verlauf).
- UI: Top-Aktionszeile (Hinzufügen links, Benachrichtigungen/Einstellungen rechts).
- Daten-/Cache-Dateien standardmäßig **nicht** im Repo (aktualisierte `.gitignore`).

### Fixed
- Duplicate-Widget-Keys, Einrückungsfehler, f-Strings.
- Start-/Fälligkeit-Edge-Cases.
- „months_before“ wird jetzt berücksichtigt.

### Security
- `data/*.json` (settings, notifications, entries) nicht mehr versioniert.
