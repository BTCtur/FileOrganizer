from __future__ import annotations

from typing import Any

Language = str

TRANSLATIONS: dict[Language, dict[str, str]] = {
    "tr": {
        "window_title": "FileOrganizer",
        "directories": "Dizinler",
        "source": "Kaynak",
        "target": "Hedef",
        "browse": "Sec",
        "options": "Secenekler",
        "language": "Dil",
        "language_turkish": "Turkce",
        "language_english": "Ingilizce",
        "info_menu": "Bilgi",
        "history_menu": "Gecmis",
        "tab_organize": "Duzenle",
        "tab_history": "Gecmis",
        "tab_settings": "Ayarlar",
        "recursive": "Alt Klasorler",
        "dry_run": "Dry run (degisiklik yapma)",
        "operation": "Islem",
        "date_basis": "Tarih Temeli",
        "folder_format": "Klasor Formati",
        "conflict": "Cakisma",
        "filters": "Filtreler",
        "extensions": "Uzantilar (virgulle)",
        "item_mode": "Oge Tipi",
        "item_mode_both": "Dosya + Klasor",
        "item_mode_files_only": "Sadece Dosya",
        "item_mode_folders_only": "Sadece Klasor",
        "include_hidden": "Gizli dosya/klasorleri dahil et",
        "min_size_kb": "Min boyut (KB)",
        "max_size_kb": "Max boyut (KB)",
        "filter_error_title": "Filtre Hatasi",
        "filter_error_invalid_size": "Boyut alani sayisal olmalidir: {field}",
        "filter_error_size_order": "Min boyut, max boyuttan buyuk olamaz.",
        "operation_move": "Tasima",
        "operation_copy": "Kopyalama",
        "date_creation_time": "Olusturma zamani",
        "date_modified_time": "Degistirme zamani",
        "conflict_overwrite": "Uzerine yaz",
        "conflict_skip": "Atla",
        "conflict_auto_rename": "Otomatik yeniden adlandir",
        "analyze": "Analiz Et",
        "start": "Baslat",
        "undo": "Son Islemi Geri Al",
        "clear_log": "Ekran Logunu Temizle",
        "log": "Log",
        "progress_text": "Ilerleme: {percent}% | Kalan sure: {eta}",
        "progress_idle": "Ilerleme: 0% | Kalan sure: --",
        "progress_done": "Ilerleme: 100% | Kalan sure: 00:00",
        "select_source": "Kaynak dizin secin",
        "select_target": "Hedef dizin secin",
        "analyze_error": "Analiz Hatasi",
        "no_actions_title": "Islem Yok",
        "no_actions_message": "Lutfen once Analiz Et calistirin.",
        "start_confirm_title": "Calistirma Onayi",
        "start_confirm_message": (
            "Toplam planlanan: {total}\n"
            "Dosya: {files}\n"
            "Klasor: {dirs}\n"
            "Islem modu: {operation}\n"
            "Dry run: {dry_run}\n\n"
            "Devam etmek istiyor musunuz?"
        ),
        "dry_run_yes": "Acik",
        "dry_run_no": "Kapali",
        "undo_error": "Geri Alma Hatasi",
        "undo_error_log": "Geri alma hatasi: {error}",
        "analyze_complete": (
            "Analiz tamamlandi: {total} islem planlandi " "({files} dosya, {dirs} klasor)."
        ),
        "plan_line": "[PLAN][{kind}] {source} -> {target}",
        "plan_more": "... ve {remaining} adet daha planli oge var.",
        "execution_done": "Islem tamamlandi. Basarisiz: {failed}",
        "undo_done": "Geri alma tamamlandi. Geri alinan: {undone}, Basarisiz: {failed}",
        "kind_file": "DOSYA",
        "kind_dir": "KLASOR",
        "history_title": "Gecmis Operasyonlar",
        "history_refresh": "Yenile",
        "history_empty": "Henuz kayitli operasyon gecmisi yok.",
        "history_load_error": "Gecmis okunamadi: {error}",
    },
    "en": {
        "window_title": "FileOrganizer",
        "directories": "Directories",
        "source": "Source",
        "target": "Target",
        "browse": "Browse",
        "options": "Options",
        "language": "Language",
        "language_turkish": "Turkish",
        "language_english": "English",
        "info_menu": "Info",
        "history_menu": "History",
        "tab_organize": "Organize",
        "tab_history": "History",
        "tab_settings": "Settings",
        "recursive": "Recursive",
        "dry_run": "Dry run (no changes)",
        "operation": "Operation",
        "date_basis": "Date basis",
        "folder_format": "Folder format",
        "conflict": "Conflict",
        "filters": "Filters",
        "extensions": "Extensions (comma-separated)",
        "item_mode": "Item Type",
        "item_mode_both": "Files + Folders",
        "item_mode_files_only": "Files only",
        "item_mode_folders_only": "Folders only",
        "include_hidden": "Include hidden files/folders",
        "min_size_kb": "Min size (KB)",
        "max_size_kb": "Max size (KB)",
        "filter_error_title": "Filter Error",
        "filter_error_invalid_size": "Size field must be numeric: {field}",
        "filter_error_size_order": "Min size cannot be greater than max size.",
        "operation_move": "Move",
        "operation_copy": "Copy",
        "date_creation_time": "Creation time",
        "date_modified_time": "Modified time",
        "conflict_overwrite": "Overwrite",
        "conflict_skip": "Skip",
        "conflict_auto_rename": "Auto rename",
        "analyze": "Analyze",
        "start": "Start",
        "undo": "Undo Last Operation",
        "clear_log": "Clear Screen Log",
        "log": "Log",
        "progress_text": "Progress: {percent}% | ETA: {eta}",
        "progress_idle": "Progress: 0% | ETA: --",
        "progress_done": "Progress: 100% | ETA: 00:00",
        "select_source": "Select source directory",
        "select_target": "Select target directory",
        "analyze_error": "Analyze Error",
        "no_actions_title": "No Actions",
        "no_actions_message": "Please run Analyze first.",
        "start_confirm_title": "Execution Confirmation",
        "start_confirm_message": (
            "Total planned: {total}\n"
            "Files: {files}\n"
            "Folders: {dirs}\n"
            "Operation mode: {operation}\n"
            "Dry run: {dry_run}\n\n"
            "Do you want to continue?"
        ),
        "dry_run_yes": "Enabled",
        "dry_run_no": "Disabled",
        "undo_error": "Undo Error",
        "undo_error_log": "Undo error: {error}",
        "analyze_complete": (
            "Analyze complete: {total} action(s) planned " "({files} file(s), {dirs} folder(s))."
        ),
        "plan_line": "[PLAN][{kind}] {source} -> {target}",
        "plan_more": "... and {remaining} more planned item(s).",
        "execution_done": "Execution completed. Failed: {failed}",
        "undo_done": "Undo completed. Undone: {undone}, Failed: {failed}",
        "kind_file": "FILE",
        "kind_dir": "DIR",
        "history_title": "Past Operations",
        "history_refresh": "Refresh",
        "history_empty": "No operation history yet.",
        "history_load_error": "Failed to read history: {error}",
    },
}


def tr(language: str, key: str, **kwargs: Any) -> str:
    lang_map = TRANSLATIONS.get(language, TRANSLATIONS["en"])
    template = lang_map.get(key) or TRANSLATIONS["en"].get(key, key)
    return template.format(**kwargs)
