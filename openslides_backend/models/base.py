from typing import Dict, Iterable, Tuple

from ..shared.patterns import Collection
from . import fields_new as fields

model_registry = {}


class ModelMetaClass(type):
    """
    Metaclass for Model base class (see below).

    It creates the registry for models and collections.
    """

    def __new__(metaclass, class_name, class_parents, class_attributes):  # type: ignore
        new_class = super().__new__(
            metaclass, class_name, class_parents, class_attributes
        )
        if class_name != "Model":
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

    def get_field(self, field_name: str) -> fields.Field:
        """
        Returns the requested model field.
        """
        for model_field_name, model_field in self.get_fields():
            if model_field_name == field_name:
                return model_field
        else:
            raise ValueError(f"Model {self} has no field {field_name}.")

    def get_fields(self) -> Iterable[Tuple[str, fields.Field]]:
        """
        Yields all fields in form of a tuple containing field name and field.
        """
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, fields.Field):
                yield attr_name, attr

    def get_relation_fields(self) -> Iterable[Tuple[str, fields.BaseRelationField]]:
        """
        Yields all relation fields (using BaseRelationField) in form of a tuple
        containing field name and field.
        """
        for model_field_name, model_field in self.get_fields():
            if isinstance(model_field, fields.BaseRelationField):
                yield model_field_name, model_field

    def get_schema(self, field: str) -> fields.Schema:
        """
        Returns JSON schema for the given field.
        """
        return getattr(self, field).get_schema()

    def get_properties(self, *fields: str) -> Dict[str, fields.Schema]:
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
