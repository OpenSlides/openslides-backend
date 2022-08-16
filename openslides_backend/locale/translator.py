import gettext
from typing import Callable, Optional

DEFAULT_LANGUAGE = "en_US"
PATH_TO_LOCALE = "/app/openslides_backend/locale"
DOMAIN = "messages"


class TranslatorSingleton:
    def __init__(self) -> None:
        self.language = DEFAULT_LANGUAGE

    def get_translate_function(self) -> Callable[[str], str]:
        t = gettext.translation(DOMAIN, PATH_TO_LOCALE, [self.language])
        if not t:

            def null_translate(msg: str) -> str:
                return msg

            return null_translate
        return t.gettext

    def set_translation_language(self, lang: Optional[str]) -> None:
        if lang is None:
            self.language = DEFAULT_LANGUAGE
        else:
            self.language = lang


Translator = TranslatorSingleton()
