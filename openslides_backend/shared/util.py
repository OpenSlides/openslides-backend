from typing import List

import bleach

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
