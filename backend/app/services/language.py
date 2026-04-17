from __future__ import annotations

import re

from langdetect import DetectorFactory, LangDetectException, detect


DetectorFactory.seed = 0
CHINESE_PATTERN = re.compile(r"[\u4e00-\u9fff]")


class LanguageService:
    def detect_language(self, text: str) -> str:
        if not text.strip():
            return "unknown"
        if CHINESE_PATTERN.search(text):
            return "zh"

        try:
            detected = detect(text[:1200])
        except LangDetectException:
            return "unknown"

        if detected.startswith("zh"):
            return "zh"
        if detected.startswith("en"):
            return "en"
        return detected

    def needs_translation(self, language: str) -> bool:
        return language.startswith("en")

