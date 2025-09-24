from typing import Any

import bleach
import simplejson as json
from bleach.css_sanitizer import CSSSanitizer

from .patterns import fqid_from_collection_and_id

ALLOWED_HTML_TAGS_STRICT = {
    # links and images
    "a",
    "img",
    # text layout
    "br",
    "p",
    "span",
    "blockquote",
    # text formating
    "mark",
    "strike",
    "s",
    "del",
    "ins",
    "strong",
    "u",
    "em",
    "sup",
    "sub",
    "pre",
    # headings
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    # lists
    "ol",
    "ul",
    "li",
    # tables
    "table",
    "caption",
    "colgroup",
    "col",
    "thead",
    "tbody",
    "th",
    "tr",
    "td",
    "div",
}

ALLOWED_HTML_TAGS_PERMISSIVE = ALLOWED_HTML_TAGS_STRICT | {"video", "iframe"}

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

ALLOWED_ATTRIBUTES_ALL = {
    "abbr",
    "accept",
    "accept-charset",
    "accesskey",
    "action",
    "align",
    "alt",
    "axis",
    "border",
    "cellpadding",
    "cellspacing",
    "char",
    "charoff",
    "charset",
    "checked",
    "clear",
    "color",
    "cols",
    "colspan",
    "colwidth",
    "compact",
    "coords",
    "datetime",
    "dir",
    "disabled",
    "enctype",
    "for",
    "frame",
    "headers",
    "height",
    "hreflang",
    "hspace",
    "id",
    "ismap",
    "itemprop",
    "label",
    "lang",
    "maxlength",
    "media",
    "method",
    "multiple",
    "name",
    "nohref",
    "noshade",
    "nowrap",
    "open",
    "prompt",
    "readonly",
    "rev",
    "rows",
    "rowspan",
    "rules",
    "scope",
    "selected",
    "shape",
    "size",
    "span",
    "start",
    "style",
    "summary",
    "tabindex",
    "title",
    "type",
    "usemap",
    "valign",
    "value",
    "vspace",
    "width",
}

ALLOWED_ATTRIBUTES = {
    "a": ["href", "target", "rel"],
    "blockquote": ["cite"],
    "img": ["longdesc", "src"],
    "div": ["itemscope", "itemtype"],
    "iframe": ["src", "frameborder"],
    "video": ["autoplay", "controls", "loop", "muted", "poster", "preload", "src"],
}

INITIAL_DATA_FILE = "data/initial-data.json"
EXAMPLE_DATA_FILE = "data/example-data.json"
ONE_ORGANIZATION_ID = 1
ONE_ORGANIZATION_FQID = fqid_from_collection_and_id("organization", ONE_ORGANIZATION_ID)


def validate_html(
    html: str,
    allowed_tags: set[str] = ALLOWED_HTML_TAGS_STRICT,
    allowed_styles: list[str] = ALLOWED_STYLES,
) -> str:
    def check_attr_allowed(tag: str, name: str, value: str) -> bool:
        if name.startswith("data-"):
            return True
        if name in ALLOWED_ATTRIBUTES_ALL:
            return True
        if tag in ALLOWED_ATTRIBUTES and name in ALLOWED_ATTRIBUTES[tag]:
            return True

        return False

    html = html.replace("\t", "")
    cleaned_html = bleach.clean(
        html,
        tags=allowed_tags,
        attributes=check_attr_allowed,
        css_sanitizer=CSSSanitizer(allowed_css_properties=allowed_styles),
    )
    return cleaned_html.replace(
        "<iframe",
        '<iframe sandbox="allow-scripts allow-same-origin" referrerpolicy="no-referrer"',
    )


def get_initial_data_file(file: str) -> dict[str, Any]:
    with open(file) as fileh:
        return json.load(fileh)
