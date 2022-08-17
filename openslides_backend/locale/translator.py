import gettext
from typing import Optional

DEFAULT_LANGUAGE = "en_US"
PATH_TO_LOCALE = "/app/openslides_backend/locale"
DOMAIN = "messages"


class TranslatorSingleton:
    def __init__(self) -> None:
        self.language = DEFAULT_LANGUAGE

    def __call__(self, msg: str) -> str:
        if not self.translation:
            return msg

        return self.translation.gettext(msg)

    def set_translation_language(self, lang: Optional[str]) -> None:
        if lang is None:
            self.language = DEFAULT_LANGUAGE
        else:
            self.language = lang
        self.translation = gettext.translation(DOMAIN, PATH_TO_LOCALE, [self.language])


Translator = TranslatorSingleton()
