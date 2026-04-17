from __future__ import annotations


def detect_language(text: str) -> str:
    sample = (text or "").strip()
    if not sample:
        return "unknown"

    chinese_chars = sum(1 for char in sample if "\u4e00" <= char <= "\u9fff")
    alphabet_chars = sum(1 for char in sample if char.isascii() and char.isalpha())

    if chinese_chars >= max(8, len(sample) // 20):
        return "zh"
    if alphabet_chars >= max(20, len(sample) // 4):
        return "en"
    return "unknown"

