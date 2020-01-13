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
    pass


class ManyToManyArrayField(RelationMixin, Field):
    def get_schema(self) -> Schema:
        return dict(
            description=self.description,
            type="array",
            items={"type": "integer"},
            uniqueItems=True,
        )
