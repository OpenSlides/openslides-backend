from typing import Any, Dict

from ....shared.patterns import ID_REGEX
from ....shared.util import validate_html

amendment_paragraphs_schema = {
    "type": "object",
    "patternProperties": {ID_REGEX: {"type": "string"}},
    "additionalProperties": False,
}


class AmendmentParagraphsMixin:
    def handle_amendment_paragraphs(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cleans and handles the amendment_paragraphs in this instance.
        Attention: modifies instance!
        """
        if instance.get("amendment_paragraphs"):
            amendment_paragraphs = instance.pop("amendment_paragraphs")
            for paragraph_number, text in amendment_paragraphs.items():
                instance[f"amendment_paragraph_${paragraph_number}"] = validate_html(
                    text
                )
        return instance
