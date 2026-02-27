# Faz 1 Proje Plani: FileOrganizer Baslangic ve Konfigurasyon

## Ozet
Bu fazda sadece plan ve baslangic konfigurasyonlari hazirlanir. Is mantigi (scan/plan/execute), GUI detay implementasyonu ve undo implementasyonu bu faza dahil degildir.

Amac: Projeyi Python 3.13+ icin calisabilir, test/lint altyapisi hazir, PyInstaller paketlemeye uygun bir iskelete getirmek.

## Kapsam
### In
- Proje klasor yapisinin olusturulmasi (`src/`, `tests/`, `logs/`)
- Konfigurasyon dosyalarinin olusturulmasi ve doldurulmasi
- Gelistirme araclarinin (pytest, ruff, black) ayarlanmasi
- Paketleme komutunun belgelenmesi (PyInstaller)

### Out
- `app.py`, `organizer.py`, `models.py`, `utils.py` islevlerinin implementasyonu
- GUI ekranlarinin tamamlanmasi
- Gercek dosya tasima/kopyalama operasyonlarinin implementasyonu

## Olusturulan/Guncellenen Dosyalar
1. `README.md`
- Proje amaci, mimari, fazlar, hizli baslangic komutlari, paketleme komutu
- Not: Tkinter stdlib oldugu icin runtime bagimliligi degildir

2. `.gitignore`
- Python, venv, cache, build/artifact, IDE, log ignore kurallari
- `logs/*.json` ignore edilir, `logs/.gitkeep` repoda tutulur

3. `requirements.txt`
- Runtime:
  - `pyinstaller>=6.0,<7.0`

4. `requirements-dev.txt`
- `pytest>=8.0,<9.0`
- `ruff>=0.6,<1.0`
- `black>=24.0,<26.0`

5. `pyproject.toml`
- `[project]`: ad, versiyon, aciklama, `requires-python = ">=3.13"`
- `tool.black`: `line-length = 100`, `target-version = ["py313"]`
- `tool.ruff`: `line-length = 100`, `target-version = "py313"`
- `tool.ruff.lint.select = ["E", "F", "I", "B", "UP"]`
- `tool.pytest.ini_options`: `testpaths = ["tests"]`, `pythonpath = [".", "src"]`

6. `src/__init__.py` (bos)
7. `tests/__init__.py` (bos)
8. `logs/.gitkeep`
9. `tests/test_smoke.py` (basit import smoke testi)

## Faz 1 Sonu Beklenen Yapi
- `.venv/`
- `requirements.txt`
- `requirements-dev.txt`
- `pyproject.toml`
- `.gitignore`
- `README.md`
- `src/__init__.py`
- `tests/__init__.py`
- `tests/test_smoke.py`
- `logs/.gitkeep`
- (korunur) `main.py`

## Faz 2 Icin Public API / Interface Sozlesmeleri
### `models.py`
- `Settings` alanlari:
  - `source_path`, `target_path`, `recursive`, `operation_mode`, `date_basis`, `folder_format`, `conflict_policy`, `dry_run`
- `PlannedAction` alanlari:
  - `source_file`, `target_file`, `status`, `error_message`

### `organizer.py`
- `scan_files(settings) -> list[Path]`
- `extract_file_date(file_path, date_basis) -> datetime`
- `generate_target_path(file_path, date, settings) -> Path`
- `plan_actions(files, settings) -> list[PlannedAction]`
- `execute_actions(actions, settings, progress_callback) -> list[PlannedAction]`
- `resolve_conflict(target_path, policy) -> Path | None`
- `write_operation_log(actions, log_file) -> None`
- `undo_last_operation(log_file) -> list[PlannedAction]`

## Test Senaryolari (Faz 1)
1. `pytest` calisir ve en az 1 smoke test gecer.
2. `ruff check .` lint hatasi vermez.
3. `black --check .` format uyumu saglar.
4. `pyproject.toml` ile test/lint araclari dogru dizinleri gorur.
5. README komutlari uygulanabilir:
- venv aktivasyonu
- bagimlilik kurulumu
- pytest/lint/format kontrolleri
- pyinstaller komutu

## Kabul Kriterleri (Faz 1)
- Repo yeni gelistirici icin tek seferde ayaga kalkar.
- Kalite araclari konfigurasyonlu ve calisir durumdadir.
- Paketleme yolu dokumante edilmistir.
- Faz 2 implementasyonu icin sozlesme zemini hazirdir.

## Varsayimlar ve Defaultlar
- Oncelik Windows, path islemleri `pathlib` ile cross-platform tasarlanir.
- Varsayilan tarih formati: `YYYY-MM-DD`
- Varsayilan islem modu: `move`
- Varsayilan tarih kaynagi: Windows'ta `creation_time`
- Varsayilan cakişma politikasi: `auto_rename`
- Faz 1'de `main.py` korunur, gecis riski azaltilir.
