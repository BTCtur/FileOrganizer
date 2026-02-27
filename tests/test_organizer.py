from __future__ import annotations

from pathlib import Path

from models import Settings
from organizer import (
    execute_actions,
    plan_actions,
    scan_files,
    undo_last_operation,
    write_operation_log,
)


def test_plan_and_execute_copy_mode(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    sample = source / "demo.txt"
    sample.write_text("hello", encoding="utf-8")

    settings = Settings(
        source_path=source, target_path=target, operation_mode="copy", dry_run=False
    )

    files = scan_files(settings)
    actions = plan_actions(files, settings)
    result = execute_actions(actions, settings)

    assert len(result) == 1
    assert result[0].status == "executed"
    assert result[0].target_file.exists()
    assert sample.exists()


def test_undo_last_operation_for_move(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    sample = source / "move-me.txt"
    sample.write_text("data", encoding="utf-8")

    settings = Settings(
        source_path=source, target_path=target, operation_mode="move", dry_run=False
    )

    files = scan_files(settings)
    actions = plan_actions(files, settings)
    executed = execute_actions(actions, settings)

    log_file = tmp_path / "operation_log.json"
    write_operation_log(executed, log_file, settings)

    undone = undo_last_operation(log_file)

    assert any(action.status == "undone" for action in undone)
    assert not executed[0].target_file.parent.exists()


def test_dry_run_does_not_move_or_create_target_dirs(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    sample = source / "dry-run.txt"
    sample.write_text("data", encoding="utf-8")

    settings = Settings(source_path=source, target_path=target, operation_mode="move", dry_run=True)

    files = scan_files(settings)
    actions = plan_actions(files, settings)
    result = execute_actions(actions, settings)

    assert len(result) == 1
    assert result[0].status == "planned"
    assert sample.exists()
    assert not result[0].target_file.parent.exists()


def test_scan_includes_directories_and_avoids_nested_duplicates(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    top_dir = source / "top"
    nested_dir = top_dir / "nested"
    nested_dir.mkdir(parents=True)
    nested_file = nested_dir / "inside.txt"
    nested_file.write_text("content", encoding="utf-8")
    root_file = source / "root.txt"
    root_file.write_text("content", encoding="utf-8")

    settings = Settings(source_path=source, target_path=target, recursive=True)
    items = scan_files(settings)

    assert top_dir in items
    assert root_file in items
    assert nested_dir not in items
    assert nested_file not in items


def test_move_directory_when_recursive_disabled(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    folder = source / "folder_a"
    folder.mkdir()
    (folder / "a.txt").write_text("abc", encoding="utf-8")

    settings = Settings(
        source_path=source,
        target_path=target,
        recursive=False,
        operation_mode="move",
        dry_run=False,
    )

    items = scan_files(settings)
    actions = plan_actions(items, settings)
    result = execute_actions(actions, settings)

    folder_actions = [action for action in result if action.source_file == folder]
    assert folder_actions
    assert folder_actions[0].status == "executed"
    assert folder_actions[0].target_file.exists()
    assert not folder.exists()


def test_undo_last_operation_for_copy_removes_empty_date_dir(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    sample = source / "copy-me.txt"
    sample.write_text("data", encoding="utf-8")

    settings = Settings(
        source_path=source, target_path=target, operation_mode="copy", dry_run=False
    )

    files = scan_files(settings)
    actions = plan_actions(files, settings)
    executed = execute_actions(actions, settings)

    log_file = tmp_path / "operation_log.json"
    write_operation_log(executed, log_file, settings)
    undo_last_operation(log_file)

    assert sample.exists()
    assert not executed[0].target_file.exists()
    assert not executed[0].target_file.parent.exists()


def test_undo_move_cleans_empty_date_dir_even_if_target_missing(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    sample = source / "lost-target.txt"
    sample.write_text("data", encoding="utf-8")

    settings = Settings(
        source_path=source, target_path=target, operation_mode="move", dry_run=False
    )

    files = scan_files(settings)
    actions = plan_actions(files, settings)
    executed = execute_actions(actions, settings)

    # Simulate external deletion before undo.
    if executed[0].target_file.exists():
        executed[0].target_file.unlink()

    log_file = tmp_path / "operation_log.json"
    write_operation_log(executed, log_file, settings)
    undo_last_operation(log_file)

    assert not executed[0].target_file.parent.exists()


def test_execute_progress_callback_contains_source_and_target(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    sample = source / "progress.txt"
    sample.write_text("data", encoding="utf-8")

    settings = Settings(
        source_path=source, target_path=target, operation_mode="copy", dry_run=False
    )

    files = scan_files(settings)
    actions = plan_actions(files, settings)
    messages: list[str] = []

    def callback(_current: int, _total: int, message: str) -> None:
        messages.append(message)

    execute_actions(actions, settings, progress_callback=callback)

    assert messages
    assert "->" in messages[0]
    assert "progress.txt" in messages[0]


def test_extension_filter_only_includes_matching_files(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    (source / "a.txt").write_text("a", encoding="utf-8")
    (source / "b.jpg").write_text("b", encoding="utf-8")

    settings = Settings(
        source_path=source,
        target_path=target,
        extension_filter=".txt",
    )

    items = scan_files(settings)
    assert source / "a.txt" in items
    assert source / "b.jpg" not in items


def test_size_filters_exclude_out_of_range_files(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    small = source / "small.txt"
    big = source / "big.txt"
    small.write_text("1234", encoding="utf-8")  # 4 bytes
    big.write_text("x" * 4096, encoding="utf-8")  # 4096 bytes

    settings = Settings(
        source_path=source,
        target_path=target,
        min_size_bytes=100,
        max_size_bytes=5000,
    )
    items = scan_files(settings)
    assert big in items
    assert small not in items


def test_hidden_files_excluded_unless_enabled(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    visible = source / "visible.txt"
    hidden = source / ".hidden.txt"
    visible.write_text("v", encoding="utf-8")
    hidden.write_text("h", encoding="utf-8")

    default_settings = Settings(source_path=source, target_path=target, include_hidden=False)
    included_settings = Settings(source_path=source, target_path=target, include_hidden=True)

    default_items = scan_files(default_settings)
    included_items = scan_files(included_settings)

    assert visible in default_items
    assert hidden not in default_items
    assert hidden in included_items


def test_extension_filter_disables_directory_level_actions(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    folder = source / "images"
    folder.mkdir()
    (folder / "a.jpg").write_text("jpg", encoding="utf-8")
    (folder / "b.txt").write_text("txt", encoding="utf-8")

    settings = Settings(
        source_path=source,
        target_path=target,
        recursive=True,
        extension_filter=".txt",
    )

    items = scan_files(settings)

    assert folder not in items
    assert (folder / "b.txt") in items
    assert (folder / "a.jpg") not in items


def test_item_mode_folders_only_returns_only_directories(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    folder = source / "folder_a"
    folder.mkdir()
    (folder / "inside.txt").write_text("x", encoding="utf-8")
    root_file = source / "root.txt"
    root_file.write_text("y", encoding="utf-8")

    settings = Settings(
        source_path=source,
        target_path=target,
        recursive=True,
        item_mode="folders_only",
    )
    items = scan_files(settings)

    assert folder in items
    assert root_file not in items


def test_operation_log_is_plain_text_with_timestamps(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    sample = source / "plain-log.txt"
    sample.write_text("data", encoding="utf-8")

    settings = Settings(
        source_path=source, target_path=target, operation_mode="copy", dry_run=False
    )
    files = scan_files(settings)
    actions = plan_actions(files, settings)
    executed = execute_actions(actions, settings)

    log_file = tmp_path / "operation.log"
    write_operation_log(executed, log_file, settings)

    content = log_file.read_text(encoding="utf-8")
    assert " | INFO | " in content
    assert "executed:" in content
    assert "{\n" not in content
