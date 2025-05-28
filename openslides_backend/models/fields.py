from decimal import Decimal
from enum import StrEnum
from typing import Any, cast

import fastjsonschema

from openslides_backend.shared.exceptions import ActionException

from ..shared.patterns import COLOR_REGEX, Collection, FullQualifiedId
from ..shared.schema import (
    decimal_schema,
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

TRUE_VALUES = ("1", "true", "yes", "t", "y")
FALSE_VALUES = ("0", "false", "no", "f", "n")


class OnDelete(StrEnum):
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

    required: bool
    read_only: bool
    constant: bool
    default: str | None
    constraints: dict[str, Any]
    is_view_field: bool

    def __init__(
        self,
        required: bool = False,
        read_only: bool = False,
        constant: bool = False,
        default: Any | None = None,
        constraints: dict[str, Any] | None = None,
        is_view_field: bool = False,
        is_primary: bool = False,
        write_fields: tuple[str, str, str, list[str]] | None = None,
    ) -> None:
        self.required = required
        self.read_only = read_only
        self.constant = constant
        self.default = default
        if not self.required and constraints and "enum" in constraints:
            constraints["enum"].append(None)
        self.constraints = constraints or {}
        self.is_view_field = is_view_field
        self.is_primary = is_primary
        self.write_fields = write_fields
        self.schema_validator = fastjsonschema.compile(self.get_schema())

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

    def validate(self, value: Any, payload: dict[str, Any] = {}) -> Any:
        """
        Overwrite in subclass to validate/sanitize the input.
        """
        return value

    def validate_with_schema(
        self, fqid: FullQualifiedId, field_name: str, value: Any
    ) -> None:
        try:
            self.schema_validator(value)
        except fastjsonschema.JsonSchemaException as e:
            raise ActionException(f"Invalid data for {fqid}/{field_name}: " + e.message)

    def check_required_not_fulfilled(
        self, instance: dict[str, Any], is_create: bool
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
        self, instance: dict[str, Any], is_create: bool
    ) -> bool:
        if self.own_field_name not in instance:
            return is_create
        return instance[self.own_field_name] is None


class BooleanField(Field):
    """
    Allow boolean fields with sring and int, converted by validate method
    """

    def get_schema(self) -> Schema:
        if self.required:
            return self.extend_schema(
                super().get_schema(), type=["boolean", "string", "integer"]
            )
        return self.extend_schema(
            super().get_schema(), type=["boolean", "string", "integer", "null"]
        )

    def check_required_not_fulfilled(
        self, instance: dict[str, Any], is_create: bool
    ) -> bool:
        if self.own_field_name not in instance:
            return is_create
        return instance[self.own_field_name] is None

    def validate(self, value: Any, payload: dict[str, Any] = {}) -> Any:
        if isinstance(value, bool):
            return value
        elif isinstance(value, str):
            if value.lower() in TRUE_VALUES:
                return True
            elif value.lower() in FALSE_VALUES:
                return False
        elif isinstance(value, int) and value in (0, 1):
            return bool(value)
        elif value is None:
            return None
        raise ValueError(f"Could not parse {value}, expect boolean")


class TextField(Field):
    def get_schema(self) -> Schema:
        if self.required:
            return self.extend_schema(super().get_schema(), type="string", minLength=1)
        return self.extend_schema(super().get_schema(), type=["string", "null"])


class CharField(TextField):
    def get_schema(self) -> Schema:
        schema = super().get_schema()
        schema.setdefault("maxLength", 256)
        return schema


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

    def validate(self, html: str | None, payload: dict[str, Any] = {}) -> str | None:
        if html is not None:
            return validate_html(html, self.get_allowed_tags())
        return None

    def get_allowed_tags(self) -> set[str]:
        return ALLOWED_HTML_TAGS_STRICT


class HTMLPermissiveField(HTMLStrictField):
    """
    HTML field which can also contain video tags.
    """

    def get_allowed_tags(self) -> set[str]:
        return ALLOWED_HTML_TAGS_PERMISSIVE


class FloatField(Field):
    def get_schema(self) -> Schema:
        if self.required:
            return self.extend_schema(super().get_schema(), type="number")
        return self.extend_schema(super().get_schema(), type=["number", "null"])

    def check_required_not_fulfilled(
        self, instance: dict[str, Any], is_create: bool
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
        # remove minimum since it is checked in the validate method
        schema.pop("minimum", None)
        return schema

    def validate(self, value: Any, payload: dict[str, Any] = {}) -> Any:
        if value is not None or self.required:
            if (min := self.constraints.get("minimum")) is not None:
                if isinstance(value, str):
                    assert Decimal(value) >= Decimal(
                        min
                    ), f"{self.own_field_name} must be bigger than or equal to {min}."
                else:
                    raise NotImplementedError(
                        f"Unexpected type: {type(value)} (value: {value}) for field {self.get_own_field_name()}"
                    )
        return value


class TimestampField(IntegerField):
    """
    Used to represent a UNIX timestamp.
    """


class ColorField(TextField):
    def get_schema(self) -> Schema:
        return self.extend_schema(super().get_schema(), pattern=COLOR_REGEX)


class ArrayField(Field):
    """
    Used for arbitrary arrays.
    """

    def __init__(self, in_array_constraints: dict | None = None, **kwargs: Any) -> None:
        self.in_array_constraints = in_array_constraints
        super().__init__(**kwargs)

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
        to: dict[Collection, str],
        on_delete: OnDelete = OnDelete.SET_NULL,
        equal_fields: str | list[str] = [],
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
        schema = self.extend_schema(super().get_schema(), **id_list_schema)
        if not self.required:
            schema["type"] = ["array", "null"]
        return schema


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

    def validate(self, value: Any, payload: dict[str, Any] = {}) -> Any:
        assert not isinstance(value, list)
        return value


class GenericRelationListField(BaseGenericRelationField):
    is_list_field = True

    def get_schema(self) -> Schema:
        return self.extend_schema(super().get_schema(), **fqid_list_schema)

    def validate(self, value: Any, payload: dict[str, Any] = {}) -> Any:
        if value is not None or self.required:
            assert isinstance(value, list), "assert list-failure"
            return [cast(FullQualifiedId, fqid) for fqid in value]
        return value


class OrganizationField(RelationField):
    """
    Special field for foreign key to organization model. We support only one
    organization (with id 1) at the moment.
    """

    def get_schema(self) -> Schema:
        return self.extend_schema(super().get_schema(), enum=[1])
