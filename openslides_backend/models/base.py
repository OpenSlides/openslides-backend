import re
from typing import Dict, Iterable, Optional, Type

from ..shared.patterns import Collection
from . import fields

model_registry: Dict[Collection, Type["Model"]] = {}


class ModelMetaClass(type):
    """
    Metaclass for Model base class (see below).

    This metaclass ensures that all fields get attributes set so that they
    know its own collection and its own field name.

    It also creates the registry for models and collections.
    """

    def __new__(metaclass, class_name, class_parents, class_attributes):  # type: ignore
        new_class = super().__new__(
            metaclass, class_name, class_parents, class_attributes
        )
        if class_name != "Model":
            new_class.field_prefix_map = {}
            for attr_name in class_attributes:
                attr = getattr(new_class, attr_name)
                if isinstance(attr, fields.Field):
                    attr.own_collection = new_class.collection
                    attr.own_field_name = attr_name

                    # save normal field name
                    new_class.field_prefix_map[attr_name] = attr
                    if isinstance(attr, fields.BaseTemplateField):
                        prefix = attr_name[: attr.index]
                        new_class.field_prefix_map[prefix] = attr
            model_registry[new_class.collection] = new_class
        return new_class


class Model(metaclass=ModelMetaClass):
    """
    Base class for models in OpenSlides.
    """

    collection: Collection
    verbose_name: str

    # saves all fields with their respective unique prefix for easier access
    field_prefix_map: Dict[str, fields.BaseRelationField]

    def __str__(self) -> str:
        return self.verbose_name

    def get_field(self, field_name: str) -> fields.Field:
        """
        Returns the requested model field.
        """
        field = self.try_get_field(field_name)
        if field:
            return field
        else:
            raise ValueError(f"Model {self} has no field {field_name}.")

    def has_field(self, field_name: str) -> bool:
        return bool(self.try_get_field(field_name))

    def try_get_field(self, field_name: str) -> Optional[fields.Field]:
        prefix = field_name.split("$")[0]
        if prefix not in self.field_prefix_map:
            return None

        field = self.field_prefix_map[prefix]
        if isinstance(field, fields.BaseTemplateField):
            # we use the regex here since we want to also match template fields
            if "$" in field_name and not re.match(field.get_regex(), field_name):
                return None
        return field

    def get_fields(self) -> Iterable[fields.Field]:
        """
        Yields all fields in form of a tuple containing field name and field.
        """
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, fields.Field):
                yield attr

    def get_relation_fields(self) -> Iterable[fields.BaseRelationField]:
        """
        Yields all relation fields (using BaseRelationField).
        """
        for model_field in self.get_fields():
            if isinstance(model_field, fields.BaseRelationField):
                yield model_field

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
