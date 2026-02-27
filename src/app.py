from __future__ import annotations

import json
import queue
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

try:
    from .i18n import tr
    from .models import Settings
    from .organizer import (
        execute_actions,
        plan_actions,
        scan_files,
        undo_last_operation,
        write_operation_log,
    )
except ImportError:
    try:
        from src.i18n import tr
        from src.models import Settings
        from src.organizer import (
            execute_actions,
            plan_actions,
            scan_files,
            undo_last_operation,
            write_operation_log,
        )
    except ImportError:
        from i18n import tr
        from models import Settings
        from organizer import (
            execute_actions,
            plan_actions,
            scan_files,
            undo_last_operation,
            write_operation_log,
        )


class FileOrganizerApp(tk.Tk):
    DATA_DIR_NAME = "FileOrganizer_data"
    LOG_FILE = Path(DATA_DIR_NAME) / "operation.log"
    UI_SETTINGS_FILE = Path(DATA_DIR_NAME) / "ui_settings.json"
    APP_VERSION = "0.2.0"
    APP_AUTHOR = "BTC (Burhan Turgay)"
    APP_YEAR = "2026"
    BG_COLOR = "#f3f3f3"
    CARD_BG = "#fbfbfb"
    BORDER_COLOR = "#dcdcdc"
    TEXT_COLOR = "#202124"
    MUTED_TEXT_COLOR = "#5f6368"
    ACCENT_COLOR = "#0f6cbd"
    ACCENT_ACTIVE = "#115ea3"

    def __init__(self) -> None:
        super().__init__()
        self.title("FileOrganizer")
        self.geometry("900x650")
        self.minsize(860, 620)
        self.configure(bg=self.BG_COLOR)
        self._apply_app_icon()

        self._planned_actions = []
        self._ui_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._execution_started_at: datetime | None = None
        self._configure_runtime_paths()

        self.source_var = tk.StringVar()
        self.target_var = tk.StringVar()
        self.language_var = tk.StringVar(value="en")
        self.recursive_var = tk.BooleanVar(value=False)
        self.operation_var = tk.StringVar(value="move")
        self.operation_display_var = tk.StringVar()
        self.date_basis_var = tk.StringVar(value="creation_time")
        self.date_basis_display_var = tk.StringVar()
        self.folder_format_var = tk.StringVar(value="YYYY-MM-DD")
        self.folder_format_display_var = tk.StringVar()
        self.conflict_var = tk.StringVar(value="auto_rename")
        self.conflict_display_var = tk.StringVar()
        self.dry_run_var = tk.BooleanVar(value=False)
        self.extension_filter_var = tk.StringVar()
        self.item_mode_var = tk.StringVar(value="both")
        self.item_mode_display_var = tk.StringVar()
        self.include_hidden_var = tk.BooleanVar(value=False)
        self.min_size_kb_var = tk.StringVar()
        self.max_size_kb_var = tk.StringVar()

        self._load_ui_settings()
        self._configure_styles()
        self._build_ui()
        self._apply_language()
        self.after(100, self._drain_queue)

    def _t(self, key: str, **kwargs: object) -> str:
        return tr(self.language_var.get(), key, **kwargs)

    def _configure_runtime_paths(self) -> None:
        if getattr(sys, "frozen", False):
            base_dir = Path(sys.executable).resolve().parent
            data_dir = base_dir / self.DATA_DIR_NAME
        else:
            data_dir = Path(self.DATA_DIR_NAME)

        data_dir.mkdir(parents=True, exist_ok=True)
        self.LOG_FILE = data_dir / "operation.log"
        self.UI_SETTINGS_FILE = data_dir / "ui_settings.json"

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=14, style="App.TFrame")
        root.pack(fill="both", expand=True)

        self._build_menubar()
        self.notebook = ttk.Notebook(root, style="App.TNotebook")
        self.notebook.pack(fill="both", expand=True)

        self.organize_tab = ttk.Frame(self.notebook, style="App.TFrame", padding=10)
        self.history_tab = ttk.Frame(self.notebook, style="App.TFrame", padding=10)
        self.settings_tab = ttk.Frame(self.notebook, style="App.TFrame", padding=10)
        self.notebook.add(self.organize_tab, text="Organize")
        self.notebook.add(self.history_tab, text="History")
        self.notebook.add(self.settings_tab, text="Settings")

        self.path_frame = ttk.LabelFrame(self.settings_tab, padding=12, style="Card.TLabelframe")
        self.path_frame.pack(fill="x")

        self.source_label = ttk.Label(self.path_frame)
        self.source_label.grid(row=0, column=0, sticky="w")
        ttk.Entry(self.path_frame, textvariable=self.source_var).grid(
            row=0, column=1, sticky="ew", padx=8
        )
        self.source_browse_button = ttk.Button(self.path_frame, command=self._pick_source)
        self.source_browse_button.grid(row=0, column=2)

        self.target_label = ttk.Label(self.path_frame)
        self.target_label.grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(self.path_frame, textvariable=self.target_var).grid(
            row=1, column=1, sticky="ew", padx=8, pady=(8, 0)
        )
        self.target_browse_button = ttk.Button(self.path_frame, command=self._pick_target)
        self.target_browse_button.grid(row=1, column=2, pady=(8, 0))
        self.path_frame.columnconfigure(1, weight=1)

        self.options_frame = ttk.LabelFrame(self.settings_tab, padding=12, style="Card.TLabelframe")
        self.options_frame.pack(fill="x", pady=10)

        self.operation_label = ttk.Label(self.options_frame)
        self.operation_label.grid(row=0, column=0, sticky="w")
        self.operation_combo = ttk.Combobox(
            self.options_frame,
            textvariable=self.operation_display_var,
            state="readonly",
        )
        self.operation_combo.grid(row=0, column=1, sticky="w")
        self.operation_combo.bind("<<ComboboxSelected>>", self._on_operation_selected)

        self.date_basis_label = ttk.Label(self.options_frame)
        self.date_basis_label.grid(row=0, column=2, sticky="w", padx=(20, 0))
        self.date_basis_combo = ttk.Combobox(
            self.options_frame,
            textvariable=self.date_basis_display_var,
            state="readonly",
        )
        self.date_basis_combo.grid(row=0, column=3, sticky="w")
        self.date_basis_combo.bind("<<ComboboxSelected>>", self._on_date_basis_selected)

        self.folder_format_label = ttk.Label(self.options_frame)
        self.folder_format_label.grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.folder_format_combo = ttk.Combobox(
            self.options_frame,
            textvariable=self.folder_format_display_var,
            state="readonly",
        )
        self.folder_format_combo.grid(row=1, column=1, sticky="w", pady=(8, 0))
        self.folder_format_combo.bind("<<ComboboxSelected>>", self._on_folder_format_selected)

        self.conflict_label = ttk.Label(self.options_frame)
        self.conflict_label.grid(row=1, column=2, sticky="w", pady=(8, 0), padx=(20, 0))
        self.conflict_combo = ttk.Combobox(
            self.options_frame,
            textvariable=self.conflict_display_var,
            state="readonly",
        )
        self.conflict_combo.grid(row=1, column=3, sticky="w", pady=(8, 0))
        self.conflict_combo.bind("<<ComboboxSelected>>", self._on_conflict_selected)

        self.filters_frame = ttk.LabelFrame(
            self.options_frame,
            padding=10,
            style="SubCard.TLabelframe",
        )
        self.filters_frame.grid(
            row=2,
            column=0,
            columnspan=4,
            sticky="ew",
            pady=(12, 0),
        )

        self.extensions_label = ttk.Label(self.filters_frame)
        self.extensions_label.grid(row=0, column=0, sticky="w")
        self.extensions_entry = ttk.Entry(
            self.filters_frame, textvariable=self.extension_filter_var
        )
        self.extensions_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        self.item_mode_label = ttk.Label(self.filters_frame)
        self.item_mode_label.grid(row=0, column=2, sticky="w", padx=(20, 0))
        self.item_mode_combo = ttk.Combobox(
            self.filters_frame,
            textvariable=self.item_mode_display_var,
            state="readonly",
            width=20,
        )
        self.item_mode_combo.grid(row=0, column=3, sticky="w", padx=(8, 0))
        self.item_mode_combo.bind("<<ComboboxSelected>>", self._on_item_mode_selected)

        self.min_size_label = ttk.Label(self.filters_frame)
        self.min_size_label.grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.min_size_entry = ttk.Entry(
            self.filters_frame, textvariable=self.min_size_kb_var, width=12
        )
        self.min_size_entry.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

        self.max_size_label = ttk.Label(self.filters_frame)
        self.max_size_label.grid(row=1, column=2, sticky="w", padx=(20, 0), pady=(8, 0))
        self.max_size_entry = ttk.Entry(
            self.filters_frame, textvariable=self.max_size_kb_var, width=12
        )
        self.max_size_entry.grid(row=1, column=3, sticky="w", padx=(8, 0), pady=(8, 0))

        self.include_hidden_checkbox = ttk.Checkbutton(
            self.filters_frame, variable=self.include_hidden_var
        )
        self.include_hidden_checkbox.grid(row=2, column=0, columnspan=4, sticky="w", pady=(8, 0))
        self.filters_frame.columnconfigure(1, weight=1)

        actions_frame = ttk.Frame(self.organize_tab, style="App.TFrame")
        actions_frame.pack(fill="x")
        self.analyze_button = ttk.Button(
            actions_frame, command=self._analyze, style="Secondary.TButton"
        )
        self.analyze_button.pack(side="left")
        self.start_button = ttk.Button(
            actions_frame,
            command=self._start,
            style="Accent.TButton",
        )
        self.start_button.pack(side="left", padx=8)
        self.undo_button = ttk.Button(
            actions_frame,
            command=self._undo,
            style="Secondary.TButton",
        )
        self.undo_button.pack(side="left", padx=8)
        self.clear_log_button = ttk.Button(
            actions_frame,
            command=self._clear_screen_log,
            style="Secondary.TButton",
        )
        self.clear_log_button.pack(side="left", padx=8)

        self.progress = ttk.Progressbar(self.organize_tab, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", pady=10)
        self.progress_text_var = tk.StringVar(value="")
        self.progress_label = ttk.Label(self.organize_tab, textvariable=self.progress_text_var)
        self.progress_label.pack(anchor="w")

        self.log_frame = ttk.LabelFrame(self.organize_tab, padding=12, style="Card.TLabelframe")
        self.log_frame.pack(fill="both", expand=True, pady=(10, 0))
        self.log_text = tk.Text(
            self.log_frame,
            height=14,
            wrap="word",
            bg="#ffffff",
            fg=self.TEXT_COLOR,
            insertbackground=self.TEXT_COLOR,
            relief="flat",
            bd=1,
            highlightthickness=1,
            highlightbackground=self.BORDER_COLOR,
            highlightcolor=self.ACCENT_COLOR,
            padx=8,
            pady=8,
        )
        self.log_text.pack(fill="both", expand=True)

        self.history_frame = ttk.LabelFrame(self.history_tab, padding=12, style="Card.TLabelframe")
        self.history_frame.pack(fill="both", expand=True)
        self.history_text = tk.Text(
            self.history_frame,
            height=18,
            wrap="none",
            bg="#ffffff",
            fg=self.TEXT_COLOR,
            insertbackground=self.TEXT_COLOR,
            relief="flat",
            bd=1,
            highlightthickness=1,
            highlightbackground=self.BORDER_COLOR,
            highlightcolor=self.ACCENT_COLOR,
            padx=8,
            pady=8,
        )
        self.history_text.pack(side="left", fill="both", expand=True)
        self.history_scroll_y = ttk.Scrollbar(
            self.history_frame,
            orient="vertical",
            command=self.history_text.yview,
        )
        self.history_scroll_y.pack(side="right", fill="y")
        self.history_text.configure(yscrollcommand=self.history_scroll_y.set)

        history_bottom = ttk.Frame(self.history_tab, style="App.TFrame")
        history_bottom.pack(fill="x", pady=(8, 0))
        self.history_refresh_button = ttk.Button(
            history_bottom,
            style="Secondary.TButton",
            command=self._load_history_text,
        )
        self.history_refresh_button.pack(side="left")

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        available_themes = set(style.theme_names())
        if "vista" in available_themes:
            style.theme_use("vista")
        elif "xpnative" in available_themes:
            style.theme_use("xpnative")
        else:
            style.theme_use("clam")

        style.configure(".", font=("Segoe UI", 10))
        style.configure(
            "App.TFrame",
            background=self.BG_COLOR,
        )
        style.configure(
            "TLabel",
            background=self.BG_COLOR,
            foreground=self.TEXT_COLOR,
        )
        style.configure(
            "Card.TLabelframe",
            background=self.CARD_BG,
            bordercolor=self.BORDER_COLOR,
            relief="flat",
            borderwidth=1,
        )
        style.configure(
            "Card.TLabelframe.Label",
            background=self.CARD_BG,
            foreground=self.TEXT_COLOR,
            font=("Segoe UI Semibold", 10),
        )
        style.configure(
            "SubCard.TLabelframe",
            background=self.CARD_BG,
            bordercolor=self.BORDER_COLOR,
            relief="flat",
            borderwidth=1,
        )
        style.configure(
            "SubCard.TLabelframe.Label",
            background=self.CARD_BG,
            foreground=self.MUTED_TEXT_COLOR,
            font=("Segoe UI", 9),
        )
        style.configure("TLabelframe", background=self.CARD_BG)
        style.configure("TLabelframe.Label", background=self.CARD_BG, foreground=self.TEXT_COLOR)
        style.configure("TCheckbutton", background=self.CARD_BG, foreground=self.TEXT_COLOR)
        style.configure("TEntry", fieldbackground="#ffffff", bordercolor=self.BORDER_COLOR)
        style.configure(
            "TCombobox",
            fieldbackground="#ffffff",
            background="#ffffff",
            foreground=self.TEXT_COLOR,
            bordercolor=self.BORDER_COLOR,
        )
        style.configure(
            "Secondary.TButton",
            background="#f8f8f8",
            foreground=self.TEXT_COLOR,
            bordercolor=self.BORDER_COLOR,
            focuscolor=self.ACCENT_COLOR,
            padding=(12, 7),
        )
        style.map(
            "Secondary.TButton",
            background=[("active", "#f3f3f3"), ("pressed", "#ececec")],
        )
        style.configure(
            "Accent.TButton",
            background=self.ACCENT_COLOR,
            foreground=self.TEXT_COLOR,
            bordercolor=self.ACCENT_COLOR,
            focuscolor=self.ACCENT_COLOR,
            padding=(12, 7),
            font=("Segoe UI Semibold", 10),
        )
        style.map(
            "Accent.TButton",
            background=[("active", self.ACCENT_ACTIVE), ("pressed", self.ACCENT_ACTIVE)],
            foreground=[("active", self.TEXT_COLOR), ("pressed", self.TEXT_COLOR)],
        )
        style.configure(
            "Horizontal.TProgressbar",
            troughcolor="#e6e6e6",
            background=self.ACCENT_COLOR,
            bordercolor="#e6e6e6",
            lightcolor=self.ACCENT_COLOR,
            darkcolor=self.ACCENT_COLOR,
            thickness=12,
        )
        style.configure("App.TNotebook", background=self.BG_COLOR, borderwidth=0)
        style.configure(
            "App.TNotebook.Tab",
            font=("Segoe UI Semibold", 10),
            padding=(16, 8),
            background="#f6f6f6",
            foreground=self.TEXT_COLOR,
            borderwidth=0,
        )
        style.map(
            "App.TNotebook.Tab",
            background=[("selected", "#ffffff"), ("active", "#efefef")],
            foreground=[("selected", self.ACCENT_COLOR)],
        )

    def _apply_app_icon(self) -> None:
        candidates: list[Path] = []
        base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
        candidates.append(base_dir / "assets" / "app_icon.ico")
        if getattr(sys, "frozen", False):
            candidates.append(Path(sys.executable).with_name("app_icon.ico"))
        else:
            candidates.append(Path(__file__).resolve().parents[1] / "assets" / "app_icon.ico")
            candidates.append(Path.cwd() / "assets" / "app_icon.ico")

        for icon_path in candidates:
            if icon_path.exists():
                try:
                    self.iconbitmap(str(icon_path))
                    return
                except Exception:  # noqa: BLE001
                    pass

    def _build_menubar(self) -> None:
        menubar = tk.Menu(self)
        language_menu = tk.Menu(menubar, tearoff=0)
        language_menu.add_radiobutton(
            label=self._t("language_turkish"),
            variable=self.language_var,
            value="tr",
            command=lambda: self._set_language("tr"),
        )
        language_menu.add_radiobutton(
            label=self._t("language_english"),
            variable=self.language_var,
            value="en",
            command=lambda: self._set_language("en"),
        )
        menubar.add_cascade(label=self._t("language"), menu=language_menu)
        options_menu = tk.Menu(menubar, tearoff=0)
        options_menu.add_checkbutton(label=self._t("recursive"), variable=self.recursive_var)
        options_menu.add_checkbutton(label=self._t("dry_run"), variable=self.dry_run_var)
        menubar.add_cascade(label=self._t("options"), menu=options_menu)
        menubar.add_command(label=self._t("history_menu"), command=self._open_history_tab)
        menubar.add_command(label=self._t("info_menu"), command=self._show_info_popup)
        self.config(menu=menubar)

    def _show_info_popup(self) -> None:
        popup = tk.Toplevel(self)
        popup.title("Bilgi / Info")
        popup.transient(self)
        popup.grab_set()
        popup.resizable(False, False)

        container = ttk.Frame(popup, padding=12)
        container.pack(fill="both", expand=True)

        info_text = (
            "TR\n"
            "Uygulama: FileOrganizer\n"
            f"Surum: {self.APP_VERSION}\n"
            f"Gelistirici: {self.APP_AUTHOR}\n"
            f"Yil: {self.APP_YEAR}\n\n"
            "EN\n"
            "Application: FileOrganizer\n"
            f"Version: {self.APP_VERSION}\n"
            f"Developer: {self.APP_AUTHOR}\n"
            f"Year: {self.APP_YEAR}\n"
        )

        info_label = ttk.Label(container, text=info_text, justify="left")
        info_label.pack(anchor="w")

        close_button = ttk.Button(container, text="Kapat / Close", command=popup.destroy)
        close_button.pack(anchor="e", pady=(12, 0))

    def _open_history_tab(self) -> None:
        self.notebook.select(self.history_tab)
        self._load_history_text()

    def _load_history_text(self) -> None:
        self.history_text.delete("1.0", "end")
        try:
            if not self.LOG_FILE.exists():
                self.history_text.insert("end", self._t("history_empty"))
                return
            content = self.LOG_FILE.read_text(encoding="utf-8").strip()
            if not content:
                self.history_text.insert("end", self._t("history_empty"))
                return
            self.history_text.insert("end", content)
        except Exception as exc:  # noqa: BLE001
            self.history_text.insert("end", self._t("history_load_error", error=str(exc)))

    def _set_language(self, language: str) -> None:
        self.language_var.set(language)
        self._apply_language()
        self._save_ui_settings()

    def _load_ui_settings(self) -> None:
        if not self.UI_SETTINGS_FILE.exists():
            return

        try:
            payload = json.loads(self.UI_SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return

        language = payload.get("language")
        if language in {"tr", "en"}:
            self.language_var.set(language)

        source_path = payload.get("source_path")
        if isinstance(source_path, str):
            self.source_var.set(source_path)

        target_path = payload.get("target_path")
        if isinstance(target_path, str):
            self.target_var.set(target_path)

        extension_filter = payload.get("extension_filter")
        if isinstance(extension_filter, str):
            self.extension_filter_var.set(extension_filter)

        min_size_kb = payload.get("min_size_kb")
        if isinstance(min_size_kb, str):
            self.min_size_kb_var.set(min_size_kb)

        max_size_kb = payload.get("max_size_kb")
        if isinstance(max_size_kb, str):
            self.max_size_kb_var.set(max_size_kb)

        include_hidden = payload.get("include_hidden")
        if isinstance(include_hidden, bool):
            self.include_hidden_var.set(include_hidden)

        item_mode = payload.get("item_mode")
        if item_mode in {"both", "files_only", "folders_only"}:
            self.item_mode_var.set(item_mode)

    def _save_ui_settings(self) -> None:
        source_path = self.source_var.get().strip()
        target_path = self.target_var.get().strip()
        payload = {
            "language": self.language_var.get(),
            "source_path": source_path,
            "target_path": target_path,
            "last_working_directory": source_path,
            "extension_filter": self.extension_filter_var.get().strip(),
            "min_size_kb": self.min_size_kb_var.get().strip(),
            "max_size_kb": self.max_size_kb_var.get().strip(),
            "include_hidden": self.include_hidden_var.get(),
            "item_mode": self.item_mode_var.get(),
        }
        self.UI_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.UI_SETTINGS_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _make_option_map(self, pairs: list[tuple[str, str]]) -> dict[str, str]:
        return {display: value for display, value in pairs}

    def _display_for_value(self, mapping: dict[str, str], value: str) -> str:
        for display, mapped_value in mapping.items():
            if mapped_value == value:
                return display
        return next(iter(mapping.keys()), value)

    def _refresh_option_translations(self) -> None:
        operation_pairs = [
            (self._t("operation_move"), "move"),
            (self._t("operation_copy"), "copy"),
        ]
        date_basis_pairs = [
            (self._t("date_creation_time"), "creation_time"),
            (self._t("date_modified_time"), "modified_time"),
        ]
        folder_format_pairs = [
            ("YYYY-MM-DD", "YYYY-MM-DD"),
            ("YYYY/MM/DD", "YYYY/MM/DD"),
        ]
        conflict_pairs = [
            (self._t("conflict_overwrite"), "overwrite"),
            (self._t("conflict_skip"), "skip"),
            (self._t("conflict_auto_rename"), "auto_rename"),
        ]
        item_mode_pairs = [
            (self._t("item_mode_both"), "both"),
            (self._t("item_mode_files_only"), "files_only"),
            (self._t("item_mode_folders_only"), "folders_only"),
        ]

        self._operation_map = self._make_option_map(operation_pairs)
        self._date_basis_map = self._make_option_map(date_basis_pairs)
        self._folder_format_map = self._make_option_map(folder_format_pairs)
        self._conflict_map = self._make_option_map(conflict_pairs)
        self._item_mode_map = self._make_option_map(item_mode_pairs)

        self.operation_combo.configure(values=list(self._operation_map.keys()))
        self.date_basis_combo.configure(values=list(self._date_basis_map.keys()))
        self.folder_format_combo.configure(values=list(self._folder_format_map.keys()))
        self.conflict_combo.configure(values=list(self._conflict_map.keys()))
        self.item_mode_combo.configure(values=list(self._item_mode_map.keys()))

        self.operation_display_var.set(
            self._display_for_value(self._operation_map, self.operation_var.get())
        )
        self.date_basis_display_var.set(
            self._display_for_value(self._date_basis_map, self.date_basis_var.get())
        )
        self.folder_format_display_var.set(
            self._display_for_value(self._folder_format_map, self.folder_format_var.get())
        )
        self.conflict_display_var.set(
            self._display_for_value(self._conflict_map, self.conflict_var.get())
        )
        self.item_mode_display_var.set(
            self._display_for_value(self._item_mode_map, self.item_mode_var.get())
        )

    def _on_operation_selected(self, _event: tk.Event[tk.Misc]) -> None:
        selected = self.operation_display_var.get()
        self.operation_var.set(self._operation_map.get(selected, "move"))

    def _on_date_basis_selected(self, _event: tk.Event[tk.Misc]) -> None:
        selected = self.date_basis_display_var.get()
        self.date_basis_var.set(self._date_basis_map.get(selected, "creation_time"))

    def _on_folder_format_selected(self, _event: tk.Event[tk.Misc]) -> None:
        selected = self.folder_format_display_var.get()
        self.folder_format_var.set(self._folder_format_map.get(selected, "YYYY-MM-DD"))

    def _on_conflict_selected(self, _event: tk.Event[tk.Misc]) -> None:
        selected = self.conflict_display_var.get()
        self.conflict_var.set(self._conflict_map.get(selected, "auto_rename"))

    def _on_item_mode_selected(self, _event: tk.Event[tk.Misc]) -> None:
        selected = self.item_mode_display_var.get()
        self.item_mode_var.set(self._item_mode_map.get(selected, "both"))

    def _apply_language(self) -> None:
        self._build_menubar()
        self.title(self._t("window_title"))
        self.notebook.tab(self.organize_tab, text=self._t("tab_organize"))
        self.notebook.tab(self.history_tab, text=self._t("tab_history"))
        self.notebook.tab(self.settings_tab, text=self._t("tab_settings"))
        self.path_frame.configure(text=self._t("directories"))
        self.source_label.configure(text=self._t("source"))
        self.target_label.configure(text=self._t("target"))
        self.source_browse_button.configure(text=self._t("browse"))
        self.target_browse_button.configure(text=self._t("browse"))

        self.options_frame.configure(text=self._t("options"))
        self.operation_label.configure(text=self._t("operation"))
        self.date_basis_label.configure(text=self._t("date_basis"))
        self.folder_format_label.configure(text=self._t("folder_format"))
        self.conflict_label.configure(text=self._t("conflict"))
        self.filters_frame.configure(text=self._t("filters"))
        self.extensions_label.configure(text=self._t("extensions"))
        self.item_mode_label.configure(text=self._t("item_mode"))
        self.min_size_label.configure(text=self._t("min_size_kb"))
        self.max_size_label.configure(text=self._t("max_size_kb"))
        self.include_hidden_checkbox.configure(text=self._t("include_hidden"))

        self.analyze_button.configure(text=self._t("analyze"))
        self.start_button.configure(text=self._t("start"))
        self.undo_button.configure(text=self._t("undo"))
        self.clear_log_button.configure(text=self._t("clear_log"))
        self.log_frame.configure(text=self._t("log"))
        self.history_frame.configure(text=self._t("history_title"))
        self.history_refresh_button.configure(text=self._t("history_refresh"))
        if self.progress["value"] >= self.progress["maximum"] and self.progress["maximum"] > 0:
            self.progress_text_var.set(self._t("progress_done"))
        elif self.progress["value"] > 0:
            percent = int((self.progress["value"] / max(1, self.progress["maximum"])) * 100)
            self.progress_text_var.set(self._t("progress_text", percent=percent, eta="--"))
        else:
            self.progress_text_var.set(self._t("progress_idle"))
        self._load_history_text()
        self._refresh_option_translations()

    def _pick_source(self) -> None:
        selected = filedialog.askdirectory(title=self._t("select_source"))
        if selected:
            self.source_var.set(selected)
            if not self.target_var.get():
                self.target_var.set(selected)
            self._save_ui_settings()

    def _pick_target(self) -> None:
        selected = filedialog.askdirectory(title=self._t("select_target"))
        if selected:
            self.target_var.set(selected)
            self._save_ui_settings()

    def _settings(self) -> Settings:
        source = Path(self.source_var.get().strip())
        target_raw = self.target_var.get().strip()
        target = Path(target_raw) if target_raw else source
        min_size_bytes = self._parse_size_kb_or_none(
            self.min_size_kb_var.get().strip(), "min_size_kb"
        )
        max_size_bytes = self._parse_size_kb_or_none(
            self.max_size_kb_var.get().strip(), "max_size_kb"
        )

        if (
            min_size_bytes is not None
            and max_size_bytes is not None
            and min_size_bytes > max_size_bytes
        ):
            raise ValueError(self._t("filter_error_size_order"))

        return Settings(
            source_path=source,
            target_path=target,
            recursive=self.recursive_var.get(),
            operation_mode=self.operation_var.get(),
            date_basis=self.date_basis_var.get(),
            folder_format=self.folder_format_var.get(),
            conflict_policy=self.conflict_var.get(),
            dry_run=self.dry_run_var.get(),
            extension_filter=self.extension_filter_var.get().strip(),
            include_hidden=self.include_hidden_var.get(),
            min_size_bytes=min_size_bytes,
            max_size_bytes=max_size_bytes,
            item_mode=self.item_mode_var.get(),
        )

    def _parse_size_kb_or_none(self, raw_value: str, field_key: str) -> int | None:
        if not raw_value:
            return None
        try:
            kb_value = float(raw_value)
        except ValueError as exc:
            raise ValueError(
                self._t("filter_error_invalid_size", field=self._t(field_key))
            ) from exc

        if kb_value < 0:
            raise ValueError(self._t("filter_error_invalid_size", field=self._t(field_key)))
        return int(kb_value * 1024)

    def _analyze(self) -> None:
        try:
            settings = self._settings()
            self._save_ui_settings()
            files = scan_files(settings)
            self._planned_actions = plan_actions(files, settings)
            self.progress["maximum"] = max(1, len(self._planned_actions))
            self.progress["value"] = 0
            self.progress_text_var.set(self._t("progress_idle"))

            file_count = sum(1 for path in files if path.is_file())
            dir_count = sum(1 for path in files if path.is_dir())
            self._log(
                self._t(
                    "analyze_complete",
                    total=len(self._planned_actions),
                    files=file_count,
                    dirs=dir_count,
                )
            )

            preview_limit = 30
            for action in self._planned_actions[:preview_limit]:
                kind = self._t("kind_dir") if action.source_file.is_dir() else self._t("kind_file")
                self._log(
                    self._t(
                        "plan_line",
                        kind=kind,
                        source=action.source_file,
                        target=action.target_file,
                    )
                )

            if len(self._planned_actions) > preview_limit:
                remaining = len(self._planned_actions) - preview_limit
                self._log(self._t("plan_more", remaining=remaining))
        except Exception as exc:  # noqa: BLE001
            title = (
                self._t("filter_error_title")
                if "size" in str(exc).lower()
                else self._t("analyze_error")
            )
            messagebox.showerror(title, str(exc))

    def _start(self) -> None:
        if not self._planned_actions:
            messagebox.showinfo(self._t("no_actions_title"), self._t("no_actions_message"))
            return

        settings = self._settings()
        file_count = sum(1 for action in self._planned_actions if action.source_file.is_file())
        dir_count = sum(1 for action in self._planned_actions if action.source_file.is_dir())
        operation_display = self._display_for_value(self._operation_map, settings.operation_mode)
        dry_run_display = self._t("dry_run_yes") if settings.dry_run else self._t("dry_run_no")

        confirmation = messagebox.askokcancel(
            self._t("start_confirm_title"),
            self._t(
                "start_confirm_message",
                total=len(self._planned_actions),
                files=file_count,
                dirs=dir_count,
                operation=operation_display,
                dry_run=dry_run_display,
            ),
        )
        if not confirmation:
            return

        self._execution_started_at = datetime.now()
        self.progress["value"] = 0
        self.progress_text_var.set(self._t("progress_text", percent=0, eta="--"))
        self._save_ui_settings()

        def worker() -> None:
            def progress_callback(current: int, total: int, message: str) -> None:
                self._ui_queue.put(("progress", (current, total, message)))

            result = execute_actions(
                self._planned_actions, settings, progress_callback=progress_callback
            )
            write_operation_log(result, self.LOG_FILE, settings)
            self._ui_queue.put(("done", result))

        threading.Thread(target=worker, daemon=True).start()

    def _undo(self) -> None:
        def worker() -> None:
            try:
                result = undo_last_operation(self.LOG_FILE)
                self._ui_queue.put(("undo_done", result))
            except Exception as exc:  # noqa: BLE001
                self._ui_queue.put(("undo_error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _clear_screen_log(self) -> None:
        self.log_text.delete("1.0", "end")

    def _drain_queue(self) -> None:
        while not self._ui_queue.empty():
            event, payload = self._ui_queue.get_nowait()
            if event == "progress":
                current, total, message = payload
                self.progress["maximum"] = max(1, total)
                self.progress["value"] = current
                self._update_progress_text(current, total)
                self._log(message)
            elif event == "done":
                actions = payload
                failed = sum(1 for action in actions if action.status == "failed")
                self.progress_text_var.set(self._t("progress_done"))
                self._log(self._t("execution_done", failed=failed))
                self._load_history_text()
            elif event == "undo_done":
                actions = payload
                undone = sum(1 for action in actions if action.status == "undone")
                failed = sum(1 for action in actions if action.status == "failed")
                self._log(self._t("undo_done", undone=undone, failed=failed))
                self._load_history_text()
            elif event == "undo_error":
                self._log(self._t("undo_error_log", error=payload))
                messagebox.showerror(self._t("undo_error"), str(payload))

        self.after(100, self._drain_queue)

    def _log(self, message: str) -> None:
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")

    def _update_progress_text(self, current: int, total: int) -> None:
        if total <= 0:
            self.progress_text_var.set(self._t("progress_idle"))
            return

        percent = int((current / total) * 100)
        if current <= 0 or self._execution_started_at is None:
            self.progress_text_var.set(self._t("progress_text", percent=percent, eta="--"))
            return

        elapsed_seconds = max((datetime.now() - self._execution_started_at).total_seconds(), 0.001)
        avg_per_item = elapsed_seconds / current
        remaining_seconds = max(int(avg_per_item * (total - current)), 0)
        eta = f"{remaining_seconds // 60:02d}:{remaining_seconds % 60:02d}"
        self.progress_text_var.set(self._t("progress_text", percent=percent, eta=eta))


def run() -> None:
    app = FileOrganizerApp()
    app.mainloop()


if __name__ == "__main__":
    run()
