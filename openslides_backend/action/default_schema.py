from typing import Dict, Iterable

from ..models.base import Model
from ..shared.schema import schema_version
from .sort_generic import sort_node_schema


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

    def get_tree_sort_schema(self) -> Dict:
        """
        Returns a default tree sort schema.
        """
        return {
            "$schema": schema_version,
            "title": f"Sort {self.model} schema",
            "description": f"Nested array of {self.model} objects to be sorted in the given meeting.",
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "meeting_id": self.model.get_schema("meeting_id"),
                    "tree": {
                        "description": (
                            f"An array of {self.model} ids to be sorted. The array should contain all "
                            "root objects of a meeting. Each node is a dictionary with an id "
                            "and optional children. In the end all objects of a meeting must "
                            "appear."
                        ),
                        "type": "array",
                        "items": sort_node_schema,
                        "minItems": 1,
                        "uniqueItems": True,
                    },
                },
                "required": ["meeting_id", "tree"],
                "additionalProperties": False,
            },
            "minItems": 1,
            "maxItems": 1,
        }

    def get_linear_sort_schema(self, id_field_to_sort: str) -> Dict:
        """
        Returns a default linear sort schema.
        """
        return {
            "$schema": schema_version,
            "title": f"Sort {self.model} schema",
            "type": "array",
            "items": {
                "description": f"Meeting id and list of {self.model} ids",
                "type": "object",
                "properties": {
                    **self.model.get_properties("meeting_id"),
                    id_field_to_sort: {
                        "type": "array",
                        "items": {"type": "integer", "min": 1},
                        "minItems": 1,
                        "uniqueItems": True,
                    },
                },
                "required": ["meeting_id", id_field_to_sort],
                "additionalProperties": False,
            },
            "minItems": 1,
            "maxItems": 1,
        }
