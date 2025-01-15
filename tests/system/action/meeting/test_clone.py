from time import time
from typing import Any, cast
from unittest.mock import MagicMock

from openslides_backend.action.action_worker import ActionWorkerState
from openslides_backend.models.mixins import MeetingModelMixin
from openslides_backend.models.models import AgendaItem, Meeting
from openslides_backend.shared.util import (
    ONE_ORGANIZATION_FQID,
    ONE_ORGANIZATION_ID,
    fqid_from_collection_and_id,
)
from tests.system.action.base import BaseActionTestCase
from tests.system.util import CountDatastoreCalls, Profiler, performance


class MeetingClone(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.test_models: dict[str, dict[str, Any]] = {
            ONE_ORGANIZATION_FQID: {
                "active_meeting_ids": [1],
                "organization_tag_ids": [1],
                "user_ids": [1],
                "template_meeting_ids": [1],
            },
            "organization_tag/1": {
                "name": "TEST",
                "color": "#eeeeee",
                "organization_id": 1,
            },
            "committee/1": {"organization_id": 1},
            "meeting/1": {
                "template_for_organization_id": 1,
                "committee_id": 1,
                "language": "en",
                "name": "Test",
                "default_group_id": 1,
                "admin_group_id": 2,
                "motions_default_amendment_workflow_id": 1,
                "motions_default_workflow_id": 1,
                "reference_projector_id": 1,
                "projector_countdown_default_time": 60,
                "projector_countdown_warning_time": 5,
                "projector_ids": [1],
                "group_ids": [1, 2],
                "motion_state_ids": [1],
                "motion_workflow_ids": [1],
                **{field: [1] for field in Meeting.all_default_projectors()},
                "is_active_in_organization_id": 1,
            },
            "group/1": {
                "meeting_id": 1,
                "name": "default group",
                "weight": 1,
                "default_group_for_meeting_id": 1,
            },
            "group/2": {
                "meeting_id": 1,
                "name": "admin group",
                "weight": 1,
                "admin_group_for_meeting_id": 1,
            },
            "motion_workflow/1": {
                "meeting_id": 1,
                "name": "blup",
                "first_state_id": 1,
                "default_amendment_workflow_meeting_id": 1,
                "default_workflow_meeting_id": 1,
                "state_ids": [1],
                "sequential_number": 1,
            },
            "motion_state/1": {
                "css_class": "lightblue",
                "meeting_id": 1,
                "workflow_id": 1,
                "name": "test",
                "weight": 1,
                "workflow_id": 1,
                "first_state_of_workflow_id": 1,
            },
            "projector/1": {
                "sequential_number": 1,
                "meeting_id": 1,
                "used_as_reference_projector_meeting_id": 1,
                "name": "Default projector",
                **{field: 1 for field in Meeting.reverse_default_projectors()},
            },
        }
        self.test_models_with_admin = {
            key: data.copy() for key, data in self.test_models.items()
        }
        self.test_models_with_admin["user/1"] = {
            "meeting_user_ids": [1],
            "meeting_ids": [1],
            "organization_id": 1,
        }
        self.test_models_with_admin["meeting_user/1"] = {
            "user_id": 1,
            "meeting_id": 1,
            "group_ids": [2],
        }
        self.test_models_with_admin["group/2"]["meeting_user_ids"] = [1]
        self.test_models_with_admin["meeting/1"].update(
            {"user_ids": [1], "meeting_user_ids": [1]}
        )
        self.test_models_with_admin["organization/1"]["user_ids"] = [1]

    def test_clone_without_users(self) -> None:
        self.set_models(self.test_models)

        response = self.request(
            "meeting.clone", {"meeting_id": 1, "set_as_template": True}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/2",
            {
                "committee_id": 1,
                "name": "Test - Copy",
                "default_group_id": 3,
                "admin_group_id": 4,
                "motions_default_amendment_workflow_id": 2,
                "motions_default_workflow_id": 2,
                "reference_projector_id": 2,
                "projector_countdown_default_time": 60,
                "projector_countdown_warning_time": 5,
                "projector_ids": [2],
                "group_ids": [3, 4],
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
        self.set_models(self.test_models_with_admin)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("group/2", {"weight": 1})

    def test_clone_with_users_inc_vote_weight(self) -> None:
        self.test_models["meeting/1"]["user_ids"] = [1]
        self.test_models["meeting/1"]["meeting_user_ids"] = [1]
        self.test_models["group/2"]["meeting_user_ids"] = [1]
        self.set_models(
            {
                "user/1": {
                    "meeting_user_ids": [1],
                    "meeting_ids": [1],
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [2],
                    "vote_weight": "1.000000",
                },
            }
        )
        self.set_models(self.test_models)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"user_ids": [1]})
        self.assert_model_exists("meeting/2", {"user_ids": [1]})
        self.assert_model_exists(
            "group/4",
            {
                "meeting_user_ids": [2],
                "meeting_id": 2,
            },
        )
        self.assert_model_exists(
            "user/1",
            {
                "meeting_user_ids": [1, 2],
                "meeting_ids": [1, 2],
                "committee_ids": [1],
                "organization_id": 1,
            },
        )
        self.assert_model_exists(
            "meeting_user/1",
            {
                "meeting_id": 1,
                "user_id": 1,
                "group_ids": [2],
                "vote_weight": "1.000000",
            },
        )
        self.assert_model_exists(
            "meeting_user/2",
            {
                "meeting_id": 2,
                "user_id": 1,
                "group_ids": [4],
                "vote_weight": "1.000000",
            },
        )

    def test_clone_with_users_min_vote_weight_NN_N(self) -> None:
        """if vote_weight and default vote weight are None, both could remain None, because
        they are not required"""
        self.test_models["meeting/1"]["user_ids"] = [1]
        self.test_models["meeting/1"]["meeting_user_ids"] = [1]
        self.test_models["group/2"]["meeting_user_ids"] = [1]
        self.set_models(
            {
                "user/1": {
                    "meeting_user_ids": [1],
                    "meeting_ids": [1],
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [2],
                },
            }
        )
        self.set_models(self.test_models)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"user_ids": [1]})
        self.assert_model_exists("meeting/2", {"user_ids": [1]})
        self.assert_model_exists(
            "user/1",
            {
                "meeting_user_ids": [1, 2],
                "meeting_ids": [1, 2],
                "committee_ids": [1],
                "organization_id": 1,
            },
        )
        self.assert_model_exists(
            "meeting_user/2",
            {
                "meeting_id": 2,
                "user_id": 1,
                "group_ids": [4],
                "vote_weight": None,
            },
        )

    def test_clone_with_users_min_vote_weight_N1_N(self) -> None:
        """vote_weight can remain None, because default_vote_weight is set greater than minimum"""
        self.test_models["meeting/1"]["user_ids"] = [1]
        self.test_models["meeting/1"]["meeting_user_ids"] = [1]
        self.test_models["group/2"]["meeting_user_ids"] = [1]
        self.set_models(
            {
                "user/1": {
                    "meeting_user_ids": [1],
                    "meeting_ids": [1],
                    "default_vote_weight": "1.000000",
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [2],
                },
            }
        )
        self.set_models(self.test_models)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"user_ids": [1]})
        self.assert_model_exists("meeting/2", {"user_ids": [1]})
        self.assert_model_exists(
            "user/1",
            {
                "meeting_user_ids": [1, 2],
                "meeting_ids": [1, 2],
                "committee_ids": [1],
                "organization_id": 1,
                "default_vote_weight": "1.000000",
            },
        )
        self.assert_model_exists(
            "meeting_user/2",
            {
                "meeting_id": 2,
                "user_id": 1,
                "group_ids": [4],
                "vote_weight": None,
            },
        )

    def test_clone_with_users_min_vote_weight_0X_1(self) -> None:
        """vote_weight set to 0: must be set to 0.000001 any way"""
        self.test_models["meeting/1"]["user_ids"] = [1]
        self.test_models["meeting/1"]["meeting_user_ids"] = [1]
        self.test_models["group/2"]["meeting_user_ids"] = [1]
        self.set_models(
            {
                "user/1": {
                    "meeting_user_ids": [1],
                    "meeting_ids": [1],
                    "default_vote_weight": "1.000000",
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [2],
                    "vote_weight": "0.000000",
                },
            }
        )
        self.set_models(self.test_models)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"user_ids": [1]})
        self.assert_model_exists("meeting/2", {"user_ids": [1]})
        self.assert_model_exists(
            "user/1",
            {
                "meeting_user_ids": [1, 2],
                "meeting_ids": [1, 2],
                "committee_ids": [1],
                "organization_id": 1,
            },
        )
        self.assert_model_exists(
            "meeting_user/2",
            {
                "meeting_id": 2,
                "user_id": 1,
                "group_ids": [4],
                "vote_weight": "0.000001",
            },
        )

    def test_clone_with_users_min_vote_weight_N0_1(self) -> None:
        """vote_weight None, default_vote_weight 0, must be set to 0.000001"""
        self.test_models["meeting/1"]["user_ids"] = [1]
        self.test_models["meeting/1"]["meeting_user_ids"] = [1]
        self.test_models["group/2"]["meeting_user_ids"] = [1]
        self.set_models(
            {
                "user/1": {
                    "meeting_user_ids": [1],
                    "meeting_ids": [1],
                    "default_vote_weight": "0.000000",
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [2],
                },
            }
        )
        self.set_models(self.test_models)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"user_ids": [1]})
        self.assert_model_exists("meeting/2", {"user_ids": [1]})
        self.assert_model_exists(
            "user/1",
            {
                "meeting_user_ids": [1, 2],
                "meeting_ids": [1, 2],
                "committee_ids": [1],
                "organization_id": 1,
                "default_vote_weight": "0.000000",
            },
        )
        self.assert_model_exists(
            "meeting_user/2",
            {
                "meeting_id": 2,
                "user_id": 1,
                "group_ids": [4],
                "vote_weight": "0.000001",
            },
        )

    def test_clone_with_ex_users(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "meeting_user_ids": [2],
                    "meeting_ids": [1],
                },
                "user/11": {
                    "username": "exuser1",
                    "organization_id": 1,
                    "meeting_user_ids": [3],
                    "meeting_ids": [1],
                },
                "user/12": {
                    "username": "admin_ids_user",
                    "organization_id": 1,
                },
                "user/13": {
                    "username": "user_ids_user",
                    "organization_id": 1,
                },
                "motion/1": {
                    "list_of_speakers_id": 1,
                    "meeting_id": 1,
                    "sequential_number": 1,
                    "state_id": 1,
                    "submitter_ids": [1],
                    "title": "dummy",
                },
                "motion_submitter/1": {
                    "meeting_user_id": 3,
                    "motion_id": 1,
                    "meeting_id": 1,
                },
                "committee/2": {"organization_id": 1},
                "meeting/1": {
                    "motion_submitter_ids": [1],
                    "motion_ids": [1],
                    "list_of_speakers_ids": [1],
                },
                "list_of_speakers/1": {
                    "content_object_id": "motion/1",
                    "meeting_id": 1,
                    "sequential_number": 1,
                },
                "motion_state/1": {
                    "motion_ids": [1],
                },
                "meeting_user/2": {
                    "user_id": 1,
                    "meeting_id": 1,
                    "group_ids": [1],
                },
                "meeting_user/3": {
                    "user_id": 11,
                    "meeting_id": 1,
                    "motion_submitter_ids": [1],
                    "group_ids": [1],
                },
            }
        )
        self.test_models["meeting/1"]["user_ids"] = [1, 11]
        self.test_models["meeting/1"]["meeting_user_ids"] = [2, 3]
        self.test_models["group/1"]["meeting_user_ids"] = [2, 3]
        self.test_models["organization/1"]["user_ids"] = [1, 11, 12, 13]
        self.test_models["organization/1"]["committee_ids"] = [1, 2]
        self.set_models(self.test_models)
        response = self.request(
            "meeting.clone",
            {"committee_id": 2, "meeting_id": 1, "admin_ids": [12], "user_ids": [13]},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"user_ids": [1, 11]})
        self.assert_model_exists(
            "meeting/2",
            {
                "committee_id": 2,
                "motion_submitter_ids": [2],
                "motion_ids": [2],
                "group_ids": [3, 4],
                "meeting_user_ids": [4, 5, 6, 7],
                "user_ids": [1, 11, 13, 12],
            },
        )

        self.assert_model_exists(
            "group/3",
            {"name": "default group", "meeting_id": 2, "meeting_user_ids": [4, 5, 6]},
        )
        self.assert_model_exists(
            "group/4", {"name": "admin group", "meeting_id": 2, "meeting_user_ids": [7]}
        )

        self.assert_model_exists(
            "user/1",
            {
                "meeting_ids": [1, 2],
                "meeting_user_ids": [2, 4],
                "committee_ids": [1, 2],
            },
        )
        self.assert_model_exists(
            "meeting_user/2", {"user_id": 1, "meeting_id": 1, "group_ids": [1]}
        )
        self.assert_model_exists(
            "meeting_user/4", {"user_id": 1, "meeting_id": 2, "group_ids": [3]}
        )

        self.assert_model_exists(
            "user/11",
            {
                "meeting_ids": [1, 2],
                "meeting_user_ids": [3, 5],
                "committee_ids": [1, 2],
            },
        )
        self.assert_model_exists(
            "meeting_user/3", {"user_id": 11, "meeting_id": 1, "group_ids": [1]}
        )
        self.assert_model_exists(
            "meeting_user/5", {"user_id": 11, "meeting_id": 2, "group_ids": [3]}
        )

        self.assert_model_exists(
            "user/12",
            {
                "username": "admin_ids_user",
                "meeting_ids": [2],
                "meeting_user_ids": [7],
                "committee_ids": [2],
            },
        )
        self.assert_model_exists(
            "meeting_user/7", {"user_id": 12, "meeting_id": 2, "group_ids": [4]}
        )

        self.assert_model_exists(
            "user/13",
            {
                "username": "user_ids_user",
                "meeting_ids": [2],
                "meeting_user_ids": [6],
                "committee_ids": [2],
            },
        )
        self.assert_model_exists(
            "meeting_user/6", {"user_id": 13, "meeting_id": 2, "group_ids": [3]}
        )

        self.assert_model_exists(
            "motion_submitter/2",
            {"meeting_user_id": 5, "meeting_id": 2, "motion_id": 2},
        )
        self.assert_model_exists(
            "motion/2",
            {
                "meeting_id": 2,
                "submitter_ids": [2],
            },
        )

    def test_clone_with_set_fields(self) -> None:
        self.test_models_with_admin["meeting/1"][
            "template_for_organization_id"
        ] = ONE_ORGANIZATION_ID
        self.set_models(self.test_models_with_admin)

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
                "start_time": 1641370959,
                "end_time": 1641370959,
                "name": "name_ORnVFSQJ",
                "external_id": "external_id",
                "template_for_organization_id": None,
            },
        )
        self.assert_model_exists("organization_tag/1", {"tagged_ids": ["meeting/2"]})

    def test_clone_with_duplicate_external_id(self) -> None:
        self.test_models["meeting/1"][
            "template_for_organization_id"
        ] = ONE_ORGANIZATION_ID
        self.test_models["meeting/1"]["external_id"] = "external_id"
        self.set_models(self.test_models)
        response = self.request(
            "meeting.clone",
            {
                "meeting_id": 1,
                "external_id": "external_id",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The external_id of the meeting is not unique in the committee scope.",
            response.json["message"],
        )

    def test_clone_with_recommendation_extension(self) -> None:
        self.set_models(self.test_models_with_admin)
        self.set_models(
            {
                "meeting/1": {
                    "motion_ids": [22, 23],
                    "list_of_speakers_ids": [1, 2],
                },
                "motion/22": {
                    "id": 22,
                    "title": "test",
                    "sequential_number": 1,
                    "meeting_id": 1,
                    "list_of_speakers_id": 1,
                    "state_id": 1,
                    "state_extension": "[motion/23]",
                    "state_extension_reference_ids": ["motion/23"],
                    "recommendation_extension": "[motion/23]",
                    "recommendation_extension_reference_ids": ["motion/23"],
                },
                "motion/23": {
                    "id": 23,
                    "title": "test",
                    "sequential_number": 2,
                    "meeting_id": 1,
                    "list_of_speakers_id": 2,
                    "state_id": 1,
                    "referenced_in_motion_state_extension_ids": [22],
                    "referenced_in_motion_recommendation_extension_ids": [22],
                },
                "motion_state/1": {
                    "motion_ids": [22, 23],
                },
                "list_of_speakers/1": {
                    "meeting_id": 1,
                    "content_object_id": "motion/22",
                    "sequential_number": 1,
                },
                "list_of_speakers/2": {
                    "meeting_id": 1,
                    "content_object_id": "motion/23",
                    "sequential_number": 2,
                },
            }
        )

        response = self.request(
            "meeting.clone",
            {
                "meeting_id": 1,
            },
        )
        self.assert_status_code(response, 200)
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
        self.test_models["meeting/1"]["template_for_organization_id"] = None
        self.test_models["meeting/1"]["meeting_user_ids"] = [115, 116]
        self.test_models["organization/1"]["user_ids"] = [1, 13, 14, 15, 16]
        self.set_models(self.test_models)
        self.set_models(
            {
                "user/13": {"username": "new_admin_user", "organization_id": 1},
                "user/14": {"username": "new_default_group_user", "organization_id": 1},
                "user/15": {
                    "username": "new_and_old_default_group_user",
                    "meeting_user_ids": [115],
                    "meeting_ids": [1],
                    "organization_id": 1,
                },
                "user/16": {
                    "username": "new_default_group_old_admin_user",
                    "meeting_user_ids": [116],
                    "meeting_ids": [1],
                    "organization_id": 1,
                },
                "group/1": {"meeting_user_ids": [115]},
                "group/2": {"meeting_user_ids": [116]},
                "meeting/1": {"user_ids": [15, 16]},
                "meeting_user/115": {
                    "meeting_id": 1,
                    "user_id": 15,
                    "group_ids": [1],
                },
                "meeting_user/116": {
                    "meeting_id": 1,
                    "user_id": 16,
                    "group_ids": [2],
                },
            }
        )

        response = self.request(
            "meeting.clone",
            {
                "meeting_id": 1,
                "user_ids": [14, 15, 16],
                "admin_ids": [13],
                "set_as_template": False,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("organization/1", {"template_meeting_ids": [1]})
        meeting2 = self.assert_model_exists(
            "meeting/2", {"template_for_organization_id": None}
        )
        self.assertCountEqual(meeting2["user_ids"], [13, 14, 15, 16])
        group3 = self.assert_model_exists("group/3")
        self.assertCountEqual(group3["meeting_user_ids"], [117, 118, 119])
        group4 = self.assert_model_exists("group/4")
        self.assertCountEqual(group4["meeting_user_ids"], [120, 118])
        self.assert_model_exists(
            "user/13",
            {
                "username": "new_admin_user",
                "meeting_user_ids": [120],
                "meeting_ids": [2],
            },
        )
        self.assert_model_exists(
            "meeting_user/120", {"meeting_id": 2, "user_id": 13, "group_ids": [4]}
        )
        self.assert_model_exists(
            "user/14",
            {
                "username": "new_default_group_user",
                "meeting_user_ids": [119],
                "meeting_ids": [2],
            },
        )
        self.assert_model_exists(
            "meeting_user/119", {"meeting_id": 2, "user_id": 14, "group_ids": [3]}
        )

        self.assert_model_exists(
            "user/15",
            {
                "username": "new_and_old_default_group_user",
                "meeting_user_ids": [115, 117],
                "meeting_ids": [1, 2],
            },
        )
        self.assert_model_exists(
            "meeting_user/115", {"meeting_id": 1, "user_id": 15, "group_ids": [1]}
        )
        self.assert_model_exists(
            "meeting_user/117", {"meeting_id": 2, "user_id": 15, "group_ids": [3]}
        )

        self.assert_model_exists(
            "user/16",
            {
                "username": "new_default_group_old_admin_user",
                "meeting_user_ids": [116, 118],
                "meeting_ids": [1, 2],
            },
        )
        self.assert_model_exists(
            "meeting_user/116", {"meeting_id": 1, "user_id": 16, "group_ids": [2]}
        )
        self.assert_model_exists(
            "meeting_user/118", {"meeting_id": 2, "user_id": 16, "group_ids": [4, 3]}
        )

    def test_clone_new_committee_and_user_with_group(self) -> None:
        self.test_models["organization/1"]["user_ids"] = [1, 13]
        self.set_models(self.test_models_with_admin)
        self.set_models(
            {
                "user/13": {
                    "username": "user_from_new_committee",
                    "meeting_user_ids": [2],
                    "meeting_ids": [1],
                    "organization_id": 1,
                    "gender_id": 1,
                },
                "gender/1": {"name": "male", "organization_id": 1, "user_ids": [3]},
                "group/1": {"meeting_user_ids": [2]},
                "committee/2": {"organization_id": 1},
                "organization/1": {"committee_ids": [1, 2], "gender_ids": [1]},
                "meeting/1": {"user_ids": [1, 13], "meeting_user_ids": [1, 2]},
                "meeting_user/2": {
                    "meeting_id": 1,
                    "user_id": 13,
                    "group_ids": [1],
                },
            }
        )
        response = self.request(
            "meeting.clone",
            {
                "meeting_id": 1,
                "user_ids": [13],
                "committee_id": 2,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/2", {"committee_id": 2, "user_ids": [13, 1]})
        self.assert_model_exists(
            "committee/2",
            {"user_ids": [1, 13], "organization_id": 1, "meeting_ids": [2]},
        )
        self.assert_model_exists(
            "user/13",
            {
                "username": "user_from_new_committee",
                "committee_ids": [1, 2],
                "meeting_ids": [1, 2],
                "meeting_user_ids": [2, 4],
                "gender_id": 1,
            },
        )
        self.assert_model_exists(
            "meeting_user/2",
            {
                "meeting_id": 1,
                "user_id": 13,
                "group_ids": [1],
            },
        )
        self.assert_model_exists(
            "meeting_user/4",
            {
                "meeting_id": 2,
                "user_id": 13,
                "group_ids": [3],
            },
        )
        self.assert_model_exists("group/3", {"meeting_user_ids": [4]})

    def test_clone_new_committee_and_add_user(self) -> None:
        self.set_models(self.test_models_with_admin)
        self.set_models(
            {
                "user/13": {
                    "username": "user_from_new_committee",
                    "organization_id": 1,
                },
                "committee/2": {"organization_id": 1},
                "organization/1": {"committee_ids": [1, 2], "user_ids": [1, 13]},
            }
        )
        response = self.request(
            "meeting.clone",
            {
                "meeting_id": 1,
                "user_ids": [13],
                "committee_id": 2,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/2", {"committee_id": 2, "user_ids": [13, 1], "default_group_id": 3}
        )
        self.assert_model_exists(
            "committee/2",
            {"user_ids": [1, 13], "organization_id": 1, "meeting_ids": [2]},
        )
        self.assert_model_exists(
            "user/13",
            {
                "username": "user_from_new_committee",
                "committee_ids": [2],
                "meeting_ids": [2],
                "meeting_user_ids": [3],
            },
        )
        self.assert_model_exists(
            "meeting_user/3",
            {
                "meeting_id": 2,
                "user_id": 13,
                "group_ids": [3],
            },
        )
        self.assert_model_exists(
            "group/3", {"meeting_user_ids": [3], "default_group_for_meeting_id": 2}
        )

    def test_clone_missing_user_id_in_meeting(self) -> None:
        self.set_models(self.test_models)
        self.set_models(
            {
                "group/1": {"meeting_user_ids": [13]},
                "meeting/1": {"user_ids": [13]},
            }
        )

        response = self.request(
            "meeting.clone",
            {
                "meeting_id": 1,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "\tgroup/1/meeting_user_ids: Relation Error:  points to meeting_user/13/group_ids, but the reverse relation for it is corrupt",
            response.json["message"],
        )

    def test_clone_missing_user_id_in_additional_users(self) -> None:
        self.set_models(self.test_models_with_admin)

        response = self.request(
            "meeting.clone",
            {
                "meeting_id": 1,
                "user_ids": [13],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Datastore service sends HTTP 400. Model 'user/13' does not exist.",
            response.json["message"],
        )

    def test_clone_with_personal_note(self) -> None:
        self.test_models_with_admin["meeting/1"]["personal_note_ids"] = [1]
        self.test_models_with_admin["meeting_user/1"]["personal_note_ids"] = [1]
        self.set_models(
            {
                "personal_note/1": {
                    "note": "test note",
                    "meeting_user_id": 1,
                    "meeting_id": 1,
                }
            }
        )
        self.set_models(self.test_models_with_admin)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {
                "meeting_user_ids": [1, 2],
            },
        )
        self.assert_model_exists(
            "meeting_user/2",
            {
                "personal_note_ids": [2],
                "user_id": 1,
                "meeting_id": 2,
            },
        )

    def test_clone_with_option(self) -> None:
        self.test_models["meeting/1"]["user_ids"] = [1]
        self.test_models["meeting/1"]["option_ids"] = [1]
        self.test_models["meeting/1"]["meeting_user_ids"] = [1]
        self.test_models["group/2"]["meeting_user_ids"] = [1]
        self.set_models(
            {
                "user/1": {
                    "meeting_user_ids": [1],
                    "option_ids": [1],
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [2],
                },
                "option/1": {"content_object_id": "user/1", "meeting_id": 1},
            }
        )
        self.set_models(self.test_models)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/1", {"option_ids": [1, 2]})

    def test_clone_with_mediafile(self) -> None:
        self.test_models["meeting/1"]["user_ids"] = [1]
        self.test_models["meeting/1"]["mediafile_ids"] = [1, 2]
        self.test_models["meeting/1"]["meeting_mediafile_ids"] = [10, 20]
        self.test_models["meeting/1"]["meeting_user_ids"] = [1]
        self.test_models["group/2"]["meeting_user_ids"] = [1]
        self.set_models(self.test_models)
        self.set_models(
            {
                "meeting/1": {
                    "logo_web_header_id": 10,
                    "font_bold_id": 20,
                    "meeting_user_ids": [1],
                },
                "user/1": {
                    "meeting_user_ids": [1],
                    "meeting_ids": [1],
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [2],
                },
                "mediafile/1": {
                    "owner_id": "meeting/1",
                    "mimetype": "text/plain",
                    "meeting_mediafile_ids": [10],
                },
                "mediafile/2": {
                    "owner_id": "meeting/1",
                    "mimetype": "text/plain",
                    "meeting_mediafile_ids": [20],
                },
                "meeting_mediafile/10": {
                    "meeting_id": 1,
                    "mediafile_id": 1,
                    "attachment_ids": [],
                    "is_public": True,
                    "used_as_logo_web_header_in_meeting_id": 1,
                },
                "meeting_mediafile/20": {
                    "meeting_id": 1,
                    "mediafile_id": 2,
                    "attachment_ids": [],
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

    def test_clone_with_mediafile_directory(self) -> None:
        self.test_models["meeting/1"]["user_ids"] = [1]
        self.test_models["meeting/1"]["meeting_user_ids"] = [1]
        self.test_models["group/2"]["meeting_user_ids"] = [1]
        self.set_models(
            {
                "user/1": {
                    "meeting_user_ids": [1],
                    "meeting_ids": [1],
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [2],
                },
            }
        )
        self.set_models(self.test_models)
        response = self.request(
            "mediafile.create_directory", {"owner_id": "meeting/1", "title": "bla"}
        )
        self.assert_status_code(response, 200)

        self.media.duplicate_mediafile = MagicMock()
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)

    def test_clone_with_organization_tag(self) -> None:
        self.test_models_with_admin["meeting/1"]["organization_tag_ids"] = [1]
        self.set_models(
            {
                "organization_tag/1": {
                    "name": "Test",
                    "color": "#ffffff",
                    "tagged_ids": ["meeting/1"],
                }
            }
        )
        self.set_models(self.test_models_with_admin)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/2", {"organization_tag_ids": [1]})
        self.assert_model_exists(
            "organization_tag/1", {"tagged_ids": ["meeting/1", "meeting/2"]}
        )

    def test_clone_with_settings(self) -> None:
        self.set_models(self.test_models_with_admin)
        settings = {
            "welcome_title": "title",
            "welcome_text": "text",
            "name": "name",
            "description": "desc",
            "location": "loc",
            "start_time": 1633522986,
            "end_time": 1633522986,
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
        self.update_model("meeting/1", settings)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        settings["name"] += " - Copy"  # type: ignore
        self.assert_model_exists("meeting/2", settings)

    def test_limit_of_meetings_error(self) -> None:
        self.test_models_with_admin[ONE_ORGANIZATION_FQID]["limit_of_meetings"] = 1
        self.set_models(self.test_models_with_admin)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 400)
        self.assertIn(
            "You cannot clone an meeting, because you reached your limit of 1 active meetings.",
            response.json["message"],
        )

    def test_limit_of_meetings_error_archived_meeting(self) -> None:
        self.test_models_with_admin[ONE_ORGANIZATION_FQID]["limit_of_meetings"] = 1
        self.test_models_with_admin[ONE_ORGANIZATION_FQID]["active_meeting_ids"] = [3]
        self.test_models_with_admin["meeting/1"]["is_active_in_organization_id"] = None
        self.set_models(self.test_models_with_admin)

        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 400)
        self.assertIn(
            "You cannot clone an meeting, because you reached your limit of 1 active meetings.",
            response.json["message"],
        )

    def test_activate_archived_meeting(self) -> None:
        self.test_models_with_admin[ONE_ORGANIZATION_FQID]["limit_of_meetings"] = 2
        self.test_models_with_admin[ONE_ORGANIZATION_FQID]["active_meeting_ids"] = [3]
        self.test_models_with_admin["meeting/1"]["is_active_in_organization_id"] = None
        self.test_models_with_admin["meeting/1"]["is_archived_in_organization_id"] = 1
        self.test_models_with_admin[ONE_ORGANIZATION_FQID]["archived_meeting_ids"] = [1]
        self.set_models(self.test_models_with_admin)

        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/2",
            {"is_active_in_organization_id": 1, "is_archived_in_organization_id": None},
        )
        self.assert_model_exists(
            ONE_ORGANIZATION_FQID,
            {"active_meeting_ids": [3, 2], "archived_meeting_ids": [1]},
        )

    def test_limit_of_meetings_ok(self) -> None:
        self.test_models_with_admin[ONE_ORGANIZATION_FQID]["limit_of_meetings"] = 2
        self.set_models(self.test_models_with_admin)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        organization = self.get_model(ONE_ORGANIZATION_FQID)
        self.assertCountEqual(organization["active_meeting_ids"], [1, 2])

    def test_create_clone(self) -> None:
        self.set_models(
            {
                "committee/1": {"organization_id": 1, "user_ids": [2, 3]},
                "user/2": {
                    "committee_ids": [1],
                    "username": "user2",
                    "organization_id": 1,
                },
                "user/3": {
                    "committee_ids": [1],
                    "username": "user3",
                    "organization_id": 1,
                },
                "organization/1": {"user_ids": [1, 2, 3]},
            }
        )
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
                "admin_ids": [2],
                "organization_tag_ids": [],
                "language": "en",
            },
        )
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)

    def test_create_clone_without_admin(self) -> None:
        self.set_models(
            {
                "committee/1": {"organization_id": 1, "user_ids": [2, 3]},
                "user/2": {
                    "committee_ids": [1],
                    "username": "user2",
                    "organization_id": 1,
                },
                "user/3": {
                    "committee_ids": [1],
                    "username": "user3",
                    "organization_id": 1,
                },
                "organization/1": {"user_ids": [1, 2, 3]},
            }
        )
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
                "admin_ids": [1],
                "organization_tag_ids": [],
                "language": "en",
            },
        )
        everything = self.datastore.get_everything()
        self.created_fqids.update(
            [
                fqid_from_collection_and_id(collection, id_)
                for collection, data in everything.items()
                for id_ in data.keys()
            ]
        )
        self.set_models(
            {"meeting_user/1": {"group_ids": []}, "group/2": {"meeting_user_ids": []}}
        )
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 400)
        assert (
            "Cannot create a non-template meeting without administrators"
            in response.json["message"]
        )

    def test_create_clone_without_admin_2(self) -> None:
        self.set_models(
            {
                "committee/1": {"organization_id": 1, "user_ids": [2, 3]},
                "user/2": {
                    "committee_ids": [1],
                    "username": "user2",
                    "organization_id": 1,
                },
                "user/3": {
                    "committee_ids": [1],
                    "username": "user3",
                    "organization_id": 1,
                },
                "organization/1": {"user_ids": [1, 2, 3]},
            }
        )
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
                "admin_ids": [1],
                "organization_tag_ids": [],
                "language": "en",
            },
        )
        everything = self.datastore.get_everything()
        self.created_fqids.update(
            [
                fqid_from_collection_and_id(collection, id_)
                for collection, data in everything.items()
                for id_ in data.keys()
            ]
        )
        self.set_models(
            {
                "meeting_user/1": {"group_ids": None},
                "group/2": {"meeting_user_ids": None},
            }
        )
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 400)
        assert (
            "Cannot create a non-template meeting without administrators"
            in response.json["message"]
        )

    def test_meeting_name_exact_fit(self) -> None:
        long_name = "A" * 93
        self.test_models_with_admin["meeting/1"]["name"] = long_name
        self.set_models(self.test_models_with_admin)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/2", {"name": long_name + " - Copy"})

    def test_meeting_name_too_long(self) -> None:
        long_name = "A" * 100
        self.test_models_with_admin["meeting/1"]["name"] = long_name
        self.set_models(self.test_models_with_admin)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/2", {"name": "A" * 90 + "... - Copy"})

    def test_permissions_explicit_source_committee_permission(self) -> None:
        self.set_models(self.test_models)
        self.set_models(
            {
                "user/1": {
                    "committee_management_ids": [1],
                    "committee_ids": [1],
                    "organization_management_level": None,
                },
            }
        )
        response = self.request(
            "meeting.clone", {"meeting_id": 1, "committee_id": 1, "admin_ids": [1]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/1", {"is_active_in_organization_id": 1, "committee_id": 1}
        )
        self.assert_model_exists(
            "meeting/2", {"is_active_in_organization_id": 1, "committee_id": 1}
        )

    def test_permissions_foreign_template_meeting_cml(self) -> None:
        self.set_models(self.test_models)
        self.set_models(
            {
                "committee/2": {"organization_id": 1},
                "user/1": {
                    "committee_management_ids": [1, 2],
                    "committee_ids": [2],
                    "organization_management_level": None,
                },
                "meeting/1": {"template_for_organization_id": 1},
            }
        )
        response = self.request(
            "meeting.clone", {"meeting_id": 1, "committee_id": 2, "admin_ids": [1]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/1", {"is_active_in_organization_id": 1, "committee_id": 1}
        )
        self.assert_model_exists(
            "meeting/2", {"is_active_in_organization_id": 1, "committee_id": 2}
        )

    def test_permissions_foreign_committee_cml_error(self) -> None:
        self.set_models(self.test_models)
        self.set_models(
            {
                "committee/2": {"organization_id": 1},
                "user/1": {
                    "committee_management_ids": [1],
                    "committee_ids": [1],
                    "organization_management_level": None,
                },
            }
        )
        response = self.request("meeting.clone", {"meeting_id": 1, "committee_id": 2})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action meeting.clone. Missing permission: CommitteeManagementLevel can_manage in committee 2",
            response.json["message"],
        )

    def test_permissions_oml_can_manage(self) -> None:
        self.set_models(self.test_models_with_admin)
        self.set_models(
            {
                "committee/2": {"organization_id": 1},
                "user/1": {
                    "organization_management_level": "can_manage_organization",
                },
            }
        )
        response = self.request("meeting.clone", {"meeting_id": 1, "committee_id": 2})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/1", {"is_active_in_organization_id": 1, "committee_id": 1}
        )
        self.assert_model_exists(
            "meeting/2", {"is_active_in_organization_id": 1, "committee_id": 2}
        )

    def test_permissions_missing_source_committee_permission(self) -> None:
        self.set_models(self.test_models_with_admin)
        self.set_models(
            {
                "committee/2": {"organization_id": 1},
                "user/1": {
                    "committee_management_ids": [2],
                    "committee_ids": [2],
                    "organization_management_level": None,
                },
            }
        )
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 403)
        self.assertIn(
            "Missing permission: CommitteeManagementLevel can_manage in committee 1",
            response.json["message"],
        )

    def test_clone_with_created_topic_and_agenda_type(self) -> None:
        self.set_models(self.test_models_with_admin)

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
        self.test_models_with_admin["meeting/1"]["user_ids"] = [1]
        self.set_models(self.test_models_with_admin)
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
        self.test_models_with_admin["meeting/1"]["is_active_in_organization_id"] = None
        self.set_models(self.test_models_with_admin)

        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"is_active_in_organization_id": None})

    def test_clone_with_forwarded_motion(self) -> None:
        self.set_models(self.test_models_with_admin)
        self.set_models(
            {
                "committee/1": {"organization_id": 1, "meeting_ids": [1, 2]},
                "meeting/1": {
                    "motion_ids": [1, 4],
                    "motion_state_ids": [1],
                    "list_of_speakers_ids": [1, 4],
                },
                "meeting/2": {
                    "motion_ids": [2, 3],
                    "is_active_in_organization_id": 1,
                },
                "motion/1": {
                    "meeting_id": 1,
                    "derived_motion_ids": [2],
                    "all_derived_motion_ids": [2],
                    "sequential_number": 1,
                    "list_of_speakers_id": 1,
                    "title": "motion1",
                    "state_id": 1,
                },
                "motion/2": {
                    "meeting_id": 2,
                    "origin_id": 1,
                    "origin_meeting_id": 1,
                    "all_origin_ids": [1],
                    "sequential_number": 1,
                    "list_of_speakers_id": 2,
                    "title": "motion1 forwarded",
                    "state_id": 2,
                },
                "motion/3": {
                    "meeting_id": 2,
                    "derived_motion_ids": [4],
                    "all_derived_motion_ids": [4],
                    "sequential_number": 2,
                    "list_of_speakers_id": 3,
                    "title": "motion3",
                    "state_id": 2,
                },
                "motion/4": {
                    "meeting_id": 1,
                    "origin_id": 3,
                    "origin_meeting_id": 2,
                    "all_origin_ids": [3],
                    "sequential_number": 1,
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
                    "sequential_number": 1,
                    "content_object_id": "motion/2",
                    "meeting_id": 2,
                },
                "list_of_speakers/3": {
                    "sequential_number": 2,
                    "content_object_id": "motion/3",
                    "meeting_id": 2,
                },
                "list_of_speakers/4": {
                    "sequential_number": 2,
                    "content_object_id": "motion/4",
                    "meeting_id": 1,
                },
                "motion_state/1": {"motion_ids": [1, 4], "meeting_id": 1},
                "motion_state/2": {"motion_ids": [2, 3], "meeting_id": 2},
            }
        )
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/3", {"motion_ids": [5, 6], "name": "Test - Copy"}
        )
        self.assert_model_exists(
            "motion/5",
            {
                "meeting_id": 3,
                "origin_id": None,
                "origin_meeting_id": None,
                "derived_motion_ids": None,
            },
        )

    def test_clone_with_underscore_attributes(self) -> None:
        self.set_models(self.test_models_with_admin)

        response = self.request(
            "meeting.clone", {"meeting_id": 1, "_collection": "testtest"}
        )
        self.assert_status_code(response, 400)

    def test_clone_vote_delegation(self) -> None:
        self.test_models["meeting/1"]["user_ids"] = [1, 2]
        self.test_models["meeting/1"]["meeting_user_ids"] = [11, 22]
        self.test_models["group/1"]["meeting_user_ids"] = [22]
        self.test_models["group/2"]["meeting_user_ids"] = [11]
        self.test_models["organization/1"]["user_ids"] = [1, 2]
        self.set_models(
            {
                "user/1": {
                    "meeting_ids": [1],
                    "meeting_user_ids": [11],
                    "organization_id": 1,
                },
                "user/2": {
                    "username": "vote_receiver",
                    "meeting_ids": [1],
                    "meeting_user_ids": [22],
                    "organization_id": 1,
                },
                "meeting_user/11": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "vote_delegated_to_id": 22,
                    "group_ids": [2],
                },
                "meeting_user/22": {
                    "meeting_id": 1,
                    "user_id": 2,
                    "vote_delegations_from_ids": [11],
                    "group_ids": [1],
                },
            }
        )
        self.set_models(self.test_models)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"user_ids": [1, 2]})
        self.assert_model_exists("meeting/2", {"user_ids": [2, 1]})
        self.assert_model_exists(
            "group/3",
            {
                "meeting_user_ids": [24],
                "meeting_id": 2,
            },
        )
        self.assert_model_exists(
            "group/4",
            {
                "meeting_user_ids": [23],
                "meeting_id": 2,
            },
        )
        self.assert_model_exists(
            "user/1",
            {
                "meeting_ids": [1, 2],
                "meeting_user_ids": [11, 23],
            },
        )
        self.assert_model_exists(
            "meeting_user/11",
            {
                "meeting_id": 1,
                "user_id": 1,
                "group_ids": [2],
            },
        )
        self.assert_model_exists(
            "meeting_user/23",
            {
                "meeting_id": 2,
                "user_id": 1,
                "group_ids": [4],
            },
        )

        self.assert_model_exists(
            "user/2",
            {
                "meeting_ids": [1, 2],
                "meeting_user_ids": [22, 24],
            },
        )
        self.assert_model_exists(
            "meeting_user/22",
            {
                "meeting_id": 1,
                "user_id": 2,
                "group_ids": [1],
            },
        )
        self.assert_model_exists(
            "meeting_user/24",
            {
                "meeting_id": 2,
                "user_id": 2,
                "group_ids": [3],
            },
        )

    def test_clone_vote_delegated_vote(self) -> None:
        self.test_models_with_admin["meeting/1"]["user_ids"] = [1]
        self.test_models_with_admin["meeting/1"]["vote_ids"] = [1]
        self.test_models_with_admin["meeting/1"]["option_ids"] = [1]
        self.test_models_with_admin["meeting/1"]["meeting_user_ids"] = [1]
        self.test_models_with_admin["user/1"]["meeting_user_ids"] = [1, 2]
        self.test_models_with_admin["user/1"]["meeting_ids"] = [1, 2]
        self.set_models(
            {
                "meeting/2": {"vote_ids": [2], "meeting_user_ids": [2]},
                "user/1": {
                    "meeting_ids": [1, 2],
                    "meeting_user_ids": [1, 2],
                    "vote_ids": [1, 2],
                    "delegated_vote_ids": [1, 2],
                },
                "meeting_user/1": {
                    "user_id": 1,
                    "meeting_id": 1,
                },
                "meeting_user/2": {
                    "user_id": 1,
                    "meeting_id": 2,
                },
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
                    "meeting_id": 2,
                },
                "option/1": {
                    "vote_ids": [1],
                    "meeting_id": 1,
                },
            },
        )
        self.set_models(self.test_models_with_admin)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "vote/3",
            {"user_id": 1, "delegated_user_id": 1, "option_id": 2, "meeting_id": 3},
        )
        self.assert_model_exists(
            "user/1",
            {
                "meeting_user_ids": [1, 2, 3],
                "vote_ids": [1, 2, 3],
                "delegated_vote_ids": [1, 2, 3],
                "meeting_ids": [1, 2, 3],
            },
        )
        self.assert_model_exists("meeting_user/3", {"user_id": 1, "meeting_id": 3})

    def test_with_action_worker(self) -> None:
        """action_worker shouldn't be cloned"""
        aw_name = "test action_worker"
        self.test_models_with_admin["action_worker/1"] = {
            "name": aw_name,
            "state": ActionWorkerState.END,
            "created": round(time() - 3),
            "timestamp": round(time()),
        }
        self.set_models(self.test_models_with_admin)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("action_worker/1", {"name": aw_name})
        self.assert_model_not_exists("action_worker/2")

    def test_with_import_preview(self) -> None:
        """import_preview shouldn't be cloned"""
        self.test_models_with_admin["import_preview/1"] = {
            "name": "topic",
            "state": "done",
            "created": round(time() - 3),
        }
        self.set_models(self.test_models_with_admin)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("import_preview/1", {"name": "topic"})
        self.assert_model_not_exists("import_preview/2")

    def test_clone_with_2_existing_meetings(self) -> None:
        self.test_models[ONE_ORGANIZATION_FQID]["active_meeting_ids"] = [1, 2]
        self.test_models["committee/1"]["meeting_ids"] = [1, 2]
        self.test_models["meeting/1"]["user_ids"] = [1]
        self.test_models["meeting/1"]["meeting_user_ids"] = [1]
        self.test_models["group/2"]["meeting_user_ids"] = [1]
        self.set_models(self.test_models)
        self.set_models(
            {
                "user/1": {
                    "meeting_user_ids": [1, 2],
                    "meeting_ids": [1, 2],
                    "committee_ids": [1],
                },
                "meeting/2": {
                    "committee_id": 1,
                    "name": "Test",
                    "default_group_id": 3,
                    "admin_group_id": 3,
                    "group_ids": [3],
                    "user_ids": [1],
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [2],
                },
                "group/3": {
                    "meeting_id": 2,
                    "name": "default group",
                    "weight": 1,
                    "default_group_for_meeting_id": 2,
                    "admin_group_for_meeting_id": 2,
                    "meeting_user_ids": [2],
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [2],
                },
                "meeting_user/2": {
                    "meeting_id": 2,
                    "user_id": 1,
                    "group_ids": [3],
                },
            },
        )

        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"user_ids": [1]})
        self.assert_model_exists("meeting/2", {"user_ids": [1]})
        self.assert_model_exists("meeting/3", {"user_ids": [1]})

        self.assert_model_exists(
            "user/1",
            {
                "meeting_user_ids": [1, 2, 3],
                "meeting_ids": [1, 2, 3],
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
                "meeting_id": 2,
                "user_id": 1,
                "group_ids": [3],
            },
        )
        self.assert_model_exists(
            "meeting_user/3",
            {
                "meeting_id": 3,
                "user_id": 1,
                "group_ids": [5],
            },
        )
        self.assert_model_exists("meeting/1", {"user_ids": [1]})
        self.assert_model_exists("meeting/2", {"user_ids": [1]})
        self.assert_model_exists("meeting/3", {"user_ids": [1]})
        self.assert_model_exists("committee/1", {"meeting_ids": [1, 2, 3]})

    def prepare_datastore_performance_test(self) -> None:
        self.set_models(
            {
                "committee/1": {"organization_id": 1, "user_ids": [2, 3]},
                "user/2": {
                    "committee_ids": [1],
                    "username": "user2",
                    "organization_id": 1,
                },
                "user/3": {
                    "committee_ids": [1],
                    "username": "user3",
                    "organization_id": 1,
                },
                "organization/1": {
                    "user_ids": [1, 2],
                    "limit_of_meetings": 0,
                    "archived_meeting_ids": [],
                },
            }
        )
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
                "admin_ids": [1],
                "organization_tag_ids": [],
                "language": "en",
            },
        )

    def test_clone_datastore_calls(self) -> None:
        self.prepare_datastore_performance_test()
        with CountDatastoreCalls() as counter:
            response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        assert counter.calls == 33

    @performance
    def test_clone_performance(self) -> None:
        self.prepare_datastore_performance_test()
        with Profiler("test_meeting_clone_performance.prof"):
            response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)

    def test_clone_amendment_paragraphs(self) -> None:
        self.test_models["meeting/1"]["user_ids"] = [1]
        self.test_models["meeting/1"]["meeting_user_ids"] = [1]
        self.test_models["group/1"]["meeting_user_ids"] = [1]
        self.set_models(
            {
                "motion/1": {
                    "list_of_speakers_id": 1,
                    "meeting_id": 1,
                    "sequential_number": 1,
                    "state_id": 1,
                    "submitter_ids": [1],
                    "title": "dummy",
                    "amendment_paragraphs": {
                        "1": "<it>test</it>",
                        "2": "</>broken",
                    },
                },
                "meeting/1": {
                    "motion_ids": [1],
                    "list_of_speakers_ids": [1],
                },
                "list_of_speakers/1": {
                    "content_object_id": "motion/1",
                    "meeting_id": 1,
                    "sequential_number": 1,
                },
                "motion_state/1": {
                    "motion_ids": [1],
                },
                "user/1": {
                    "meeting_user_ids": [1],
                    "meeting_ids": [1],
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [1],
                },
            }
        )
        self.set_models(self.test_models)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 400)
        assert (
            "motion/1/amendment_paragraphs error: Invalid html in 1\n\tmotion/1/amendment_paragraphs error: Invalid html in 2"
            in response.json["message"]
        )

    def test_permissions_oml_locked_meeting(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "meeting/1": {
                    "locked_from_inside": True,
                    "template_for_organization_id": 1,
                },
                ONE_ORGANIZATION_FQID: {"template_meeting_ids": [1]},
            }
        )
        response = self.request("meeting.clone", {"meeting_id": 1, "committee_id": 2})
        self.assert_status_code(response, 400)
        assert "Cannot clone locked meeting." in response.json["message"]

    def test_clone_require_duplicate_from_allowed(self) -> None:
        self.set_models(self.test_models_with_admin)
        self.set_models(
            {
                "meeting/1": {"template_for_organization_id": 1, "name": "m1"},
                "organization/1": {
                    "template_meeting_ids": [1],
                },
                "user/1": {
                    "organization_management_level": None,
                    "committee_ids": [1],
                    "committee_management_ids": [1],
                },
                "committee/1": {"user_ids": [1], "manager_ids": [1]},
            }
        )
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)

    def test_clone_template_allowed(self) -> None:
        self.set_models(self.test_models_with_admin)
        self.set_models(
            {
                "meeting/1": {"template_for_organization_id": 1, "name": "m1"},
                "organization/1": {
                    "template_meeting_ids": [1],
                },
                "user/1": {
                    "organization_management_level": None,
                    "committee_ids": [1],
                    "committee_management_ids": [1],
                },
                "committee/1": {"user_ids": [1], "manager_ids": [1]},
            }
        )
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)

    def test_clone_non_template_and_committee_change_not_allowed(self) -> None:
        self.test_models[ONE_ORGANIZATION_FQID]["template_meeting_ids"] = None
        self.test_models["meeting/1"]["template_for_organization_id"] = None
        self.set_models(self.test_models)
        self.set_models(
            {
                "user/1": {
                    "committee_ids": [1, 2],
                    "committee_management_ids": [1, 2],
                },
                "committee/1": {"user_ids": [1], "manager_ids": [1]},
                "committee/2": {"user_ids": [1], "manager_ids": [1]},
            }
        )
        response = self.request("meeting.clone", {"meeting_id": 1, "committee_id": 2})
        self.assert_status_code(response, 403)
        assert (
            response.json["message"]
            == "Cannot clone meeting to a different committee if it is a non-template meeting."
        )

    def test_clone_with_list_election(self) -> None:
        self.create_meeting()
        self.set_user_groups(1, [2])
        self.create_user("Huey", [3])
        self.create_user("Dewey", [3])
        self.create_user("Louie", [3])
        self.set_models(
            {
                "user/2": {
                    "organization_id": 1,
                    "poll_candidate_ids": [1],
                },
                "user/3": {
                    "organization_id": 1,
                    "poll_candidate_ids": [2],
                },
                "user/4": {
                    "organization_id": 1,
                    "poll_candidate_ids": [3],
                },
                "organization/1": {
                    "user_ids": [1, 2, 3, 4],
                },
                "motion_workflow/1": {
                    "name": "Workflow",
                    "sequential_number": 1,
                    "default_amendment_workflow_meeting_id": 1,
                },
                "motion_state/1": {
                    "name": "State",
                    "weight": 1,
                },
                "projector/1": {
                    "name": "default",
                    "meeting_id": 1,
                    "used_as_reference_projector_meeting_id": 1,
                    "sequential_number": 1,
                    **{
                        key: 1 for key in MeetingModelMixin.reverse_default_projectors()
                    },
                },
                "list_of_speakers/1": {
                    "id": 1,
                    "closed": False,
                    "meeting_id": 1,
                    "content_object_id": "assignment/1",
                    "sequential_number": 1,
                },
                "meeting/1": {
                    "id": 1,
                    "name": "Duckburg town government",
                    "poll_ids": [1],
                    "option_ids": [1, 2],
                    "projector_ids": [1],
                    "assignment_ids": [1],
                    "poll_candidate_ids": [1, 2, 3],
                    "list_of_speakers_ids": [1],
                    "reference_projector_id": 1,
                    "poll_candidate_list_ids": [1],
                    **{key: [1] for key in MeetingModelMixin.all_default_projectors()},
                    "motions_default_amendment_workflow_id": 1,
                },
                "assignment/1": {
                    "id": 1,
                    "phase": "search",
                    "title": "Duckburg town council",
                    "poll_ids": [1],
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
