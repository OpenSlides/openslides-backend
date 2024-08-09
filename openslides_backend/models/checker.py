import re
from collections.abc import Callable, Iterable
from decimal import InvalidOperation
from typing import Any, cast

import fastjsonschema

from openslides_backend.migrations import get_backend_migration_index
from openslides_backend.models.base import model_registry
from openslides_backend.models.fields import (
    BaseRelationField,
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
from openslides_backend.shared.schema import (
    models_map_object,
    number_string_json_schema,
    schema_version,
)
from openslides_backend.shared.util import ALLOWED_HTML_TAGS_STRICT, validate_html

SCHEMA = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "title": "Schema for initial and example data.",
        **models_map_object,
    }
)
NUMBER_STRING_JSON_SCHEMA = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "title": "Schema for amendment paragraph",
        **number_string_json_schema,
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
    return value is None or isinstance(value, int)


def check_float(value: Any) -> bool:
    return value is None or isinstance(value, (int, float))


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


checker_map: dict[type[Field], Callable[..., bool]] = {
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


# All meeting internal collection have the field `meeting_id` except for meeting and mediafile.
# Users are needed for working relations.
MEETING_COLLECTIONS = {
    collection
    for collection, model in model_registry.items()
    if model().has_field("meeting_id")
} | {"meeting", "user", "mediafile"}


class Checker:
    modes = ("internal", "external", "all")

    def __init__(
        self,
        data: dict[str, dict[str, Any]],
        mode: str = "all",
        migration_mode: str = "strict",
        repair: bool = False,
        fields_to_remove: dict[str, list] = {},
    ) -> None:
        """
        The checker checks the data without access to datastore.
        It differentiates between import data from the same organization instance,
        typically using the meeting.clone action, or from another organization,
        typically the meeting.import action with data from OS3.
        To check all included collections, use 'all'. Typical usage is the check of
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
        all: All collections are valid and have to be present in the data

        Repair: Set missing fields with default value automatically.

        migration_mode:
        strict: only allow the current backend migration index
        permissive: also allow a lower migration index

        fields_to_remove:
            A dict with collection as key and a list of fieldnames to remove from instance.
            Works only with repair set.
            First use case: meeting.clone and meeting.import need to remove the fields
            origin_id and derived_motion_id, because in the copy they are not forwarded.

        Not all collections must be given and missing fields are ignored, but
        required fields and fields with a default value must be present.
        """
        self.data = data
        self.mode = mode
        self.migration_mode = migration_mode
        self.repair = repair
        self.fields_to_remove = fields_to_remove
        self.allowed_collections = (
            set(model_registry.keys()) if self.mode == "all" else MEETING_COLLECTIONS
        )
        # TODO: mediafile blob handling.
        self.errors: list[str] = []

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
        given_collections = {
            collection
            for collection in self.data.keys()
            if not collection.startswith("_")
        }
        if diff := given_collections - self.allowed_collections:
            err = f"Collections in file do not match with models.py. Invalid collections: {', '.join(diff)}."
            raise CheckException(err)

    def check_model(self, collection: str, model: dict[str, Any]) -> None:
        if self.repair and collection in self.fields_to_remove:
            [model.pop(field, None) for field in self.fields_to_remove[collection]]

        errors = self.check_normal_fields(model, collection)

        if not errors:
            self.check_types(model, collection)
            self.check_special_fields(model, collection)
            self.check_relations(model, collection)
            self.check_calculated_fields(model, collection)

    def check_normal_fields(self, model: dict[str, Any], collection: str) -> bool:
        model_fields = model.keys()
        all_collection_fields = {
            field.get_own_field_name() for field in self.get_fields(collection)
        }
        required_or_default_collection_fields = {
            field.get_own_field_name()
            for field in self.get_fields(collection)
            if field.required or field.default is not None
        }

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
        self, model: dict[str, Any], collection: str, fieldnames: set[str]
    ) -> set[str]:
        remaining_fields = set()
        for fieldname in fieldnames:
            field = self.get_model(collection).get_field(fieldname)
            if field.default is not None:
                model[fieldname] = field.default
            else:
                remaining_fields.add(fieldname)
        return remaining_fields

    def check_types(self, model: dict[str, Any], collection: str) -> None:
        for field in model.keys():
            field_type = self.get_type_from_collection(field, collection)
            enum = self.get_enum_from_collection_field(field, collection)

            checker: Callable[..., bool] | None = None
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
        return self.get_model(collection).get_field(field)

    def get_enum_from_collection_field(
        self, field: str, collection: str
    ) -> set[str] | None:
        field_type = self.get_model(collection).get_field(field)
        return field_type.constraints.get("enum")

    def check_special_fields(self, model: dict[str, Any], collection: str) -> None:
        if collection != "motion":
            return
        if "amendment_paragraphs" in model:
            msg = f"{collection}/{model['id']}/amendment_paragraphs error: "
            try:
                NUMBER_STRING_JSON_SCHEMA(model["amendment_paragraphs"])
            except fastjsonschema.exceptions.JsonSchemaException as e:
                self.errors.append(
                    msg + str(e),
                )
                return
            for key, html in model["amendment_paragraphs"].items():
                if model["amendment_paragraphs"][key] != validate_html(
                    html, ALLOWED_HTML_TAGS_STRICT
                ):
                    self.errors.append(msg + f"Invalid html in {key}")
        if "recommendation_extension" in model:
            basemsg = (
                f"{collection}/{model['id']}/recommendation_extension: Relation Error: "
            )
            RECOMMENDATION_EXTENSION_REFERENCE_IDS_PATTERN = re.compile(
                r"\[(?P<fqid>\w+/\d+)\]"
            )
            recommendation_extension = model["recommendation_extension"]
            if recommendation_extension is None:
                recommendation_extension = ""

            possible_rerids = RECOMMENDATION_EXTENSION_REFERENCE_IDS_PATTERN.findall(
                recommendation_extension
            )
            for fqid_str in possible_rerids:
                re_collection, re_id_ = collection_and_id_from_fqid(fqid_str)
                if re_collection != "motion":
                    self.errors.append(
                        basemsg + f"Found {fqid_str} but only motion is allowed."
                    )
                if not self.find_model(re_collection, int(re_id_)):
                    self.errors.append(
                        basemsg
                        + f"Found {fqid_str} in recommendation_extension but not in models."
                    )

    def check_relations(self, model: dict[str, Any], collection: str) -> None:
        for field in model.keys():
            try:
                self.check_relation(model, collection, field)
            except CheckException as e:
                self.errors.append(
                    f"{collection}/{model['id']}/{field} error: " + str(e)
                )

    def check_relation(
        self, model: dict[str, Any], collection: str, field: str
    ) -> None:
        field_type = self.get_type_from_collection(field, collection)
        basemsg = f"{collection}/{model['id']}/{field}: Relation Error: "

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
                    foreign_collection,
                    foreign_id,
                    foreign_field,
                    basemsg,
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
                        foreign_collection,
                        foreign_id,
                        foreign_field,
                        basemsg,
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
                    foreign_collection,
                    foreign_id,
                    foreign_field,
                    basemsg,
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
                        foreign_collection,
                        foreign_id,
                        foreign_field,
                        basemsg,
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

    def get_to(self, field: str, collection: str) -> tuple[str, str | None]:
        field_type = cast(
            BaseRelationField, self.get_model(collection).get_field(field)
        )
        return (
            field_type.get_target_collection(),
            field_type.to.get(field_type.get_target_collection()),
        )

    def check_calculated_fields(
        self,
        model: dict[str, Any],
        collection: str,
    ) -> None:
        if collection != "meeting_mediafile":
            return

        source_model = self.find_model("mediafile", model["mediafile_id"])

        access_group_ids = model.get("access_group_ids")
        parent_is_public = None
        parent_inherited_access_group_ids = None
        if source_model and source_model.get("parent_id"):
            source_parent = self.find_model("mediafile", source_model["parent_id"])
            meeting = self.find_model("meeting", model["meeting_id"])
            # relations are checked beforehand, so parent always exists
            assert source_parent
            assert meeting
            parent_ids = set(meeting.get("meeting_mediafile_ids", [])).intersection(
                source_parent.get("meeting_mediafile_ids", [])
            )
            assert len(parent_ids) <= 1
            if len(parent_ids):
                parent = self.find_model(collection, parent_ids.pop())
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

    def find_model(self, collection: str, id: int) -> dict[str, Any] | None:
        return self.data.get(collection, {}).get(str(id))

    def check_reverse_relation(
        self,
        collection: str,
        id: int,
        foreign_collection: str,
        foreign_id: int,
        foreign_field: str | None,
        basemsg: str,
    ) -> None:
        if foreign_field is None:
            raise ValueError("Foreign field is None.")
        foreign_field_type = self.get_type_from_collection(
            foreign_field, foreign_collection
        )
        actual_foreign_field = foreign_field
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

    def split_fqid(self, fqid: str) -> tuple[str, int]:
        try:
            collection, _id = fqid.split("/")
            id = int(_id)
            if self.mode == "external" and collection not in self.allowed_collections:
                raise CheckException(f"Fqid {fqid} has an invalid collection")
            return collection, id
        except (ValueError, AttributeError):
            raise CheckException(f"Fqid {fqid} is malformed")

    def split_collectionfield(self, collectionfield: str) -> tuple[str, str]:
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
