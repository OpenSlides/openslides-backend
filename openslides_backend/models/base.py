from typing import Dict, Iterable, Tuple

from ..shared.patterns import Collection
from .fields import BackReferences, Field, RelationMixin, Schema


class Model:
    """
    Base class for models in OpenSlides.
    """

    collection: Collection
    verbose_name: str

    def __str__(self) -> str:
        return self.verbose_name

    def get_fields(self) -> Iterable[Tuple[str, Field]]:
        """
        Yields all fields in form of a tuple containing field name and field.
        """
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, Field):
                yield attr_name, attr

    def get_field(self, field_name: str) -> Field:
        """
        Returns the requested model field.
        """
        for model_field_name, model_field in self.get_fields():
            if model_field_name == field_name:
                return model_field
        else:
            raise ValueError(f"Model {self} has no field {field_name}.")

    def get_reference_fields(self) -> Iterable[Tuple[str, Field]]:
        """
        Yields all reference fields (using RelationMixin) in form of a tuple
        containing field name and field.
        """
        for model_field_name, model_field in self.get_fields():
            if isinstance(model_field, RelationMixin):
                yield model_field_name, model_field

    def get_schema(self, field: str) -> Schema:
        """
        Returns JSON schema for the given field.
        """
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
                raise TypeError(f"{field} is not a field of {self}")
        return properties

    def get_back_references(self) -> Iterable[Tuple[str, RelationMixin]]:
        """
        Yields all reference fields that are set by other models (using the
        related_name argument).
        """
        for field in BackReferences.get(self.collection, []):
            yield field.related_name, field
