from app.services.language import LanguageService


def test_detects_english_text_and_requires_translation() -> None:
    service = LanguageService()

    detected_language = service.detect_language("OpenAI released a new model update for developers.")

    assert detected_language == "en"
    assert service.needs_translation(detected_language) is True


def test_detects_chinese_text_without_translation() -> None:
    service = LanguageService()

    detected_language = service.detect_language("今天论坛里讨论了很多关于模型推理和产品节奏的话题。")

    assert detected_language == "zh"
    assert service.needs_translation(detected_language) is False

