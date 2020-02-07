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

    def is_single_reference(self) -> bool:
        return False

    def is_multiple_reference(self) -> bool:
        return False


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


class RelationMixin:
    def __init__(self, to: Collection, related_name: str, **kwargs: Any) -> None:
        self.to = to
        self.related_name = related_name
        self.on_delete = "protect"  # TODO: Enable cascade
        BackReferences[self.to].append(self)
        super().__init__(**kwargs)  # type: ignore


BackReferences: Dict[Collection, List[RelationMixin]] = defaultdict(list)


class RequiredForeignKeyField(RelationMixin, IdField):
    def is_single_reference(self) -> bool:
        return True


class ForeignKeyField(RequiredForeignKeyField):
    def get_schema(self) -> Schema:
        schema = super().get_schema()
        schema["type"] = ["integer", "null"]
        return schema


class ManyToManyArrayField(RelationMixin, Field):
    def get_schema(self) -> Schema:
        return dict(
            description=self.description,
            type="array",
            items={"type": "integer", "minimum": 1},
            uniqueItems=True,
        )

    def is_multiple_reference(self) -> bool:
        return True
