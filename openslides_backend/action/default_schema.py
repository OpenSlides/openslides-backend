from typing import Any, Dict, Iterable, Optional

from ..models.base import Model
from ..shared.schema import schema_version
from ..shared.typing import Schema
from .sort_generic import sort_node_schema


class DefaultSchema:
    """
    Container for default create, update and delete action schemas.
    """

    def __init__(self, model: Model) -> None:
        self.model = model

    def get_default_schema(
        self,
        required_properties: Iterable[str] = [],
        optional_properties: Iterable[str] = [],
        additional_required_fields: Dict[str, Any] = {},
        additional_optional_fields: Dict[str, Any] = {},
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Schema:
        """
        Returns a default schema with properties and required properties as given.
        The additional_fields can be used to add additional field definitions to a
        payload which are not present in the model.
        """
        return {
            "$schema": schema_version,
            "title": title,
            "description": description,
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    **self.model.get_properties(
                        *required_properties, *optional_properties
                    ),
                    **additional_required_fields,
                    **additional_optional_fields,
                },
                "required": list(required_properties)
                + list(additional_required_fields.keys()),
                "additionalProperties": False,
            },
            "minItems": 1,
            "uniqueItems": True,
        }

    def get_create_schema(
        self,
        required_properties: Iterable[str] = [],
        optional_properties: Iterable[str] = [],
        additional_required_fields: Dict[str, Any] = {},
        additional_optional_fields: Dict[str, Any] = {},
    ) -> Schema:
        return self.get_default_schema(
            required_properties,
            optional_properties,
            additional_required_fields,
            additional_optional_fields,
            title=f"{self.model} create schema",
            description=f"An array of new {self.model} objects.",
        )

    def get_update_schema(
        self,
        required_properties: Iterable[str] = [],
        optional_properties: Iterable[str] = [],
        additional_required_fields: Dict[str, Any] = {},
        additional_optional_fields: Dict[str, Any] = {},
    ) -> Schema:
        """
        Returns a default update schema with properties as given. The required
        property 'id' is added.
        """
        return self.get_default_schema(
            ["id"] + list(required_properties),
            optional_properties,
            additional_required_fields,
            additional_optional_fields,
            title=f"{self.model} update schema",
            description=f"An array of {self.model} objects to be (partially) updated.",
        )

    def get_delete_schema(self) -> Schema:
        """
        Returns a default delete schema.
        """
        return self.get_default_schema(
            required_properties=["id"],
            title=f"{self.model} delete schema",
            description=f"An array of {self.model} objects to be deleted.",
        )

    def get_single_item_schema(
        self,
        item_schema: Dict,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Schema:
        return {
            "$schema": schema_version,
            "title": title,
            "description": description,
            "type": "array",
            "items": item_schema,
            "minItems": 1,
            "maxItems": 1,
        }

    def get_tree_sort_schema(self) -> Schema:
        """
        Returns a default tree sort schema.
        """
        return self.get_single_item_schema(
            title=f"Sort {self.model} schema",
            description=f"Nested array of {self.model} objects to be sorted in the given meeting.",
            item_schema={
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
        )

    def get_linear_sort_schema(
        self, id_field_to_sort: str, id_field_main: str = "meeting_id"
    ) -> Schema:
        """
        Returns a default linear sort schema.
        """
        return self.get_single_item_schema(
            title=f"Sort {self.model} schema",
            item_schema={
                "description": f"Meeting id and list of {self.model} ids",
                "type": "object",
                "properties": {
                    **self.model.get_properties(id_field_main),
                    id_field_to_sort: {
                        "type": "array",
                        "items": {"type": "integer", "min": 1},
                        "minItems": 1,
                        "uniqueItems": True,
                    },
                },
                "required": [id_field_main, id_field_to_sort],
                "additionalProperties": False,
            },
        )
