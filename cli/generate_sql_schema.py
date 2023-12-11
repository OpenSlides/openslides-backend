import hashlib
import os
import re
import string
import sys
from collections import defaultdict
from copy import deepcopy
from decimal import Decimal
from enum import Enum
from string import Formatter
from textwrap import dedent
from typing import Any, Callable, Dict, List, Tuple, TypedDict, Union, cast

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
    alter_table_final: str
    undecided: str
    final_info: str

class SQL_Delete_Update_Options(str, Enum):
    RESTRICT = "RESTRICT"
    CASCADE = "CASCADE"
    SET_NULL = "SET NULL"
    SET_DEFAULT = "SET DEFAULT"
    NO_ACTION = "NO ACTION"


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
    """Main work is done here by recursing the models and their fields and determine the method to use"""

    @classmethod
    def generate_the_code(cls) -> Tuple[str, str, str, str, List[str]]:
        """Development purposes: used for output at the end of the schema.sql
        to see which yml-attributes are still not handled
        Return values:
          pre_code: Type definitions etc., which should all appear before first table definitions
          table_name_code: All table definitions
          view_name_code: All view definitions, after all views, because of view field definition by sql
          alter_table_final_code: Changes on tables defining relations after, which should appear after all table/views definition to be sequence independant
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
                # "to",  # will be used for creating view-fields, but also replacement for fk-reference to id
                # "on_delete", # must have other name then the key-value-store one
                # "equal_fields", # Seems we need, see example_transactional.sql between meeting and groups?
                # "unique",  # still to design
            )
        )
        missing_handled_attributes = []
        pre_code: str = ""
        table_name_code: str = ""
        view_name_code: str = ""
        alter_table_final_code: str = ""
        final_info_code: str = ""

        for table_name, fields in MODELS.items():
            if table_name == "_migration_index":
                continue
            schema_zone_texts: SchemaZoneTexts = defaultdict(str)  # type: ignore

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
                    if (enum_ := fdata.get("enum")) or (
                        enum_ := fdata.get("items", {}).get("enum")
                    ):
                        pre_code += Helper.get_enum_type_definition(
                            table_name, fname, enum_
                        )
                    result = method_or_str(table_name, fname, fdata, type_)
                    for k, v in result.items():
                        schema_zone_texts[k] += v or ""  # type: ignore

            if code := schema_zone_texts["table"]:
                table_name_code += Helper.get_table_head(table_name)
                table_name_code += Helper.get_table_body_end(code) + "\n\n"
            if code := schema_zone_texts["alter_table"]:
                table_name_code += code + "\n"
            if code := schema_zone_texts["undecided"]:
                table_name_code += Helper.get_undecided_all(table_name, code)
            if code := schema_zone_texts["view"]:
                view_name_code += Helper.get_view_head(table_name)
                view_name_code += Helper.get_view_body_end(table_name, code)
            if code := schema_zone_texts["alter_table_final"]:
                alter_table_final_code += code + "\n"
            if code := schema_zone_texts["final_info"]:
                final_info_code += code + "\n"

        return (
            pre_code,
            table_name_code,
            view_name_code,
            alter_table_final_code,
            final_info_code,
            missing_handled_attributes,
        )

    @classmethod
    def get_method(
        cls, fname: str, fdata: Dict[str, Any]
    ) -> Tuple[Union[str, Callable[..., SchemaZoneTexts]], str]:
        if fdata.get("calculated"):
            return (
                f"    {fname} type:{fdata.get('type')} is marked as a calculated field\n",
                "",
            )
        if fname == "id":
            type_ = "primary_key"
            return (FIELD_TYPES[type_].get("method", "").__get__(cls), type_)
        if (
            (type_ := fdata.get("type", ""))
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
        tmpl = FIELD_TYPES[type_]["pg_type"]
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

    @classmethod
    def get_relation_type(
        cls, table_name: str, fname: str, fdata: Dict[str, Any], type_: str
    ) -> SchemaZoneTexts:
        text: SchemaZoneTexts = cls.get_schema_simple_types(
            table_name, fname, fdata, "number"
        )
        foreign_table, fk_columns = Helper.get_foreign_key_table_column(fdata)
        initially_deferred = ModelsHelper.is_fk_initially_deferred(
            table_name, foreign_table
        )
        text["alter_table_final"] = Helper.get_foreign_key_table_constraint(
            table_name, foreign_table, fname, fk_columns, initially_deferred
        )
        return text

    @classmethod
    def get_relation_list_n_1_type(
        cls, table_name: str, fname: str, ref_column: str, foreign_table: str, foreign_column: str, foreign_field: Dict[str, Any]
    ) -> SchemaZoneTexts:
        """
        Fields in view, values builded by SQL
        """
        table_letter = Helper.get_table_letter(table_name)
        letters = [table_letter]
        foreign_letter = Helper.get_table_letter(foreign_table, letters)
        foreign_table = Helper.get_table_name(foreign_table)
        return f"(select array_agg({foreign_letter}.{ref_column}) from {foreign_table} {foreign_letter} where {foreign_letter}.{foreign_column} = {table_letter}.{ref_column}) as {fname},\n"

    @classmethod
    def get_relation_list_type(
        cls, table_name: str, fname: str, fdata: Dict[str, Any], type_: str
    ) -> SchemaZoneTexts:
        """
        Infos to get:
          - n:1 this is always a view, tried to be self generated
          - n:m generate an intermediate table with id
          - required own key, required one of the referenced table to the own
          - reference
        """
        text: SchemaZoneTexts = {}
        foreign_table, foreign_column, foreign_field = ModelsHelper.get_field_definition_from_to(fdata.get("to"))
        if foreign_field["type"] == "relation" and not foreign_field.get("sql"):
            _, ref_column = Helper.get_foreign_key_table_column(fdata)
            text["view"] = cls.get_relation_list_n_1_type(table_name, fname, ref_column, foreign_table, foreign_column, foreign_field)
        text["final_info"] = f"{table_name}.{fname}: {foreign_table}.{foreign_column}: Type: {foreign_field['type']}, Required:{foreign_field.get('required', '-')} SQL: {bool(foreign_field.get('sql'))}\n"
        return text


class Helper:
    ref_compiled = compiled = re.compile(r"(^\w+\b).*?\((.*?)\)")
    FILE_TEMPLATE = dedent(
        """
        -- schema.sql for initial database setup OpenSlides
        -- Code generated. DO NOT EDIT.

        """
    )
    FIELD_TEMPLATE = string.Template(
        "    ${field_name} ${type}${primary_key}${required}${minimum}${minLength}${default},\n"
    )
    ENUM_DEFINITION_TEMPLATE = string.Template(
        dedent(
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
        )
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
    def get_table_letter(table_name: str, letters: List[str] = []) -> str:
        letter = Helper.get_table_name(table_name)[0]
        count = -1
        l = letter
        while True:
            if letter in letters:
                count += 1
                if count == 0:
                    l = "".join([part[0] for part in table_name.split("_")])[:2]
                    letter = l
                else:
                    letter = l + str(count)
            else:
                return letter

    @staticmethod
    def get_table_head(table_name: str) -> str:
        return f"\nCREATE TABLE IF NOT EXISTS {Helper.get_table_name(table_name)} (\n"

    @staticmethod
    def get_table_body_end(code: str) -> str:
        code = code[:-2] + "\n"  # last attribute line without ",", but with "\n"
        code += ");\n\n"
        return code

    @staticmethod
    def get_view_head(table_name: str) -> str:
        return f"\nCREATE OR REPLACE VIEW {Helper.get_view_name(table_name)} AS SELECT *,\n"

    @staticmethod
    def get_view_body_end(table_name: str, code: str) -> str:
        code = code[:-2] + "\n"  # last attribute line without ",", but with "\n"
        code += f"FROM {Helper.get_table_name(table_name)} {Helper.get_table_letter(table_name)};\n\n"
        return code

    @staticmethod
    def get_alter_table_final_code(code: str) -> str:
        return f"-- Alter table final relation commands\n{code}\n\n"

    @staticmethod
    def get_undecided_all(table_name: str, code: str) -> str:
        return (
            f"/*\n Fields without SQL definition for table {table_name}\n\n{code}\n*/\n"
        )

    @staticmethod
    def get_enum_type_name(
        table_name: str,
        fname: str,
    ) -> str:
        return f"enum_{table_name}_{fname}"

    @staticmethod
    def get_enum_type_definition(table_name: str, fname: str, enum_: List[Any]) -> str:
        # enums per type are always strings in postgres
        enumeration = ", ".join([f"'{str(item)}'" for item in enum_])
        subst = {
            "enum_type": Helper.get_enum_type_name(table_name, fname),
            "enumeration": enumeration,
        }
        return Helper.ENUM_DEFINITION_TEMPLATE.substitute(subst)

    @staticmethod
    def get_foreign_key_table_constraint(
        table_name: str,
        foreign_table: str,
        own_columns: Union[List[str], str],
        fk_columns: Union[List[str], str],
        initially_deferred: bool = False,
        delete_action: str = "",
        update_action: str = "",
        special_field_name: str = "",
    ) -> str:
        FOREIGN_KEY_TABLE_CONSTRAINT_TEMPLATE = string.Template(
            "ALTER TABLE ${own_table} ADD FOREIGN KEY(${own_columns}) REFERENCES ${foreign_table}(${fk_columns})${initially_deferred}"
        )

        if initially_deferred:
            text_initially_deferred = " INITIALLY DEFERRED"
        else:
            text_initially_deferred = ""
        if isinstance(own_columns, list):
            own_columns = "(" + ", ".join(own_columns) + ")"
        if isinstance(fk_columns, list):
            own_columns = "(" + ", ".join(fk_columns) + ")"
        own_table = Helper.get_table_name(table_name)
        foreign_table = Helper.get_table_name(foreign_table)
        result = FOREIGN_KEY_TABLE_CONSTRAINT_TEMPLATE.substitute(
            {
                "own_table": own_table,
                "foreign_table": foreign_table,
                "own_columns": own_columns,
                "fk_columns": fk_columns,
                "initially_deferred": text_initially_deferred,
            }
        )
        result += Helper.get_on_action_mode(delete_action, True)
        result += Helper.get_on_action_mode(update_action, False)
        result += ";\n"
        return result

    @staticmethod
    def get_on_action_mode(action: str, delete: bool) -> str:
        if action:
            if (actionUpper := action.upper()) in SQL_Delete_Update_Options:
                return f" ON {'DELETE' if delete else 'UPDATE'} {SQL_Delete_Update_Options(actionUpper)}"
            else:
                raise Exception(f"{action} is not a valid action mode")
        return ""

    @staticmethod
    def get_foreign_key_table_column(field: Dict[str, Any]) -> Tuple[str, str]:
        if reference := field.get("reference"):
            result = Helper.ref_compiled.search(reference)
            if result is None:
                return reference.strip(), "id"
            re_groups = result.groups()
            cols = re_groups[1]
            if cols:
                cols = ",".join([col.strip() for col in cols.split(",")])
            else:
                cols = "id"
            return re_groups[0], cols
        elif to := field.get("to"):
            return to.split("/")[0], "id"
        else:
            raise Exception("Relation field without reference and to")

    @staticmethod
    def get_initials(
        table_name: str, fname: str, type_: str, fdata: Dict[str, Any]
    ) -> Tuple[SubstDict, SchemaZoneTexts]:
        text: SchemaZoneTexts = {}
        flist: List[str] = [
            cast(str, form[1])
            for form in Formatter().parse(Helper.FIELD_TEMPLATE.template)
        ]
        subst: SubstDict = cast(SubstDict, {k: "" for k in flist})
        if (enum_ := fdata.get("enum")) or fdata.get("items"):
            subst_type = Helper.get_enum_type_name(table_name, fname)
            if not enum_:
                subst_type += "[]"
        else:
            subst_type = FIELD_TYPES[type_]["pg_type"]
        subst.update({"field_name": fname, "type": subst_type})
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


class ModelsHelper:
    @staticmethod
    def is_fk_initially_deferred(own_table: str, foreign_table: str) -> bool:
        """
        The "Initially deferred" in fk-definition is necessary,
        if 2 related tables require both the relation to the other table
        """

        def _first_to_second(t1: str, t2: str) -> bool:
            for field in MODELS[t1].values():
                if field.get("required") and field["type"].startswith("relation"):
                    ftable, _ = Helper.get_foreign_key_table_column(field)
                    if ftable == t2:
                        return True
            return False

        if _first_to_second(own_table, foreign_table):
            return _first_to_second(foreign_table, own_table)
        return False

    @staticmethod
    def get_field_definition_from_to(to: str) -> Tuple[str, str, Dict[str, Any]]:
        tname, fname = to.split("/")
        field = MODELS[tname][fname]
        return tname, fname, field


FIELD_TYPES: Dict[str, Dict[str, Any]] = {
    "string": {
        "pg_type": string.Template("varchar(${maxLength})"),
        "method": GenerateCodeBlocks.get_schema_simple_types,
    },
    "number": {
        "pg_type": "integer",
        "method": GenerateCodeBlocks.get_schema_simple_types,
    },
    "boolean": {
        "pg_type": "boolean",
        "method": GenerateCodeBlocks.get_schema_simple_types,
    },
    "JSON": {"pg_type": "jsonb", "method": GenerateCodeBlocks.get_schema_simple_types},
    "HTMLStrict": {
        "pg_type": "text",
        "method": GenerateCodeBlocks.get_schema_simple_types,
    },
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
    "relation": {"pg_type": "integer", "method": GenerateCodeBlocks.get_relation_type},
    "relation-list": {"pg_type": "integer[]", "method": GenerateCodeBlocks.get_relation_list_type},
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

    (
        pre_code,
        table_name_code,
        view_name_code,
        alter_table_code,
        final_info_code,
        missing_handled_attributes,
    ) = GenerateCodeBlocks.generate_the_code()
    with open(DESTINATION, "w") as dest:
        dest.write(Helper.FILE_TEMPLATE)
        dest.write("-- MODELS_YML_CHECKSUM = " + repr(checksum) + "\n")
        dest.write("-- Type definitions")
        dest.write(pre_code)
        dest.write("\n\n-- Table definitions")
        dest.write(table_name_code)
        dest.write("-- View definitions\n")
        dest.write(view_name_code)
        dest.write("-- Alter table relations\n")
        dest.write(alter_table_code)
        dest.write(
            f"\n/*   Relation-list infos \n{final_info_code}\n*/"
        )
        dest.write(
            f"\n/*   Missing attribute handling for {', '.join(missing_handled_attributes)} */"
        )
    print(f"Models file {DESTINATION} successfully created.")


if __name__ == "__main__":
    main()
