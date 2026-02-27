from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

OperationMode = Literal["move", "copy"]
DateBasis = Literal["creation_time", "modified_time"]
FolderFormat = Literal["YYYY-MM-DD", "YYYY/MM/DD"]
ConflictPolicy = Literal["overwrite", "skip", "auto_rename"]
ActionStatus = Literal["planned", "executed", "skipped", "failed", "undone"]
ItemMode = Literal["both", "files_only", "folders_only"]


@dataclass(slots=True)
class Settings:
    source_path: Path
    target_path: Path
    recursive: bool = False
    operation_mode: OperationMode = "move"
    date_basis: DateBasis = "creation_time"
    folder_format: FolderFormat = "YYYY-MM-DD"
    conflict_policy: ConflictPolicy = "auto_rename"
    dry_run: bool = True
    extension_filter: str = ""
    include_hidden: bool = False
    min_size_bytes: int | None = None
    max_size_bytes: int | None = None
    item_mode: ItemMode = "both"


@dataclass(slots=True)
class PlannedAction:
    source_file: Path
    target_file: Path
    status: ActionStatus = "planned"
    error_message: str = ""
