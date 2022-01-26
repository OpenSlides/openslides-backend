import hashlib
import os
import string
import sys
from collections import ChainMap
from textwrap import dedent, indent
from typing import Any, Dict, List, Optional, Union

import requests
import yaml

from openslides_backend.models.fields import OnDelete
from openslides_backend.shared.patterns import KEYSEPARATOR, Collection

SOURCE = "./global/meta/models.yml"

DESTINATION = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
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

FILE_TEMPLATE = dedent(
    """\
    # Code generated. DO NOT EDIT.

    from openslides_backend.models import fields
    from openslides_backend.models.base import Model
    from openslides_backend.shared.patterns import Collection
    """
)

MODELS: Dict[str, Dict[str, Any]] = {}


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
                type: structured-relation
                name: another_$_attribute
                replacement_collection: ...
                through:
                - ...
                - ...

        another_model:
          another_$_attribute:
            type: template
            replacement_collection: ...
            fields:
              type: relation-list
              to:
                collection: some_model
                field: some_attribute
    """

    global MODELS

    # Retrieve models.yml from call-parameter for testing purposes, local file or GitHub
    if len(sys.argv) > 1 and sys.argv[1] != "check":
        file = sys.argv[1]
    else:
        file = SOURCE

    if os.path.isfile(file):
        with open(file, "rb") as x:
            models_yml = x.read()
    else:
        models_yml = requests.get(file).content

    # calc checksum to assert the models.py is up-to-date
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
    with open(DESTINATION, "w") as dest:
        dest.write(FILE_TEMPLATE)
        dest.write("\nMODELS_YML_CHECKSUM = " + repr(checksum) + "\n")
        for collection, fields in MODELS.items():
            if collection == "_migration_index":
                continue
            model = Model(collection, fields)
            dest.write(model.get_code())

    print(f"Models file {DESTINATION} successfully created.")


def get_model_field(collection: str, field_name: str) -> Union[str, Dict]:
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
    attributes: Dict[str, "Attribute"]

    MODEL_TEMPLATE = string.Template(
        dedent(
            """

            class ${class_name}(Model):
                collection = Collection("${collection}")
                verbose_name = "${verbose_name}"

            """
        )
    )

    ADDITIONAL_MODEL_CODE = {
        "agenda_item": dedent(
            """
            AGENDA_ITEM = "common"
            INTERNAL_ITEM = "internal"
            HIDDEN_ITEM = "hidden"
            """
        ),
        "poll": dedent(
            """
            STATE_CREATED = "created"
            STATE_STARTED = "started"
            STATE_FINISHED = "finished"
            STATE_PUBLISHED = "published"

            TYPE_ANALOG = "analog"
            TYPE_NAMED = "named"
            TYPE_PSEUDOANONYMOUS = "pseudoanonymous"
            """
        ),
    }

    def __init__(self, collection: str, fields: Dict[str, Dict[str, Any]]) -> None:
        self.collection = collection
        assert collection
        self.attributes = {}
        for field_name, field in fields.items():
            if field.get("calculated"):
                continue
            self.attributes[field_name] = Attribute(field)

    def get_code(self) -> str:
        verbose_name = " ".join(self.collection.split("_"))
        code = self.MODEL_TEMPLATE.substitute(
            dict(
                class_name=self.get_class_name(),
                collection=self.collection,
                verbose_name=verbose_name,
            )
        )
        for field_name, attribute in self.attributes.items():
            code += attribute.get_code(field_name)
        code += indent(self.ADDITIONAL_MODEL_CODE.get(self.collection, ""), " " * 4)
        return code

    def get_class_name(self) -> str:
        return "".join([part.capitalize() for part in self.collection.split("_")])


class Attribute(Node):
    type: str
    replacement_collection: Optional[Collection] = None
    replacement_enum: Optional[List[str]] = None
    to: Optional["To"] = None
    fields: Optional["Attribute"] = None
    required: bool = False
    read_only: bool = False
    default: Any = None
    on_delete: Optional[OnDelete] = None
    equal_fields: Optional[Union[str, List[str]]] = None
    contraints: Dict[str, Any]

    is_template: bool = False

    FIELD_TEMPLATE = string.Template(
        "    ${field_name} = fields.${field_class}(${properties})\n"
    )

    def __init__(
        self, value: Union[str, Dict], is_inner_attribute: bool = False
    ) -> None:
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
            if self.type == "template":
                self.is_template = True
                replacement_str = value.get("replacement_collection")
                self.replacement_collection = (
                    Collection(replacement_str) if replacement_str else None
                )
                inner_value = value.get("fields")
                assert not is_inner_attribute and inner_value
                self.fields = type(self)(inner_value, is_inner_attribute=True)
                if self.fields.type in ("relation", "relation-list"):
                    self.replacement_enum = value.get("replacement_enum")
                    assert not self.replacement_collection or not self.replacement_enum
                    if self.replacement_enum:
                        self.required = self.fields.required
            else:
                if self.type in RELATION_FIELD_CLASSES.keys():
                    self.to = To(value.get("to", {}))
                    self.on_delete = value.get("on_delete")
                else:
                    assert self.type in COMMON_FIELD_CLASSES.keys(), (
                        "Invalid type: " + self.type
                    )
                self.required = value.get("required", False)
                self.read_only = value.get("read_only", False)
                self.default = value.get("default")
                self.equal_fields = value.get("equal_fields")
                for k, v in value.items():
                    if k not in (
                        "type",
                        "to",
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

    def get_code(self, field_name: str) -> str:
        structured_field_sign = field_name.find("$")
        if structured_field_sign == -1:
            assert not self.is_template
            return self.get_code_for_normal(field_name)
        assert self.is_template
        field_name = field_name.replace("$", "", 1)
        assert field_name.find("$") == -1
        return self.get_code_for_template(field_name, structured_field_sign)

    def get_code_for_normal(self, field_name: str) -> str:
        if field_name == "organization_id":
            field_class = "OrganizationField"
        else:
            field_class = self.FIELD_CLASSES[self.type]
        properties = ""
        if self.to:
            properties += self.to.get_properties()
        if self.on_delete:
            assert self.on_delete in [mode.value for mode in OnDelete]
            properties += f"on_delete=fields.OnDelete.{self.on_delete}, "
        if self.required:
            properties += "required=True, "
        if self.read_only:
            properties += "read_only=True, "
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

    def get_code_for_template(self, field_name: str, index: int) -> str:
        assert self.fields is not None
        field_class = f"Template{self.FIELD_CLASSES[self.fields.type]}"
        properties = f"index={index}, "
        if self.replacement_collection:
            properties += f"replacement_collection={repr(self.replacement_collection)},"
        if self.fields.to:
            properties += self.fields.to.get_properties()
        if self.fields.required:
            properties += "required=True,"
        if self.fields.on_delete:
            assert self.fields.on_delete in [mode.value for mode in OnDelete]
            properties += f"on_delete=fields.OnDelete.{self.fields.on_delete},"
        if self.contraints:
            properties += f"constraints={repr(self.contraints)},"
        if self.fields.contraints:
            properties += f"constraints={repr(self.fields.contraints)},"
        if self.replacement_enum:
            properties += f"replacement_enum={repr(self.replacement_enum)},"
        return self.FIELD_TEMPLATE.substitute(
            dict(field_name=field_name, field_class=field_class, properties=properties)
        )


class To(Node):
    to: Dict[Collection, str]  # collection <-> field_name

    def __init__(self, value: Union[str, Dict]) -> None:
        if isinstance(value, str):
            self.to = self.parse_collectionfield(value)
        elif isinstance(value, list):
            self.to = dict(ChainMap(*[self.parse_collectionfield(cf) for cf in value]))
        else:
            assert isinstance(value, dict)
            collections = value.get("collections")
            assert isinstance(collections, list)
            self.to = {Collection(c): value["field"] for c in collections}

    def parse_collectionfield(self, collectionfield: str) -> Dict[Collection, str]:
        """
        Parses the given collectionfield into its parts and returns a dict consisting of a single
        respective entry.
        """
        collection, field = collectionfield.split(KEYSEPARATOR)
        return {Collection(collection): field}

    def get_properties(self) -> str:
        return "to=" + repr(self.to) + ","


if __name__ == "__main__":
    main()
