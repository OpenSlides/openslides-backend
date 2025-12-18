from copy import deepcopy
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from unittest import TestCase

from psycopg.types.json import Jsonb

from openslides_backend.migrations import get_backend_migration_index
from openslides_backend.models.base import model_registry
from openslides_backend.models.checker import Checker, CheckException
from openslides_backend.models.fields import (
    BooleanField,
    CharArrayField,
    CharField,
    ColorField,
    DecimalField,
    FloatField,
    GenericRelationField,
    GenericRelationListField,
    HTMLPermissiveField,
    HTMLStrictField,
    IntegerField,
    RelationField,
    RelationListField,
    TextArrayField,
    TextField,
    TimestampField,
)
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

BACKEND_MIGRATION_INDEX = get_backend_migration_index()


class TestCheckerCheckMigrationIndex(TestCase):
    def check_migration_index(
        self,
        data: dict[str, Any],
        expected_error: str | None = None,
        migration_mode: Literal["strict", "permissive"] = "strict",
    ) -> None:
        try:
            Checker(
                data=data,
                mode="internal",
                migration_mode=migration_mode,
            ).run_check()
            self.assertIsNone(expected_error)
        except CheckException as ce:
            self.assertEqual(ce.args[0], expected_error)

    def test_migration_index_correct(self) -> None:
        self.check_migration_index({"_migration_index": BACKEND_MIGRATION_INDEX})
        self.check_migration_index(
            {"_migration_index": BACKEND_MIGRATION_INDEX - 1},
            migration_mode="permissive",
        )

    def test_migration_index_is_none_error(self) -> None:
        self.check_migration_index(
            data={"_migration_index": None},
            expected_error="JSON does not match schema: data._migration_index must be integer",
        )

    def test_no_migration_index_error(self) -> None:
        self.check_migration_index(
            data={},
            expected_error="JSON does not match schema: data must contain ['_migration_index'] properties",
        )

    def test_migration_index_too_small_error(self) -> None:
        self.check_migration_index(
            data={"_migration_index": 0},
            expected_error="JSON does not match schema: data._migration_index must be bigger than or equal to 1",
        )

    def test_migration_index_lower_than_backend_MI_permissive_mode(self) -> None:
        migration_index = BACKEND_MIGRATION_INDEX - 1
        self.check_migration_index(
            data={"_migration_index": migration_index},
            migration_mode="permissive",
        )

    def test_migration_index_higher_than_backend_MI_error(self) -> None:
        migration_index = BACKEND_MIGRATION_INDEX + 1
        msg = f"\tThe given migration index ({migration_index}) is higher than the backend ({BACKEND_MIGRATION_INDEX})."

        self.check_migration_index(
            data={"_migration_index": migration_index},
            expected_error=msg,
        )
        self.check_migration_index(
            data={"_migration_index": migration_index},
            expected_error=msg,
            migration_mode="permissive",
        )

    def test_migration_index_lower_than_backend_MI_error(self) -> None:
        migration_index = BACKEND_MIGRATION_INDEX - 1
        self.check_migration_index(
            data={"_migration_index": migration_index},
            expected_error=f"\tThe given migration index ({migration_index}) is lower than the backend ({BACKEND_MIGRATION_INDEX}).",
        )


class TestCheckerCheckData(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.migration_index: dict[str, Any] = {
            "_migration_index": BACKEND_MIGRATION_INDEX
        }
        self.theme_data: dict[str, Any] = {
            "organization": {"1": {"id": 1, "theme_id": 1, "theme_ids": [1]}},
            "theme": {
                "1": {
                    "id": 1,
                    "name": "Theme 1",
                    "organization_id": 1,
                    "theme_for_organization_id": 1,
                }
            },
        }
        self.meeting_data: dict[str, Any] = {
            "organization": {
                "1": {
                    "id": 1,
                    "theme_id": 1,
                    "theme_ids": [1],
                    "committee_ids": [1],
                    "active_meeting_ids": [1],
                }
            },
            "theme": {
                "1": {
                    "id": 1,
                    "name": "Theme 1",
                    "organization_id": 1,
                    "theme_for_organization_id": 1,
                }
            },
            "committee": {
                "1": {
                    "id": 1,
                    "name": "Committee 1",
                    "organization_id": 1,
                    "meeting_ids": [1],
                }
            },
            "meeting": {
                "1": {
                    "id": 1,
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                    "motions_default_amendment_workflow_id": 1,
                    "motions_default_workflow_id": 1,
                    "group_ids": [1],
                    "default_group_id": 1,
                    "projector_ids": [1],
                    "reference_projector_id": 1,
                    "default_projector_motion_poll_ids": [1],
                    "default_projector_message_ids": [1],
                    "default_projector_countdown_ids": [1],
                    "default_projector_agenda_item_list_ids": [1],
                    "default_projector_assignment_poll_ids": [1],
                    "default_projector_mediafile_ids": [1],
                    "default_projector_current_los_ids": [1],
                    "default_projector_motion_block_ids": [1],
                    "default_projector_topic_ids": [1],
                    "default_projector_list_of_speakers_ids": [1],
                    "default_projector_amendment_ids": [1],
                    "default_projector_assignment_ids": [1],
                    "default_projector_motion_ids": [1],
                    "default_projector_poll_ids": [1],
                    "motion_workflow_ids": [1],
                    "motion_state_ids": [1],
                }
            },
            "group": {
                "1": {
                    "id": 1,
                    "meeting_id": 1,
                    "name": "default",
                    "default_group_for_meeting_id": 1,
                }
            },
            "projector": {
                "1": {
                    "id": 1,
                    "meeting_id": 1,
                    "used_as_reference_projector_meeting_id": 1,
                    "used_as_default_projector_for_agenda_item_list_in_meeting_id": 1,
                    "used_as_default_projector_for_topic_in_meeting_id": 1,
                    "used_as_default_projector_for_list_of_speakers_in_meeting_id": 1,
                    "used_as_default_projector_for_current_los_in_meeting_id": 1,
                    "used_as_default_projector_for_motion_in_meeting_id": 1,
                    "used_as_default_projector_for_amendment_in_meeting_id": 1,
                    "used_as_default_projector_for_motion_block_in_meeting_id": 1,
                    "used_as_default_projector_for_assignment_in_meeting_id": 1,
                    "used_as_default_projector_for_mediafile_in_meeting_id": 1,
                    "used_as_default_projector_for_message_in_meeting_id": 1,
                    "used_as_default_projector_for_countdown_in_meeting_id": 1,
                    "used_as_default_projector_for_assignment_poll_in_meeting_id": 1,
                    "used_as_default_projector_for_motion_poll_in_meeting_id": 1,
                    "used_as_default_projector_for_poll_in_meeting_id": 1,
                }
            },
            "motion_workflow": {
                "1": {
                    "id": 1,
                    "name": "flo",
                    "meeting_id": 1,
                    "first_state_id": 1,
                    "default_workflow_meeting_id": 1,
                    "default_amendment_workflow_meeting_id": 1,
                    "state_ids": [1],
                }
            },
            "motion_state": {
                "1": {
                    "id": 1,
                    "name": "stasis",
                    "weight": 1,
                    "meeting_id": 1,
                    "workflow_id": 1,
                    "first_state_of_workflow_id": 1,
                }
            },
        }
        self.organization_tag_data: dict[str, Any] = {
            "organization_tag": {
                "1": {
                    "id": 1,
                    "name": "test",
                    "color": "#11aaee",
                    "organization_id": 1,
                }
            }
        }
        self.extended_user_data: dict[str, Any] = {
            "user": {
                "1": {
                    "id": 1,
                    "organization_id": 1,
                    "username": "johndoe",
                    "default_vote_weight": Decimal("1.00000"),
                    "is_active": True,
                    "is_physical_person": True,
                    "can_change_own_password": False,
                    "committee_ids": [1],
                }
            }
        }

    def check_data(
        self,
        data: dict[str, Any],
        expected_error: str | list[str] | None = None,
        mode: Literal["internal", "external", "all"] = "all",
        repair: bool = True,
        fields_to_remove: dict[str, list[str]] = {},
    ) -> None:
        try:
            Checker(
                data=self.migration_index | data,
                mode=mode,
                repair=repair,
                fields_to_remove=fields_to_remove,
            ).run_check()
            self.assertIsNone(expected_error)
        except CheckException as ce:
            error_message = ce.args[0]
            if isinstance(expected_error, list):
                for message_part in expected_error:
                    self.assertIn(message_part, error_message)
            else:
                self.assertEqual(error_message, expected_error)

    # check_collections()
    def test_collections_do_not_match_models_error(self) -> None:
        invalid_collections = [
            "invalid_regular_collection",
            "another_one",
        ]
        self.check_data(
            data={collection: {} for collection in invalid_collections},
            repair=False,
            expected_error=[
                "Collections in file do not match with models.py. Invalid collections:",
            ]
            + invalid_collections,
        )

    def test_collections_do_not_match_meeting_models_error(self) -> None:
        self.check_data(
            data={"theme": {"1": {"id": 1}}},
            mode="internal",
            repair=False,
            expected_error="Collections in file do not match with models.py. Invalid collections: theme.",
        )

    # check id
    def test_id_mismatch_error(self) -> None:
        self.check_data(
            data={"theme": {"1": {"id": 2, "name": "Theme 1", "organization_id": 1}}},
            expected_error=["\ttheme/1: Id must be the same as model['id']"],
        )

    # check_normal_fields()
    def test_skipped_fields_error(self) -> None:
        invalid_data = {"accent_501": "#123432", "primary_499": "#83aa87"}
        self.theme_data["theme"]["1"].update(invalid_data)
        self.check_data(
            data=self.theme_data,
            repair=False,
            expected_error=["\ttheme/1: Invalid fields "] + list(invalid_data.keys()),
        )

    def test_fix_missing_default_values_repair_true(self) -> None:
        self.check_data(self.theme_data)

    def test_fix_missing_default_values_repair_false_error(self) -> None:
        self.check_data(
            data=self.theme_data,
            repair=False,
            expected_error=[
                "\ttheme/1: Missing fields ",
                "accent_500",
                "primary_500",
                "warn_500",
            ],
        )

    def test_missing_required_field_error(self) -> None:
        del self.theme_data["theme"]["1"]["name"]
        self.check_data(
            data=self.theme_data,
            expected_error="\ttheme/1: Missing fields name",
        )

    # check_types()
    def test_empty_required_field_error(self) -> None:
        self.theme_data["theme"]["1"]["name"] = None
        self.check_data(
            data=self.theme_data,
            expected_error="\ttheme/1/name: Field required but empty.",
        )

    def test_correct_meeting(self) -> None:
        """Also checks that no errors are raised for missing sequential_numbers."""
        self.check_data(self.meeting_data)

    def test_required_skip_special_fields(self) -> None:
        skip_fields = [
            {
                "field_name": "committee_id",
                "related_collection": "committee",
                "back_relation": "meeting_ids",
            },
            {
                "field_name": "is_active_in_organization_id",
                "related_collection": "organization",
                "back_relation": "active_meeting_ids",
            },
        ]
        for relation in skip_fields:
            data = deepcopy(self.meeting_data)
            data["meeting"]["1"][relation["field_name"]] = None
            del data[relation["related_collection"]]["1"][relation["back_relation"]]
            self.check_data(data)

    def test_invalid_enum_error(self) -> None:
        self.theme_data["organization"]["1"]["default_language"] = "1337"
        self.check_data(
            data=self.theme_data,
            expected_error="\torganization/1/default_language: Value error: Value 1337 is not a valid enum value",
        )

    def test_correct_types(self) -> None:
        self.meeting_data.update(
            {
                **self.organization_tag_data,
                "projection": {"1": {"id": 1, "meeting_id": 1}},
                "gender": {
                    "1": {
                        "id": 1,
                        "organization_id": 1,
                        "name": "male",
                        "user_ids": [1],
                    }
                },
                "user": {"1": {"id": 1, "organization_id": 1, "username": "johndoe"}},
            }
        )
        self.meeting_data["meeting"]["1"].update(
            {
                "organization_tag_ids": [1],
                "all_projection_ids": [1],
                "projection_ids": [1],
            }
        )
        self.meeting_data["organization"]["1"].update(
            {"organization_tag_ids": [1], "gender_ids": [1]}
        )

        correct_value_types: list[dict[str, Any]] = [
            {
                "field_type": CharField,
                "collection": "organization",
                "field_name": "name",
                "value": "OpenSlides",
            },
            {
                "field_type": HTMLStrictField,
                "collection": "organization",
                "field_name": "description",
                "value": "Descriptive text",
            },
            {
                "field_type": HTMLPermissiveField,
                "collection": "meeting",
                "field_name": "welcome_text",
                "value": "Frieldnly welcome text",
            },
            {
                "field_type": GenericRelationField,
                "collection": "projection",
                "field_name": "content_object_id",
                "value": "meeting/1",
            },
            {
                "field_type": IntegerField,
                "collection": "organization",
                "field_name": "limit_of_users",
                "value": 100,
            },
            {
                "field_type": TimestampField,
                "collection": "meeting",
                "field_name": "start_time",
                "value": 123,
            },
            {
                "field_type": TimestampField,
                "collection": "meeting",
                "field_name": "end_time",
                "value": datetime.fromtimestamp(124),
            },
            {
                "field_type": RelationField,
                "collection": "user",
                "field_name": "gender_id",
                "value": 1,
            },
            {
                "field_type": FloatField,
                "collection": "meeting",
                "field_name": "export_pdf_line_height",
                "value": 1.25,
            },
            {
                "field_type": BooleanField,
                "collection": "organization",
                "field_name": "enable_anonymous",
                "value": False,
            },
            {
                "field_type": CharArrayField,
                "collection": "group",
                "field_name": "permissions",
                "value": ["1", "2"],
            },
            {
                "field_type": TextArrayField,
                "collection": "group",
                "field_name": "permissions",
                "value": ["1" * 257, "2" * 420],
            },
            {
                "field_type": GenericRelationListField,
                "collection": "organization_tag",
                "field_name": "tagged_ids",
                "value": ["meeting/1"],
            },
            {
                "field_type": RelationListField,
                "collection": "gender",
                "field_name": "user_ids",
                "value": [1],
            },
            {
                "field_type": DecimalField,
                "collection": "user",
                "field_name": "default_vote_weight",
                "value": "1.0000",
            },
            {
                "field_type": DecimalField,
                "collection": "user",
                "field_name": "default_vote_weight",
                "value": Decimal("1.0000"),
            },
            {
                "field_type": ColorField,
                "collection": "theme",
                "field_name": "accent_500",
                "value": "#e412a3",
            },
            {
                "field_type": TextField,
                "collection": "meeting",
                "field_name": "motions_preamble",
                "value": "The assembly may decide:",
            },
        ]

        # Check correct values
        for field in correct_value_types:
            self.meeting_data[field["collection"]]["1"][field["field_name"]] = field[
                "value"
            ]
        self.check_data(self.meeting_data)

        # Check None
        self.meeting_data["meeting"]["1"].update(
            {"organization_tag_ids": None, "projection_ids": None}
        )
        for field in correct_value_types:
            if field["field_type"] != TimestampField:
                self.meeting_data[field["collection"]]["1"][field["field_name"]] = None
        self.check_data(
            data=self.meeting_data,
            expected_error="\tprojection/1/content_object_id: Field required but empty.",
        )

    def test_correct_types_json(self) -> None:
        raw_values = [
            None,
            [1, "2"],
            {"first": 1, "second": "2", "third": False},
        ]
        json_values = raw_values + [Jsonb(v) for v in raw_values]
        for value in json_values:
            self.theme_data["organization"]["1"]["saml_attr_mapping"] = value
            self.check_data(data=self.theme_data)

    def test_incorrect_types_json(self) -> None:
        raw_values = [1, "2", 3.0, {1, 2}, {"second": 2.0}, Decimal("4.567")]
        json_values = raw_values + [Jsonb(v) for v in raw_values]
        field_type = model_registry["organization"]().get_field("saml_attr_mapping")
        error = [
            f"organization/1/saml_attr_mapping: Type error: Type is not {field_type}"
        ]

        for value in json_values:
            self.theme_data["organization"]["1"]["saml_attr_mapping"] = value
            self.check_data(
                data=self.theme_data,
                expected_error=error,
            )

    def test_incorrect_fqid_error(self) -> None:
        base_error = "projection/1/content_object_id: Type error: Type is not GenericRelationField(to={'projector_countdown': 'projection_ids', 'projector_message': 'projection_ids', 'poll': 'projection_ids', 'topic': 'projection_ids', 'agenda_item': 'projection_ids', 'assignment': 'projection_ids', 'motion_block': 'projection_ids', 'list_of_speakers': 'projection_ids', 'meeting_mediafile': 'projection_ids', 'motion': 'projection_ids', 'meeting': 'projection_ids'}, is_list_field=False, on_delete=SET_NULL, required=True, constraints={}, equal_fields=['meeting_id'])"
        map_invalid_values_to_special_errors = {
            "meetings/1": "projection/1/content_object_id error: The collection meetings is not supported as a reverse relation in projection/content_object_id.",
            "meeting/a": None,
            "just_a_string": None,
            "no_id/": None,
            "/1": None,
        }

        self.meeting_data.update({"projection": {"1": {"id": 1, "meeting_id": 1}}})
        self.meeting_data["meeting"]["1"]["all_projection_ids"] = [1]

        for value, value_error in map_invalid_values_to_special_errors.items():
            self.meeting_data["projection"]["1"]["content_object_id"] = value
            if not value_error:
                value_error = (
                    f"projection/1/content_object_id error: Fqid {value} is malformed"
                )
            self.check_data(
                data=self.meeting_data,
                expected_error=[base_error, value_error],
            )

    def test_incorrect_fqid_list_error(self) -> None:
        base_error = "organization_tag/1/tagged_ids: Type error: Type is not GenericRelationListField(to={'committee': 'organization_tag_ids', 'meeting': 'organization_tag_ids'}, is_list_field=True, on_delete=SET_NULL, required=False, constraints={}, equal_fields=[])"
        map_invalid_values_to_special_errors = {
            "meetings/1": "organization_tag/1/tagged_ids error: The collection meetings is not supported as a reverse relation in organization_tag/tagged_ids.",
            "meeting/a": None,
            "just_a_string": None,
            "no_id/": None,
            "/1": None,
        }

        self.meeting_data.update(self.organization_tag_data)
        self.meeting_data["organization"]["1"].update({"organization_tag_ids": [1]})

        for value, value_error in map_invalid_values_to_special_errors.items():
            self.meeting_data["organization_tag"]["1"]["tagged_ids"] = [value]
            if not value_error:
                value_error = (
                    f"organization_tag/1/tagged_ids error: Fqid {value} is malformed"
                )
            self.check_data(
                data=self.meeting_data,
                expected_error=[base_error, value_error],
            )

    def test_incorrect_value_type_list_field_error(self) -> None:
        list_fields: dict[str, Any] = {
            "group": "permissions",
            "organization_tag": "tagged_ids",
            "organization": "gender_ids",
        }
        invalid_values = [set(), dict(), 1, "2", True, 4.0, Decimal("5.600")]
        self.meeting_data.update(self.organization_tag_data)
        for value in invalid_values:
            for collection, field_name in list_fields.items():
                self.meeting_data[collection]["1"][field_name] = value
            # TODO: after unifying type checking logic also check field type in the message
            self.check_data(
                data=self.meeting_data,
                expected_error=[
                    f"{collection}/1/{field_name}: Type error: Type is not"
                    for field in list_fields
                ],
            )

    # check_special_fields()
    def set_motion_data(self, motion_ids: list[int]) -> None:
        self.meeting_data["meeting"]["1"]["list_of_speakers_ids"] = motion_ids
        self.meeting_data["meeting"]["1"]["motion_ids"] = motion_ids
        self.meeting_data["motion_state"]["1"]["motion_ids"] = motion_ids
        self.meeting_data["motion"] = {
            str(id_): {
                "id": id_,
                "meeting_id": 1,
                "state_id": 1,
                "title": f"motion {id_}",
                "list_of_speakers_id": id_,
            }
            for id_ in motion_ids
        }
        self.meeting_data["list_of_speakers"] = {
            str(id_): {
                "id": id_,
                "content_object_id": f"motion/{id_}",
                "meeting_id": 1,
            }
            for id_ in motion_ids
        }

    def test_amendment_paragraphs_error(self) -> None:
        self.set_motion_data([1])
        self.meeting_data["motion"]["1"]["amendment_paragraphs"] = {
            "1": "<it>test</it>",
            "2": "</>broken",
            "3": '<img target="_blank">forbidden attribute</img>',
        }
        self.check_data(
            data=self.meeting_data,
            expected_error="\tmotion/1/amendment_paragraphs error: Invalid html in 1\n\tmotion/1/amendment_paragraphs error: Invalid html in 2\n\tmotion/1/amendment_paragraphs error: Invalid html in 3",
        )

    def test_motion_extensions_error(self) -> None:
        self.set_motion_data([1, 2])
        errors = []
        for field_name in ["recommendation_extension", "state_extension"]:
            self.meeting_data["motion"]["1"][field_name] = "ext [motion/3] [theme/1]"
            errors.append(
                f"\tmotion/1/{field_name}: Relation Error: Found motion/3 in {field_name} but not in models.\n\tmotion/1/{field_name}: Relation Error: Found theme/1 but only motion is allowed."
            )

        self.check_data(data=self.meeting_data, expected_error=errors)

    def test_external_mode_forbidden_field_error(self) -> None:
        for collection in ["theme", "committee", "organization"]:
            del self.meeting_data[collection]
        self.meeting_data.update(
            {"mediafile": {"1": {"id": 1, "owner_id": ONE_ORGANIZATION_FQID}}}
        )
        self.check_data(
            data=self.meeting_data,
            mode="external",
            expected_error="\tmeeting/1/committee_id: Relation Error: points to committee/1, which is not allowed in an external import.\n\tmeeting/1/is_active_in_organization_id: Relation Error: points to organization/1, which is not allowed in an external import.\n\tmediafile/1/owner_id error: Fqid organization/1 has an invalid collection.",
        )

    def test_external_mode_forbidden_field_repair_false_error(self) -> None:
        self.check_data(
            data=self.extended_user_data,
            mode="external",
            repair=False,
            fields_to_remove={"user": ["committee_ids"]},
            expected_error="\tuser/1/committee_ids: Relation Error: points to committee/user_ids, which is not allowed in an external import.",
        )

    def test_external_mode_forbidden_field_in_fields_to_remove_repair_true(
        self,
    ) -> None:
        self.check_data(
            data=self.extended_user_data,
            mode="external",
            fields_to_remove={"user": ["committee_ids"]},
        )

    def test_reverse_relation_corrupt_error(self) -> None:
        self.meeting_data["committee"]["1"]["meeting_ids"] = None
        self.check_data(
            data=self.meeting_data,
            expected_error="\tmeeting/1/committee_id: Relation Error: points to committee/1/meeting_ids, but the reverse relation for it is corrupt.",
        )

    # check_calculated_fields()
    def test_calculated_fields(self) -> None:
        """
        Check that no errors are raised for:
        * meeting-wide mediafiles with and without meeting_mediafiles
        * orga-wide mediafiles: grand-parent and parent without meeting_mediafiles,
          child with meeting_mediafile and used as font in the meeting
        """
        mediafiles_data: dict[str, Any] = {
            "mediafile": {
                "1": {
                    "id": 1,
                    "owner_id": "meeting/1",
                    "child_ids": [2],
                    "meeting_mediafile_ids": [11],
                },
                "2": {
                    "id": 2,
                    "owner_id": "meeting/1",
                    "parent_id": 1,
                    "meeting_mediafile_ids": [12],
                },
                "3": {
                    "id": 3,
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "is_directory": True,
                    "child_ids": [4],
                },
                "4": {
                    "id": 4,
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "is_directory": True,
                    "parent_id": 3,
                    "child_ids": [5],
                },
                "5": {
                    "id": 5,
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "parent_id": 4,
                    "meeting_mediafile_ids": [15],
                },
            },
            "meeting_mediafile": {
                "11": {
                    "id": 11,
                    "mediafile_id": 1,
                    "meeting_id": 1,
                    "is_public": False,
                    "access_group_ids": [1],
                    "inherited_access_group_ids": [1],
                },
                "12": {
                    "id": 12,
                    "mediafile_id": 2,
                    "meeting_id": 1,
                    "is_public": False,
                    "inherited_access_group_ids": [1],
                },
                "15": {
                    "id": 15,
                    "mediafile_id": 5,
                    "meeting_id": 1,
                    "is_public": False,
                    "access_group_ids": [2],
                    "inherited_access_group_ids": [2],
                    "used_as_font_regular_in_meeting_id": 1,
                },
            },
        }
        self.meeting_data["meeting"]["1"].update(
            {
                "admin_group_id": 2,
                "group_ids": [1, 2],
                "mediafile_ids": [1, 2],
                "meeting_mediafile_ids": [11, 12, 15],
                "font_regular_id": 15,
            }
        )
        self.meeting_data["group"]["1"].update(
            {
                "meeting_mediafile_access_group_ids": [11],
                "meeting_mediafile_inherited_access_group_ids": [11, 12],
            }
        )
        self.meeting_data["group"]["2"] = {
            "id": 2,
            "meeting_id": 1,
            "name": "admin",
            "admin_group_for_meeting_id": 1,
            "meeting_mediafile_access_group_ids": [15],
            "meeting_mediafile_inherited_access_group_ids": [15],
        }
        self.meeting_data["organization"]["1"]["mediafile_ids"] = [3, 4, 5]
        self.check_data(
            data=self.meeting_data | mediafiles_data,
        )

    def test_calculated_fields_error(self) -> None:
        mediafiles_data: dict[str, Any] = {
            "mediafile": {
                "1": {
                    "id": 1,
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "child_ids": [2],
                },
                "2": {
                    "id": 2,
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "parent_id": 1,
                    "meeting_mediafile_ids": [12],
                },
            },
            "meeting_mediafile": {
                "12": {
                    "id": 12,
                    "mediafile_id": 2,
                    "meeting_id": 1,
                    "is_public": True,
                },
            },
        }
        self.meeting_data["meeting"]["1"].update(
            {
                "admin_group_id": 2,
                "group_ids": [1, 2],
                "meeting_mediafile_ids": [12],
            }
        )
        self.meeting_data["group"]["2"] = {
            "id": 2,
            "meeting_id": 1,
            "name": "admin",
            "admin_group_for_meeting_id": 1,
        }
        self.meeting_data["organization"]["1"]["mediafile_ids"] = [1, 2]
        self.check_data(
            data=self.meeting_data | mediafiles_data,
            expected_error="\tmeeting_mediafile/12: is_public is wrong. False != True\n\tmeeting_mediafile/12: inherited_access_group_ids is wrong",
        )

    # get_to_generic_case()
    def test_get_to_generic_case_error(self) -> None:
        self.meeting_data.update(
            {
                "projection": {
                    "1": {
                        "id": 1,
                        "meeting_id": 1,
                        "content_object_id": "theme/1",
                    }
                },
            }
        )
        self.meeting_data["meeting"]["1"].update({"all_projection_ids": [1]})
        self.check_data(
            data=self.meeting_data,
            expected_error="\tprojection/1/content_object_id error: The collection theme is not supported as a reverse relation in projection/content_object_id.",
        )
