from ..shared.patterns import Collection
from .fields import Field, Schema


class Model:
    """
    Base class for models in OpenSlides.
    """

    collection: Collection
    verbose_name: str

    def __str__(self) -> str:
        return self.verbose_name

    def get_field(self, field: str) -> Field:
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if attr_name == field and isinstance(attr, Field):
                return attr
        else:
            raise ValueError(f"Model {self} has no field {field}.")

    def get_schema(self, field: str) -> Schema:
        """
        Returns JSON schema for the given field.
        """
        return getattr(self, field).get_schema()
