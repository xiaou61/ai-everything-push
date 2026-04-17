from __future__ import annotations

from deep_translator import GoogleTranslator
import httpx

from app.core.config import Settings, get_settings


class TranslationService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def translate_to_chinese(self, text: str, source_language: str) -> str:
        if not text.strip() or not source_language.startswith("en"):
            return text

        translated = self._translate_with_openai(text)
        if translated:
            return translated

        try:
            return GoogleTranslator(source="en", target="zh-CN").translate(text[:3000])
        except Exception:
            return text

    def _translate_with_openai(self, text: str) -> str | None:
        if not self.settings.openai_api_key or not self.settings.openai_model:
            return None

        try:
            response = httpx.post(
                f"{self.settings.openai_base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.settings.openai_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "请把英文内容翻译成简体中文，保留专有名词、产品名和链接语义，直接输出译文。",
                        },
                        {
                            "role": "user",
                            "content": text[:3000],
                        },
                    ],
                    "temperature": 0.2,
                },
                timeout=self.settings.request_timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
            return content.strip()
        except Exception:
            return None

