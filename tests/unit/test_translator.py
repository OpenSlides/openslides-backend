from unittest import TestCase

from babel import Locale
from babel.messages.catalog import Catalog
from babel.messages.pofile import PoFileParser

from openslides_backend.i18n.translator import _Translator


class TranslatorTest(TestCase):
    def setUp(self) -> None:
        catalog = Catalog(
            locale=Locale("de"), last_translator="Bob", charset="utf-8", fuzzy=False
        )
        parser = PoFileParser(catalog)
        parser.parse(
            [
                'msgid "a"',
                'msgstr "b"',
                "",
                'msgid "c"',
                'msgstr "d"',
                "",
                'msgid "e"',
                'msgstr ""',
            ]
        )
        self.translator = _Translator({"de": catalog})

    def test_translate_wrong_language(self) -> None:
        assert self.translator.translate("c") == "c"

    def test_translate_normal(self) -> None:
        self.translator.set_translation_language("de")
        assert self.translator.translate("a") == "b"

    def test_translate_unknown_phrase(self) -> None:
        self.translator.set_translation_language("de")
        assert (
            self.translator.translate("abcdefghijklmnopqrstuvwxyz")
            == "abcdefghijklmnopqrstuvwxyz"
        )

    def test_translate_untranslated(self) -> None:
        self.translator.set_translation_language("de")
        assert self.translator.translate("e") == "e"

    def test_translate_order_sorted_header_non_alphabetical(self) -> None:
        self.translator.set_translation_language("en,de")
        assert self.translator.translate("c") == "c"

    def test_translate_order_sorted_header_alphabetical(self) -> None:
        self.translator.set_translation_language("de,en")
        assert self.translator.translate("c") == "d"

    def test_translate_weight_sorted_header_asc(self) -> None:
        self.translator.set_translation_language("en;q=0.5,de;q=0.8")
        assert self.translator.translate("c") == "c"

    def test_translate_weight_sorted_header_desc(self) -> None:
        self.translator.set_translation_language("en;q=0.8,de;q=0.5")
        assert self.translator.translate("c") == "d"

    def test_translate_half_weight_sorted_header_asc(self) -> None:
        self.translator.set_translation_language("en;q=0.5,de")
        assert self.translator.translate("c") == "c"

    def test_translate_half_weight_sorted_header_desc(self) -> None:
        self.translator.set_translation_language("en,de;q=0.5")
        assert self.translator.translate("c") == "d"
