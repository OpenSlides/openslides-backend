import argparse
import os
import string
import subprocess
from collections import ChainMap
from io import StringIO, TextIOBase
from textwrap import dedent
from typing import Any, Optional, cast

import requests
import yaml

from openslides_backend.models.base import Model as BaseModel
from openslides_backend.models.fields import OnDelete
from openslides_backend.models.mixins import (
    AgendaItemModelMixin,
    MeetingModelMixin,
    PollModelMixin,
)
from openslides_backend.shared.patterns import KEYSEPARATOR, Collection

SOURCE = "./global/meta/models.yml"

ROOT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
)

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

MODELS: dict[str, dict[str, Any]] = {}


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
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", nargs="?", default=SOURCE)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    # Retrieve models.yml from call-parameter for testing purposes, local file or GitHub
    file = args.filename
    if os.path.isfile(file):
        with open(file, "rb") as x:
            models_yml = x.read()
    else:
        models_yml = requests.get(file).content

    # open output stream
    dest: TextIOBase
    if args.check:
        dest = StringIO()
    else:
        dest = open(DESTINATION, "w")

    # Load and parse models.yml
    global MODELS
    MODELS = yaml.safe_load(models_yml)
    with dest:
        dest.write(FILE_TEMPLATE)
        dest.write(
            "from .mixins import "
            + ", ".join(mixin.__name__ for mixin in MODEL_MIXINS.values())
            + "\n"
        )
        for collection, fields in MODELS.items():
            if collection.startswith("_"):
                continue
            model = Model(collection, fields)
            dest.write(model.get_code())

        if args.check:
            result = subprocess.run(
                ["black", "-c", cast(StringIO, dest).getvalue()],
                capture_output=True,
                text=True,
                cwd=ROOT,
            )
            result.check_returncode()
            with open(DESTINATION) as f:
                assert f.read() == result.stdout
            print("Models file up-to-date.")
        else:
            print(f"Models file {DESTINATION} successfully created.")


def get_model_field(collection: str, field_name: str) -> str | dict:
    """
    Helper function the get a specific model field. Used to create generic relations.
    """

    model = MODELS.get(collection)
    if model is None:
        raise ValueError(f"Collection {collection} does not exist.")
    value = model.get(field_name)
    if value is None:
        raise ValueError(f"Field {field_name} does not exist.")
    return value


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
            self.attributes[field_name] = Attribute(field)

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
    contraints: dict[str, Any]

    FIELD_TEMPLATE = string.Template(
        "    ${field_name} = fields.${field_class}(${properties})\n"
    )

    def __init__(self, value: str | dict) -> None:
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
                self.to = To(value.get("to", {}))
                self.on_delete = value.get("on_delete")
            else:
                assert self.type in COMMON_FIELD_CLASSES.keys(), (
                    "Invalid type: " + self.type
                )
            self.required = value.get("required", False)
            self.read_only = value.get("read_only", False)
            self.constant = value.get("constant", False)
            self.default = value.get("default")
            self.equal_fields = value.get("equal_fields")
            for k, v in value.items():
                if k not in (
                    "type",
                    "to",
                    "required",
                    "read_only",
                    "constant",
                    "default",
                    "on_delete",
                    "equal_fields",
                    "items",
                    "restriction_mode",
                ):
                    self.contraints[k] = v
                elif self.type in ("string[]", "number[]") and k == "items":
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
        if self.contraints:
            properties += f"constraints={repr(self.contraints)}, "
        if self.in_array_constraints and self.type in ("string[]", "number[]"):
            properties += f"in_array_constraints={repr(self.in_array_constraints)}"
        return self.FIELD_TEMPLATE.substitute(
            dict(
                field_name=field_name,
                field_class=field_class,
                properties=properties.rstrip(", "),
            )
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
