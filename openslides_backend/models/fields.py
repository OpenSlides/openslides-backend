from typing import Any

from .types import Schema


class Field:
    """
    Base class for model fields.
    """

    def __init__(self, description: str) -> None:
        self.description = description

    def get_schema(self) -> Schema:
        raise NotImplementedError

    def is_single_reference(self) -> bool:
        return False

    def is_multiple_reference(self) -> bool:
        return False


class IdField(Field):
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


class RelationMixin:
    def __init__(self, to: str, related_name: str, **kwargs: Any) -> None:
        self.to = to
        self.related_name = related_name
        super().__init__(**kwargs)  # type: ignore


class ForeignKeyField(RelationMixin, IdField):
    def is_single_reference(self) -> bool:
        return True


class ManyToManyArrayField(RelationMixin, Field):
    def get_schema(self) -> Schema:
        return dict(
            description=self.description,
            type="array",
            items={"type": "integer"},
            uniqueItems=True,
        )

    def is_multiple_reference(self) -> bool:
        return True
