from collections.abc import Iterable

from ..shared.exceptions import ActionException
from ..shared.patterns import Collection
from . import fields

model_registry: dict[Collection, type["Model"]] = {}


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
            for attr_name in class_attributes:
                attr = getattr(new_class, attr_name)
                if isinstance(attr, fields.Field):
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

    def get_field(self, field_name: str) -> fields.Field:
        """
        Returns the requested model field.
        """
        field = self.try_get_field(field_name)
        if not field:
            raise ValueError(f"Model {self} has no field {field_name}.")
        return field

    def has_field(self, field_name: str) -> bool:
        """
        Returns True if the model has such a field.
        """
        return bool(self.try_get_field(field_name))

    def try_get_field(self, field_name: str) -> fields.Field | None:
        """
        Returns the field for the given field name or None if field is not found.
        """
        field = getattr(self, field_name, None)
        if isinstance(field, fields.Field):
            return field
        return None

    def get_fields(self) -> Iterable[fields.Field]:
        """
        Yields all fields of this model.
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

    def get_writable_fields(self) -> Iterable[fields.Field]:
        """
        Yields all writable fields of this model.
        """
        for model_field in self.get_fields():
            if not isinstance(model_field, fields.RelationListField) or (
                not model_field.is_view_field or model_field.write_fields
            ):
                yield model_field

    def get_property(self, field_name: str) -> fields.Schema:
        """
        Returns JSON schema for the given field. Throws an error if it's read_only.
        """
        field = self.get_field(field_name)
        if field.read_only:
            raise ActionException(
                f"The field {field_name} is read_only and cannot be used in a payload schema."
            )
        return {field_name: field.get_schema()}

    def get_properties(self, *fields: str) -> dict[str, fields.Schema]:
        """
        Returns a dictionary of field schemas used for the properties keyword in
        an action schema.
        """
        properties = {}
        for field in fields:
            properties.update(self.get_property(field))
        return properties

    def get_required_fields(self) -> Iterable[fields.Field]:
        """
        Yields all required fields
        """
        for model_field in self.get_fields():
            if model_field.required:
                yield model_field
