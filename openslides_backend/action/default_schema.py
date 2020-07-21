from typing import Dict, Iterable

from ..models.base import Model
from ..shared.schema import schema_version


class DefaultSchema:
    """
    Container for default create, update and delete action schemas.
    """

    def __init__(self, model: Model) -> None:
        self.model = model

    def get_create_schema(
        self, properties: Iterable[str], required_properties: Iterable[str]
    ) -> Dict:
        """
        Returns a default create schema with properties and required properties as given.
        """
        return {
            "$schema": schema_version,
            "title": f"New {self.model} schema",
            "description": f"An array of new {self.model} objects.",
            "type": "array",
            "items": {
                "type": "object",
                "properties": self.model.get_properties(*properties),
                "required": list(required_properties),
                "additionalProperties": False,
            },
            "minItems": 1,
            "uniqueItems": True,
        }

    def get_update_schema(self, properties: Iterable[str]) -> Dict:
        """
        Returns a default update schema with properties as given. The required
        property 'id' is added.
        """
        return {
            "$schema": schema_version,
            "title": f"Update {self.model} schema",
            "description": f"An array of {self.model} objects to be updated.",
            "type": "array",
            "items": {
                "type": "object",
                "properties": self.model.get_properties("id", *properties),
                "required": ["id"],
                "additionalProperties": False,
            },
            "minItems": 1,
            "uniqueItems": True,
        }

    def get_delete_schema(self) -> Dict:
        """
        Returns a default delete schema.
        """
        return {
            "$schema": schema_version,
            "title": f"Delete {self.model} schema",
            "description": f"An array of {self.model} objects to be deleted.",
            "type": "array",
            "items": {
                "type": "object",
                "properties": self.model.get_properties("id"),
                "required": ["id"],
                "additionalProperties": False,
            },
            "minItems": 1,
            "uniqueItems": True,
        }
