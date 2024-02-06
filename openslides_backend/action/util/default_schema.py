from collections.abc import Iterable
from typing import Any

from ...models.base import Model
from ...shared.schema import id_list_schema, required_id_schema, schema_version
from ...shared.typing import Schema

sort_node_schema = {
    "$schema": schema_version,
    "title": "Sort node schema",
    "id": "tree_sort_node",
    "description": "A node inside a sort tree.",
    "type": "object",
    "properties": {
        "id": required_id_schema,
        "children": {
            "type": "array",
            "items": {"type": "object", "$ref": "tree_sort_node"},
            "minItems": 1,
            "uniqueItems": True,
        },
    },
    "required": ["id"],
    "additionalProperties": False,
}


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
        additional_required_fields: dict[str, Any] = {},
        additional_optional_fields: dict[str, Any] = {},
        title: str | None = None,
        description: str | None = None,
    ) -> Schema:
        """
        Returns a default schema with properties and required properties as given.
        The additional_fields can be used to add additional field definitions to a
        schema which are not present in the model.
        """
        schema = {
            "$schema": schema_version,
            "title": title,
            "description": description,
            "type": "object",
            "properties": {
                **self.model.get_properties(*required_properties, *optional_properties),
                **additional_required_fields,
                **additional_optional_fields,
            },
            "required": list(required_properties)
            + list(additional_required_fields.keys()),
            "additionalProperties": False,
        }
        return schema

    def get_create_schema(
        self,
        required_properties: Iterable[str] = [],
        optional_properties: Iterable[str] = [],
        additional_required_fields: dict[str, Any] = {},
        additional_optional_fields: dict[str, Any] = {},
    ) -> Schema:
        return self.get_default_schema(
            required_properties,
            optional_properties,
            additional_required_fields,
            additional_optional_fields,
            title=f"Create schema for single {self.model}",
            description=f"A new {self.model} object.",
        )

    def get_update_schema(
        self,
        required_properties: Iterable[str] = [],
        optional_properties: Iterable[str] = [],
        additional_required_fields: dict[str, Any] = {},
        additional_optional_fields: dict[str, Any] = {},
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
            title=f"Update schema for single {self.model}",
            description=f"An instance of {self.model} to be (partially) updated.",
        )

    def get_delete_schema(self) -> Schema:
        """
        Returns a default delete schema.
        """
        return self.get_default_schema(
            required_properties=["id"],
            title=f"Delete schema for single {self.model}",
            description=f"An instance of {self.model} to be deleted.",
        )

    def get_tree_sort_schema(self) -> Schema:
        """
        Returns a default tree sort schema.
        """
        return self.get_default_schema(
            title=f"Sort {self.model} schema",
            description=f"Nested array of {self.model} objects to be sorted in the given meeting.",
            required_properties=["meeting_id"],
            additional_required_fields={
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
        )

    def get_linear_sort_schema(
        self, id_field_to_sort: str, id_field_main: str = "meeting_id"
    ) -> Schema:
        """
        Returns a default linear sort schema.
        """
        return self.get_default_schema(
            title=f"Sort {self.model} schema",
            required_properties=[id_field_main],
            additional_required_fields={
                id_field_to_sort: id_list_schema,
            },
        )
