from typing import Any, List

import bleach
import simplejson as json

ALLOWED_HTML_TAGS_STRICT = [
    "a",
    "img",  # links and images
    "br",
    "p",
    "span",
    "blockquote",  # text layout
    "strike",
    "del",
    "ins",
    "strong",
    "u",
    "em",
    "sup",
    "sub",
    "pre",  # text formating
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",  # headings
    "ol",
    "ul",
    "li",  # lists
    "table",
    "caption",
    "thead",
    "tbody",
    "th",
    "tr",
    "td",  # tables
    "div",
]

ALLOWED_HTML_TAGS_PERMISSIVE = ALLOWED_HTML_TAGS_STRICT + ["video"]

ALLOWED_STYLES = [
    "color",
    "background-color",
    "height",
    "width",
    "text-align",
    "vertical-align",
    "float",
    "text-decoration",
    "margin",
    "padding",
    "line-height",
    "max-width",
    "min-width",
    "max-height",
    "min-height",
    "overflow",
    "word-break",
    "word-wrap",
]

INITIAL_DATA_FILE = "global/data/initial-data.json"
EXAMPLE_DATA_FILE = "global/data/example-data.json"
ONE_ORGANIZATION_ID = 1
ONE_ORGANIZATION_FQID = "organization/1"


def validate_html(
    html: str,
    allowed_tags: List[str] = ALLOWED_HTML_TAGS_STRICT,
    allowed_styles: List[str] = ALLOWED_STYLES,
) -> str:
    def allow_all(tag: str, name: str, value: str) -> bool:
        return True

    html = html.replace("\t", "")
    return bleach.clean(
        html,
        tags=allowed_tags,
        attributes=allow_all,
        styles=allowed_styles,
    )


def get_initial_data_file(file: str) -> Any:
    with open(file) as fileh:
        return json.load(fileh)
