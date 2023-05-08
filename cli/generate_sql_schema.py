import hashlib
import os
import string
import sys
from enum import Enum
from textwrap import dedent, indent
from typing import Any, Dict, List, Optional, Union

import requests
import yaml

#from openslides_backend.shared.patterns import KEYSEPARATOR, Collection

SOURCE = "./global/meta/models.yml"
DESTINATION = "./global/meta/schema.sql"

COMMON_FIELD_CLASSES = {
    "string": "CharField",
    "number": "IntegerField",
    "boolean": "BooleanField",
    "JSON": "JSONField",
    "HTMLStrict": "HTMLStrictField",
    "HTMLPermissive": "HTMLPermissiveField",
    "float": "FloatField",
    "decimal": "DecimalField",
    "timestamp": "TimestampField",
    "color": "ColorField",
    "string[]": "CharArrayField",
    "number[]": "NumberArrayField",
    "text": "TextField",
}

RELATION_FIELD_CLASSES = {
    "relation": "RelationField",
    "relation-list": "RelationListField",
    "generic-relation": "GenericRelationField",
    "generic-relation-list": "GenericRelationListField",
}

POSTGRES_FROM_YML = {
    "string": string.Template("varchar(${length})"),
    "number": "integer",
    "boolean": "boolean",
    "JSON": "jsonb",
    "HTMLStrict": "text",
    "HTMLPermissive": "text",
    "float": "real",
    "decimal": string.Template("decimal(${length})"),
    "timestamp": "timestamptz",
    "color": "varchar(7)",
    "string[]": string.Template("varchar(${length})[]"),
    "number[]": "integer[]",
    "text": "text",
    "relation": "integer",
    "relation-list": "integer[]",
    "generic-relation": "integer",
    "generic-relation-list": "integer[]",
}

FILE_TEMPLATE = dedent(
    """
    -- schema.sql for initial database setup OpenSlides
    -- Code generated. DO NOT EDIT.

    """
)

MODELS: Dict[str, Dict[str, Any]] = {}


def main() -> None:
    """
    Main entry point for this script to generate the schema.sql from models.yml.
    """

    global MODELS

    # Retrieve models.yml from call-parameter for testing purposes, local file or GitHub
    if len(sys.argv) > 1:
        file = sys.argv[1]
    else:
        file = SOURCE

    if os.path.isfile(file):
        with open(file, "rb") as x:
            models_yml = x.read()
    else:
        models_yml = requests.get(file).content

    # calc checksum to assert the schema.sql is up-to-date
    checksum = hashlib.md5(models_yml).hexdigest()

    if len(sys.argv) > 1 and sys.argv[1] == "check":
        from openslides_backend.models.models import MODELS_YML_CHECKSUM

        assert checksum == MODELS_YML_CHECKSUM
        print("models.py is up to date (checksum-comparison)")
        sys.exit(0)

    # Fix broken keys
    models_yml = models_yml.replace(" yes:".encode(), ' "yes":'.encode())
    models_yml = models_yml.replace(" no:".encode(), ' "no":'.encode())

    # Load and parse models.yml
    MODELS = yaml.safe_load(models_yml)
    alter_table_code:str = ""
    create_view_code:str = ""
    with open(DESTINATION, "w") as dest:
        dest.write(FILE_TEMPLATE)
        dest.write("-- MODELS_YML_CHECKSUM = " + repr(checksum) + "\n")
        for obj_name, fields in MODELS.items():
            if obj_name == "_migration_index":
                continue
            if (entity_desc :=fields.get("entity_description")) and (type_ := entity_desc.get("type")) and type_ == "view":
                view = ViewCreator(obj_name, fields)
                create_view_code += view.get_code()
            else:
                table = TableCreator(obj_name, fields)
                create_code, alter_code = table.get_code()
                dest.write(create_code)
                alter_table_code += alter_code
        dest.write(alter_table_code)
        dest.write(create_view_code)

    print(f"Models file {DESTINATION} successfully created.")


class Creator():
    name: str
    attributes: Dict[str, "Attribute"]
    obj_description: Dict[str, Any]

    def __init__(self, name: str, fields: Dict[str, Dict[str, Any]]) -> None:
        self.name = name
        assert name
        self.attributes = {}
        self.obj_description = {}
        for field_name, field in fields.items():
            if field.get("calculated"):
                continue
            if field_name == "entity_description":
                self.obj_description = field
            else:
                self.attributes[field_name] = Attribute(field)

class TableCreator(Creator):
    def get_code(self) -> tuple[str, str]:
        code = f"\nCREATE TABLE IF NOT EXISTS {self.name} (\n"
        for field_name, attribute in self.attributes.items():
            code += attribute.get_create_table_code(field_name)
        code = code[:-2] + "\n"  # last attribute line without ",", but with "\n"
        code += ");\n\n"

        alter_code: str = ""
        for field_name, attribute in self.attributes.items():
            if (line:= attribute.get_alter_table_code(self.name, field_name)):
                alter_code += line
        return code, alter_code


class ViewCreator(Creator):
    def get_code(self) -> tuple[str, str]:
        assert self.obj_description.get('table') and self.obj_description.get('table_letter'), f"View {self.name} needs table and table_letter attribute in entity description"
        code = f"\nCREATE OR REPLACE VIEW {self.name} AS SELECT id,\n"
        for field_name, attribute in self.attributes.items():
            if attribute.select:
                code += attribute.get_create_view_code(field_name)
        code = code[:-2] + "\n"  # last attribute line without ",", but with "\n"

        code += f"FROM {self.obj_description.get('table')} {self.obj_description.get('table_letter')};\n\n"

        return code

class OnDelete(str, Enum):
    PROTECT = "PROTECT"
    CASCADE = "CASCADE"
    SET_NULL = "SET_NULL"


class Attribute():
    type: str
    length: int
    replacement_collection: Optional[str] = None
    replacement_enum: Optional[List[str]] = None
    fields: Optional["Attribute"] = None
    references: Optional[str] = None
    required: bool = False
    read_only: bool = False
    default: Any = None
    on_delete: Optional[OnDelete] = None
    equal_fields: Optional[Union[str, List[str]]] = None
    contraints: Dict[str, Any]
    select: Optional[str] = None

    FIELD_TEMPLATE = string.Template(
        "    ${field_name} ${type}${primary_key}${required},\n"
    )
    REFERENCES_TEMPLATE = " REFERENCES %s"

    def __init__(self, value: Union[str, Dict]) -> None:
        self.FIELD_CLASSES = {
            **COMMON_FIELD_CLASSES,
            **RELATION_FIELD_CLASSES,
        }
        self.contraints = {}
        self.in_array_constraints = {}
        if isinstance(value, str):
            self.type = value
        else:
            self.type = value.get("type", "")
            if self.type in RELATION_FIELD_CLASSES.keys():
                self.on_delete = value.get("on_delete")
            else:
                assert self.type in COMMON_FIELD_CLASSES.keys(), (
                    "Invalid type: " + self.type
                )
            self.length = value.get("length")
            self.references = value.get("references")
            self.required = value.get("required", False)
            self.read_only = value.get("read_only", False)
            self.default = value.get("default")
            self.select = value.get("select")
            self.equal_fields = value.get("equal_fields")
            for k, v in value.items():
                if k not in (
                    "type",
                    "required",
                    "read_only",
                    "default",
                    "on_delete",
                    "equal_fields",
                    "items",
                    "restriction_mode",
                ):
                    self.contraints[k] = v
                elif self.type in ("string[]", "number[]") and k == "items":
                    self.in_array_constraints.update(v)

    def get_create_table_code(self, field_name: str) -> str:
        type_:str = POSTGRES_FROM_YML[self.type]
        if isinstance(type_, string.Template):
            if self.length:
                type_ = type_.substitute({"length": self.length})
            elif self.type == "decimal":
                type_ = type_.substitute({"length": 6})
            else:  # string
                type_ = type_.substitute({"length": 50})
        subst_dict = {
            "field_name": field_name,
            "type": type_,
            "primary_key": "",
            "required": "",
            #"default": ""
        }
        if field_name == "id":
            subst_dict["primary_key"] = " PRIMARY KEY GENERATED ALWAYS AS IDENTITY"
        else:
            if self.required:
                subst_dict["required"] = " NOT NULL"
            if self.default:
                subst_dict["default"] = f" DEFAULT {self.default}"

        return self.FIELD_TEMPLATE.substitute(subst_dict)

    def get_alter_table_code(self, table_name: str, field_name: str) -> Optional[str]:
        if self.references:
            return f"ALTER TABLE {table_name} ADD FOREIGN KEY ({field_name}) REFERENCES {self.references};\n"
        return

    def get_create_view_code(self, field_name: str) -> str:
        return f"({self.select}) as {field_name},\n"


if __name__ == "__main__":
    main()
