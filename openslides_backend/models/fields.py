from collections import defaultdict
from typing import Any, Dict, List

from ..shared.patterns import Collection, FullQualifiedId

Schema = Dict[str, Any]


class Field:
    """
    Base class for model fields. Subclasses extend the schema. All Fields can be
    extended further via the kwargs in the constructor, e.g. to introduce new
    constraints. All constraints from jsonschema are valid.
    """

    def __init__(self, description: str = "", **constraints: Any) -> None:
        self.description = description
        self.constraints = constraints

    def get_schema(self) -> Schema:
        """
        Returns a JSON schema for this field.
        """
        return dict(description=self.description, **self.constraints)

    def extend_schema(self, schema: Schema, **kwargs: Any) -> Schema:
        """
        Use in subclasses to extend the schema of the the super class.
        """
        schema.update(kwargs)
        return schema


class ArrayField(Field):
    """ Used for arbitrary arrays. """

    def get_schema(self) -> Schema:
        return self.extend_schema(super().get_schema(), type="array")


class IntegerField(Field):
    def get_schema(self) -> Schema:
        return self.extend_schema(super().get_schema(), type="integer")


class PositiveIntegerField(IntegerField):
    def get_schema(self) -> Schema:
        return self.extend_schema(super().get_schema(), minimum=1)


class IdField(PositiveIntegerField):
    pass


class TimestampField(PositiveIntegerField):
    """ Used to represent a UNIX timestamp. """

    pass


class BooleanField(Field):
    def get_schema(self) -> Schema:
        return self.extend_schema(super().get_schema(), type="boolean")


class TextField(Field):
    def get_schema(self) -> Schema:
        return self.extend_schema(super().get_schema(), type="string")


class RequiredTextField(TextField):
    def get_schema(self) -> Schema:
        return self.extend_schema(super().get_schema(), minLength=1)


class CharField(TextField):
    def get_schema(self) -> Schema:
        return self.extend_schema(super().get_schema(), maxLength=256)


class RequiredCharField(CharField):
    def get_schema(self) -> Schema:
        return self.extend_schema(super().get_schema(), minLength=1)


class RelationMixin(Field):
    """
    Field that provides a relation to another Collection.
    We support 1:m, m:n 1:1 and m:1 relations.
    Args:
        to: The collection this field is related to.
        related_name: The name of the array field of the related model. This
            string may contain a $ as special character. I this case the $ will
            be replaced by an id of a specific field of this model e. g. the
            meeting id. This is only possible if the structured_relation argument
            is set. In the end there will be a lot of fields in the related
            model.
        structured_relation: A list of foreign key field names. The first one is a
            field of this model. We follow this relation. The second one is a field
            of the model related by the first one. We go on this way until the last
            one, where we can find the id that should be used to replace the $ used
            in related_name argument. Attention: If the value of these fields
            changed, all relations would have been broken. So such fields should not be
            updated at all.
        generic_relation: If this flag is true the reverse field contains
            FQFields of different collections i. e. it is a generic field.
        delete_protection: If this flag is true the instance can not be delete
            if this field is not empty.
    """

    on_delete: str

    own_collection: Collection
    own_field_name: str

    type: str

    def __init__(
        self,
        to: Collection,
        related_name: str,
        structured_relation: List[str] = None,
        generic_relation: bool = False,
        delete_protection: bool = False,
        **kwargs: Any,
    ) -> None:
        if structured_relation is not None:
            if "$" not in related_name:
                raise ValueError(
                    "Setting structured_relation requires a $ in related_name."
                )
        else:
            if "$" in related_name:
                raise ValueError(
                    "A $ in related name requires setting structured_relation."
                )
        self.to = to
        self.related_name = related_name
        self.structured_relation = structured_relation
        self.generic_relation = generic_relation
        self.delete_protection = delete_protection
        if generic_relation:
            ReverseRelations[self.to].append(GenericRelationFieldWrapper(self))
        else:
            ReverseRelations[self.to].append(self)
        super().__init__(**kwargs)  # type: ignore

    def get_reverse_schema(self) -> Schema:
        """
        Returns the reverse side of the field schema.
        """
        raise NotImplementedError

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}(to={self.to}, related_name={self.related_name}, "
            f"structured_relation={self.structured_relation}, "
            f"generic_relation={self.generic_relation}, type={self.type}, "
            f"delete_protection={self.delete_protection}, description={self.description})"
        )


ReverseRelations: Dict[Collection, List[RelationMixin]] = defaultdict(list)


class GenericRelationFieldWrapper(RelationMixin):
    def __init__(self, instance: RelationMixin) -> None:
        object.__setattr__(self, "instance", instance)

    def __setattr__(self, name: str, value: Any) -> None:
        object.__setattr__(object.__getattribute__(self, "instance"), name, value)

    def __getattribute__(self, name: str) -> Any:
        def get_reverse_schema(self: Any) -> Schema:
            # TODO: Fix this schema wrapping for 1:m and m:n cases.
            return self.extend_schema(
                self.get_reverse_schema(), type="string", pattern=FullQualifiedId.REGEX
            )

        instance = object.__getattribute__(self, "instance")
        if name == "get_reverse_schema":
            return lambda *args, **kargs: get_reverse_schema(instance)
        return instance.__getattribute__(name)


class RequiredOneToOneField(RelationMixin, IdField):
    on_delete = "protect"  # TODO: Enable cascade
    type = "1:1"

    def get_reverse_schema(self) -> Schema:
        return self.get_schema()


class OneToOneField(RelationMixin, IdField):
    on_delete = "set_null"  # TODO: Enable cascade
    type = "1:1"

    def get_schema(self) -> Schema:
        return self.extend_schema(super().get_schema(), type=["integer", "null"])

    def get_reverse_schema(self) -> Schema:
        return self.get_schema()


class RequiredForeignKeyField(RelationMixin, IdField):
    on_delete = "protect"  # TODO: Enable cascade
    type = "1:m"

    def get_reverse_schema(self) -> Schema:
        return dict(
            description=self.description,
            type="array",
            items={"type": "integer", "minimum": 1},
            uniqueItems=True,
        )


class ForeignKeyField(RequiredForeignKeyField):
    on_delete = "set_null"  # TODO: Enable cascade

    def get_schema(self) -> Schema:
        return self.extend_schema(super().get_schema(), type=["integer", "null"])


class ManyToManyArrayField(RelationMixin, IdField):
    type = "m:n"

    def get_schema(self) -> Schema:
        return self.extend_schema(
            super().get_schema(),
            type="array",
            items={"type": "integer", "minimum": 1},
            uniqueItems=True,
        )

    def get_reverse_schema(self) -> Schema:
        return self.get_schema()
