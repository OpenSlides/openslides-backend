import re
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union, cast

from ..shared.patterns import COLOR_PATTERN, ID_REGEX, Collection, string_to_fqid
from ..shared.schema import (
    decimal_schema,
    fqid_list_schema,
    id_list_schema,
    optional_fqid_schema,
    optional_id_schema,
    optional_str_list_schema,
    optional_str_schema,
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
        self.read_only = read_only
        self.default = default
        if not self.required and constraints and "enum" in constraints:
            constraints["enum"].append(None)
        self.constraints = constraints or {}

    def get_schema(self) -> Schema:
        """
        Returns a JSON schema for this field.
        """
        return dict(**self.constraints)

    def get_payload_schema(self, *args: Any, **kwargs: Any) -> Schema:
        """Calls get_schema by default."""
        return self.get_schema()

    def extend_schema(self, schema: Schema, **kwargs: Any) -> Schema:
        """
        Use in subclasses to extend the schema of the the super class.
        """
        schema.update(kwargs)
        return schema

    def validate(self, value: Any, payload: Dict[str, Any] = {}) -> Any:
        """
        Overwrite in subclass to validate/sanitize the input.
        """
        return value

    def check_required_not_fulfilled(
        self, instance: Dict[str, Any], is_create: bool
    ) -> bool:
        if self.own_field_name not in instance:
            return is_create
        return not instance[self.own_field_name]

    def get_own_field_name(self) -> str:
        return self.own_field_name


class IntegerField(Field):
    def get_schema(self) -> Schema:
        if self.required:
            return self.extend_schema(super().get_schema(), type="integer")
        return self.extend_schema(super().get_schema(), type=["integer", "null"])

    def check_required_not_fulfilled(
        self, instance: Dict[str, Any], is_create: bool
    ) -> bool:
        if self.own_field_name not in instance:
            return is_create
        return instance[self.own_field_name] is None


class BooleanField(Field):
    def get_schema(self) -> Schema:
        if self.required:
            return self.extend_schema(super().get_schema(), type="boolean")
        return self.extend_schema(super().get_schema(), type=["boolean", "null"])

    def check_required_not_fulfilled(
        self, instance: Dict[str, Any], is_create: bool
    ) -> bool:
        if self.own_field_name not in instance:
            return is_create
        return instance[self.own_field_name] is None


class TextField(Field):
    def get_schema(self) -> Schema:
        if self.required:
            return self.extend_schema(super().get_schema(), type="string", minLength=1)
        return self.extend_schema(super().get_schema(), type=["string", "null"])


class CharField(TextField):
    def get_schema(self) -> Schema:
        return self.extend_schema(super().get_schema(), maxLength=256)


class JSONField(Field):
    def get_schema(self) -> Schema:
        types = ["object", "array"]
        if not self.required:
            types.append("null")
        return self.extend_schema(super().get_schema(), type=types)


class HTMLStrictField(TextField):
    """
    Field for restricted HTML.
    """

    def validate(
        self, html: Optional[str], payload: Dict[str, Any] = {}
    ) -> Optional[str]:
        if html is not None:
            return validate_html(html, self.get_allowed_tags())
        return None

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
        if self.required:
            return self.extend_schema(super().get_schema(), type="number")
        return self.extend_schema(super().get_schema(), type=["number", "null"])

    def check_required_not_fulfilled(
        self, instance: Dict[str, Any], is_create: bool
    ) -> bool:
        if self.own_field_name not in instance:
            return is_create
        return instance[self.own_field_name] is None


class DecimalField(Field):
    """
    Represents a decimal number with fixed precision. Currently always decimal(6), has
    to be changed if other precisions are needed. Given as string since precision is of
    utmost importance.
    """

    def get_schema(self) -> Schema:
        schema = self.extend_schema(super().get_schema(), **decimal_schema)
        if not self.required:
            schema["type"] = ["string", "null"]
        return schema

    def validate(self, value: Any, payload: Dict[str, Any] = {}) -> Any:
        if (min := self.constraints.get("minimum")) is not None:
            if type(value) == str:
                assert Decimal(value) >= Decimal(
                    min
                ), f"{self.own_field_name} must be bigger than or equal to {min}."
            else:
                raise NotImplementedError()
        return value


class TimestampField(IntegerField):
    """
    Used to represent a UNIX timestamp.
    """


class ColorField(TextField):
    def get_schema(self) -> Schema:
        return self.extend_schema(super().get_schema(), pattern=COLOR_PATTERN)


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
        if self.required:
            return self.extend_schema(super().get_schema(), type="array", default=[])
        return self.extend_schema(super().get_schema(), type=["array", "null"])


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

    def validate(self, value: Any, payload: Dict[str, Any] = {}) -> Any:
        assert not isinstance(value, list)
        if value:
            return string_to_fqid(value)
        return value


class GenericRelationListField(BaseGenericRelationField):
    is_list_field = True

    def get_schema(self) -> Schema:
        return self.extend_schema(super().get_schema(), **fqid_list_schema)

    def validate(self, value: Any, payload: Dict[str, Any] = {}) -> Any:
        if value is not None or self.required:
            assert isinstance(value, list), "assert list-failure"
            return [string_to_fqid(fqid) for fqid in value]
        return value


class OrganizationField(RelationField):
    """
    Special field for foreign key to organization model. We support only one
    organization (with id 1) at the moment.
    """

    def get_schema(self) -> Schema:
        return self.extend_schema(super().get_schema(), enum=[1])


class BaseTemplateField(Field):

    replacement_collection: Optional[Collection]
    replacement_enum: Optional[List[str]]
    index: int

    def __init__(self, **kwargs: Any) -> None:
        self.replacement_collection = kwargs.pop("replacement_collection", None)
        self.replacement_enum = kwargs.pop("replacement_enum", None)
        self.index = kwargs.pop("index")
        super().__init__(**kwargs)

    def get_own_field_name(self) -> str:
        return self.get_template_field_name()

    def get_payload_schema(
        self, replacement_pattern: Optional[str] = None, *args: Any, **kwargs: Any
    ) -> Schema:
        schema = {
            "type": "object",
            "additionalProperties": False,
        }

        if self.replacement_enum:
            subschema: Schema = self.get_schema()
            schema.update(
                {"properties": {name: subschema for name in self.replacement_enum}}
            )
        else:
            if not replacement_pattern:
                if self.replacement_collection:
                    replacement_pattern = ID_REGEX
                else:
                    replacement_pattern = ".*"
            schema.update(
                {"patternProperties": {replacement_pattern: self.get_schema()}}
            )
        return schema

    def get_regex(self) -> str:
        """
        For internal usage. To find the replacement, please use [try_]get_replacement.
        """
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

    def get_template_field_name(self) -> str:
        return self.get_structured_field_name("")

    def get_structured_field_name(self, replacement: Any) -> str:
        return (
            self.own_field_name[: self.index]
            + "$"
            + str(replacement)
            + self.own_field_name[self.index :]
        )

    def is_template_field(self, field_name: str) -> bool:
        return field_name == self.get_template_field_name()

    def try_get_replacement(self, field_name: str) -> Optional[str]:
        match = re.match(self.get_regex(), field_name)
        if not match:
            return None
        replacement = match.group(1)
        if not replacement:
            raise ValueError(
                "You try to get the replacement of a template field: " + field_name
            )
        if self.replacement_collection and not replacement.isnumeric():
            raise ValueError(
                f"Replacements for Structured Relation Fields must be ids. Invalid replacement: {replacement}"
            )
        if replacement.startswith("_"):
            raise ValueError(f"Replacements must not start with '_': {field_name}")
        return replacement


class BaseTemplateRelationField(BaseTemplateField, BaseRelationField):
    def check_required_not_fulfilled(
        self, instance: Dict[str, Any], is_create: bool
    ) -> bool:
        own_field_name = self.get_own_field_name()
        assert hasattr(
            self, "replacement_enum"
        ), f"field {own_field_name} required is only implemented with replacement_enum"
        if own_field_name not in instance:
            return is_create
        if is_create and set(instance.get(own_field_name, ())) != set(
            cast(List[str], self.replacement_enum)
        ):
            return True
        parts = own_field_name.split("$")
        template = parts[0] + "$%s" + parts[1]
        return any(
            # Check every structure field and return True (=Error) if any structure field is empty.
            # If structure-field doesn't exist, it will not try to set anything empty and return True.
            not instance.get(template % replace_text, True)
            for replace_text in instance[own_field_name]
        )


class TemplateRelationField(BaseTemplateRelationField, RelationField):
    def get_schema(self) -> Schema:
        if self.constraints and self.constraints.get("enum"):
            return self.extend_schema(super().get_schema(), **optional_str_schema)
        else:
            id_schema = required_id_schema if self.required else optional_id_schema
            return self.extend_schema(super().get_schema(), **id_schema)


class TemplateRelationListField(BaseTemplateRelationField, RelationListField):
    def get_schema(self) -> Schema:
        schema = super().get_schema()
        if self.constraints:
            for key in self.constraints.keys():
                del schema[key]
        if self.constraints and self.constraints.get("enum"):
            schema = self.extend_schema(schema, **optional_str_list_schema)
        else:
            schema = self.extend_schema(schema, **id_list_schema)
        if self.constraints:
            schema["items"].update(self.constraints)
        if not hasattr(self, "required") or not self.required:
            schema["type"] = ["array", "null"]
        return schema


class TemplateCharField(BaseTemplateField, CharField):
    pass


class TemplateDecimalField(BaseTemplateField, DecimalField):
    def validate(self, value: Any, payload: Dict[str, Any] = {}) -> Any:
        if (min := self.constraints.get("minimum")) is not None:
            if type(value) == dict:
                assert all(
                    (Decimal(v) >= Decimal(min))
                    for v in value.values()
                    if v is not None
                ), f"{self.get_own_field_name()} must be bigger than or equal to {min}."
            elif type(value) == list:
                assert all(
                    (
                        Decimal(
                            cast(
                                Union[Decimal, float, str],
                                payload.get(
                                    self.get_structured_field_name(replacement)
                                ),
                            )
                        )
                        >= Decimal(min)
                    )
                    for replacement in value
                ), f"{self.get_own_field_name()} must be bigger than or equal to {min}."
            else:
                raise NotImplementedError()
        return value


class TemplateHTMLStrictField(BaseTemplateField, HTMLStrictField):
    def validate(self, value: Any, payload: Dict[str, Any] = {}) -> Any:
        if type(value) == dict:
            sup: Any = super()
            return {key: sup.validate(struc) for key, struc in value.items()}
        elif type(value) == list:
            return value
        elif value is None:
            return None
        raise NotImplementedError()
