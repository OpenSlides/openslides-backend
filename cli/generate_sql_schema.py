import hashlib
import os
import string
import sys
from collections import defaultdict
from decimal import Decimal
from enum import Enum
from string import Formatter
from textwrap import dedent
from typing import Any, Callable, Dict, List, Optional, Tuple, TypedDict, Union

import requests
import yaml

SOURCE = "./global/meta/models.yml"
DESTINATION = "./global/meta/schema.sql"
MODELS: Dict[str, Dict[str, Any]] = {}


class SchemaZoneTexts(TypedDict, total=False):
    """TypedDict definition for generation of different sql-code parts"""

    table: str
    view: str
    alter_table: str
    undecided: str


class SubstDict(TypedDict, total=False):
    """dict for substitutions of field templates"""

    field_name: str
    type: str
    primary_key: str
    required: str
    default: str
    minimum: str
    minLength: str
    enum_: str


class GenerateCodeBlocks:
    """Main work is done here by recursing the models and their fields and determine the method to use
    """
    @classmethod
    def generate_the_code(cls) -> (str, str, List[str]):
        """ Development purposes: used for output at the end of the schema.sql
        to see which yml-attributes are still not handled
        Return values:
          pre_code: Type definitions etc., which should all appear before first table definitions
          table_name_code: All table and view definitions
          missing_handled_atributes: List of unhandled attributes. handled one's are to be set manually.
        """
        handled_attributes = set(
            (
                "required",
                "maxLength",
                "minLength",
                "default",
                "type",
                "restriction_mode",
                "minimum",
                "calculated",
                "description",
                "read_only",
                "enum",
                "items",
                # "to",  # will be removed, meanwhile replacement for reference
                # "on_delete", # must have other name then the key-value-store one
                # "equal_fields", # do we want or need?
                # "unique",  # still to design
            )
        )
        missing_handled_attributes = []
        pre_code: str = ""
        table_name_code: str = ""

        for table_name, fields in MODELS.items():
            if table_name == "_migration_index":
                continue
            schema_zone_texts: SchemaZoneTexts = defaultdict(str)

            for fname, fdata in fields.items():
                for attr in fdata:
                    if (
                        attr not in handled_attributes
                        and attr not in missing_handled_attributes
                    ):
                        missing_handled_attributes.append(attr)
                method_or_str, type_ = cls.get_method(fname, fdata)
                if isinstance(method_or_str, str):
                    schema_zone_texts["undecided"] += method_or_str
                else:
                    if (enum_ := fdata.get("enum")) or (enum_ := fdata.get("items", {}).get("enum")):
                        pre_code += Helper.get_enum_type_definition(table_name, fname, enum_)
                    result = method_or_str(table_name, fname, fdata, type_)
                    for k, v in result.items():
                        schema_zone_texts[k] += v

            if code := schema_zone_texts["table"]:
                table_name_code += Helper.get_table_head(table_name)
                table_name_code += Helper.get_table_body_end(code)
            if code := schema_zone_texts["alter_table"]:
                table_name_code += code + "\n\n"
            if code := schema_zone_texts["view"]:
                table_name_code += Helper.get_view_head(table_name)
                table_name_code += Helper.get_view_body_end(code)
            if code := schema_zone_texts["undecided"]:
                table_name_code += Helper.get_undecided_all(table_name, code)
        return pre_code, table_name_code, missing_handled_attributes

    @classmethod
    def get_method(
        cls, fname: str, fdata: Dict[str, Any]
    ) -> Tuple[Union[str, Callable[Dict[str, Any], str]], str]:
        if fdata.get("calculated"):
            return (
                f"    {fname} type:{fdata.get('type')} is marked as a calculated field\n",
                "",
            )
        if fname == "id":
            type_ = "primary_key"
            return (FIELD_TYPES[type_].get("method").__get__(cls), type_)
        if (
            (type_ := fdata.get("type"))
            and type_ in FIELD_TYPES
            and (method := FIELD_TYPES[type_].get("method"))
        ):
            return (method.__get__(cls), type_)  # returns the callable classmethod
        text = "no method defined" if type_ else "Unknown Type"
        return (f"    {fname} type:{fdata.get('type')} {text}\n", type_)

    @classmethod
    def get_schema_simple_types(
        cls, table_name: str, fname: str, fdata: Dict[str, Any], type_: str
    ) -> SchemaZoneTexts:
        text: SchemaZoneTexts
        subst, text = Helper.get_initials(table_name, fname, type_, fdata)
        if isinstance((tmp := subst["type"]), string.Template):
            if maxLength := fdata.get("maxLength"):
                tmp = tmp.substitute({"maxLength": maxLength})
            elif isinstance(type_, Decimal):
                tmp = tmp.substitute({"maxLength": 6})
            elif isinstance(type_, str):  # string
                tmp = tmp.substitute({"maxLength": 256})
            subst["type"] = tmp
        text["table"] = Helper.FIELD_TEMPLATE.substitute(subst)
        return text

    @classmethod
    def get_schema_color(
        cls, table_name: str, fname: str, fdata: Dict[str, Any], type_: str
    ) -> SchemaZoneTexts:
        text: SchemaZoneTexts
        subst, text = Helper.get_initials(table_name, fname, type_, fdata)
        tmpl: str = FIELD_TYPES[type_]["pg_type"]
        subst["type"] = tmpl.substitute(subst)
        if default := fdata.get("default"):
            subst["default"] = f" DEFAULT {int(default[1:], 16)}"
        text["table"] = Helper.FIELD_TEMPLATE.substitute(subst)
        return text

    @classmethod
    def get_schema_primary_key(
        cls, table_name: str, fname: str, fdata: Dict[str, Any], type_: str
    ) -> SchemaZoneTexts:
        text: SchemaZoneTexts
        subst, text = Helper.get_initials(table_name, fname, type_, fdata)
        subst["primary_key"] = " PRIMARY KEY GENERATED ALWAYS AS IDENTITY"
        text["table"] = Helper.FIELD_TEMPLATE.substitute(subst)
        return text


class Helper:
    FIELD_TEMPLATE = string.Template(
        "    ${field_name} ${type}${primary_key}${required}${minimum}${minLength}${default},\n"
    )
    ENUM_DEFINITION_TEMPLATE = string.Template(dedent(
        """
        DO $$$$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '${enum_type}') THEN
                CREATE TYPE ${enum_type} AS ENUM (${enumeration});
            ELSE
                RAISE NOTICE 'type "${enum_type}" already exists, skipping';
            END IF;
        END$$$$;
        """
    ))
    FILE_TEMPLATE = dedent(
        """
        -- schema.sql for initial database setup OpenSlides
        -- Code generated. DO NOT EDIT.

        """
    )

    @staticmethod
    def get_table_name(table_name: str) -> str:
        return table_name + "T"

    @staticmethod
    def get_view_name(table_name: str) -> str:
        if table_name in ("group", "user"):
            return table_name + "_"
        return table_name

    @staticmethod
    def get_table_letter(table_name: str) -> str:
        return Helper.get_table_name(table_name)[0]

    @staticmethod
    def get_table_head(table_name: str) -> str:
        return f"\nCREATE TABLE IF NOT EXISTS {Helper.get_table_name(table_name)} (\n"

    @staticmethod
    def get_table_body_end(code: str) -> str:
        code = code[:-2] + "\n"  # last attribute line without ",", but with "\n"
        code += ");\n\n"
        return code

    @staticmethod
    def get_view_head(table_name) -> str:
        return f"\nCREATE OR REPLACE VIEW {Helper.get_view_name(table_name)} AS SELECT *,\n"

    @staticmethod
    def get_view_body_end(table_name, code: str) -> str:
        code = code[:-2] + "\n"  # last attribute line without ",", but with "\n"
        code += f"FROM {Helper.get_table_name(table_name)} {Helper.get_table_letter(table_name)};\n\n"
        return code

    @staticmethod
    def get_undecided_all(table_name, code) -> str:
        return (
            f"/*\n Fields without SQL definition for table {table_name}\n\n{code}\n*/\n"
        )

    @staticmethod
    def get_enum_type_name(table_name, fname, ) -> str:
        return f"enum_{table_name}_{fname}"

    @staticmethod
    def get_enum_type_definition(table_name: str, fname:str, enum_: List[Any]) -> str:
        # enums per type are always strings in postgres
        enumeration = ", ".join([f"'{str(item)}'" for item in enum_])
        subst = {"enum_type": Helper.get_enum_type_name(table_name, fname), "enumeration": enumeration}
        return Helper.ENUM_DEFINITION_TEMPLATE.substitute(subst)

    @staticmethod
    def get_initials(
        table_name: str, fname: str, type_: str, fdata: Dict[str, Any]
    ) -> (SubstDict, SchemaZoneTexts):
        text: SchemaZoneTexts = {}
        flist = [form[1] for form in Formatter().parse(Helper.FIELD_TEMPLATE.template)]
        subst: SubstDict = {k: "" for k in flist}
        if (enum_ := fdata.get("enum")) or fdata.get("items"):
            subst_type = Helper.get_enum_type_name(table_name, fname)
            if not enum_:
                subst_type += "[]"
        else:
            subst_type = FIELD_TYPES[type_]["pg_type"]
        subst.update(
            {
                "field_name": fname,
                "type": subst_type
            }
        )
        if fdata.get("required"):
            subst["required"] = " NOT NULL"
        if (default := fdata.get("default")) is not None:
            if isinstance(default, str) or type_ in ("string", "text"):
                subst["default"] = f" DEFAULT '{default}'"
            elif isinstance(default, (int, bool, float)):
                subst["default"] = f" DEFAULT {default}"
            elif isinstance(default, list):
                tmp = '{"' + '", "'.join(default) + '"}'
                subst["default"] = f" DEFAULT '{tmp}'"
            else:
                raise Exception(
                    f"{table_name}.{fname}: seems to be an invalid default value"
                )
        if (minimum := fdata.get("minimum")) is not None:
            subst[
                "minimum"
            ] = f" CONSTRAINT minimum_{fname} CHECK ({fname} >= {minimum})"
        if minLength := fdata.get("minLength"):
            subst[
                "minLength"
            ] = f" CONSTRAINT minLength_{fname} CHECK (char_length({fname}) >= {minLength})"
        if comment := fdata.get("description"):
            text[
                "alter_table"
            ] = f"comment on column {Helper.get_table_name(table_name)}.{fname} is '{comment}';\n"
        return subst, text


FIELD_TYPES = {
    "string": {
        "pg_type": string.Template("varchar(${maxLength})"),
        "method": GenerateCodeBlocks.get_schema_simple_types,
    },
    "number": {"pg_type": "integer", "method": GenerateCodeBlocks.get_schema_simple_types},
    "boolean": {"pg_type": "boolean", "method": GenerateCodeBlocks.get_schema_simple_types},
    "JSON": {"pg_type": "jsonb", "method": GenerateCodeBlocks.get_schema_simple_types},
    "HTMLStrict": {"pg_type": "text", "method": GenerateCodeBlocks.get_schema_simple_types},
    "HTMLPermissive": {
        "pg_type": "text",
        "method": GenerateCodeBlocks.get_schema_simple_types,
    },
    "float": {"pg_type": "real", "method": GenerateCodeBlocks.get_schema_simple_types},
    "decimal": {
        "pg_type": string.Template("decimal(${maxLength})"),
        "method": GenerateCodeBlocks.get_schema_simple_types,
    },
    "decimal(6)": {
        "pg_type": "decimal(6)",
        "method": GenerateCodeBlocks.get_schema_simple_types,
    },
    "timestamp": {
        "pg_type": "timestamptz",
        "method": GenerateCodeBlocks.get_schema_simple_types,
    },
    "color": {
        "pg_type": string.Template(
            "integer CHECK (${field_name} >= 0 and ${field_name} <= 16777215)"
        ),
        "method": GenerateCodeBlocks.get_schema_color,
    },
    "string[]": {
        "pg_type": string.Template("varchar(${maxLength})[]"),
        "method": GenerateCodeBlocks.get_schema_simple_types,
    },
    "number[]": {
        "pg_type": "integer[]",
        "method": GenerateCodeBlocks.get_schema_simple_types,
    },
    "text": {"pg_type": "text", "method": GenerateCodeBlocks.get_schema_simple_types},
    "relation": {"pg_type": "integer", "method": ""},
    "relation-list": {"pg_type": "integer[]", "method": ""},
    "generic-relation": {"pg_type": "varchar(100)", "method": ""},
    "generic-relation-list": {"pg_type": "varchar(100)[]", "method": ""},
    # special defined
    "primary_key": {
        "pg_type": "integer",
        "method": GenerateCodeBlocks.get_schema_primary_key,
    },
}


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

    pre_code, table_name_code, missing_handled_attributes =GenerateCodeBlocks.generate_the_code()
    with open(DESTINATION, "w") as dest:
        dest.write(Helper.FILE_TEMPLATE)
        dest.write("-- MODELS_YML_CHECKSUM = " + repr(checksum) + "\n")
        dest.write("-- Type definitions")
        dest.write(pre_code)
        dest.write("\n\n-- Table and view definitions")
        dest.write(table_name_code)
        dest.write(
            f"\n/*   Missing attribute handling for {', '.join(missing_handled_attributes)} */"
        )
    print(f"Models file {DESTINATION} successfully created.")

class OnDelete(str, Enum):
    PROTECT = "PROTECT"
    CASCADE = "CASCADE"
    SET_NULL = "SET_NULL"


class Attribute:
    type: str
    maxLength: int
    replacement_collection: Optional[str] = None
    replacement_enum: Optional[List[str]] = None
    fields: Optional["Attribute"] = None
    references: Optional[str] = None
    required: bool = False
    read_only: bool = False
    deferred_foreign_key: bool = False
    default: Any = None
    on_delete: Optional[OnDelete] = None
    equal_fields: Optional[Union[str, List[str]]] = None
    contraints: Dict[str, Any]
    select: Optional[str] = None

    FIELD_TEMPLATE = string.Template(
        "    ${field_name} ${type}${primary_key}${required}${default},\n"
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
            self.maxLength = value.get("maxLength")
            self.references = value.get("references")
            self.required = value.get("required", False)
            self.read_only = value.get("read_only", False)
            self.deferred_foreign_key = value.get("deferred_foreign_key", False)
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
        type_: str = POSTGRES_FROM_YML[self.type]
        if isinstance(type_, string.Template):
            if self.maxLength:
                type_ = type_.substitute({"maxLength": self.maxLength})
            elif self.type == "decimal":
                type_ = type_.substitute({"maxLength": 6})
            else:  # string
                type_ = type_.substitute({"maxLength": 256})
        subst_dict = {
            "field_name": field_name,
            "type": type_,
            "primary_key": "",
            "required": "",
            "default": "",
        }
        if self.required:
            subst_dict["required"] = " NOT NULL"
        if self.default is not None:
            subst_dict["default"] = f" DEFAULT '{self.default}'"

        return self.FIELD_TEMPLATE.substitute(subst_dict)

    def get_alter_table_code(self, table_name: str, field_name: str) -> Optional[str]:
        if self.references:
            if self.deferred_foreign_key:
                return f"ALTER TABLE {table_name} ADD FOREIGN KEY ({field_name}) REFERENCES {self.references} INITIALLY DEFERRED;\n"
            else:
                return f"ALTER TABLE {table_name} ADD FOREIGN KEY ({field_name}) REFERENCES {self.references};\n"
        return

    def get_create_view_code(self, field_name: str) -> str:
        return f"({self.select}) as {field_name},\n"


if __name__ == "__main__":
    main()
