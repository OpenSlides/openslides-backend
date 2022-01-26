import re
from typing import Dict, Iterable, Optional, Type

from ..shared.exceptions import ActionException
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

                    # Save field name. For template fields also save prefix.
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

    # Saves all fields with their respective unique prefix for easier access.
    # Template fields are saved twice. Once with the pythonic name from models.py and
    # once only with the prefix.
    field_prefix_map: Dict[str, fields.BaseRelationField]

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
        Returns True if the model has such a field (including populated template fields).
        """
        return bool(self.try_get_field(field_name))

    def try_get_field(self, field_name: str) -> Optional[fields.Field]:
        """
        Returns the field for the given field name. You may give the
        pythonic field name or even a populated template field.

        E. g. for User the `group__ids` field alias `group_$_ids` field is also found
        if you look for `group_$42_ids`.

        Returns None if field is not found.
        """
        prefix = field_name.split("$")[0]
        if prefix not in self.field_prefix_map:
            return None

        field = self.field_prefix_map[prefix]
        if isinstance(field, fields.BaseTemplateField):
            # We use the regex here since we want to also match template fields.
            if "$" in field_name and not re.match(field.get_regex(), field_name):
                return None
        return field

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

    def get_property(
        self, field_name: str, replacement_pattern: Optional[str] = None
    ) -> fields.Schema:
        """
        Returns JSON schema for the given field. Throws an error if it's read_only.
        """
        field = self.get_field(field_name)
        if field.read_only:
            raise ActionException(
                f"The field {field_name} is read_only and cannot be used in a payload schema."
            )
        return {field_name: field.get_payload_schema(replacement_pattern)}

    def get_properties(self, *fields: str) -> Dict[str, fields.Schema]:
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

                if isinstance(
                    model_field,
                    (
                        fields.RelationListField,
                        fields.GenericRelationListField,
                        fields.BaseTemplateField,
                    ),
                ) and (
                    not hasattr(model_field, "replacement_enum")
                    or not model_field.replacement_enum  # type: ignore
                ):
                    raise NotImplementedError(
                        f"{self.collection.collection}.{model_field.own_field_name}"
                    )
                yield model_field
