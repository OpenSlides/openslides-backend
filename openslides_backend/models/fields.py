import re
from enum import Enum
from typing import Any, Dict, List, Optional, Union

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
from ..shared.util import (
    ALLOWED_HTML_TAGS_PERMISSIVE,
    ALLOWED_HTML_TAGS_STRICT,
    validate_html,
)


class OnDelete(Enum):
    PROTECT = "PROTECT"
    CASCADE = "CASCADE"
    SET_NULL = "SET_NULL"


class Field:
    """
    Base class for model fields. Subclasses extend the schema.
    """

    # set by the using model
    own_collection: Collection
    own_field_name: str

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

    def validate(self, html: str) -> str:
        return validate_html(html, self.get_allowed_tags())

    def get_allowed_tags(self) -> List[str]:
        return ALLOWED_HTML_TAGS_STRICT


class HTMLPermissiveField(HTMLStrictField):
    """
    HTML field which can also contain video tags.
    """

    def get_allowed_tags(self) -> List[str]:
        return ALLOWED_HTML_TAGS_PERMISSIVE


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
    is_list_field: bool

    def __init__(
        self,
        to: Dict[Collection, str],
        on_delete: OnDelete = OnDelete.SET_NULL,
        equal_fields: Union[str, List[str]] = [],
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.to = to
        self.on_delete = on_delete
        if isinstance(equal_fields, list):
            self.equal_fields = equal_fields
        else:
            self.equal_fields = [equal_fields]

    def get_target_collection(self) -> Collection:
        """
        Should only be used for non-generic relations to fetch the single target collection.
        Returns the first collection of the relation.
        """
        return next(iter(self.to.keys()))

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}(to={self.to}, is_list_field={self.is_list_field}, "
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

    replacement: Optional[str]
    index: int

    def __init__(self, **kwargs: Any) -> None:
        self.replacement = kwargs.pop("replacement", None)
        self.index = kwargs.pop("index")
        super().__init__(**kwargs)

    def get_regex(self) -> str:
        """ For internal usage. To find the replacement, please use [try_]get_replacement """
        return (
            r"^"
            + self.own_field_name[: self.index]
            + r"\$"
            + r"([a-zA-Z0-9_\-]*)"
            + self.own_field_name[self.index :]
            + r"$"
        )

    def get_replacement(self, field_name: str) -> str:
        replacement = self.try_get_replacement(field_name)
        if not replacement:
            raise ValueError(
                f"{field_name} does not contain a valid replacement for a structured field."
            )
        return replacement

    def try_get_replacement(self, field_name: str) -> Optional[str]:
        match = re.match(self.get_regex(), field_name)
        if not match:
            return None
        else:
            replacement = match.group(1)
            if not replacement:
                raise ValueError(
                    "You try to get the replacement of a template field: " + field_name
                )
            if self.replacement and not replacement.isnumeric():
                raise ValueError(
                    f"Replacements for Structured Relation Fields must be ids. Invalid replacement: {replacement}"
                )
            if replacement.startswith("_"):
                raise ValueError(f"Replacements must not start with '_': {field_name}")
            return replacement


class BaseTemplateRelationField(BaseTemplateField, BaseRelationField):
    pass


class TemplateRelationField(BaseTemplateRelationField, RelationField):
    pass


class TemplateRelationListField(BaseTemplateRelationField, RelationListField):
    pass


class TemplateHTMLStrictField(BaseTemplateField, HTMLStrictField):
    pass
