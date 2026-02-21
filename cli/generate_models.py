import os
import string
from argparse import Namespace
from collections import ChainMap
from textwrap import dedent
from typing import Any, Optional

from cli.util.util import ROOT, assert_equal, open_output, parse_arguments
from meta.dev.src.helper_get_names import (
    DEFAULT_COLLECTION_META,
    FieldSqlErrorType,
    HelperGetNames,
    InternalHelper,
    TableFieldType,
)
from openslides_backend.models.base import Model as BaseModel
from openslides_backend.models.fields import OnDelete
from openslides_backend.models.mixins import (
    AgendaItemModelMixin,
    MeetingModelMixin,
    PollModelMixin,
)
from openslides_backend.shared.patterns import KEYSEPARATOR, Collection

DESTINATION = os.path.abspath(
    os.path.join(
        ROOT,
        "openslides_backend",
        "models",
        "models.py",
    )
)

COMMON_FIELD_CLASSES = {
    "string": "CharField",
    "number": "IntegerField",
    "boolean": "BooleanField",
    "JSON": "JSONField",
    "HTMLStrict": "HTMLStrictField",
    "HTMLPermissive": "HTMLPermissiveField",
    "float": "FloatField",
    "decimal(6)": "DecimalField",
    "timestamp": "TimestampField",
    "color": "ColorField",
    "string[]": "CharArrayField",
    "number[]": "NumberArrayField",
    "text": "TextField",
    "text[]": "TextArrayField",
}

RELATION_FIELD_CLASSES = {
    "relation": "RelationField",
    "relation-list": "RelationListField",
    "generic-relation": "GenericRelationField",
    "generic-relation-list": "GenericRelationListField",
}

MODEL_MIXINS: dict[str, type] = {
    "agenda_item": AgendaItemModelMixin,
    "meeting": MeetingModelMixin,
    "poll": PollModelMixin,
}

FILE_TEMPLATE = dedent(
    """\
    # Code generated. DO NOT EDIT.

    from . import fields
    from .base import Model
    """
)


def main() -> None:
    """
    Main entry point for this script to generate the models.py from models.yml.

    Example: The FQField some_model/some_attribute and its reverse part are defined
    like this:

        some_model:
          some_attribute:
            type: relation
            to:
              collection: another_model
              field:
                type: relation
                name: another_attribute

        another_model:
          another_attribute:
            type: relation_list
            to: some_model/some_attribute_id
    """
    args: Namespace = parse_arguments(DEFAULT_COLLECTION_META)

    InternalHelper.read_models_yml()

    # Load and parse models.yml
    with open_output(DESTINATION, args.check) as dest:
        dest.write(FILE_TEMPLATE)
        dest.write(
            "from .mixins import "
            + ", ".join(mixin.__name__ for mixin in MODEL_MIXINS.values())
            + "\n"
        )
        for collection, fields in InternalHelper.MODELS.items():
            if collection.startswith("_"):
                continue
            model = Model(collection, fields)
            dest.write(model.get_code())

        if args.check:
            assert_equal(dest, DESTINATION)
            print("Models file up-to-date.")
        else:
            print(f"Models file {DESTINATION} successfully created.")


class Node:
    """
    We walk down the YML tree and parse the elements in this order (if appropriate):

    Model -> Attribute -> To -> RelationField
    """

    # Empty parent class perhaps to be used later.


class Model(Node):
    collection: str
    attributes: dict[str, "Attribute"]

    MODEL_TEMPLATE = string.Template(
        dedent(
            """
            class ${class_name}(${base_classes}):
                collection = "${collection}"
                verbose_name = "${verbose_name}"
            """
        )
    )

    def __init__(self, collection: str, fields: dict[str, dict[str, Any]]) -> None:
        self.collection = collection
        assert collection
        self.attributes = {}
        for field_name, field in fields.items():
            if field.get("calculated"):
                continue
            self.attributes[field_name] = Attribute(
                field.copy(), collection, field_name
            )

    def get_code(self) -> str:
        verbose_name = " ".join(self.collection.split("_"))
        base_classes: list[type] = [BaseModel]
        if self.collection in MODEL_MIXINS:
            base_classes.append(MODEL_MIXINS[self.collection])
        code = (
            self.MODEL_TEMPLATE.substitute(
                {
                    "class_name": self.get_class_name(),
                    "base_classes": ", ".join(cls.__name__ for cls in base_classes),
                    "collection": self.collection,
                    "verbose_name": verbose_name,
                }
            )
            + "\n"
        )
        for field_name, attribute in self.attributes.items():
            code += attribute.get_code(field_name)
        return code

    def get_class_name(self) -> str:
        return "".join([part.capitalize() for part in self.collection.split("_")])


class Attribute(Node):
    type: str
    to: Optional["To"] = None
    fields: Optional["Attribute"] = None
    required: bool = False
    read_only: bool = False
    constant: bool = False
    default: Any = None
    on_delete: OnDelete | None = None
    equal_fields: str | list[str] | None = None
    constraints: dict[str, Any]
    is_view_field: bool = False
    is_primary: bool = False
    write_fields: tuple[str, str, str, list[str]] | None = None

    FIELD_TEMPLATE = string.Template(
        "    ${field_name} = fields.${field_class}(${properties})\n"
    )

    def __init__(
        self, value: str | dict, collection_name: str, field_name: str
    ) -> None:
        self.FIELD_CLASSES = {
            **COMMON_FIELD_CLASSES,
            **RELATION_FIELD_CLASSES,
        }
        self.constraints = {}
        self.in_array_constraints = {}
        if isinstance(value, str):
            self.type = value
        else:
            self.type = value.get("type", "")
            if self.type in RELATION_FIELD_CLASSES.keys():
                self.is_view_field, self.is_primary, self.write_fields = (
                    self.get_view_field_state_write_fields(
                        collection_name, field_name, value
                    )
                )
                self.to = To(value.pop("to"))
                self.on_delete = value.pop("on_delete", None)
            else:
                assert self.type in COMMON_FIELD_CLASSES.keys(), (
                    "Invalid type: " + self.type
                )
            value.pop("type")
            self.required = value.pop("required", False)
            self.read_only = value.pop("read_only", False)
            self.constant = value.pop("constant", False)
            self.default = value.pop("default", None)
            self.equal_fields = value.pop("equal_fields", None)
            for k, v in value.items():
                if k not in (
                    "items",
                    "restriction_mode",
                    # database metadata
                    "reference",
                    "sql",
                    "deferred",
                    "unique",
                ):
                    self.constraints[k] = v
                elif self.type in ("string[]", "number[]", "text[]") and k == "items":
                    self.in_array_constraints.update(v)

    def get_code(self, field_name: str) -> str:
        if field_name == "organization_id":
            field_class = "OrganizationField"
        else:
            field_class = self.FIELD_CLASSES[self.type]
        properties = ""
        if self.to:
            properties += self.to.get_properties()
        if self.on_delete:
            assert self.on_delete in [mode for mode in OnDelete]
            properties += f"on_delete=fields.OnDelete.{self.on_delete}, "
        if self.is_view_field:
            properties += "is_view_field=True, "
        if self.is_primary:
            properties += "is_primary=True, "
        if self.required:
            properties += "required=True, "
        if self.read_only:
            properties += "read_only=True, "
        if self.constant:
            properties += "constant=True, "
        if self.default is not None:
            properties += f"default={repr(self.default)}, "
        if self.equal_fields is not None:
            properties += f"equal_fields={repr(self.equal_fields)}, "
        if self.constraints:
            properties += f"constraints={repr(self.constraints)}, "
        if self.write_fields is not None:
            properties += f"write_fields={repr(self.write_fields)}, "
        if self.in_array_constraints and self.type in (
            "string[]",
            "number[]",
            "text[]",
        ):
            properties += f"in_array_constraints={repr(self.in_array_constraints)}"

        return self.FIELD_TEMPLATE.substitute(
            dict(
                field_name=field_name,
                field_class=field_class,
                properties=properties.rstrip(", "),
            )
        )

    def get_view_field_state_write_fields(
        self, collection_name: str, field_name: str, value: dict[str, Any]
    ) -> tuple[bool, bool, tuple[str, str, str, list[str]] | None]:
        """
        Purpose:
            Checks whether a field is a view field and if other fields need to be written in an intermediate
            table.
        Input:
        - collection_name
        - field_name
        - value : represents the definition of the field ( field_name in collection_name )
        Returns:
        - is_view_field : whether the field is a view field or not
        - is_primary: wether the field is primary or not
        - write_fields:
            - None if no fields need to be written
            - Tuple
                table_name : name of the intermediate table
                field1
                field2
                foreign_fields
        """
        # variable declaration
        own: TableFieldType
        field_type: str
        state: FieldSqlErrorType
        primary: bool
        error: str
        is_view_field: bool
        foreign: TableFieldType
        foreign_type: str
        table_name: str = ""
        field1: str = ""
        field2: str = ""
        write_fields: tuple[str, str, str, list[str]] | None = None

        # create TableFieldType own out of collection_name, field_name, value as field_def
        own = TableFieldType(collection_name, field_name, value)
        field_type = own.field_def.get("type", "")

        # get the foreign field list and check the relations
        foreign_fields = InternalHelper.get_definitions_from_foreign_list(
            value.get("to", None), value.get("reference", None)
        )
        state, primary, _, error = InternalHelper.check_relation_definitions(
            own, foreign_fields
        )
        is_view_field = state == FieldSqlErrorType.SQL

        if not value.get("sql"):
            foreign = foreign_fields[0]
            foreign_type = foreign.field_def.get("type", "")
            if "relation-list" == field_type == foreign_type:
                table_name = HelperGetNames.get_nm_table_name(own, foreign)
                field1 = HelperGetNames.get_field_in_n_m_relation_list(
                    own, foreign.table
                )
                field2 = HelperGetNames.get_field_in_n_m_relation_list(
                    foreign, own.table
                )
                if field1 == field2:
                    field1 += "_1"
                    field2 += "_2"
                if own.table == foreign.table:
                    write_fields = (table_name, field2, field1, [])
                else:
                    write_fields = (table_name, field1, field2, [])
            elif "generic-relation-list" in (field_type, foreign_type):
                write_fields = self.get_write_fields_for_generic(
                    own, foreign_fields, primary
                )

        assert error == "", error

        return is_view_field, primary, write_fields

    def get_write_fields_for_generic(
        self, own: TableFieldType, foreign_fields: list[TableFieldType], primary: bool
    ) -> tuple[str, str, str, list[str]] | None:
        if primary:
            table_name = HelperGetNames.get_gm_table_name(own)
        else:
            table_name = HelperGetNames.get_gm_table_name(foreign_fields[0])
        field1 = f"{own.table}_{own.ref_column}"
        field2 = own.intermediate_column
        return (
            table_name,
            field1,
            field2,
            [f"{field2}_{field.table}_{field.ref_column}" for field in foreign_fields],
        )


class To(Node):
    to: dict[Collection, str]  # collection <-> field_name

    def __init__(self, value: str | dict) -> None:
        if isinstance(value, str):
            self.to = self.parse_collectionfield(value)
        elif isinstance(value, list):
            self.to = dict(ChainMap(*[self.parse_collectionfield(cf) for cf in value]))
        else:
            assert isinstance(value, dict)
            collections = value.get("collections")
            assert isinstance(collections, list)
            self.to = {c: value["field"] for c in collections}

    def parse_collectionfield(self, collectionfield: str) -> dict[Collection, str]:
        """
        Parses the given collectionfield into its parts and returns a dict consisting of a single
        respective entry.
        """
        collection, field = collectionfield.split(KEYSEPARATOR)
        return {collection: field}

    def get_properties(self) -> str:
        return "to=" + repr(self.to) + ","


if __name__ == "__main__":
    main()
