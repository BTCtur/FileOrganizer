from __future__ import annotations

import json
import re
import shutil
import stat
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

try:
    from .models import PlannedAction, Settings
    from .utils import format_date, is_subdirectory, safe_rename
except ImportError:
    try:
        from src.models import PlannedAction, Settings
        from src.utils import format_date, is_subdirectory, safe_rename
    except ImportError:
        from models import PlannedAction, Settings
        from utils import format_date, is_subdirectory, safe_rename

ProgressCallback = Callable[[int, int, str], None]


DATE_DIR_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATE_SEGMENT_PATTERN = re.compile(r"^\d{2}$|^\d{4}$")
DATA_DIR_NAME = "FileOrganizer_data"


def scan_files(settings: Settings) -> list[Path]:
    source = settings.source_path
    if not source.exists() or not source.is_dir():
        raise ValueError(f"Source path is not a directory: {source}")

    target = settings.target_path
    if is_subdirectory(source, target) and source != target:
        raise ValueError("Target directory cannot be inside source directory.")

    pattern = "**/*" if settings.recursive else "*"
    all_candidates = [path for path in source.glob(pattern) if path != source]
    all_candidates = [
        path for path in all_candidates if _path_allowed_by_hidden_filter(path, settings)
    ]
    all_candidates = [
        path for path in all_candidates if _path_allowed_by_runtime_exclusions(path, settings)
    ]

    # If file-specific filters are active, scan files only.
    # Directory-level actions would bypass extension/size filters by moving whole folders.
    file_filter_active = bool(settings.extension_filter.strip()) or (
        settings.min_size_bytes is not None or settings.max_size_bytes is not None
    )
    files_only_mode = settings.item_mode == "files_only"
    folders_only_mode = settings.item_mode == "folders_only"

    if file_filter_active or files_only_mode:
        selected_files: list[Path] = []
        for path in all_candidates:
            if not path.is_file():
                continue
            if not _file_allowed_by_filters(path, settings):
                continue
            selected_files.append(path)
        return selected_files

    if folders_only_mode:
        directories = sorted(
            (path for path in all_candidates if path.is_dir()),
            key=lambda p: len(p.parts),
        )
        selected_directories: list[Path] = []
        for directory in directories:
            if not any(parent in directory.parents for parent in selected_directories):
                selected_directories.append(directory)
        return selected_directories

    # Keep directories and files, but avoid duplicate nested actions:
    # if a directory is selected, its children should not be moved/copied again.
    directories = sorted(
        (path for path in all_candidates if path.is_dir()), key=lambda p: len(p.parts)
    )
    selected_directories: list[Path] = []
    for directory in directories:
        if not any(parent in directory.parents for parent in selected_directories):
            selected_directories.append(directory)

    selected: list[Path] = list(selected_directories)
    for path in all_candidates:
        if not path.is_file():
            continue
        if any(parent in path.parents for parent in selected_directories):
            continue
        if not _file_allowed_by_filters(path, settings):
            continue
        selected.append(path)

    return selected


def extract_file_date(file_path: Path, date_basis: str) -> datetime:
    stat = file_path.stat()
    if date_basis == "creation_time":
        timestamp = stat.st_ctime
    elif date_basis == "modified_time":
        timestamp = stat.st_mtime
    else:
        raise ValueError(f"Unsupported date basis: {date_basis}")
    return datetime.fromtimestamp(timestamp)


def generate_target_path(file_path: Path, date: datetime, settings: Settings) -> Path:
    date_folder = format_date(date, settings.folder_format)
    return settings.target_path / date_folder / file_path.name


def resolve_conflict(target_path: Path, policy: str) -> Path | None:
    if not target_path.exists():
        return target_path

    if policy == "overwrite":
        return target_path
    if policy == "skip":
        return None
    if policy == "auto_rename":
        return safe_rename(target_path)

    raise ValueError(f"Unsupported conflict policy: {policy}")


def plan_actions(files: list[Path], settings: Settings) -> list[PlannedAction]:
    actions: list[PlannedAction] = []
    for file_path in files:
        file_date = extract_file_date(file_path, settings.date_basis)
        target = generate_target_path(file_path, file_date, settings)
        resolved_target = resolve_conflict(target, settings.conflict_policy)

        if resolved_target is None:
            actions.append(
                PlannedAction(
                    source_file=file_path,
                    target_file=target,
                    status="skipped",
                    error_message="Skipped due to conflict policy.",
                )
            )
            continue

        actions.append(
            PlannedAction(source_file=file_path, target_file=resolved_target, status="planned")
        )
    return actions


def execute_actions(
    actions: list[PlannedAction],
    settings: Settings,
    progress_callback: ProgressCallback | None = None,
) -> list[PlannedAction]:
    total = len(actions)

    def progress_message(action: PlannedAction) -> str:
        return f"{action.status}: {action.source_file} -> {action.target_file}"

    for index, action in enumerate(actions, start=1):
        if action.status == "skipped":
            if progress_callback:
                progress_callback(index, total, progress_message(action))
            continue

        try:
            if settings.dry_run:
                action.status = "planned"
            elif settings.operation_mode == "move":
                action.target_file.parent.mkdir(parents=True, exist_ok=True)
                if settings.conflict_policy == "overwrite" and action.target_file.exists():
                    if action.target_file.is_dir():
                        shutil.rmtree(action.target_file)
                    else:
                        action.target_file.unlink()
                shutil.move(str(action.source_file), str(action.target_file))
                action.status = "executed"
            elif settings.operation_mode == "copy":
                action.target_file.parent.mkdir(parents=True, exist_ok=True)
                if action.source_file.is_dir():
                    if settings.conflict_policy == "overwrite" and action.target_file.exists():
                        shutil.rmtree(action.target_file)
                    shutil.copytree(action.source_file, action.target_file)
                else:
                    if settings.conflict_policy == "overwrite" and action.target_file.exists():
                        if action.target_file.is_dir():
                            shutil.rmtree(action.target_file)
                        else:
                            action.target_file.unlink()
                    shutil.copy2(action.source_file, action.target_file)
                action.status = "executed"
            else:
                raise ValueError(f"Unsupported operation mode: {settings.operation_mode}")

        except Exception as exc:  # noqa: BLE001
            action.status = "failed"
            action.error_message = str(exc)

        if progress_callback:
            progress_callback(index, total, progress_message(action))

    return actions


def write_operation_log(actions: list[PlannedAction], log_file: Path, settings: Settings) -> None:
    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "operation_mode": settings.operation_mode,
        "dry_run": settings.dry_run,
        "actions": [
            {
                "source_file": str(action.source_file),
                "target_file": str(action.target_file),
                "status": action.status,
                "error_message": action.error_message,
            }
            for action in actions
        ],
    }

    log_file.parent.mkdir(parents=True, exist_ok=True)
    state_file = _state_file_for_log(log_file)
    state_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines: list[str] = []
    lines.append(_log_line("INFO", "Operation run started"))
    lines.append(
        _log_line(
            "INFO",
            f"Mode={settings.operation_mode} DryRun={settings.dry_run} Total={len(actions)}",
        )
    )
    for action in actions:
        message = f"{action.status}: {action.source_file} -> {action.target_file}"
        if action.error_message:
            message = f"{message} | error={action.error_message}"
        level = "ERROR" if action.status == "failed" else "INFO"
        lines.append(_log_line(level, message))
    lines.append(_log_line("INFO", "Operation run finished"))

    with log_file.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def undo_last_operation(log_file: Path) -> list[PlannedAction]:
    state_file = _state_file_for_log(log_file)
    if not state_file.exists():
        raise FileNotFoundError(f"State log file not found: {state_file}")

    payload = json.loads(state_file.read_text(encoding="utf-8"))
    operation_mode = payload.get("operation_mode", "move")

    undone: list[PlannedAction] = []
    for item in reversed(payload.get("actions", [])):
        action = PlannedAction(
            source_file=Path(item["source_file"]),
            target_file=Path(item["target_file"]),
            status=item.get("status", "planned"),
            error_message=item.get("error_message", ""),
        )

        if action.status != "executed":
            undone.append(action)
            continue

        try:
            if operation_mode == "move":
                if action.target_file.exists():
                    action.source_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(action.target_file), str(action.source_file))
                _cleanup_empty_date_dirs(action.target_file.parent)
                action.status = "undone"
            elif operation_mode == "copy":
                if action.target_file.exists():
                    if action.target_file.is_dir():
                        shutil.rmtree(action.target_file)
                    else:
                        action.target_file.unlink()
                _cleanup_empty_date_dirs(action.target_file.parent)
                action.status = "undone"
            else:
                raise ValueError(f"Unsupported operation mode in log: {operation_mode}")

        except Exception as exc:  # noqa: BLE001
            action.status = "failed"
            action.error_message = str(exc)

        undone.append(action)

    write_back = {
        **payload,
        "undone_at": datetime.now().isoformat(timespec="seconds"),
        "undo_actions": [
            {
                "source_file": str(action.source_file),
                "target_file": str(action.target_file),
                "status": action.status,
                "error_message": action.error_message,
            }
            for action in undone
        ],
    }
    state_file.write_text(json.dumps(write_back, indent=2), encoding="utf-8")

    lines: list[str] = []
    lines.append(_log_line("INFO", "Undo run started"))
    lines.append(_log_line("INFO", f"Mode={operation_mode} Total={len(undone)}"))
    for action in undone:
        message = f"{action.status}: {action.source_file} <- {action.target_file}"
        if action.error_message:
            message = f"{message} | error={action.error_message}"
        level = "ERROR" if action.status == "failed" else "INFO"
        lines.append(_log_line(level, message))
    lines.append(_log_line("INFO", "Undo run finished"))

    with log_file.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    return undone


def _cleanup_empty_date_dirs(start_dir: Path) -> None:
    current = start_dir
    while current.exists() and current.is_dir():
        if any(current.iterdir()):
            break
        if not _is_date_like_dir_name(current.name):
            break
        current.rmdir()
        current = current.parent


def _is_date_like_dir_name(name: str) -> bool:
    return bool(DATE_DIR_PATTERN.match(name) or DATE_SEGMENT_PATTERN.match(name))


def _state_file_for_log(log_file: Path) -> Path:
    return log_file.with_suffix(".state.json")


def _log_line(level: str, message: str) -> str:
    timestamp = datetime.now().isoformat(timespec="seconds")
    return f"{timestamp} | {level} | {message}"


def _path_allowed_by_hidden_filter(path: Path, settings: Settings) -> bool:
    if settings.include_hidden:
        return True
    return not _is_hidden(path)


def _file_allowed_by_filters(path: Path, settings: Settings) -> bool:
    if settings.extension_filter.strip():
        allowed_exts = _normalize_extensions(settings.extension_filter)
        if path.suffix.lower() not in allowed_exts:
            return False

    size = path.stat().st_size
    if settings.min_size_bytes is not None and size < settings.min_size_bytes:
        return False
    if settings.max_size_bytes is not None and size > settings.max_size_bytes:
        return False

    return True


def _normalize_extensions(raw: str) -> set[str]:
    parts = [segment.strip().lower() for segment in raw.split(",") if segment.strip()]
    normalized: set[str] = set()
    for part in parts:
        if not part.startswith("."):
            part = f".{part}"
        normalized.add(part)
    return normalized


def _is_hidden(path: Path) -> bool:
    if path.name.startswith("."):
        return True

    # On Windows, check file attribute for hidden bit when available.
    stat_value = path.stat()
    attributes = getattr(stat_value, "st_file_attributes", 0)
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_HIDDEN", 0))


def _path_allowed_by_runtime_exclusions(path: Path, settings: Settings) -> bool:
    if DATA_DIR_NAME in path.parts:
        return False

    # Exclude running executable/script path when source/target points to the app folder.
    protected_files: set[Path] = set()
    if getattr(sys, "frozen", False):
        protected_files.add(Path(sys.executable).resolve())
    else:
        protected_files.add(Path(__file__).resolve())

    try:
        resolved_path = path.resolve()
    except OSError:
        resolved_path = path

    if resolved_path in protected_files:
        return False

    return True
