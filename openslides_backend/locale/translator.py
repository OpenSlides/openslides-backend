import gettext
from typing import Callable, Optional


class TranslatorSingleton:
    def __init__(self) -> None:
        self.language = "en_US"

    def get_translate_function(self) -> Callable[[str], str]:
        t = gettext.translation(
            "messages", "/app/openslides_backend/locale", [self.language]
        )
        if not t:

            def null_translate(msg: str) -> str:
                return msg

            return null_translate
        return t.gettext

    def set_translation_language(self, lang: Optional[str]) -> None:
        if lang is None:
            self.language = "en_US"
        else:
            self.language = lang


Translator = TranslatorSingleton()
