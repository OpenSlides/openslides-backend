import gettext
import pathlib
from typing import List, Optional

DEFAULT_LANGUAGE = "en_US"
DOMAIN = "messages"


class _Translator:
    def __init__(self) -> None:
        self.set_translation_language(DEFAULT_LANGUAGE)

    def translate(self, msg: str) -> str:
        return self.translation.gettext(msg)

    def set_translation_language(self, lang_header: Optional[str]) -> None:
        if lang_header is None:
            langs = [DEFAULT_LANGUAGE]
        else:
            langs = self.parse_language_header(lang_header)
            if DEFAULT_LANGUAGE not in langs:
                langs.append(DEFAULT_LANGUAGE)
        self.translation = gettext.translation(
            DOMAIN, pathlib.Path(__file__).parent.resolve(), langs
        )

    def parse_language_header(self, lang_header: str) -> List[str]:
        languages = lang_header.split(",")
        result = []
        for language in languages:
            parts = language.split(";")
            result.append(parts[0].strip())
        return result


Translator = _Translator()
translate = Translator.translate
