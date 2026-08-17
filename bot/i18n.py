import json
import os
from pathlib import Path

LOCALES_DIR = Path(__file__).parent.parent / "locales"


class I18n:
    def __init__(self):
        self.locales = {}
        self.load_locales()

    def load_locales(self):
        for lang in ["uz", "ru"]:
            file_path = LOCALES_DIR / f"{lang}.json"
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    self.locales[lang] = json.load(f)
            else:
                self.locales[lang] = {}

    def get(self, key: str, lang: str = "uz", **kwargs) -> str:
        text = self.locales.get(lang, {}).get(
            key, self.locales.get("uz", {}).get(key, key)
        )
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass
        return text


i18n = I18n()
