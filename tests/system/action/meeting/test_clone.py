from datetime import datetime
from decimal import Decimal
from typing import Any, cast
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import pytest
from psycopg.types.json import Jsonb

from openslides_backend.action.action_worker import ActionWorkerState
from openslides_backend.models.mixins import MeetingModelMixin
from openslides_backend.models.models import AgendaItem, Meeting
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.patterns import fqid_from_collection_and_id
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID, ONE_ORGANIZATION_ID
from tests.system.action.base import BaseActionTestCase
from tests.system.util import CountDatastoreCalls, Profiler, performance


class MeetingClone(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.meeting_data: dict[str, Any] = {
            "template_for_organization_id": 1,
            "projector_countdown_default_time": 60,
            "projector_countdown_warning_time": 5,
        }
        self.archived_meeting_data: dict[str, Any] = {
            "is_active_in_organization_id": None,
            "is_archived_in_organization_id": 1,
        }
        self.test_models: dict[str, dict[str, Any]] = {
            "committee/63": {"name": "Receiver", "organization_id": 1},
            "organization_tag/1": {
                "name": "TEST",
                "color": "#eeeeee",
                "organization_id": 1,
            },
        }

    def set_test_data(self) -> None:
        self.create_meeting(meeting_data=self.meeting_data)
        self.set_models(self.test_models)

    def set_test_data_with_admin(self) -> None:
        self.set_test_data()
        self.set_user_groups(1, [2])

    def create_meeting_with_internal_action(self, admin_ids: list[int] = [1]) -> None:
        self.create_user("user2")
        self.create_user("user3")
        self.create_committee()
        self.execute_action_internally(
            "meeting.create",
            {
                "committee_id": 1,
                "name": "meeting",
                "description": "",
                "location": "",
                "start_time": 1633039200,
                "end_time": 1633039200,
                "user_ids": [2, 3],
                "admin_ids": admin_ids,
                "organization_tag_ids": [],
                "language": "en",
            },
        )
        self.created_fqids.update(
            [
                fqid_from_collection_and_id(collection, id_)
                for collection, data in self.datastore.get_everything().items()
                for id_ in data.keys()
            ]
        )

    def test_clone_without_users(self) -> None:
        self.set_test_data()
        response = self.request(
            "meeting.clone", {"meeting_id": 1, "set_as_template": True}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/2",
            {
                "committee_id": 60,
                "name": "OpenSlides - Copy",
                "default_group_id": 4,
                "admin_group_id": 5,
                "motions_default_amendment_workflow_id": 2,
                "motions_default_workflow_id": 2,
                "reference_projector_id": 2,
                "projector_countdown_default_time": 60,
                "projector_countdown_warning_time": 5,
                "projector_ids": [2],
                "group_ids": [4, 5, 6],
                "motion_state_ids": [2],
                "motion_workflow_ids": [2],
                **{field: [2] for field in Meeting.all_default_projectors()},
                "template_for_organization_id": ONE_ORGANIZATION_ID,
            },
        )
        self.assert_model_exists(
            "organization/1", {"template_meeting_ids": [1, 2], "user_ids": [1]}
        )

    def test_clone_group_with_weight(self) -> None:
        self.set_test_data_with_admin()
        self.set_models({"group/2": {"weight": 1}})
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("group/2", {"weight": 1})
        self.assert_model_exists("group/5", {"weight": 1})

    def test_clone_with_users_inc_vote_weight(self) -> None:
        self.set_test_data_with_admin()
        self.set_models({"meeting_user/1": {"vote_weight": "1.000000"}})
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"user_ids": [1]})
        self.assert_model_exists("meeting/2", {"user_ids": [1]})
        self.assert_model_exists(
            "group/5",
            {"meeting_user_ids": [2], "meeting_id": 2},
        )
        self.assert_model_exists(
            "user/1",
            {
                "meeting_user_ids": [1, 2],
                "meeting_ids": [1, 2],
                "committee_ids": [60],
                "organization_id": 1,
            },
        )
        self.assert_model_exists(
            "meeting_user/1",
            {
                "meeting_id": 1,
                "user_id": 1,
                "group_ids": [2],
                "vote_weight": Decimal("1.000000"),
            },
        )
        self.assert_model_exists(
            "meeting_user/2",
            {
                "meeting_id": 2,
                "user_id": 1,
                "group_ids": [5],
                "vote_weight": Decimal("1.000000"),
            },
        )

    def test_clone_with_users_min_vote_weight_NN_N(self) -> None:
        """if vote_weight and default vote weight are None, both could remain None, because
        they are not required"""
        self.set_test_data()
        self.set_user_groups(1, [2])
        self.set_models({"user/1": {"default_vote_weight": None}})
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"user_ids": [1]})
        self.assert_model_exists("meeting/2", {"user_ids": [1]})
        self.assert_model_exists(
            "user/1",
            {
                "meeting_user_ids": [1, 2],
                "meeting_ids": [1, 2],
                "committee_ids": [60],
                "organization_id": 1,
                "default_vote_weight": None,
            },
        )
        self.assert_model_exists(
            "meeting_user/2",
            {
                "meeting_id": 2,
                "user_id": 1,
                "group_ids": [5],
                "vote_weight": None,
            },
        )

    def test_clone_with_users_min_vote_weight_N1_N(self) -> None:
        """vote_weight can remain None, because default_vote_weight is set greater than minimum"""
        self.set_test_data_with_admin()
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"user_ids": [1]})
        self.assert_model_exists("meeting/2", {"user_ids": [1]})
        self.assert_model_exists(
            "user/1",
            {
                "meeting_user_ids": [1, 2],
                "meeting_ids": [1, 2],
                "committee_ids": [60],
                "organization_id": 1,
                "default_vote_weight": Decimal("1.000000"),
            },
        )
        self.assert_model_exists(
            "meeting_user/2",
            {
                "meeting_id": 2,
                "user_id": 1,
                "group_ids": [5],
                "vote_weight": None,
            },
        )

    def test_clone_with_ex_users(self) -> None:
        self.set_test_data()
        self.create_motion(1)
        self.set_user_groups(1, [1])
        original_user_ids_user_id = self.create_user_for_meeting(1)
        admin_ids_user_id = self.create_user("admin_ids_user")
        user_ids_user_id = self.create_user("user_ids_user")
        self.set_models(
            {
                "motion_submitter/1": {
                    "meeting_user_id": 2,
                    "motion_id": 1,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "meeting.clone",
            {
                "committee_id": 63,
                "meeting_id": 1,
                "admin_ids": [admin_ids_user_id],
                "user_ids": [user_ids_user_id],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/1", {"user_ids": [1, original_user_ids_user_id]}
        )
        self.assert_model_exists(
            "meeting/2",
            {
                "committee_id": 63,
                "motion_submitter_ids": [original_user_ids_user_id],
                "motion_ids": [2],
                "group_ids": [4, 5, 6],
                "meeting_user_ids": [3, 4, 5, 6],
                "user_ids": [
                    1,
                    original_user_ids_user_id,
                    admin_ids_user_id,
                    user_ids_user_id,
                ],
            },
        )
        # Order of assigning ids to meeting users in cloned meeting:
        # m_users from origin meeting -> new regular users -> new admins
        self.assert_model_exists(
            "group/4",
            {"name": "group1", "meeting_id": 2, "meeting_user_ids": [3, 4, 5]},
        )
        self.assert_model_exists(
            "group/5", {"name": "group2", "meeting_id": 2, "meeting_user_ids": [6]}
        )

        self.assert_model_exists(
            "user/1",
            {
                "meeting_ids": [1, 2],
                "meeting_user_ids": [1, 3],
                "committee_ids": [60, 63],
            },
        )
        self.assert_model_exists(
            "meeting_user/1", {"user_id": 1, "meeting_id": 1, "group_ids": [1]}
        )
        self.assert_model_exists(
            "meeting_user/3", {"user_id": 1, "meeting_id": 2, "group_ids": [4]}
        )

        self.assert_model_exists(
            "user/2",
            {
                "meeting_ids": [1, 2],
                "meeting_user_ids": [2, 4],
                "committee_ids": [60, 63],
            },
        )
        self.assert_model_exists(
            "meeting_user/2",
            {"user_id": original_user_ids_user_id, "meeting_id": 1, "group_ids": [1]},
        )
        self.assert_model_exists(
            "meeting_user/4",
            {"user_id": original_user_ids_user_id, "meeting_id": 2, "group_ids": [4]},
        )

        self.assert_model_exists(
            "user/3",
            {
                "username": "admin_ids_user",
                "meeting_ids": [2],
                "meeting_user_ids": [6],
                "committee_ids": [63],
            },
        )
        self.assert_model_exists(
            "meeting_user/6",
            {"user_id": admin_ids_user_id, "meeting_id": 2, "group_ids": [5]},
        )

        self.assert_model_exists(
            "user/4",
            {
                "username": "user_ids_user",
                "meeting_ids": [2],
                "meeting_user_ids": [5],
                "committee_ids": [63],
            },
        )
        self.assert_model_exists(
            "meeting_user/5",
            {"user_id": user_ids_user_id, "meeting_id": 2, "group_ids": [4]},
        )

        self.assert_model_exists(
            "motion_submitter/2",
            {"meeting_user_id": 4, "meeting_id": 2, "motion_id": 2},
        )
        self.assert_model_exists(
            "motion/2",
            {"meeting_id": 2, "submitter_ids": [2]},
        )

    def test_clone_with_set_fields(self) -> None:
        self.set_test_data_with_admin()
        response = self.request(
            "meeting.clone",
            {
                "meeting_id": 1,
                "welcome_title": "Modifizierte Name",
                "description": "blablabla",
                "start_time": 1641370959,
                "end_time": 1641370959,
                "location": "Testraum",
                "organization_tag_ids": [1],
                "name": "name_ORnVFSQJ",
                "external_id": "external_id",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("organization/1", {"template_meeting_ids": [1]})
        self.assert_model_exists(
            "meeting/2",
            {
                "welcome_title": "Modifizierte Name",
                "description": "blablabla",
                "location": "Testraum",
                "organization_tag_ids": [1],
                "start_time": datetime.fromtimestamp(1641370959, tz=ZoneInfo("UTC")),
                "end_time": datetime.fromtimestamp(1641370959, tz=ZoneInfo("UTC")),
                "name": "name_ORnVFSQJ",
                "external_id": "external_id",
                "template_for_organization_id": None,
            },
        )
        self.assert_model_exists("organization_tag/1", {"tagged_ids": ["meeting/2"]})

    def test_clone_with_differing_external_id(self) -> None:
        external_id = "external_id"
        self.meeting_data["external_id"] = external_id
        self.set_test_data_with_admin()
        new_ext_id = external_id + "_something"
        response = self.request(
            "meeting.clone",
            {
                "meeting_id": 1,
                "committee_id": 63,
                "external_id": new_ext_id,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/2",
            {"external_id": new_ext_id, "template_for_organization_id": None},
        )

    def test_clone_with_duplicate_external_id(self) -> None:
        external_id = "external_id"
        self.meeting_data["external_id"] = external_id
        self.set_test_data_with_admin()
        response = self.request("meeting.clone", {"meeting_id": 1, "committee_id": 63})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/2",
            {"external_id": None, "template_for_organization_id": None},
        )

    def test_clone_with_recommendation_extension(self) -> None:
        self.set_test_data_with_admin()
        self.create_motion(1, 23)
        self.create_motion(
            meeting_id=1,
            base=22,
            motion_data={
                "state_extension": "[motion/23]",
                "state_extension_reference_ids": ["motion/23"],
                "recommendation_extension": "[motion/23]",
                "recommendation_extension_reference_ids": ["motion/23"],
            },
        )
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/2", {"motion_ids": [24, 25], "list_of_speakers_ids": [24, 25]}
        )
        self.assert_model_exists(
            "motion/24",
            {
                "state_extension": "[motion/25]",
                "state_extension_reference_ids": ["motion/25"],
                "recommendation_extension": "[motion/25]",
                "recommendation_extension_reference_ids": ["motion/25"],
            },
        )
        self.assert_model_exists(
            "motion/25",
            {
                "referenced_in_motion_state_extension_ids": [24],
                "referenced_in_motion_recommendation_extension_ids": [24],
            },
        )

    def test_clone_user_ids_and_admin_ids(self) -> None:
        del self.meeting_data["template_for_organization_id"]
        self.set_test_data()
        new_admin_user_id = self.create_user("new_admin_user")
        new_default_group_user_id = self.create_user("new_default_group_user")
        new_and_old_default_group_user_id = self.create_user(
            "new_and_old_default_group_user", [1]
        )
        new_default_group_old_admin_user_id = self.create_user(
            "new_default_group_old_admin_user", [2]
        )
        response = self.request(
            "meeting.clone",
            {
                "meeting_id": 1,
                "user_ids": [
                    new_default_group_user_id,
                    new_and_old_default_group_user_id,
                    new_default_group_old_admin_user_id,
                ],
                "admin_ids": [new_admin_user_id],
                "set_as_template": False,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("organization/1", {"template_meeting_ids": None})
        self.assert_model_exists(
            "meeting/2",
            {
                "template_for_organization_id": None,
                "user_ids": [
                    new_admin_user_id,
                    new_default_group_user_id,
                    new_and_old_default_group_user_id,
                    new_default_group_old_admin_user_id,
                ],
            },
        )
        self.assert_model_exists("group/4", {"meeting_user_ids": [3, 4, 5]})
        self.assert_model_exists("group/5", {"meeting_user_ids": [4, 6]})
        self.assert_model_exists(
            "user/2",
            {
                "username": "new_admin_user",
                "meeting_user_ids": [6],
                "meeting_ids": [2],
            },
        )
        self.assert_model_exists(
            "meeting_user/6",
            {"meeting_id": 2, "user_id": new_admin_user_id, "group_ids": [5]},
        )
        self.assert_model_exists(
            "user/3",
            {
                "username": "new_default_group_user",
                "meeting_user_ids": [5],
                "meeting_ids": [2],
            },
        )
        self.assert_model_exists(
            "meeting_user/5",
            {"meeting_id": 2, "user_id": new_default_group_user_id, "group_ids": [4]},
        )

        self.assert_model_exists(
            "user/4",
            {
                "username": "new_and_old_default_group_user",
                "meeting_user_ids": [1, 3],
                "meeting_ids": [1, 2],
            },
        )
        self.assert_model_exists(
            "meeting_user/1",
            {
                "meeting_id": 1,
                "user_id": new_and_old_default_group_user_id,
                "group_ids": [1],
            },
        )
        self.assert_model_exists(
            "meeting_user/3",
            {
                "meeting_id": 2,
                "user_id": new_and_old_default_group_user_id,
                "group_ids": [4],
            },
        )

        self.assert_model_exists(
            "user/5",
            {
                "username": "new_default_group_old_admin_user",
                "meeting_user_ids": [2, 4],
                "meeting_ids": [1, 2],
            },
        )
        self.assert_model_exists(
            "meeting_user/2",
            {
                "meeting_id": 1,
                "user_id": new_default_group_old_admin_user_id,
                "group_ids": [2],
            },
        )
        self.assert_model_exists(
            "meeting_user/4",
            {
                "meeting_id": 2,
                "user_id": new_default_group_old_admin_user_id,
                "group_ids": [4, 5],
            },
        )

    def test_clone_new_committee_and_user_with_group(self) -> None:
        self.set_test_data_with_admin()
        self.create_user("user_from_new_committee", [1])
        self.set_models(
            {
                "user/2": {"gender_id": 1},
                "gender/1": {"name": "male", "organization_id": 1},
            }
        )
        response = self.request(
            "meeting.clone",
            {"meeting_id": 1, "committee_id": 63, "user_ids": [2]},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/2", {"committee_id": 63, "user_ids": [1, 2]})
        self.assert_model_exists(
            "committee/63",
            {"user_ids": [1, 2], "organization_id": 1, "meeting_ids": [2]},
        )
        self.assert_model_exists(
            "user/2",
            {
                "username": "user_from_new_committee",
                "committee_ids": [60, 63],
                "meeting_ids": [1, 2],
                "meeting_user_ids": [2, 4],
                "gender_id": 1,
            },
        )
        self.assert_model_exists(
            "meeting_user/2",
            {
                "meeting_id": 1,
                "user_id": 2,
                "group_ids": [1],
            },
        )
        self.assert_model_exists(
            "meeting_user/4",
            {
                "meeting_id": 2,
                "user_id": 2,
                "group_ids": [4],
            },
        )
        self.assert_model_exists("group/4", {"meeting_user_ids": [4]})

    def test_clone_new_committee_and_add_user(self) -> None:
        self.set_test_data_with_admin()
        self.create_user("user_from_new_committee")
        response = self.request(
            "meeting.clone",
            {"meeting_id": 1, "user_ids": [2], "committee_id": 63},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/2", {"committee_id": 63, "user_ids": [1, 2], "default_group_id": 4}
        )
        self.assert_model_exists(
            "committee/63",
            {"user_ids": [1, 2], "organization_id": 1, "meeting_ids": [2]},
        )
        self.assert_model_exists(
            "user/2",
            {
                "username": "user_from_new_committee",
                "committee_ids": [63],
                "meeting_ids": [2],
                "meeting_user_ids": [3],
            },
        )
        self.assert_model_exists(
            "meeting_user/3",
            {
                "meeting_id": 2,
                "user_id": 2,
                "group_ids": [4],
            },
        )
        self.assert_model_exists(
            "group/4", {"meeting_user_ids": [3], "default_group_for_meeting_id": 2}
        )

    def test_clone_missing_user_id_in_additional_users(self) -> None:
        self.set_test_data_with_admin()
        response = self.request("meeting.clone", {"meeting_id": 1, "user_ids": [13]})
        self.assert_status_code(response, 400)
        self.assertEqual("Model 'user/13' does not exist.", response.json["message"])

    def test_clone_with_personal_note(self) -> None:
        self.set_test_data_with_admin()
        self.set_models(
            {
                "personal_note/1": {
                    "note": "test note",
                    "meeting_user_id": 1,
                    "meeting_id": 1,
                }
            }
        )
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/1", {"meeting_user_ids": [1, 2]})
        self.assert_model_exists(
            "meeting_user/2",
            {"personal_note_ids": [2], "user_id": 1, "meeting_id": 2},
        )
        self.assert_model_exists(
            "personal_note/2", {"meeting_user_id": 2, "meeting_id": 2}
        )

    def test_clone_with_option(self) -> None:
        self.set_test_data_with_admin()
        self.set_models({"option/1": {"content_object_id": "user/1", "meeting_id": 1}})
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/1", {"option_ids": [1, 2]})
        self.assert_model_exists(
            "option/2", {"content_object_id": "user/1", "meeting_id": 2}
        )

    def test_clone_with_mediafile(self) -> None:
        self.set_test_data_with_admin()
        self.set_models(
            {
                "meeting/1": {
                    "logo_web_header_id": 10,
                    "font_bold_id": 20,
                },
                "mediafile/1": {
                    "owner_id": "meeting/1",
                    "mimetype": "text/plain",
                },
                "mediafile/2": {
                    "owner_id": "meeting/1",
                    "mimetype": "text/plain",
                },
                "meeting_mediafile/10": {
                    "meeting_id": 1,
                    "mediafile_id": 1,
                    "is_public": True,
                    "used_as_logo_web_header_in_meeting_id": 1,
                },
                "meeting_mediafile/20": {
                    "meeting_id": 1,
                    "mediafile_id": 2,
                    "is_public": True,
                    "used_as_font_bold_in_meeting_id": 1,
                },
            }
        )
        self.media.duplicate_mediafile = MagicMock()
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.media.duplicate_mediafile.assert_called_with(2, 4)
        self.assert_model_exists(
            "meeting_mediafile/21",
            {
                "meeting_id": 2,
                "mediafile_id": 3,
                "used_as_logo_web_header_in_meeting_id": 2,
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/22",
            {
                "meeting_id": 2,
                "mediafile_id": 4,
                "used_as_font_bold_in_meeting_id": 2,
            },
        )
        self.assert_model_exists(
            "meeting/2", {"logo_web_header_id": 21, "font_bold_id": 22}
        )

    @pytest.mark.skip(
        "Handle after merging main with fixes for mediafiles in meeting.clone."
    )
    def test_clone_with_mediafile_directory(self) -> None:
        self.set_test_data_with_admin()
        self.create_mediafile(1, 1, is_directory=True)
        self.media.duplicate_mediafile = MagicMock()
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.media.duplicate_mediafile.assert_not_called(1, 2)
        self.assert_model_exists(
            "meeting_mediafile/2",
            {
                "parent_id": None,
                "is_directory": True,
                "title": "file_1",
                "mimetype": "text/plain",
                "filename": "text-1.txt",
                "owner_id": "meeting/1",
            },
        )

    def test_clone_with_linked_orga_wide_font(self) -> None:
        self.set_test_data_with_admin()
        self.set_models(
            {
                "meeting/1": {"font_regular_id": 11},
                "group/2": {"meeting_mediafile_inherited_access_group_ids": [11]},
                "mediafile/16": {
                    "is_directory": True,
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                },
                "mediafile/17": {
                    "parent_id": 16,
                    "is_directory": False,
                    "mimetype": "font/woff",
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                },
                "meeting_mediafile/11": {
                    "is_public": False,
                    "meeting_id": 1,
                    "mediafile_id": 17,
                },
            }
        )

        self.media.duplicate_mediafile = MagicMock()
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/2",
            {
                "admin_group_id": 5,
                "meeting_mediafile_ids": [12],
                "font_regular_id": 12,
            },
        )
        self.assert_model_exists(
            "group/5",
            {
                "admin_group_for_meeting_id": 2,
                "meeting_mediafile_inherited_access_group_ids": [12],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/12",
            {
                "is_public": False,
                "meeting_id": 2,
                "mediafile_id": 17,
                "access_group_ids": None,
                "inherited_access_group_ids": [5],
                "used_as_font_regular_in_meeting_id": 2,
            },
        )
        self.assert_model_exists("mediafile/17", {"meeting_mediafile_ids": [11, 12]})
        self.media.duplicate_mediafile.assert_not_called()

    def test_clone_with_organization_tag(self) -> None:
        self.test_models["organization_tag/1"]["tagged_ids"] = ["meeting/1"]
        self.set_test_data_with_admin()
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/2", {"organization_tag_ids": [1]})
        self.assert_model_exists(
            "organization_tag/1", {"tagged_ids": ["meeting/1", "meeting/2"]}
        )

    def test_clone_with_settings(self) -> None:
        timestamp = datetime.fromtimestamp(1633522986)
        timestamp_with_tz = timestamp.replace(tzinfo=ZoneInfo("UTC"))
        settings = {
            "welcome_title": "title",
            "welcome_text": "text",
            "name": "name",
            "description": "desc",
            "location": "loc",
            "start_time": timestamp,
            "end_time": timestamp,
            "conference_show": True,
            "conference_auto_connect": True,
            "conference_los_restriction": True,
            "conference_stream_url": "url",
            "conference_stream_poster_url": "url",
            "conference_open_microphone": True,
            "conference_open_video": True,
            "conference_auto_connect_next_speakers": 42,
            "conference_enable_helpdesk": True,
            "applause_enable": True,
            "applause_type": "applause-type-particles",
            "applause_show_level": True,
            "applause_min_amount": 42,
            "applause_max_amount": 42,
            "applause_timeout": 42,
            "applause_particle_image_url": "url",
            "projector_countdown_default_time": 42,
            "projector_countdown_warning_time": 42,
            "export_csv_encoding": "iso-8859-15",
            "export_csv_separator": ";",
            "export_pdf_pagenumber_alignment": "left",
            "export_pdf_fontsize": 12,
            "export_pdf_pagesize": "A5",
            "agenda_show_subtitles": True,
            "agenda_enable_numbering": False,
            "agenda_number_prefix": "prefix",
            "agenda_numeral_system": "roman",
            "agenda_item_creation": "always",
            "agenda_new_items_default_visibility": "common",
            "agenda_show_internal_items_on_projector": False,
            "list_of_speakers_amount_last_on_projector": 42,
            "list_of_speakers_amount_next_on_projector": 42,
            "list_of_speakers_couple_countdown": False,
            "list_of_speakers_show_amount_of_speakers_on_slide": False,
            "list_of_speakers_present_users_only": True,
            "list_of_speakers_show_first_contribution": True,
            "list_of_speakers_hide_contribution_count": True,
            "list_of_speakers_enable_point_of_order_speakers": True,
            "list_of_speakers_enable_pro_contra_speech": True,
            "list_of_speakers_can_set_contribution_self": True,
            "list_of_speakers_speaker_note_for_everyone": True,
            "list_of_speakers_initially_closed": True,
            "motions_preamble": "preamble",
            "motions_default_line_numbering": "inline",
            "motions_line_length": 42,
            "motions_reason_required": True,
            "motions_origin_motion_toggle_default": True,
            "motions_enable_origin_motion_display": True,
            "motions_enable_text_on_projector": True,
            "motions_enable_reason_on_projector": True,
            "motions_enable_sidebox_on_projector": True,
            "motions_enable_recommendation_on_projector": True,
            "motions_show_referring_motions": True,
            "motions_show_sequential_number": True,
            "motions_recommendations_by": "rec",
            "motions_recommendation_text_mode": "original",
            "motions_default_sorting": "weight",
            "motions_number_type": "manually",
            "motions_number_min_digits": 42,
            "motions_number_with_blank": True,
            "motions_amendments_enabled": True,
            "motions_amendments_in_main_list": True,
            "motions_amendments_of_amendments": True,
            "motions_amendments_prefix": "prefix",
            "motions_amendments_text_mode": "freestyle",
            "motions_amendments_multiple_paragraphs": True,
            "motions_supporters_min_amount": 42,
            "motions_export_title": "title",
            "motions_export_preamble": "pre",
            "motions_export_submitter_recommendation": True,
            "motions_export_follow_recommendation": True,
            "motion_poll_ballot_paper_selection": "NUMBER_OF_DELEGATES",
            "motion_poll_ballot_paper_number": 42,
            "motion_poll_default_type": "pseudoanonymous",
            "motion_poll_default_method": "YNA",
            "motion_poll_default_onehundred_percent_base": "YN",
            "users_enable_presence_view": True,
            "users_enable_vote_weight": True,
            "users_enable_vote_delegations": True,
            "users_allow_self_set_present": True,
            "users_pdf_welcometitle": "title",
            "users_pdf_welcometext": "text",
            "users_pdf_wlan_ssid": "wifi",
            "users_pdf_wlan_password": "pw",
            "users_pdf_wlan_encryption": "WEP",
            "users_email_sender": "sender",
            "users_email_replyto": "replyto",
            "users_email_subject": "subject",
            "users_email_body": "body",
            "assignments_export_title": "title",
            "assignments_export_preamble": "pre",
            "assignment_poll_ballot_paper_selection": "NUMBER_OF_DELEGATES",
            "assignment_poll_ballot_paper_number": 42,
            "assignment_poll_add_candidates_to_list_of_speakers": True,
            "assignment_poll_enable_max_votes_per_option": False,
            "assignment_poll_sort_poll_result_by_votes": True,
            "assignment_poll_default_type": "pseudoanonymous",
            "assignment_poll_default_method": "YNA",
            "assignment_poll_default_onehundred_percent_base": "YNA",
        }
        self.meeting_data.update(settings)
        self.set_test_data_with_admin()
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        settings["name"] = f"{settings['name']} - Copy"
        settings["start_time"] = timestamp_with_tz
        settings["end_time"] = timestamp_with_tz
        self.assert_model_exists("meeting/2", settings)

    def test_limit_of_meetings_error(self) -> None:
        self.set_test_data_with_admin()
        self.set_models({ONE_ORGANIZATION_FQID: {"limit_of_meetings": 1}})
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "You cannot clone an meeting, because you reached your limit of 1 active meetings.",
            response.json["message"],
        )

    def test_limit_of_meetings_error_archived_meeting(self) -> None:
        self.meeting_data.update(self.archived_meeting_data)
        self.set_test_data_with_admin()
        self.create_meeting(4)
        self.set_models({ONE_ORGANIZATION_FQID: {"limit_of_meetings": 1}})
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "You cannot clone an meeting, because you reached your limit of 1 active meetings.",
            response.json["message"],
        )

    def test_activate_archived_meeting(self) -> None:
        self.meeting_data.update(self.archived_meeting_data)
        self.set_test_data_with_admin()
        self.create_meeting(4)
        self.set_models({ONE_ORGANIZATION_FQID: {"limit_of_meetings": 2}})
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/5",
            {"is_active_in_organization_id": 1, "is_archived_in_organization_id": None},
        )
        self.assert_model_exists(
            ONE_ORGANIZATION_FQID,
            {"active_meeting_ids": [4, 5], "archived_meeting_ids": [1]},
        )

    def test_limit_of_meetings_ok(self) -> None:
        self.set_test_data_with_admin()
        self.set_models({ONE_ORGANIZATION_FQID: {"limit_of_meetings": 2}})
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(ONE_ORGANIZATION_FQID, {"active_meeting_ids": [1, 2]})

    def test_create_clone(self) -> None:
        self.create_meeting_with_internal_action(admin_ids=[2])
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/2",
            {
                "committee_id": 1,
                "name": "meeting - Copy",
                "description": "",
                "location": "",
                "start_time": datetime.fromtimestamp(1633039200, ZoneInfo("UTC")),
                "end_time": datetime.fromtimestamp(1633039200, ZoneInfo("UTC")),
                "meeting_user_ids": [3, 4],
                "user_ids": [2, 3],
                "language": "en",
                "group_ids": [5, 6, 7, 8],
                "default_group_id": 5,
                "admin_group_id": 6,
            },
        )
        self.assert_model_exists(
            "group/5", {"default_group_for_meeting_id": 2, "meeting_user_ids": [4]}
        )
        self.assert_model_exists(
            "meeting_user/4", {"user_id": 3, "meeting_id": 2, "group_ids": [5]}
        )
        self.assert_model_exists(
            "group/6", {"admin_group_for_meeting_id": 2, "meeting_user_ids": [3]}
        )
        self.assert_model_exists(
            "meeting_user/3", {"user_id": 2, "meeting_id": 2, "group_ids": [6]}
        )

    def test_create_clone_without_admin(self) -> None:
        self.create_meeting_with_internal_action()
        self.set_user_groups(1, [])
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Cannot create a non-template meeting without administrators",
            response.json["message"],
        )

    def test_meeting_name_exact_fit(self) -> None:
        long_name = "A" * 93
        self.meeting_data["name"] = long_name
        self.set_test_data_with_admin()
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/2", {"name": long_name + " - Copy"})

    def test_meeting_name_too_long(self) -> None:
        self.meeting_data["name"] = "A" * 100
        self.set_test_data_with_admin()
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/2", {"name": "A" * 90 + "... - Copy"})

    def test_permissions_explicit_source_committee_permission(self) -> None:
        self.set_test_data()
        self.set_committee_management_level([60], 1)
        self.set_organization_management_level(None)
        response = self.request(
            "meeting.clone", {"meeting_id": 1, "committee_id": 60, "admin_ids": [1]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/1", {"is_active_in_organization_id": 1, "committee_id": 60}
        )
        self.assert_model_exists(
            "meeting/2", {"is_active_in_organization_id": 1, "committee_id": 60}
        )

    def test_permissions_foreign_template_meeting_cml(self) -> None:
        self.set_organization_management_level(None)
        self.set_test_data()
        self.set_committee_management_level([60, 63], 1)
        response = self.request(
            "meeting.clone", {"meeting_id": 1, "committee_id": 63, "admin_ids": [1]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/1", {"is_active_in_organization_id": 1, "committee_id": 60}
        )
        self.assert_model_exists(
            "meeting/2", {"is_active_in_organization_id": 1, "committee_id": 63}
        )

    def test_permissions_foreign_committee_cml_error(self) -> None:
        self.set_organization_management_level(None)
        self.set_test_data()
        self.set_committee_management_level([60], 1)
        response = self.request("meeting.clone", {"meeting_id": 1, "committee_id": 63})
        self.assert_status_code(response, 403)
        self.assertEqual(
            "You are not allowed to perform action meeting.clone. Missing permission: CommitteeManagementLevel can_manage in committee 63",
            response.json["message"],
        )

    def test_permissions_oml_can_manage(self) -> None:
        self.set_test_data_with_admin()
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
        )
        response = self.request("meeting.clone", {"meeting_id": 1, "committee_id": 63})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/1", {"is_active_in_organization_id": 1, "committee_id": 60}
        )
        self.assert_model_exists(
            "meeting/2", {"is_active_in_organization_id": 1, "committee_id": 63}
        )

    def test_permissions_missing_source_committee_permission(self) -> None:
        self.test_models["committee/63"]["manager_ids"] = [1]
        self.set_organization_management_level(None)
        self.set_test_data_with_admin()
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 403)
        self.assertEqual(
            "You are not allowed to perform action meeting.clone. Missing permission: CommitteeManagementLevel can_manage in committee 60",
            response.json["message"],
        )

    def test_clone_with_created_topic_and_agenda_type(self) -> None:
        self.set_test_data_with_admin()
        result = self.execute_action_internally(
            "topic.create",
            {
                "meeting_id": 1,
                "title": "test",
                "agenda_type": AgendaItem.INTERNAL_ITEM,
                "agenda_duration": 60,
            },
        )
        topic_fqid = f"topic/{cast(list[dict[str, int]], result)[0]['id']}"
        topic = self.get_model(topic_fqid)
        self.assertNotIn("agenda_type", topic)
        self.assertNotIn("agenda_duration", topic)
        agenda_item_fqid = f"agenda_item/{topic.get('agenda_item_id')}"
        self.assert_model_exists(
            agenda_item_fqid,
            {
                "type": AgendaItem.INTERNAL_ITEM,
                "duration": 60,
                "content_object_id": topic_fqid,
            },
        )

        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)

    def test_clone_with_created_motion_and_agenda_type(self) -> None:
        self.set_test_data_with_admin()
        response = self.request(
            "motion.create",
            {
                "meeting_id": 1,
                "title": "test",
                "text": "Motion test",
                "agenda_create": False,
                "agenda_type": AgendaItem.INTERNAL_ITEM,
                "agenda_duration": 60,
            },
        )
        self.assert_status_code(response, 200)
        motion_fqid = f'motion/{response.json["results"][0][0]["id"]}'
        self.assert_model_exists(
            motion_fqid,
            {
                "agenda_item_id": None,
                "agenda_create": None,
                "agenda_type": None,
                "agenda_duration": None,
            },
        )
        self.assert_model_exists("motion_submitter/1", {"meeting_user_id": 1})
        self.assert_model_exists("user/1", {"meeting_user_ids": [1]})
        self.assert_model_exists(
            "meeting_user/1",
            {"meeting_id": 1, "user_id": 1, "motion_submitter_ids": [1]},
        )
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)

    def test_clone_with_archived_meeting(self) -> None:
        """
        Archived meeting stays archived by cloning
        """
        self.meeting_data.update(self.archived_meeting_data)
        self.set_test_data_with_admin()
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"is_active_in_organization_id": None})

    def test_clone_with_forwarded_motion(self) -> None:
        self.set_test_data_with_admin()
        self.create_meeting(4)
        self.set_models(
            {
                "meeting/4": {"committee_id": 60},
                "motion/1": {
                    "meeting_id": 1,
                    "all_derived_motion_ids": [2],
                    "sequential_number": 1,
                    "list_of_speakers_id": 1,
                    "title": "motion1",
                    "state_id": 1,
                },
                "motion/2": {
                    "meeting_id": 4,
                    "origin_id": 1,
                    "origin_meeting_id": 1,
                    "sequential_number": 2,
                    "list_of_speakers_id": 2,
                    "title": "motion1 forwarded",
                    "state_id": 4,
                },
                "motion/3": {
                    "meeting_id": 4,
                    "all_derived_motion_ids": [4],
                    "sequential_number": 3,
                    "list_of_speakers_id": 3,
                    "title": "motion3",
                    "state_id": 4,
                },
                "motion/4": {
                    "meeting_id": 1,
                    "origin_id": 3,
                    "origin_meeting_id": 4,
                    "sequential_number": 4,
                    "list_of_speakers_id": 4,
                    "title": "motion3 forwarded",
                    "state_id": 1,
                },
                "list_of_speakers/1": {
                    "sequential_number": 1,
                    "content_object_id": "motion/1",
                    "meeting_id": 1,
                },
                "list_of_speakers/2": {
                    "sequential_number": 2,
                    "content_object_id": "motion/2",
                    "meeting_id": 4,
                },
                "list_of_speakers/3": {
                    "sequential_number": 3,
                    "content_object_id": "motion/3",
                    "meeting_id": 4,
                },
                "list_of_speakers/4": {
                    "sequential_number": 4,
                    "content_object_id": "motion/4",
                    "meeting_id": 1,
                },
            }
        )
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/5", {"motion_ids": [5, 6], "name": "OpenSlides - Copy"}
        )
        self.assert_model_exists(
            "motion/5",
            {
                "meeting_id": 5,
                "origin_id": None,
                "all_origin_ids": None,
                "origin_meeting_id": None,
                "derived_motion_ids": None,
            },
        )

    def test_clone_with_underscore_attributes(self) -> None:
        self.set_test_data_with_admin()
        response = self.request(
            "meeting.clone", {"meeting_id": 1, "_collection": "testtest"}
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Action meeting.clone: data must not contain {'_collection'} properties",
            response.json["message"],
        )

    def test_clone_vote_delegation(self) -> None:
        self.set_test_data_with_admin()
        self.create_user("vote_receiver", [1])
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"user_ids": [1, 2]})
        self.assert_model_exists("meeting/2", {"user_ids": [1, 2]})
        self.assert_model_exists(
            "group/4",
            {
                "meeting_user_ids": [4],
                "meeting_id": 2,
            },
        )
        self.assert_model_exists(
            "group/5",
            {
                "meeting_user_ids": [3],
                "meeting_id": 2,
            },
        )
        self.assert_model_exists(
            "user/1",
            {
                "meeting_ids": [1, 2],
                "meeting_user_ids": [1, 3],
            },
        )
        self.assert_model_exists(
            "meeting_user/1",
            {
                "meeting_id": 1,
                "user_id": 1,
                "group_ids": [2],
            },
        )
        self.assert_model_exists(
            "meeting_user/3",
            {
                "meeting_id": 2,
                "user_id": 1,
                "group_ids": [5],
            },
        )

        self.assert_model_exists(
            "user/2",
            {
                "meeting_ids": [1, 2],
                "meeting_user_ids": [2, 4],
            },
        )
        self.assert_model_exists(
            "meeting_user/2",
            {
                "meeting_id": 1,
                "user_id": 2,
                "group_ids": [1],
            },
        )
        self.assert_model_exists(
            "meeting_user/4",
            {
                "meeting_id": 2,
                "user_id": 2,
                "group_ids": [4],
            },
        )

    def test_clone_vote_delegated_vote(self) -> None:
        self.set_test_data_with_admin()
        self.create_meeting(4)
        self.set_user_groups(1, [2, 5])
        self.set_models(
            {
                "vote/1": {
                    "user_id": 1,
                    "delegated_user_id": 1,
                    "meeting_id": 1,
                    "option_id": 1,
                    "user_token": "asdfgh",
                },
                "vote/2": {
                    "user_id": 1,
                    "delegated_user_id": 1,
                    "meeting_id": 4,
                    "option_id": 2,
                    "user_token": "hjkl",
                },
                "option/1": {"meeting_id": 1},
                "option/2": {"meeting_id": 4},
            },
        )
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "vote/3",
            {"user_id": 1, "delegated_user_id": 1, "option_id": 3, "meeting_id": 5},
        )
        self.assert_model_exists(
            "user/1",
            {
                "meeting_user_ids": [1, 2, 3],
                "vote_ids": [1, 2, 3],
                "delegated_vote_ids": [1, 2, 3],
                "meeting_ids": [1, 4, 5],
            },
        )
        self.assert_model_exists("meeting_user/3", {"user_id": 1, "meeting_id": 5})

    def test_with_action_worker(self) -> None:
        """action_worker shouldn't be cloned"""
        aw_name = "test action_worker"
        self.set_test_data_with_admin()
        self.set_models(
            {
                "action_worker/1": {
                    "name": aw_name,
                    "state": ActionWorkerState.END,
                    "created": datetime.now(),
                    "timestamp": datetime.now(),
                    "user_id": 1,
                }
            }
        )
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("action_worker/1", {"name": aw_name})
        self.assert_model_not_exists("action_worker/2")

    def test_with_import_preview(self) -> None:
        """import_preview shouldn't be cloned"""
        self.set_test_data_with_admin()
        self.set_models(
            {
                "import_preview/1": {
                    "name": "topic",
                    "state": "done",
                    "created": datetime.now(),
                }
            }
        )
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("import_preview/1", {"name": "topic"})
        self.assert_model_not_exists("import_preview/2")

    def test_clone_with_2_existing_meetings(self) -> None:
        del self.test_models["committee/63"]
        self.set_test_data()
        self.create_meeting(4, meeting_data={"committee_id": 60})
        self.set_user_groups(1, [2, 5])
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"user_ids": [1]})
        self.assert_model_exists("meeting/4", {"user_ids": [1]})
        self.assert_model_exists("meeting/5", {"user_ids": [1]})

        self.assert_model_exists(
            "user/1",
            {
                "meeting_user_ids": [1, 2, 3],
                "meeting_ids": [1, 4, 5],
            },
        )
        self.assert_model_exists(
            "meeting_user/1",
            {
                "meeting_id": 1,
                "user_id": 1,
                "group_ids": [2],
            },
        )
        self.assert_model_exists(
            "meeting_user/2",
            {
                "meeting_id": 4,
                "user_id": 1,
                "group_ids": [5],
            },
        )
        self.assert_model_exists(
            "meeting_user/3",
            {
                "meeting_id": 5,
                "user_id": 1,
                "group_ids": [8],
            },
        )
        self.assert_model_exists(
            "meeting/1", {"user_ids": [1], "meeting_user_ids": [1]}
        )
        self.assert_model_exists(
            "meeting/4", {"user_ids": [1], "meeting_user_ids": [2]}
        )
        self.assert_model_exists(
            "meeting/5", {"user_ids": [1], "meeting_user_ids": [3]}
        )
        self.assert_model_exists("committee/60", {"meeting_ids": [1, 4, 5]})

    def test_clone_datastore_calls(self) -> None:
        self.create_meeting_with_internal_action()
        with CountDatastoreCalls() as counter:
            response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        assert counter.calls == 9

    @performance
    def test_clone_performance(self) -> None:
        self.create_meeting_with_internal_action()
        with Profiler("test_meeting_clone_performance.prof"):
            response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)

    def test_clone_amendment_paragraphs(self) -> None:
        self.set_test_data()
        self.set_user_groups(1, [1])
        self.set_models(
            {
                "motion/1": {
                    "list_of_speakers_id": 1,
                    "meeting_id": 1,
                    "sequential_number": 1,
                    "state_id": 1,
                    "title": "dummy",
                    "amendment_paragraphs": Jsonb(
                        {
                            "1": "<it>test</it>",
                            "2": "</>broken",
                        }
                    ),
                },
                "list_of_speakers/1": {
                    "content_object_id": "motion/1",
                    "meeting_id": 1,
                    "sequential_number": 1,
                },
            }
        )
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "\tmotion/1/amendment_paragraphs error: Invalid html in 1\n\tmotion/1/amendment_paragraphs error: Invalid html in 2",
            response.json["message"],
        )

    def test_permissions_oml_locked_meeting(self) -> None:
        self.create_meeting(
            meeting_data={"locked_from_inside": True, "template_for_organization_id": 1}
        )
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
        )
        response = self.request("meeting.clone", {"meeting_id": 1, "committee_id": 63})
        self.assert_status_code(response, 400)
        self.assertEqual("Cannot clone locked meeting.", response.json["message"])

    def test_permissions_oml_locked_meeting_with_can_manage_settings(self) -> None:
        self.meeting_data["locked_from_inside"] = True
        self.set_test_data()
        bob_id = self.create_user("bob")
        self.set_group_permissions(1, [Permissions.Meeting.CAN_MANAGE_SETTINGS])
        self.set_user_groups(1, [1])
        response = self.request(
            "meeting.clone", {"meeting_id": 1, "admin_ids": [bob_id]}
        )
        self.assert_status_code(response, 200)

    def test_clone_template_allowed(self) -> None:
        self.set_test_data_with_admin()
        self.set_committee_management_level([60])
        self.set_organization_management_level(None)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)

    def test_clone_non_template_and_committee_change_not_allowed(self) -> None:
        del self.meeting_data["template_for_organization_id"]
        self.set_test_data()
        self.set_committee_management_level([60, 63])
        response = self.request("meeting.clone", {"meeting_id": 1, "committee_id": 63})
        self.assert_status_code(response, 403)
        self.assertEqual(
            response.json["message"],
            "Cannot clone meeting to a different committee if it is a non-template meeting.",
        )

    def test_clone_with_list_election(self) -> None:
        self.create_meeting(meeting_data={"name": "Duckburg town government"})
        self.set_user_groups(1, [2])
        self.create_user("Huey", [3])
        self.create_user("Dewey", [3])
        self.create_user("Louie", [3])
        self.set_models(
            {
                "list_of_speakers/1": {
                    "id": 1,
                    "closed": False,
                    "meeting_id": 1,
                    "content_object_id": "assignment/1",
                    "sequential_number": 1,
                },
                "assignment/1": {
                    "id": 1,
                    "phase": "search",
                    "title": "Duckburg town council",
                    "meeting_id": 1,
                    "open_posts": 0,
                    "sequential_number": 1,
                    "list_of_speakers_id": 1,
                },
                "poll_candidate/1": {
                    "id": 1,
                    "weight": 1,
                    "user_id": 2,
                    "meeting_id": 1,
                    "poll_candidate_list_id": 1,
                },
                "poll_candidate/2": {
                    "id": 2,
                    "weight": 2,
                    "user_id": 3,
                    "meeting_id": 1,
                    "poll_candidate_list_id": 1,
                },
                "poll_candidate/3": {
                    "id": 3,
                    "weight": 3,
                    "user_id": 4,
                    "meeting_id": 1,
                    "poll_candidate_list_id": 1,
                },
                "poll_candidate_list/1": {
                    "id": 1,
                    "option_id": 1,
                    "meeting_id": 1,
                    "poll_candidate_ids": [1, 2, 3],
                },
                "option/1": {
                    "id": 1,
                    "weight": 1,
                    "poll_id": 1,
                    "meeting_id": 1,
                    "content_object_id": "poll_candidate_list/1",
                },
                "option/2": {
                    "id": 2,
                    "text": "global option",
                    "weight": 1,
                    "meeting_id": 1,
                    "used_as_global_option_in_poll_id": 1,
                },
                "poll/1": {
                    "id": 1,
                    "type": "pseudoanonymous",
                    "state": "created",
                    "title": "First election",
                    "backend": "fast",
                    "global_no": False,
                    "votescast": "0.000000",
                    "global_yes": False,
                    "meeting_id": 1,
                    "option_ids": [1],
                    "pollmethod": "YNA",
                    "votesvalid": "0.000000",
                    "votesinvalid": "0.000000",
                    "global_abstain": False,
                    "global_option_id": 2,
                    "max_votes_amount": 1,
                    "min_votes_amount": 1,
                    "content_object_id": "assignment/1",
                    "sequential_number": 1,
                    "is_pseudoanonymized": True,
                    "max_votes_per_option": 1,
                    "onehundred_percent_base": "disabled",
                },
            }
        )
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/2",
            {
                "committee_id": 60,
                "list_of_speakers_ids": [2],
                "assignment_ids": [2],
                "poll_candidate_list_ids": [2],
                "poll_candidate_ids": [4, 5, 6],
                "option_ids": [3, 4],
                "poll_ids": [2],
                "projector_ids": [2],
                "reference_projector_id": 2,
                **{key: [2] for key in MeetingModelMixin.all_default_projectors()},
                "motions_default_amendment_workflow_id": 2,
            },
        )
