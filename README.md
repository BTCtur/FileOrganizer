# FileOrganizer

FileOrganizer is a Python/Tkinter desktop app that organizes selected files and folders into date-based target folders.

## Current Behavior

- Source directory is required.
- Target directory is optional; if empty, source directory is used.
- `Recursive` is **disabled by default** (safer default).
- Both files and folders can be moved/copied.
- Date basis options:
  - `creation_time` (default)
  - `modified_time`
- Folder format options:
  - `YYYY-MM-DD`
  - `YYYY/MM/DD`
- Operation mode:
  - `move` (default)
  - `copy`
- Conflict policy:
  - `overwrite`
  - `skip`
  - `auto_rename`
- Dry-run mode:
  - `Dry run (no changes)` enabled => only planning, no filesystem changes.

## Undo

- GUI includes `Undo Last Operation`.
- Undo uses `logs/operation_log.json`.
- For `move`: moves items back to original location.
- For `copy`: removes created target items.

## Architecture

- GUI Layer: Tkinter UI, user options, progress and log display.
- Core Engine: scanning, planning, execute, conflict handling, undo, JSON logging.

## Quick Start (Windows PowerShell)

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
python main.py
```

## Quality Checks

```powershell
pytest
ruff check .
black --check .
```

## Build EXE

```powershell
pyinstaller --onefile --windowed src/app.py
```

Current output: `dist/app.exe`

## Notes

- Tkinter is part of the Python standard library, so it is not listed in `requirements.txt`.
- Logs are written under `logs/`.
