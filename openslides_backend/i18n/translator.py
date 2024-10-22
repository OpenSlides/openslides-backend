from pathlib import Path

from babel.messages.catalog import Catalog
from babel.messages.pofile import read_po

DEFAULT_LANGUAGE = "en"


class _Translator:
    translations: dict[str, Catalog] = {}
    current_language: str

    def __init__(self) -> None:
        # read all po files at startup
        path = Path(__file__).parent / "messages"
        for file in path.glob("*.po"):
            with file.open("r") as f:
                self.translations[file.stem] = read_po(f)
        # empty catalog for en since it is not used anyway
        self.translations[DEFAULT_LANGUAGE] = Catalog()
        self.current_language = DEFAULT_LANGUAGE

    def translate(self, msg: str) -> str:
        translation = self.translations[self.current_language].get(msg)
        if translation:
            return translation.string
        else:
            return msg

    def set_translation_language(self, lang_header: str | None) -> None:
        langs = []
        if lang_header is not None:
            langs = self.parse_language_header(lang_header)
        for lang in langs:
            if lang in self.translations:
                self.current_language = lang
                break
        else:
            self.current_language = DEFAULT_LANGUAGE

    def parse_language_header(self, lang_header: str) -> list[str]:
        # each language is separated by a comma
        languages = lang_header.split(",")
        result = []
        for language in languages:
            # the language can be followed by a quality value
            parts = language.split(";")
            lang = parts[0]
            if len(parts) == 1:
                q = 1.0
            else:
                # quantity is given in the form of "q=*"
                q = float(parts[1].split("=")[1])
            # extract language code from string - may be suffixed by a region
            code = lang.split("_")[0]
            code = code.split("-")[0]
            result.append((q, code))
        # sort by quality value and return only the codes
        return [t[1] for t in result]


Translator = _Translator()
translate = Translator.translate
