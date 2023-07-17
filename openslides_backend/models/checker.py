from collections import defaultdict
from decimal import InvalidOperation
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple, Type, cast

import fastjsonschema

from openslides_backend.migrations import get_backend_migration_index
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
    TextField,
    TimestampField,
)
from openslides_backend.models.helper import calculate_inherited_groups_helper
from openslides_backend.models.models import Meeting, Model
from openslides_backend.shared.patterns import (
    COLOR_PATTERN,
    DECIMAL_PATTERN,
    EXTENSION_REFERENCE_IDS_PATTERN,
    collection_and_id_from_fqid,
)
from openslides_backend.shared.schema import models_map_object

SCHEMA = fastjsonschema.compile(
    {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Schema for initial and example data.",
        **models_map_object,
    }
)

external_motion_fields = [
    "origin_id",
    "origin_meeting_id",
    "derived_motion_ids",
    "all_origin_ids",
    "all_derived_motion_ids",
]


class CheckException(Exception):
    pass


def check_string(value: Any) -> bool:
    return value is None or isinstance(value, str)


def check_color(value: Any) -> bool:
    return value is None or bool(isinstance(value, str) and COLOR_PATTERN.match(value))


def check_number(value: Any) -> bool:
    return value is None or type(value) == int


def check_float(value: Any) -> bool:
    return value is None or type(value) in (int, float)


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
    return value is None or bool(
        isinstance(value, str) and DECIMAL_PATTERN.match(value)
    )


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


checker_map: Dict[Type[Field], Callable[..., bool]] = {
    CharField: check_string,
    HTMLStrictField: check_string,
    HTMLPermissiveField: check_string,
    GenericRelationField: check_string,
    IntegerField: check_number,
    TimestampField: check_number,
    RelationField: check_number,
    FloatField: check_float,
    BooleanField: check_boolean,
    CharArrayField: check_string_list,
    GenericRelationListField: check_string_list,
    NumberArrayField: check_number_list,
    RelationListField: check_number_list,
    DecimalField: check_decimal,
    ColorField: check_color,
    JSONField: check_json,
    TextField: check_string,
}


class Checker:
    modes = ("internal", "external", "all")

    def __init__(
        self,
        data: Dict[str, Dict[str, Any]],
        mode: str = "all",
        migration_mode: str = "strict",
        repair: bool = False,
        fields_to_remove: Dict[str, List] = {},
    ) -> None:
        """
        The checker checks the data without access to datastore.
        It differentiates between import data from the same organization instance,
        typically using the meeting.clone action, or from another organization,
        typically the meeting.import action with data from OS3.
        To check all included collections, use 'all'. Typical usage is he check of
        the example-data.json.

        Mode:
        external: checks that there are no relations to collections
            outside the meeting, except users. The users must be included in data
            and will be imported as new users
        internal: assumes that all relations to collections outside
            the meeting are valid, because the original instance is the same.
            The integrity of this kind of relations is not checked, because there
            is no database involved in command line version. Users are not included
            in data, because they exist in same database.
        all: All collections are valid and has to be in the data

        Repair: Set missing fields with default value automatically.

        migration_mode:
        strict: only allow the current backend migration index
        permissive: also allow a lower migration index

        fields_to_remove:
            A dict with collection as key and a list of fieldnames to remove from instance.
            Works only with repair set.
            First use case: meeting.clone and meeting.import need to remove the fields
            origin_id and derived_motion_id, because they in the copy they are not forwarded.

        Not all collections must be given and missing fields are ignore, but
        required fields and fields with a default value must be present.
        """
        self.data = data
        self.mode = mode
        self.migration_mode = migration_mode
        self.repair = repair
        self.fields_to_remove = fields_to_remove

        meeting_collections = [
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
            "chat_message",
            "point_of_order_category",
        ]
        if self.mode == "all":
            self.allowed_collections = [
                "organization",
                "user",
                "organization_tag",
                "theme",
                "committee",
            ] + meeting_collections
        else:
            self.allowed_collections = meeting_collections
            # TODO: mediafile blob handling.
            self.allowed_collections.append("user")

        self.errors: List[str] = []

        self.template_prefixes: Dict[
            str, Dict[str, Tuple[str, int, int]]
        ] = defaultdict(dict)
        self.generate_template_prefixes()

    def check_migration_index(self) -> None:
        # Unfortunately, TypedDict does not support any kind of generic or pattern property to
        # distinguish between the MI and the collections, so we have to cast the field here
        migration_index = cast(int, self.data["_migration_index"])
        backend_mi = get_backend_migration_index()
        if migration_index > backend_mi:
            self.errors.append(
                f"The given migration index ({migration_index}) is higher than the backend ({backend_mi})."
            )
        elif self.migration_mode == "strict" and migration_index < backend_mi:
            self.errors.append(
                f"The given migration index ({migration_index}) is lower than the backend ({backend_mi})."
            )

    def get_model(self, collection: str) -> Model:
        ModelClass = model_registry[collection]
        return ModelClass()

    def get_fields(self, collection: str) -> Iterable[Field]:
        return self.get_model(collection).get_fields()

    def generate_template_prefixes(self) -> None:
        for collection in self.allowed_collections:
            for field in self.get_fields(collection):
                if not isinstance(field, BaseTemplateField):
                    continue
                field_name = field.get_template_field_name()
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
        self.check_migration_index()
        self.check_collections()
        for collection, models in self.data.items():
            if collection.startswith("_"):
                continue
            for id_, model in models.items():
                if model["id"] != int(id_):
                    self.errors.append(
                        f"{collection}/{id_}: Id must be the same as model['id']"
                    )
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
        c1 = set(
            collection
            for collection in self.data.keys()
            if not collection.startswith("_")
        )
        c2 = set(self.allowed_collections)
        err = "Collections in file do not match with models.py."
        if c1 - c2:
            err += f" Invalid collections: {', '.join(c1-c2)}."
            raise CheckException(err)

    def check_model(self, collection: str, model: Dict[str, Any]) -> None:
        if self.repair and collection in self.fields_to_remove:
            [model.pop(field, None) for field in self.fields_to_remove[collection]]

        errors = self.check_normal_fields(model, collection)

        if not errors:
            errors = self.check_template_fields(model, collection)

        if not errors:
            self.check_types(model, collection)
            self.check_relations(model, collection)
            self.check_calculated_fields(model, collection)

    def check_normal_fields(self, model: Dict[str, Any], collection: str) -> bool:
        model_fields = set(
            x
            for x in model.keys()
            if self.is_normal_field(x) or self.is_template_field(x)
        )
        all_collection_fields = set(
            field.get_own_field_name() for field in self.get_fields(collection)
        )
        required_or_default_collection_fields = set(
            field.get_own_field_name()
            for field in self.get_fields(collection)
            if field.required or field.default is not None
        )

        errors = False
        if diff := required_or_default_collection_fields - model_fields:
            if self.repair:
                diff = self.fix_missing_default_values(model, collection, diff)
            if diff:
                error = f"{collection}/{model['id']}: Missing fields {', '.join(diff)}"
                self.errors.append(error)
                errors = True
        if diff := model_fields - all_collection_fields:
            error = f"{collection}/{model['id']}: Invalid fields {', '.join(f'{field} (value: {model[field]})' for field in diff)}"
            self.errors.append(error)
            errors = True

        for field in self.get_fields(collection):
            if (fieldname := field.get_own_field_name()) in model_fields:
                try:
                    field.validate(model[fieldname], model)
                except AssertionError as e:
                    error = f"{collection}/{model['id']}/{fieldname}: {str(e)}"
                    self.errors.append(error)
                    errors = True
                except InvalidOperation:
                    # invalide decimal json, will be checked at check_types
                    pass
        return errors

    def fix_missing_default_values(
        self, model: Dict[str, Any], collection: str, fieldnames: Set[str]
    ) -> Set[str]:
        remaining_fields = set()
        for fieldname in fieldnames:
            field = self.get_model(collection).get_field(fieldname)
            if field.default is not None:
                model[fieldname] = field.default
            else:
                remaining_fields.add(fieldname)
        return remaining_fields

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
            replacements = model.get(template_field.get_template_field_name())

            if replacements is None:
                replacements = []

            if not isinstance(replacements, list):
                self.errors.append(
                    f"{collection}/{model['id']}/{template_field.get_own_field_name()}: Replacements for the template field must be a list"
                )
                field_error = True
                continue
            for replacement in replacements:
                if not isinstance(replacement, str):
                    self.errors.append(
                        f"{collection}/{model['id']}/{template_field.get_own_field_name()}: Each replacement for the template field must be a string"
                    )
                    field_error = True
            if field_error:
                errors = True
                continue
            replacement_collection = None
            if template_field.replacement_collection:
                replacement_collection = template_field.replacement_collection

            for replacement in replacements:
                structured_field = self.make_structured(template_field, replacement)
                if model.get(structured_field) is None:
                    self.errors.append(
                        f"{collection}/{model['id']}/{template_field.get_own_field_name()}: Missing {structured_field} since it is given as a replacement"
                    )
                    errors = True

                if replacement_collection:
                    try:
                        as_id = int(replacement)
                    except (TypeError, ValueError):
                        self.errors.append(
                            f"{collection}/{model['id']}/{template_field.get_own_field_name()}: Replacement {replacement} is not an integer"
                        )
                    if not self.find_model(replacement_collection, as_id):
                        self.errors.append(
                            f"{collection}/{model['id']}/{template_field.get_own_field_name()}: Replacement {replacement} does not exist as a model of collection {replacement_collection}"
                        )

            if template_field.replacement_enum:
                replacement_enum = template_field.replacement_enum
                for replacement in replacements:
                    if replacement not in replacement_enum:
                        self.errors.append(
                            f"{collection}/{model['id']}/{template_field.get_own_field_name()}: Replacement {replacement} does not match replacement_enum {replacement_enum}"
                        )

            for field in model.keys():
                if self.is_structured_field(field) and model[field]:
                    try:
                        _template_field, _replacement = self.to_template_field(
                            collection, field
                        )
                        if (
                            template_field.get_own_field_name() == _template_field
                            and _replacement not in model.get(_template_field, [])
                        ):
                            self.errors.append(
                                f"{collection}/{model['id']}/{field}: Invalid structured field. Missing replacement {_replacement} in {template_field.get_own_field_name()}"
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
            for _type in type(field_type).mro():
                if _type in checker_map:
                    checker = checker_map[_type]
                    break
            else:
                raise NotImplementedError(
                    f"TODO implement check for field type {field_type}"
                )

            if not checker(model[field]):
                error = f"{collection}/{model['id']}/{field}: Type error: Type is not {field_type}"
                self.errors.append(error)

            # check if required field is not empty
            # committee_id is a special case, because it is filled after the
            # replacement
            # is_active_in_organization_id is also skipped, see PR #901
            skip_fields = (Meeting.committee_id, Meeting.is_active_in_organization_id)
            if (
                field_type.required
                and field_type.check_required_not_fulfilled(model, False)
                and field_type not in skip_fields
            ):
                error = f"{collection}/{model['id']}/{field}: Field required but empty."
                self.errors.append(error)

            if enum and model[field] not in enum:
                error = f"{collection}/{model['id']}/{field}: Value error: Value {model[field]} is not a valid enum value"
                self.errors.append(error)

    def get_type_from_collection(self, field: str, collection: str) -> Field:
        if self.is_structured_field(field):
            field, _ = self.to_template_field(collection, field)

        field_type = self.get_model(collection).get_field(field)
        return field_type

    def get_enum_from_collection_field(
        self, field: str, collection: str
    ) -> Optional[Set[str]]:
        if self.is_structured_field(field):
            field, _ = self.to_template_field(collection, field)

        field_type = self.get_model(collection).get_field(field)
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

        if collection == "user" and field == "organization_id":
            return

        if isinstance(field_type, RelationField):
            foreign_id = model[field]
            if not foreign_id:
                return

            foreign_collection, foreign_field = self.get_to(field, collection)

            if foreign_collection in self.allowed_collections:
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
            elif self.mode == "external":
                self.errors.append(
                    f"{basemsg} points to {foreign_collection}/{foreign_id}, which is not allowed in an external import."
                )
        elif isinstance(field_type, RelationListField):
            foreign_ids = model[field]
            if not foreign_ids:
                return

            foreign_collection, foreign_field = self.get_to(field, collection)

            if foreign_collection in self.allowed_collections:
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
            elif self.mode == "external":
                self.errors.append(
                    f"{basemsg} points to {foreign_collection}/{foreign_field}, which is not allowed in an external import."
                )

        elif isinstance(field_type, GenericRelationField) and model[field] is not None:
            foreign_collection, foreign_id = self.split_fqid(model[field])
            foreign_field = self.get_to_generic_case(
                collection, field, foreign_collection
            )

            if foreign_collection in self.allowed_collections:
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
            elif self.mode == "external":
                self.errors.append(
                    f"{basemsg} points to {foreign_collection}/{foreign_id}, which is not allowed in an external import."
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
                if foreign_collection in self.allowed_collections:
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
                elif self.mode == "external":
                    self.errors.append(
                        f"{basemsg} points to {foreign_collection}/{foreign_id}, which is not allowed in an external import."
                    )

        elif collection == "motion":
            for prefix in ("state", "recommendation"):
                if field == f"{prefix}_extension" and (
                    value := model.get(f"{prefix}_extension")
                ):
                    matches = EXTENSION_REFERENCE_IDS_PATTERN.findall(value)
                    for fqid in matches:
                        re_collection, re_id = collection_and_id_from_fqid(fqid)
                        if re_collection != "motion":
                            self.errors.append(
                                basemsg + f"Found {fqid} but only motion is allowed."
                            )
                        if not self.find_model(re_collection, int(re_id)):
                            self.errors.append(
                                basemsg
                                + f"Found {fqid} in {prefix}_extension but not in models."
                            )

    def get_to(self, field: str, collection: str) -> Tuple[str, Optional[str]]:
        if self.is_structured_field(field):
            field, _ = self.to_template_field(collection, field)

        field_type = cast(
            BaseRelationField, self.get_model(collection).get_field(field)
        )
        return (
            field_type.get_target_collection(),
            field_type.to.get(field_type.get_target_collection()),
        )

    def check_calculated_fields(
        self,
        model: Dict[str, Any],
        collection: str,
    ) -> None:
        if collection != "mediafile":
            return

        access_group_ids = model.get("access_group_ids")
        parent_is_public = None
        parent_inherited_access_group_ids = None
        if model.get("parent_id"):
            parent = self.find_model(collection, model["parent_id"])
            # relations are checked beforehand, so parent always exists
            assert parent
            parent_is_public = parent["is_public"]
            parent_inherited_access_group_ids = parent["inherited_access_group_ids"]
        is_public, inherited_access_group_ids = calculate_inherited_groups_helper(
            access_group_ids, parent_is_public, parent_inherited_access_group_ids
        )
        if is_public != model["is_public"]:
            self.errors.append(
                f"{collection}/{model['id']}: is_public is wrong. {is_public} != {model['is_public']}"
            )
        if set(inherited_access_group_ids) != set(
            model.get("inherited_access_group_ids") or []
        ):
            self.errors.append(
                f"{collection}/{model['id']}: inherited_access_group_ids is wrong"
            )

    def find_model(self, collection: str, id: int) -> Optional[Dict[str, Any]]:
        return self.data.get(collection, {}).get(str(id))

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
                    replacement = model.get(f"{replacement_collection}_id")
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
                " but the reverse relation for it is corrupt"
            )

    def split_fqid(self, fqid: str) -> Tuple[str, int]:
        try:
            collection, _id = fqid.split("/")
            id = int(_id)
            if self.mode == "external" and collection not in self.allowed_collections:
                raise CheckException(f"Fqid {fqid} has an invalid collection")
            return collection, id
        except (ValueError, AttributeError):
            raise CheckException(f"Fqid {fqid} is malformed")

    def split_collectionfield(self, collectionfield: str) -> Tuple[str, str]:
        collection, field = collectionfield.split("/")
        if collection not in self.allowed_collections:
            raise CheckException(
                f"Collectionfield {collectionfield} has an invalid collection"
            )
        if field not in [
            field.get_own_field_name() for field in self.get_fields(collection)
        ]:
            raise CheckException(
                f"Collectionfield {collectionfield} has an invalid field"
            )
        return collection, field

    def get_to_generic_case(
        self, collection: str, field: str, foreign_collection: str
    ) -> str:
        """Returns all reverse relations as collectionfields"""
        to = cast(BaseRelationField, self.get_model(collection).get_field(field)).to
        if isinstance(to, dict):
            if foreign_collection not in to.keys():
                raise CheckException(
                    f"The collection {foreign_collection} is not supported "
                    "as a reverse relation in {collection}/{field}"
                )
            return to[foreign_collection]

        for cf in to:
            c, f = self.split_collectionfield(cf.collection)
            if c == foreign_collection:
                return f

        raise CheckException(
            f"The collection {foreign_collection} is not supported as a reverse relation in {collection}/{field}"
        )
