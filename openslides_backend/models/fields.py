from collections import defaultdict
from typing import Any, Dict, List

from ..shared.patterns import Collection

Schema = Dict[str, Any]


class Field:
    """
    Base class for model fields.
    """

    def __init__(self, description: str) -> None:
        self.description = description

    def get_schema(self) -> Schema:
        """
        Returns a JSON schema for this field.
        """
        raise NotImplementedError


class IdField(Field):
    def get_schema(self) -> Schema:
        return dict(description=self.description, type="integer", minimum=1,)


class IntegerField(Field):
    def get_schema(self) -> Schema:
        return dict(description=self.description, type="integer",)


class PositiveIntegerField(Field):
    def get_schema(self) -> Schema:
        return dict(description=self.description, type="integer", minimum=1,)


class CharField(Field):
    def get_schema(self) -> Schema:
        return dict(description=self.description, type="string", maxLength=256,)


class RequiredCharField(CharField):
    def get_schema(self) -> Schema:
        schema = super().get_schema()
        schema["minLength"] = 1
        return schema


class TextField(Field):
    def get_schema(self) -> Schema:
        return dict(description=self.description, type="string",)


class TimestampField(Field):
    def get_schema(self) -> Schema:
        return dict(description=self.description, type="integer", minimum=1,)


class RelationMixin(Field):
    """
    Field that provides a relation to another Collection.

    At the moment we only support 1:m and m:n relations but not 1:1 or m:1 relations.

    Args:
        to: The collection this field is related to.
        related_name: The name of the array field of the related model. This
            string may contain a $ as special character. I this case the $ will
            be replaced by an id of a specific field of this model e. g. the
            meeting id. This is only possible if the structured_relation argument
            is set. In the end there will be a lot of fields in the related
            model.
        structured_relation: The name of the foreign key field of this model where
            we can find the id that should be used to replace the $ used in
            related_name argument. Attention: If the value of this field
            changes, all relations have to be adjusted. So don't use a
            writable field at all.
        generic_relation: If this flag is true the reverse field contains
            FQFields of different collections i. e. it is a generic field.
    """

    on_delete: str

    own_collection: Collection
    own_field_name: str

    def __init__(
        self,
        to: Collection,
        related_name: str,
        structured_relation: str = None,
        generic_relation: bool = False,
        **kwargs: Any
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
        ReverseRelations[self.to].append(self)
        super().__init__(**kwargs)  # type: ignore

    def is_single_relation(self) -> bool:
        raise NotImplementedError

    def is_multiple_relation(self) -> bool:
        return not self.is_single_relation()


ReverseRelations: Dict[Collection, List[RelationMixin]] = defaultdict(list)


class RequiredForeignKeyField(RelationMixin, IdField):

    on_delete = "protect"  # TODO: Enable cascade

    def is_single_relation(self) -> bool:
        return True


class ForeignKeyField(RequiredForeignKeyField):

    on_delete = "set_null"  # TODO: Enable cascade

    def get_schema(self) -> Schema:
        schema = super().get_schema()
        schema["type"] = ["integer", "null"]
        return schema


class ManyToManyArrayField(RelationMixin):
    def get_schema(self) -> Schema:
        return dict(
            description=self.description,
            type="array",
            items={"type": "integer", "minimum": 1},
            uniqueItems=True,
        )

    def is_single_relation(self) -> bool:
        return False
