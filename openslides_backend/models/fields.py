from enum import Enum
from typing import Any, Dict, List, Union

import bleach

from ..shared.patterns import Collection, string_to_fqid
from ..shared.schema import (
    fqid_list_schema,
    id_list_schema,
    optional_fqid_schema,
    optional_id_schema,
    required_fqid_schema,
    required_id_schema,
)
from ..shared.typing import Schema


class OnDelete(Enum):
    PROTECT = "PROTECT"
    CASCADE = "CASCADE"
    SET_NULL = "SET_NULL"


class Field:
    """
    Base class for model fields. Subclasses extend the schema.
    """

    def __init__(
        self,
        required: bool = False,
        read_only: bool = False,
        default: Any = None,
        constraints: Dict[str, Any] = None,
    ) -> None:
        self.required = required
        self.read_only = read_only  # TODO: Use this flag in generic and custom actions.
        self.default = default
        self.constraints = constraints or {}

    def get_schema(self) -> Schema:
        """
        Returns a JSON schema for this field.
        """
        return dict(**self.constraints)

    def extend_schema(self, schema: Schema, **kwargs: Any) -> Schema:
        """
        Use in subclasses to extend the schema of the the super class.
        """
        schema.update(kwargs)
        return schema

    def validate(self, value: Any) -> Any:
        """
        Overwrite in subclass to validate/sanitize the input.
        """
        return value


class IntegerField(Field):
    def get_schema(self) -> Schema:
        if self.required:
            return self.extend_schema(super().get_schema(), type="integer")
        return self.extend_schema(super().get_schema(), type=["integer", "null"])


class BooleanField(Field):
    def get_schema(self) -> Schema:
        if self.required:
            return self.extend_schema(super().get_schema(), type="boolean")
        return self.extend_schema(super().get_schema(), type=["boolean", "null"])


class TextField(Field):
    def get_schema(self) -> Schema:
        schema = self.extend_schema(super().get_schema(), type="string")
        if self.required:
            schema = self.extend_schema(schema, minLength=1)
        return schema


class CharField(TextField):
    def get_schema(self) -> Schema:
        return self.extend_schema(super().get_schema(), maxLength=256)


class JSONField(TextField):
    pass


class HTMLStrictField(TextField):
    """
    Field for restricted HTML.
    """

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

    def validate(self, html: str) -> str:
        def allow_all(tag: str, name: str, value: str) -> bool:
            return True

        html = html.replace("\t", "")
        return bleach.clean(
            html,
            tags=self.get_allowed_tags(),
            attributes=allow_all,
            styles=self.ALLOWED_STYLES,
        )

    def get_allowed_tags(self) -> List[str]:
        return self.ALLOWED_HTML_TAGS_STRICT


class HTMLPermissiveField(HTMLStrictField):
    """
    HTML field which can also contain video tags.
    """

    ALLOWED_HTML_TAGS_PERMISSIVE = ["video"]

    def get_allowed_tags(self) -> List[str]:
        return super().get_allowed_tags() + self.ALLOWED_HTML_TAGS_PERMISSIVE


class FloatField(Field):
    def get_schema(self) -> Schema:
        raise NotImplementedError


class DecimalField(Field):
    """
    Represents a decimal number with fixed precision. Currently always decimal(6), has
    to be changed if other precisions are needed. Given as string since precision is of
    utmost importance.
    """

    def get_schema(self) -> Schema:
        return self.extend_schema(
            super().get_schema(), type="string", pattern=r"^-?(\d|[1-9]\d+)\.\d{6}$"
        )


class TimestampField(IntegerField):
    """
    Used to represent a UNIX timestamp.
    """

    pass


class ArrayField(Field):
    """
    Used for arbitrary arrays.
    """

    def __init__(self, in_array_constraints: Dict = None, **kwargs: Any) -> None:
        if "default" not in kwargs:
            kwargs["default"] = []
        super().__init__(**kwargs)
        self.in_array_constraints = in_array_constraints

    def get_schema(self) -> Schema:
        return self.extend_schema(super().get_schema(), type="array", default=[])


class CharArrayField(ArrayField):
    def get_schema(self) -> Schema:
        items = dict(type="string", maxLength=256)
        if self.in_array_constraints is not None:
            items.update(self.in_array_constraints)
        return self.extend_schema(super().get_schema(), items=items)


class NumberArrayField(ArrayField):
    def get_schema(self) -> Schema:
        items = dict(type="integer")
        if self.in_array_constraints is not None:
            items.update(self.in_array_constraints)
        return self.extend_schema(super().get_schema(), items=items)


class BaseRelationField(Field):
    own_collection: Collection
    own_field_name: str
    is_list_field: bool

    def __init__(
        self,
        to: Union[Collection, List[Collection]],
        related_name: str,
        structured_relation: List[str] = None,
        structured_tag: str = None,
        generic_relation: bool = False,
        on_delete: OnDelete = OnDelete.SET_NULL,
        equal_fields: Union[str, List[str]] = [],
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        if structured_relation is not None or structured_tag is not None:
            assert not (structured_relation is not None and structured_tag is not None)
            assert structured_relation != []
            if "$" not in related_name:
                raise ValueError(
                    "Setting structured_relation or structured_tag requires a $ in related_name."
                )
        else:
            if "$" in related_name:
                raise ValueError(
                    "A $ in related name requires setting structured_relation or structured_tag."
                )
        self.to = to
        self.related_name = related_name
        self.structured_relation = structured_relation
        self.structured_tag = structured_tag
        self.generic_relation = generic_relation
        self.on_delete = on_delete
        if isinstance(equal_fields, list):
            self.equal_fields = equal_fields
        else:
            self.equal_fields = [equal_fields]

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}(to={self.to}, related_name={self.related_name}, "
            f"structured_relation={self.structured_relation}, structured_tag={self.structured_tag}, "
            f"generic_relation={self.generic_relation}, is_list_field={self.is_list_field}, "
            f"on_delete={self.on_delete}, required={self.required}, "
            f"constraints={self.constraints}, equal_fields={self.equal_fields})"
        )


class RelationField(BaseRelationField):
    is_list_field = False

    def get_schema(self) -> Schema:
        if self.required:
            schema = required_id_schema
        else:
            schema = optional_id_schema
        return self.extend_schema(super().get_schema(), **schema)


class RelationListField(BaseRelationField):
    is_list_field = True

    def get_schema(self) -> Schema:
        return self.extend_schema(super().get_schema(), **id_list_schema)


class BaseGenericRelationField(BaseRelationField):
    pass


class GenericRelationField(BaseGenericRelationField):
    is_list_field = False

    def get_schema(self) -> Schema:
        if self.required:
            schema = required_fqid_schema
        else:
            schema = optional_fqid_schema
        return self.extend_schema(super().get_schema(), **schema)

    def validate(self, value: Any) -> Any:
        assert not isinstance(value, list)
        return string_to_fqid(value)


class GenericRelationListField(BaseGenericRelationField):
    is_list_field = True

    def get_schema(self) -> Schema:
        return self.extend_schema(super().get_schema(), **fqid_list_schema)

    def validate(self, value: Any) -> Any:
        assert isinstance(value, list)
        return [string_to_fqid(fqid) for fqid in value]


class OrganisationField(RelationField):
    """
    Special field for foreign key to organisation model. We support only one
    organisation (with id 1) at the moment.
    """

    def get_schema(self) -> Schema:
        return self.extend_schema(super().get_schema(), enum=[1])


class BaseTemplateField(Field):
    def __init__(self, **kwargs: Any) -> None:
        self.replacement = kwargs.pop("replacement")
        self.index = kwargs.pop("index")
        super().__init__(**kwargs)


class BaseTemplateRelationField(BaseTemplateField, BaseRelationField):
    pass


class TemplateRelationField(BaseTemplateRelationField, RelationField):
    pass


class TemplateRelationListField(BaseTemplateRelationField, RelationListField):
    pass


class TemplateHTMLStrictField(BaseTemplateField, HTMLStrictField):
    pass
