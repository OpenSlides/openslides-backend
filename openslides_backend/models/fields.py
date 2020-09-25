from typing import Any, Dict, List, Union

from ..shared.patterns import Collection, FullQualifiedId

Schema = Dict[str, Any]


class Field:
    """
    Base class for model fields. Subclasses extend the schema.
    """

    def __init__(
        self,
        required: bool = False,
        read_only: bool = False,
        constraints: Dict[str, Any] = None,
    ) -> None:
        self.required = required
        self.read_only = read_only  # TODO: Use this flag in generic and custom actions.
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


class HTMLField(TextField):
    pass


class FloatField(Field):
    def get_schema(self) -> Schema:
        raise NotImplementedError


class DecimalField(Field):
    def get_schema(self) -> Schema:
        raise NotImplementedError


class DatetimeField(IntegerField):
    """
    Used to represent a UNIX timestamp.
    """

    pass


class ArrayField(Field):
    """
    Used for arbitrary arrays.
    """

    def __init__(self, in_array_constraints: Dict = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.in_array_constraints = in_array_constraints

    def get_schema(self) -> Schema:
        return self.extend_schema(super().get_schema(), type="array")


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
        delete_protection: bool = False,
        # constraints: Dict[str, Any] = None,
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
        self.delete_protection = delete_protection

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}(to={self.to}, related_name={self.related_name}, "
            f"structured_relation={self.structured_relation}, structured_tag={self.structured_tag}, "
            f"generic_relation={self.generic_relation}, is_list_field={self.is_list_field}, "
            f"delete_protection={self.delete_protection}, required={self.required}, "
            f"constraints={self.constraints})"
        )

    def on_delete(self) -> str:
        # TODO: Enable cascade
        if self.required:
            return "protect"
        return "set_null"


class RelationField(BaseRelationField):
    is_list_field = False

    def get_schema(self) -> Schema:
        if self.required:
            return self.extend_schema(super().get_schema(), type="integer", mininum=1)
        return self.extend_schema(super().get_schema(), type=["integer", "null"])


class RelationListField(BaseRelationField):
    is_list_field = True

    def get_schema(self) -> Schema:
        return self.extend_schema(
            super().get_schema(),
            type="array",
            items={"type": "integer", "minimum": 1},
            uniqueItems=True,
        )


class GenericRelationField(BaseRelationField):
    is_list_field = False

    def get_schema(self) -> Schema:
        schema = self.extend_schema(
            super().get_schema(), type="string", pattern=FullQualifiedId.REGEX
        )
        if self.required:
            schema = self.extend_schema(schema, minLength=1)
        return schema


class GenericRelationListField(BaseRelationField):
    is_list_field = True

    def get_schema(self) -> Schema:
        return self.extend_schema(
            super().get_schema(),
            type="array",
            items={"type": "string", "pattern": FullQualifiedId.REGEX},
            uniqueItems=True,
        )


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


class TemplateRelationField(BaseTemplateField, RelationField):
    pass


class TemplateRelationListField(BaseTemplateField, RelationListField):
    pass


class TemplateHTMLField(BaseTemplateField, HTMLField):
    pass
