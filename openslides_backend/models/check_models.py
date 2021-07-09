import json
import re
import sys
from collections import defaultdict
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple, Type, cast

import fastjsonschema

from openslides_backend.models.base import model_registry
from openslides_backend.models.fields import (
    BaseRelationField,
    BaseTemplateField,
    BooleanField,
    CharArrayField,
    CharField,
    ColorField,
    DecimalField,
    Field,
    FloatField,
    GenericRelationField,
    GenericRelationListField,
    HTMLPermissiveField,
    HTMLStrictField,
    IntegerField,
    JSONField,
    NumberArrayField,
    RelationField,
    RelationListField,
    TimestampField,
)
from openslides_backend.models.models import Model
from openslides_backend.shared.patterns import Collection

SCHEMA = fastjsonschema.compile(
    {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Schema for initial and example data.",
        "type": "object",
        "patternProperties": {
            "^[a-z_]+$": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"id": {"type": "number"}},
                    "required": ["id"],
                },
            }
        },
        "additionalProperties": False,
    }
)


class CheckException(Exception):
    pass


def check_string(value: Any) -> bool:
    return value is None or isinstance(value, str)


color_regex = re.compile("^#[0-9a-f]{6}$")


def check_color(value: Any) -> bool:
    return value is None or bool(isinstance(value, str) and color_regex.match(value))


def check_number(value: Any) -> bool:
    return value is None or isinstance(value, int)


def check_float(value: Any) -> bool:
    return value is None or isinstance(value, int) or isinstance(value, float)


def check_boolean(value: Any) -> bool:
    return value is None or value is False or value is True


def check_string_list(value: Any) -> bool:
    return check_x_list(value, check_string)


def check_number_list(value: Any) -> bool:
    return check_x_list(value, check_number)


def check_x_list(value: Any, fn: Callable) -> bool:
    if value is None:
        return True
    if not isinstance(value, list):
        return False
    return all([fn(sv) for sv in value])


def check_decimal(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        pattern = r"^-?(\d|[1-9]\d+)\.\d{6}$"
        if re.match(pattern, value):
            return True
    return False


def check_json(value: Any, root: bool = True) -> bool:
    if value is None:
        return True
    if not root and (isinstance(value, int) or isinstance(value, str)):
        return True
    if isinstance(value, list):
        return all(check_json(x, root=False) for x in value)
    if isinstance(value, dict):
        return all(check_json(x, root=False) for x in value.values())
    return False


class Checker:
    def __init__(self, data: Dict[str, List[Any]], is_import: bool = False) -> None:
        self.data = data

        self.models: Dict[str, Type["Model"]] = {
            collection.collection: model_registry[collection]
            for collection in model_registry
        }

        if is_import:
            self.modify_models_for_import()

        self.errors: List[str] = []

        self.template_prefixes: Dict[
            str, Dict[str, Tuple[str, int, int]]
        ] = defaultdict(dict)
        self.generate_template_prefixes()
        self.create_data_cache()

    def get_fields(self, collection: str) -> Iterable[Field]:
        return self.models[collection]().get_fields()

    def modify_models_for_import(self) -> None:
        collection_allowlist = (
            "user",
            "meeting",
            "group",
            "personal_note",
            "tag",
            "agenda_item",
            "list_of_speakers",
            "speaker",
            "topic",
            "motion",
            "motion_submitter",
            "motion_comment",
            "motion_comment_section",
            "motion_category",
            "motion_block",
            "motion_change_recommendation",
            "motion_state",
            "motion_workflow",
            "motion_statute_paragraph",
            "poll",
            "option",
            "vote",
            "assignment",
            "assignment_candidate",
            "mediafile",
            "projector",
            "projection",
            "projector_message",
            "projector_countdown",
            "chat_group",
        )
        for collection in list(self.models.keys()):
            if collection not in collection_allowlist:
                del self.models[collection]
        # TODO: mediafile blob handling.

    def generate_template_prefixes(self) -> None:
        for collection in self.models.keys():
            for field in self.get_fields(collection):
                if not isinstance(field, BaseTemplateField):
                    continue
                field_name = field.get_structured_field_name("")
                parts = field_name.split("$")
                prefix = parts[0]
                suffix = parts[1]
                if prefix in self.template_prefixes[collection]:
                    raise ValueError(
                        f"the template prefix {prefix} is not unique within {collection}"
                    )
                self.template_prefixes[collection][prefix] = (
                    field_name,
                    len(prefix),
                    len(suffix),
                )

    def create_data_cache(self) -> None:
        self.data_cache: Dict[str, Dict[int, Any]] = defaultdict(dict)
        for collection in self.data:
            for entry in self.data[collection]:
                self.data_cache[collection][int(entry["id"])] = entry

    def is_template_field(self, field: str) -> bool:
        return "$_" in field or field.endswith("$")

    def is_structured_field(self, field: str) -> bool:
        return "$" in field and not self.is_template_field(field)

    def is_normal_field(self, field: str) -> bool:
        return "$" not in field

    def make_structured(self, field: BaseTemplateField, replacement: Any) -> str:
        if type(replacement) not in (str, int):
            raise CheckException(
                f"Invalid type {type(replacement)} for the replacement of field {field}"
            )
        return field.get_structured_field_name(replacement)

    def to_template_field(
        self, collection: str, structured_field: str
    ) -> Tuple[str, str]:
        """Returns template_field, replacement"""
        parts = structured_field.split("$")
        descriptor = self.template_prefixes[collection].get(parts[0])
        if not descriptor:
            raise CheckException(
                f"Unknown template field for prefix {parts[0]} in collection {collection}"
            )
        return (
            descriptor[0],
            structured_field[descriptor[1] + 1 : len(structured_field) - descriptor[2]],
        )

    def run_check(self) -> None:
        self.check_json()
        self.check_collections()
        for collection, models in self.data.items():
            for model in models:
                self.check_model(collection, model)
        if self.errors:
            errors = [f"\t{error}" for error in self.errors]
            raise CheckException("\n".join(errors))

    def check_json(self) -> None:
        try:
            SCHEMA(self.data)
        except fastjsonschema.exceptions.JsonSchemaException as e:
            raise CheckException(f"JSON does not match schema: {str(e)}")

    def check_collections(self) -> None:
        c1 = set(self.data.keys())
        c2 = set(self.models.keys())
        if c1 != c2:
            err = "Collections in file do not match with models.py."
            if c2 - c1:
                err += f" Missing collections: {', '.join(c2-c1)}."
            if c1 - c2:
                err += f" Invalid collections: {', '.join(c1-c2)}."
            raise CheckException(err)

    def check_model(self, collection: str, model: Dict[str, Any]) -> None:
        errors = self.check_normal_fields(model, collection)

        if not errors:
            errors = self.check_template_fields(model, collection)

        if not errors:
            self.check_types(model, collection)
            self.check_relations(model, collection)

    def check_normal_fields(self, model: Dict[str, Any], collection: str) -> bool:
        model_fields = set(
            x
            for x in model.keys()
            if self.is_normal_field(x) or self.is_template_field(x)
        )
        collection_fields_types = (
            x
            for x in self.models[collection]().get_fields()
            if self.is_normal_field(x.own_field_name)
            or self.is_template_field(x.own_field_name)
        )
        collection_fields = set(
            field.own_field_name
            if not isinstance(field, BaseTemplateField)
            else field.get_structured_field_name("")
            for field in collection_fields_types
        )

        errors = False
        if collection_fields - model_fields:
            error = f"{collection}/{model['id']}: Missing fields {', '.join(collection_fields - model_fields)}"
            self.errors.append(error)
            errors = True
        if model_fields - collection_fields:
            error = f"{collection}/{model['id']}: Invalid fields {', '.join(model_fields - collection_fields)}"
            self.errors.append(error)
            errors = True
        return errors

    def check_template_fields(self, model: Dict[str, Any], collection: str) -> bool:
        """
        Only checks that for each replacement a structured field exists and
        not too many structured fields. Does not check the content.
        Returns True on errors.
        """
        errors = False
        for template_field in self.get_fields(collection):
            if not isinstance(template_field, BaseTemplateField):
                continue
            field_error = False
            replacements = model.get(template_field.get_structured_field_name(""))

            if not isinstance(replacements, list):
                self.errors.append(
                    f"{collection}/{model['id']}/{template_field.own_field_name}: Replacements for the template field must be a list"
                )
                field_error = True
                continue
            for replacement in replacements:
                if not isinstance(replacement, str):
                    self.errors.append(
                        f"{collection}/{model['id']}/{template_field.own_field_name}: Each replacement for the template field must be a string"
                    )
                    field_error = True
            if field_error:
                errors = True
                continue
            replacement_collection = None
            if template_field.replacement_collection:
                replacement_collection = (
                    template_field.replacement_collection.collection
                )

            for replacement in replacements:
                structured_field = self.make_structured(template_field, replacement)
                if structured_field not in model:
                    self.errors.append(
                        f"{collection}/{model['id']}/{template_field.own_field_name}: Missing {structured_field} since it is given as a replacement"
                    )
                    errors = True

                if replacement_collection:
                    try:
                        as_id = int(replacement)
                    except (TypeError, ValueError):
                        self.errors.append(
                            f"{collection}/{model['id']}/{template_field.own_field_name}: Replacement {replacement} is not an integer"
                        )
                    if not self.find_model(replacement_collection, as_id):
                        self.errors.append(
                            f"{collection}/{model['id']}/{template_field.own_field_name}: Replacement {replacement} does not exist as a model of collection {replacement_collection}"
                        )

            for field in model.keys():
                if self.is_structured_field(field):
                    try:
                        _template_field, _replacement = self.to_template_field(
                            collection, field
                        )
                        if (
                            template_field.own_field_name == _template_field
                            and _replacement not in model[template_field.own_field_name]
                        ):
                            self.errors.append(
                                f"{collection}/{model['id']}/{field}: Invalid structured field. Missing replacement {_replacement} in {template_field.own_field_name}"
                            )
                            errors = True
                    except CheckException as e:
                        self.errors.append(
                            f"{collection}/{model['id']}/{field} error: " + str(e)
                        )
                        errors = True

        return errors

    def check_types(self, model: Dict[str, Any], collection: str) -> None:
        for field in model.keys():
            if self.is_template_field(field):
                continue

            field_type = self.get_type_from_collection(field, collection)
            enum = self.get_enum_from_collection_field(field, collection)

            checker: Optional[Callable[..., bool]] = None
            if isinstance(field_type, CharField):
                checker = check_string
            elif isinstance(field_type, HTMLStrictField):
                checker = check_string
            elif isinstance(field_type, HTMLPermissiveField):
                checker = check_string
            elif isinstance(field_type, GenericRelationField):
                checker = check_string
            elif isinstance(field_type, IntegerField):
                checker = check_number
            elif isinstance(field_type, TimestampField):
                checker = check_number
            elif isinstance(field_type, RelationField):
                checker = check_number
            elif isinstance(field_type, FloatField):
                checker = check_float
            elif isinstance(field_type, BooleanField):
                checker = check_boolean
            elif isinstance(field_type, CharArrayField):
                checker = check_string_list
            elif isinstance(field_type, GenericRelationListField):
                checker = check_string_list
            elif isinstance(field_type, NumberArrayField):
                checker = check_number_list
            elif isinstance(field_type, RelationListField):
                checker = check_number_list
            elif isinstance(field_type, DecimalField):
                checker = check_decimal
            elif isinstance(field_type, ColorField):
                checker = check_color
            elif isinstance(field_type, JSONField):
                checker = check_json
            else:
                raise NotImplementedError(
                    f"TODO implement check for field type {field_type}"
                )

            if not checker(model[field]):
                error = f"{collection}/{model['id']}/{field}: Type error: Type is not {field_type}"
                self.errors.append(error)

            if enum and model[field] not in enum:
                error = f"{collection}/{model['id']}/{field}: Value error: Value {model[field]} is not a valid enum value"
                self.errors.append(error)

    def get_type_from_collection(self, field: str, collection: str) -> Field:
        if self.is_structured_field(field):
            field, _ = self.to_template_field(collection, field)

        field_type = self.models[collection]().get_field(field)
        return field_type

    def get_enum_from_collection_field(
        self, field: str, collection: str
    ) -> Optional[Set[str]]:
        if self.is_structured_field(field):
            field, _ = self.to_template_field(collection, field)

        field_type = self.models[collection]().get_field(field)
        return field_type.constraints.get("enum")

    def check_relations(self, model: Dict[str, Any], collection: str) -> None:
        for field in model.keys():
            try:
                self.check_relation(model, collection, field)
            except CheckException as e:
                self.errors.append(
                    f"{collection}/{model['id']}/{field} error: " + str(e)
                )

    def check_relation(
        self, model: Dict[str, Any], collection: str, field: str
    ) -> None:
        if self.is_template_field(field):
            return

        field_type = self.get_type_from_collection(field, collection)
        basemsg = f"{collection}/{model['id']}/{field}: Relation Error: "

        replacement = None
        if self.is_structured_field(field):
            _, replacement = self.to_template_field(collection, field)

        if isinstance(field_type, RelationField):
            foreign_id = model[field]
            if foreign_id is None:
                return

            foreign_collection, foreign_field = self.get_to(field, collection)

            self.check_reverse_relation(
                collection,
                model["id"],
                model,
                foreign_collection,
                foreign_id,
                foreign_field,
                basemsg,
                replacement,
            )

        elif isinstance(field_type, RelationListField):
            foreign_ids = model[field]
            if foreign_ids is None:
                return

            foreign_collection, foreign_field = self.get_to(field, collection)

            for foreign_id in foreign_ids:
                self.check_reverse_relation(
                    collection,
                    model["id"],
                    model,
                    foreign_collection,
                    foreign_id,
                    foreign_field,
                    basemsg,
                    replacement,
                )

        elif isinstance(field_type, GenericRelationField) and model[field] is not None:
            foreign_collection, foreign_id = self.split_fqid(model[field])
            foreign_field = self.get_to_generic_case(
                collection, field, foreign_collection
            )

            self.check_reverse_relation(
                collection,
                model["id"],
                model,
                foreign_collection,
                foreign_id,
                foreign_field,
                basemsg,
                replacement,
            )

        elif (
            isinstance(field_type, GenericRelationListField)
            and model[field] is not None
        ):
            for fqid in model[field]:
                foreign_collection, foreign_id = self.split_fqid(fqid)
                foreign_field = self.get_to_generic_case(
                    collection, field, foreign_collection
                )

                self.check_reverse_relation(
                    collection,
                    model["id"],
                    model,
                    foreign_collection,
                    foreign_id,
                    foreign_field,
                    basemsg,
                    replacement,
                )

    def get_to(self, field: str, collection: str) -> Tuple[str, Optional[str]]:
        if self.is_structured_field(field):
            field, _ = self.to_template_field(collection, field)

        field_type = cast(BaseRelationField, self.models[collection]().get_field(field))
        return (
            field_type.get_target_collection().collection,
            field_type.to.get(field_type.get_target_collection()),
        )

    def find_model(self, collection: str, id: int) -> Optional[Dict[str, Any]]:
        collection_dict = self.data_cache.get(collection, {})
        return collection_dict.get(id)

    def check_reverse_relation(
        self,
        collection: str,
        id: int,
        model: Dict[str, Any],
        foreign_collection: str,
        foreign_id: int,
        foreign_field: Optional[str],
        basemsg: str,
        replacement: Optional[str],
    ) -> None:
        if foreign_field is None:
            raise ValueError("Foreign field is None.")
        foreign_field_type = self.get_type_from_collection(
            foreign_field, foreign_collection
        )
        actual_foreign_field = foreign_field
        if self.is_template_field(foreign_field):
            if replacement:
                actual_foreign_field = cast(
                    BaseTemplateField, foreign_field_type
                ).get_structured_field_name(replacement)
            else:
                replacement_collection = cast(
                    BaseTemplateField, foreign_field_type
                ).replacement_collection
                if replacement_collection:
                    replacement = model.get(f"{replacement_collection.collection}_id")
                if not replacement:
                    self.errors.append(
                        f"{basemsg} points to {foreign_collection}/{foreign_id}/{foreign_field},"
                        f" but there is no replacement for {replacement_collection}"
                    )
                actual_foreign_field = self.make_structured(
                    cast(BaseTemplateField, foreign_field_type), replacement
                )

        foreign_model = self.find_model(foreign_collection, foreign_id)
        foreign_value = (
            foreign_model.get(actual_foreign_field)
            if foreign_model is not None
            else None
        )
        fqid = f"{collection}/{id}"
        error = False
        if isinstance(foreign_field_type, RelationField):
            error = foreign_value != id
        elif isinstance(foreign_field_type, RelationListField):
            error = not foreign_value or id not in foreign_value
        elif isinstance(foreign_field_type, GenericRelationField):
            error = foreign_value != fqid
        elif isinstance(foreign_field_type, GenericRelationListField):
            error = not foreign_value or fqid not in foreign_value
        else:
            raise NotImplementedError()

        if error:
            self.errors.append(
                f"{basemsg} points to {foreign_collection}/{foreign_id}/{actual_foreign_field},"
                " but the reverse relation for is corrupt"
            )

    def split_fqid(self, fqid: str) -> Tuple[str, int]:
        try:
            collection, _id = fqid.split("/")
            id = int(_id)
            if collection not in self.models.keys():
                raise CheckException(f"Fqid {fqid} has an invalid collection")
            return collection, id
        except (ValueError, AttributeError):
            raise CheckException(f"Fqid {fqid} is malformed")

    def split_collectionfield(self, collectionfield: str) -> Tuple[str, str]:
        collection, field = collectionfield.split("/")
        if collection not in self.models.keys():
            raise CheckException(
                f"Collectionfield {collectionfield} has an invalid collection"
            )
        if field not in [
            field.own_field_name for field in self.models[collection]().get_fields()
        ]:  # Note: this has to be adopted when supporting template fields
            raise CheckException(
                f"Collectionfield {collectionfield} has an invalid field"
            )
        return collection, field

    def get_to_generic_case(
        self, collection: str, field: str, foreign_collection: str
    ) -> str:
        """Returns all reverse relations as collectionfields"""
        to = cast(BaseRelationField, self.models[collection]().get_field(field)).to
        if isinstance(to, dict):
            if Collection(foreign_collection) not in to.keys():
                raise CheckException(
                    f"The collection {foreign_collection} is not supported "
                    "as a reverse relation in {collection}/{field}"
                )
            return to[Collection(foreign_collection)]

        for cf in to:
            c, f = self.split_collectionfield(cf.collection)
            if c == foreign_collection:
                return f

        raise CheckException(
            f"The collection {foreign_collection} is not supported as a reverse relation in {collection}/{field}"
        )


def main() -> int:
    files = sys.argv[1:]

    is_import = "--import" in files
    if is_import:
        files = [x for x in files if x != "--import"]

    failed = False
    for f in files:
        with open(f) as data:
            try:
                Checker(json.load(data), is_import=is_import).run_check()
            except CheckException as e:
                print(f"Check for {f} failed:\n", e)
                failed = True
            else:
                print(f"Check for {f} successful.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
