# Project Checklist

## Core Setup
- [x] Project skeleton created (`src/`, `tests/`, `logs/`)
- [x] Tooling configured (`pytest`, `ruff`, `black`)
- [x] UTF-8 standard enforced (`.editorconfig`)
- [x] PyInstaller build pipeline working

## Implemented Features
- [x] Directory selection (source/target)
- [x] Analyze + execute flow in GUI
- [x] Move/Copy operation modes
- [x] Conflict handling (`overwrite`, `skip`, `auto_rename`)
- [x] Dry-run mode (no filesystem changes)
- [x] Recursive option (default: disabled)
- [x] File and folder processing support
- [x] Standard text operation log writing with per-action timestamps (`operation.log`)
- [x] Separate state log for undo consistency (`operation.state.json`)
- [x] Undo last operation from GUI
- [x] Undo removes empty date folders
- [x] Background threading to avoid UI freeze
- [x] Analyze and execution logs show detailed source -> target actions in app textbox
- [x] Application language selection (Turkish/English)
- [x] Language selector moved to native top menu bar
- [x] Info/Bilgi menu with bilingual popup (TR+EN app details)
- [x] Default UI language set to English
- [x] UI remembers selected language
- [x] UI remembers last selected source/target directories (`ui_settings.json`)
- [x] UI stores and restores `last_working_directory` in `ui_settings.json`
- [x] Option values (move/date/conflict) are localized in TR/EN display
- [x] `Recursive` and `Dry run` moved to native top menu `Options`
- [x] Start confirmation dialog added (planned totals + move/copy + dry-run summary)
- [x] Advanced filtering (extension, hidden files/folders, min/max size)
- [x] Item type filtering (`Files + Folders` / `Files only` / `Folders only`)
- [x] Extension/size filters run file-only mode (prevents folder-level bypass)
- [x] Clear screen log button (does not delete log files)
- [x] History view for past operations (`operation.log`)
- [x] Tabbed layout applied (`Organize` / `History` / `Settings`)
- [x] Settings moved to dedicated `Settings` tab
- [x] Menu `History/Gecmis` now switches to `History` tab
- [x] History tab includes refresh action and auto-refresh after run/undo
- [x] Windows 11-like visual theme improvements (Segoe UI, cards, modern buttons/tabs)
- [x] Start button visibility fixed for Windows theme/accent styles
- [x] Runtime data folder moved to `FileOrganizer_data` (next to EXE)
- [x] App runtime files excluded from organize operations (`FileOrganizer_data`, running EXE)
- [x] App info/version synchronized to `0.2.0`
- [x] App author updated to `BTC (Burhan Turgay)` in UI and EXE metadata

## Quality
- [x] Unit tests for organizer flow
- [x] Smoke tests
- [x] Lint checks passing
- [x] Format checks passing

## Packaging
- [x] Windows executable build (`dist/FileOrganizer.exe`)
- [x] Add custom app icon
- [x] Add version metadata to EXE

## Next Improvements
- [x] Progress percentage + ETA in GUI
- [ ] Advanced include/exclude rules (multiple patterns and presets)
- [ ] Safer confirmation summary before execute
- [ ] Add more UI languages beyond TR/EN
- [x] Optional history view for past operations
- [ ] End-to-end GUI test scenario
