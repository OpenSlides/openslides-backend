from typing import Dict, Iterable, Tuple

from ..shared.patterns import Collection
from .fields import Field, RelationMixin, ReverseRelations, Schema

model_registry = {}


class ModelMetaClass(type):
    """
    Metaclass for Model base class (see below).

    This metaclass ensures that relation fields get attributes set so that they
    know its own collection and its own field name.

    It also creates the registry for models and collections.
    """

    def __new__(metaclass, class_name, class_parents, class_attributes):  # type: ignore
        new_class = super().__new__(
            metaclass, class_name, class_parents, class_attributes
        )
        if class_name != "Model":
            for attr_name in class_attributes:
                attr = getattr(new_class, attr_name)
                if isinstance(attr, RelationMixin):
                    attr.own_collection = new_class.collection
                    attr.own_field_name = attr_name
            model_registry[new_class.collection] = new_class
        return new_class


class Model(metaclass=ModelMetaClass):
    """
    Base class for models in OpenSlides.
    """

    collection: Collection
    verbose_name: str

    def __str__(self) -> str:
        return self.verbose_name

    def get_field(self, field_name: str, only_common: bool = False) -> Field:
        """
        Returns the requested model field. Reverse relations are included.
        """
        for model_field_name, model_field in self.get_fields(only_common=only_common):
            if model_field_name == field_name:
                return model_field
        else:
            message = f"Model {self} has no field {field_name}."
            if only_common:
                message += " Reverse relations are not checked."
            raise ValueError(message)

    def get_fields(self, only_common: bool = False) -> Iterable[Tuple[str, Field]]:
        """
        Yields all fields in form of a tuple containing field name and field.
        Reverse relations are included.
        """
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, Field):
                yield attr_name, attr
        if not only_common:
            yield from self.get_reverse_relations()

    def get_relation_fields(self) -> Iterable[Tuple[str, RelationMixin]]:
        """
        Yields all relation fields (using RelationMixin) in form of a tuple
        containing field name and field. Reverse relations are not included.
        """
        for model_field_name, model_field in self.get_fields(only_common=True):
            if isinstance(model_field, RelationMixin):
                yield model_field_name, model_field

    def get_reverse_relations(self) -> Iterable[Tuple[str, RelationMixin]]:
        """
        Yields all reverse relation fields that are set by other models (using
        the related_name argument).
        """
        for field in ReverseRelations.get(self.collection, []):
            yield field.related_name, field

    def get_schema(self, field: str) -> Schema:
        """
        Returns JSON schema for the given field.
        """
        for field_name, field_obj in self.get_reverse_relations():
            if field == field_name:
                return field_obj.get_reverse_schema()
        return getattr(self, field).get_schema()

    def get_properties(self, *fields: str) -> Dict[str, Schema]:
        """
        Returns a dictionary of field schemas used for the properties keyword in
        an action schema.
        """
        properties = {}
        for field in fields:
            try:
                properties[field] = self.get_schema(field)
            except AttributeError:
                raise ValueError(f"{field} is not a field of {self}")
        return properties


def load_models() -> None:
    """
    This function just imports all models so that the fields are recognized by the
    system.

    New models have to be added here.
    """
    from . import (  # noqa
        agenda_item,
        committee,
        group,
        mediafile,
        meeting,
        motion,
        motion_block,
        motion_category,
        motion_state,
        motion_statute_paragraph,
        motion_workflow,
        tag,
        topic,
        user,
    )


load_models()
