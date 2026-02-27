from i18n import tr


def test_translation_returns_turkish_text() -> None:
    assert tr("tr", "analyze") == "Analiz Et"


def test_translation_returns_english_text() -> None:
    assert tr("en", "analyze") == "Analyze"


def test_translation_falls_back_to_english_for_unknown_language() -> None:
    assert tr("xx", "undo") == "Undo Last Operation"
