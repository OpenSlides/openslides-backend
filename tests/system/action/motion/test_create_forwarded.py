from typing import Any
from unittest.mock import MagicMock, call

from openslides_backend.action.actions.motion.mixins import TextHashMixin
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID, ONE_ORGANIZATION_ID
from tests.system.action.base import BaseActionTestCase
from tests.util import Response


class MotionCreateForwardedTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.test_model: dict[str, dict[str, Any]] = {
            "meeting/1": {
                "name": "name_XDAddEAW",
                "committee_id": 53,
                "is_active_in_organization_id": 1,
                "group_ids": [111],
                "motion_ids": [12],
                "meeting_user_ids": [1],
                "user_ids": [1],
                "structure_level_ids": [1, 2, 3],
            },
            "meeting/2": {
                "name": "name_SNLGsvIV",
                "motions_default_workflow_id": 12,
                "motions_default_amendment_workflow_id": 12,
                "committee_id": 52,
                "is_active_in_organization_id": 1,
                "default_group_id": 112,
                "group_ids": [112],
                "meeting_user_ids": [2],
                "user_ids": [
                    1,
                ],
            },
            "user/1": {
                "meeting_ids": [1, 2],
                "first_name": "the",
                "last_name": "administrator",
                "title": "Worship",
                "pronoun": "he",
                "meeting_user_ids": [1, 2],
            },
            "motion_workflow/12": {
                "name": "name_workflow1",
                "first_state_id": 34,
                "state_ids": [34],
                "meeting_id": 2,
            },
            "motion_state/34": {
                "name": "name_state34",
                "meeting_id": 2,
            },
            "motion_state/30": {
                "name": "name_UVEKGkwf",
                "meeting_id": 1,
                "allow_motion_forwarding": True,
                "allow_amendment_forwarding": True,
            },
            "motion/12": {
                "title": "title_FcnPUXJB",
                "meeting_id": 1,
                "state_id": 30,
            },
            "committee/52": {
                "name": "committee_receiver",
                "meeting_ids": [2],
                "receive_forwardings_from_committee_ids": [53],
                "user_ids": [1],
            },
            "committee/53": {
                "name": "committee_forwarder",
                "meeting_ids": [1],
                "forward_to_committee_ids": [52],
                "user_ids": [1],
            },
            "group/111": {
                "name": "Grp Meeting1",
                "meeting_id": 1,
                "meeting_user_ids": [1],
            },
            "group/112": {"name": "YZJAwUPK", "meeting_id": 2, "meeting_user_ids": [2]},
            "meeting_user/1": {
                "id": 1,
                "user_id": 1,
                "meeting_id": 1,
                "group_ids": [111],
                "structure_level_ids": [1, 2, 3],
            },
            "structure_level/1": {
                "meeting_user_ids": [1],
                "meeting_id": 1,
                "name": "is",
            },
            "structure_level/2": {
                "meeting_user_ids": [1],
                "meeting_id": 1,
                "name": "very",
            },
            "structure_level/3": {
                "meeting_user_ids": [1],
                "meeting_id": 1,
                "name": "good",
            },
            "meeting_user/2": {
                "id": 2,
                "user_id": 1,
                "meeting_id": 2,
                "group_ids": [112],
            },
            "mediafile/1": {
                "owner_id": "meeting/1",
                "mimetype": "text/plain",
            },
            "mediafile/2": {
                "owner_id": ONE_ORGANIZATION_FQID,
                "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                "mimetype": "text/plain",
            },
            "mediafile/3": {
                "owner_id": "meeting/1",
                "mimetype": "text/plain",
                "is_directory": True,
                "child_ids": [4],
            },
            "mediafile/4": {
                "owner_id": "meeting/1",
                "mimetype": "text/plain",
                "parent_id": 3,
            },
            "mediafile/5": {
                "owner_id": ONE_ORGANIZATION_FQID,
                "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                "mimetype": "text/plain",
                "is_directory": True,
                "child_ids": [6],
            },
            "mediafile/6": {
                "owner_id": ONE_ORGANIZATION_FQID,
                "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                "mimetype": "text/plain",
                "parent_id": 5,
            },
        }

    def test_correct_origin_id_set(self) -> None:
        self.set_models(self.test_model)
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 2,
                "origin_id": 12,
                "text": "test",
                "reason": "reason_jLvcgAMx",
            },
        )
        self.assert_status_code(response, 200)
        model = self.assert_model_exists(
            "motion/13",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 2,
                "origin_id": 12,
                "origin_meeting_id": 1,
                "all_derived_motion_ids": None,
                "all_origin_ids": [12],
                "reason": "reason_jLvcgAMx",
                "submitter_ids": None,
                "additional_submitter": "committee_forwarder",
                "state_id": 34,
            },
        )
        assert model.get("forwarded")
        self.assert_model_not_exists("motion_submitter/1")
        self.assert_model_not_exists("user/2")
        self.assert_model_not_exists("meeting_user/3")
        self.assert_model_exists(
            "motion/12", {"derived_motion_ids": [13], "all_derived_motion_ids": [13]}
        )
        # test history
        self.assert_history_information("motion/12", ["Forwarded to {}", "meeting/2"])
        self.assert_history_information("motion/13", ["Motion created (forwarded)"])

    def test_no_origin_id(self) -> None:
        self.set_models(self.test_model)
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_Xcdfgee",
                "origin_id": 12,
                "text": "test",
                "reason": "reason_jLvcgAMx",
            },
        )
        self.assert_status_code(response, 400)
        assert response.json["message"] == "data must contain ['meeting_id'] properties"

    def test_no_meeting_id(self) -> None:
        self.set_models(self.test_model)
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 2,
                "text": "test",
                "reason": "reason_jLvcgAMx",
            },
        )
        self.assert_status_code(response, 400)
        assert response.json["message"] == "data must contain ['origin_id'] properties"

    def test_correct_existing_unregistered_forward_user(self) -> None:
        self.set_models(self.test_model)
        self.set_models(
            {
                "user/2": {
                    "username": "committee_forwarder",
                    "is_physical_person": True,
                    "is_active": True,
                },
            }
        )
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 2,
                "origin_id": 12,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        model = self.assert_model_exists(
            "motion/13",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 2,
                "origin_id": 12,
                "all_derived_motion_ids": None,
                "all_origin_ids": [12],
                "submitter_ids": None,
                "additional_submitter": "committee_forwarder",
            },
        )
        assert model.get("forwarded")
        self.assert_model_exists(
            "motion/12", {"derived_motion_ids": [13], "all_derived_motion_ids": [13]}
        )

    def test_correct_origin_id_wrong_1(self) -> None:
        self.test_model["committee/53"]["forward_to_committee_ids"] = []
        self.set_models(self.test_model)
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_Xcdfgee",
                "text": "text",
                "meeting_id": 2,
                "origin_id": 12,
            },
        )
        self.assert_status_code(response, 400)
        assert "Committee id 52 not in []" in response.json["message"]

    def test_missing_origin(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "meeting_222",
                    "is_active_in_organization_id": 1,
                },
            }
        )
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_Xcdfgee",
                "text": "text",
                "meeting_id": 222,
                "origin_id": 12,
            },
        )
        self.assert_status_code(response, 400)
        assert "Model 'motion/12' does not exist." in response.json["message"]

    def test_all_origin_ids_complex(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "name_XDAddEAW",
                    "committee_id": 53,
                    "is_active_in_organization_id": 1,
                },
                "meeting/2": {
                    "name": "name_SNLGsvIV",
                    "motions_default_workflow_id": 12,
                    "committee_id": 52,
                    "is_active_in_organization_id": 1,
                    "default_group_id": 112,
                    "group_ids": [112],
                },
                "user/1": {"meeting_ids": [1, 2]},
                "motion_workflow/12": {
                    "name": "name_workflow1",
                    "first_state_id": 34,
                    "state_ids": [34],
                    "meeting_id": 2,
                },
                "motion_state/34": {
                    "name": "name_state34",
                    "meeting_id": 2,
                    "allow_motion_forwarding": True,
                },
                "motion/6": {
                    "title": "title_FcnPUXJB layer 1",
                    "meeting_id": 1,
                    "state_id": 34,
                    "derived_motion_ids": [11, 12],
                    "all_origin_ids": [],
                    "all_derived_motion_ids": [11, 12, 13],
                },
                "motion/11": {
                    "title": "test11 layer 2",
                    "meeting_id": 1,
                    "state_id": 34,
                    "origin_id": 6,
                    "derived_motion_ids": [13],
                    "all_origin_ids": [6],
                    "all_derived_motion_ids": [13],
                },
                "motion/12": {
                    "title": "test12 layer 2",
                    "meeting_id": 1,
                    "state_id": 34,
                    "origin_id": 6,
                    "derived_motion_ids": [],
                    "all_origin_ids": [6],
                    "all_derived_motion_ids": [],
                },
                "motion/13": {
                    "title": "test13 layer 3",
                    "meeting_id": 1,
                    "state_id": 34,
                    "origin_id": 11,
                    "derived_motion_ids": [],
                    "all_origin_ids": [6, 11],
                    "all_derived_motion_ids": [],
                },
                "committee/52": {"name": "committee_receiver"},
                "committee/53": {
                    "name": "committee_forwarder",
                    "forward_to_committee_ids": [52],
                },
                "group/112": {"name": "YZJAwUPK", "meeting_id": 2},
            }
        )
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_XXX_leyer 3",
                "meeting_id": 2,
                "origin_id": 11,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/14",
            {
                "origin_id": 11,
                "all_origin_ids": [6, 11],
                "all_derived_motion_ids": None,
            },
        )
        self.assert_model_exists(
            "motion/13",
            {"origin_id": 11, "all_origin_ids": [6, 11], "all_derived_motion_ids": []},
        )
        self.assert_model_exists(
            "motion/12",
            {"origin_id": 6, "all_origin_ids": [6], "all_derived_motion_ids": []},
        )
        self.assert_model_exists(
            "motion/11",
            {"origin_id": 6, "all_origin_ids": [6], "all_derived_motion_ids": [13, 14]},
        )
        self.assert_model_exists(
            "motion/6",
            {
                "origin_id": None,
                "all_origin_ids": [],
                "all_derived_motion_ids": [11, 12, 13, 14],
            },
        )
        self.assert_history_information("motion/11", ["Forwarded to {}", "meeting/2"])
        self.assert_history_information("motion/6", None)

    def test_forward_with_deleted_motion_in_all_origin_ids(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "committee_id": 53,
                    "is_active_in_organization_id": 1,
                },
                "meeting/2": {
                    "motions_default_workflow_id": 12,
                    "committee_id": 52,
                    "is_active_in_organization_id": 1,
                    "default_group_id": 112,
                    "group_ids": [112],
                },
                "user/1": {"meeting_ids": [1, 2]},
                "motion_workflow/12": {
                    "first_state_id": 34,
                    "state_ids": [34],
                    "meeting_id": 2,
                },
                "motion_state/34": {
                    "meeting_id": 2,
                    "allow_motion_forwarding": True,
                },
                "motion/1": {
                    "title": "deleted",
                    "meeting_id": 1,
                    "state_id": 34,
                    "derived_motion_ids": [2],
                    "all_derived_motion_ids": [2],
                },
                "motion/2": {
                    "title": "motion",
                    "meeting_id": 1,
                    "state_id": 34,
                    "origin_id": 1,
                    "all_origin_ids": [1],
                },
                "committee/52": {"name": "committee_receiver"},
                "committee/53": {
                    "name": "committee_forwarder",
                    "forward_to_committee_ids": [52],
                },
                "group/112": {"meeting_id": 2},
            }
        )
        response = self.request("motion.delete", {"id": 1})
        self.assert_model_exists("motion/2", {"all_origin_ids": []})
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "new",
                "meeting_id": 2,
                "origin_id": 2,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)

    def test_not_allowed_to_forward_amendments_directly(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "name_XDAddEAW",
                    "committee_id": 53,
                    "is_active_in_organization_id": 1,
                },
                "user/1": {"meeting_ids": [1, 2]},
                "motion/6": {
                    "title": "title_FcnPUXJB layer 1",
                    "meeting_id": 1,
                    "state_id": 34,
                    "derived_motion_ids": [],
                    "all_origin_ids": [],
                    "all_derived_motion_ids": [],
                    "amendment_ids": [11],
                },
                "motion/11": {
                    "title": "test11 layer 2",
                    "meeting_id": 1,
                    "state_id": 34,
                    "derived_motion_ids": [],
                    "all_origin_ids": [],
                    "all_derived_motion_ids": [],
                    "lead_motion_id": 6,
                },
                "motion_workflow/12": {
                    "name": "name_workflow1",
                    "first_state_id": 34,
                    "state_ids": [34],
                    "meeting_id": 1,
                },
                "motion_state/34": {
                    "name": "name_state34",
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_foo",
                "meeting_id": 1,
                "origin_id": 11,
                "text": "test",
            },
        )
        self.assert_status_code(response, 403)
        assert "Amendments cannot be forwarded." in response.json["message"]

    def test_allowed_to_forward_amendments_indirectly(self) -> None:
        self.set_models(self.test_model)
        self.set_models(
            {
                "meeting/1": {
                    "name": "name_XDAddEAW",
                    "committee_id": 53,
                    "is_active_in_organization_id": 1,
                    "motion_ids": [12, 13],
                },
                "user/1": {"meeting_ids": [1, 2]},
                "motion/12": {
                    "title": "title_FcnPUXJB layer 1",
                    "meeting_id": 1,
                    "derived_motion_ids": [],
                    "all_origin_ids": [],
                    "all_derived_motion_ids": [],
                    "amendment_ids": [13],
                },
                "motion/13": {
                    "title": "amendment",
                    "meeting_id": 1,
                    "derived_motion_ids": [],
                    "all_origin_ids": [],
                    "all_derived_motion_ids": [],
                    "lead_motion_id": 12,
                    "state_id": 30,
                    "amendment_paragraphs": {"0": "texts"},
                },
            }
        )
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_foo",
                "meeting_id": 2,
                "origin_id": 12,
                "text": "test",
                "with_amendments": True,
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0] == [
            {
                "id": 14,
                "non_forwarded_amendment_amount": 0,
                "sequential_number": 1,
                "amendment_result_data": [
                    {
                        "amendment_result_data": [],
                        "id": 15,
                        "non_forwarded_amendment_amount": 0,
                        "sequential_number": 2,
                    }
                ],
            }
        ]
        self.assert_model_exists(
            "motion/14",
            {
                "origin_id": 12,
                "title": "test_foo",
                "meeting_id": 2,
                "text": "test",
                "amendment_ids": [15],
                "state_id": 34,
                "additional_submitter": "committee_forwarder",
            },
        )
        self.assert_model_exists(
            "motion/15",
            {
                "lead_motion_id": 14,
                "origin_id": 13,
                "title": "amendment",
                "meeting_id": 2,
                "state_id": 34,
                "amendment_paragraphs": {"0": "texts"},
                "additional_submitter": "committee_forwarder",
                "marked_forwarded": False,
            },
        )

    def test_allowed_to_forward_amendments_indirectly_complex(self) -> None:
        self.set_models(self.test_model)
        user1 = self.create_user("first_submitter", [111])
        user2 = self.create_user("second_submitter", [111])
        self.set_models(
            {
                f"user/{user1}": {"first_name": "A", "last_name": "man"},
                f"user/{user2}": {
                    "title": "A",
                    "first_name": "hairy",
                    "last_name": "woman",
                },
                "meeting/1": {
                    "name": "name_XDAddEAW",
                    "committee_id": 53,
                    "is_active_in_organization_id": 1,
                    "motion_ids": [12, 13, 14, 15],
                },
                "user/1": {"meeting_ids": [1, 2]},
                "motion/12": {
                    "number": "MAIN",
                    "title": "title_FcnPUXJB layer 1",
                    "meeting_id": 1,
                    "derived_motion_ids": [],
                    "all_origin_ids": [],
                    "all_derived_motion_ids": [],
                    "amendment_ids": [13, 14, 15],
                    "submitter_ids": [1, 2],
                },
                "motion_submitter/1": {
                    "motion_id": 12,
                    "meeting_user_id": 3,
                    "weight": 1,
                },
                "motion_submitter/2": {
                    "motion_id": 12,
                    "meeting_user_id": 4,
                    "weight": 2,
                },
                "motion/13": {
                    "number": "AMNDMNT1",
                    "title": "amendment1",
                    "meeting_id": 1,
                    "derived_motion_ids": [],
                    "all_origin_ids": [],
                    "all_derived_motion_ids": [],
                    "lead_motion_id": 12,
                    "state_id": 30,
                    "amendment_paragraphs": {"0": "texts"},
                    "submitter_ids": [3],
                },
                "motion_submitter/3": {
                    "motion_id": 13,
                    "meeting_user_id": 3,
                    "weight": 1,
                },
                "motion/14": {
                    "number": "AMNDMNT2",
                    "title": "amendment2",
                    "meeting_id": 1,
                    "derived_motion_ids": [],
                    "all_origin_ids": [],
                    "all_derived_motion_ids": [],
                    "lead_motion_id": 12,
                    "state_id": 31,
                    "amendment_paragraphs": {"0": "NO!!!"},
                },
                "motion/15": {
                    "number": "AMNDMNT3",
                    "title": "amendment3",
                    "meeting_id": 1,
                    "derived_motion_ids": [],
                    "all_origin_ids": [],
                    "all_derived_motion_ids": [],
                    "lead_motion_id": 12,
                    "state_id": 30,
                    "amendment_paragraphs": {"0": "tests"},
                    "amendment_ids": [16, 17],
                },
                "motion/16": {
                    "number": "AMNDMNT4",
                    "title": "amendment4",
                    "meeting_id": 1,
                    "derived_motion_ids": [],
                    "all_origin_ids": [],
                    "all_derived_motion_ids": [],
                    "lead_motion_id": 15,
                    "state_id": 30,
                    "amendment_paragraphs": {"0": "testssss"},
                },
                "motion/17": {
                    "number": "AMNDMNT5",
                    "title": "amendment5",
                    "meeting_id": 1,
                    "derived_motion_ids": [],
                    "all_origin_ids": [],
                    "all_derived_motion_ids": [],
                    "lead_motion_id": 15,
                    "state_id": 31,
                    "amendment_paragraphs": {"0": "test"},
                },
                "meeting/2": {
                    "motions_default_workflow_id": 12,
                    "motions_default_amendment_workflow_id": 13,
                },
                "motion_state/31": {
                    "name": "No forward state",
                    "meeting_id": 1,
                },
                "motion_workflow/13": {
                    "name": "name_workflow2",
                    "first_state_id": 35,
                    "state_ids": [35],
                    "meeting_id": 2,
                },
                "motion_state/35": {
                    "name": "name_state35",
                    "meeting_id": 2,
                },
            }
        )
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_foo",
                "meeting_id": 2,
                "origin_id": 12,
                "text": "test",
                "with_amendments": True,
                "use_original_submitter": True,
                "use_original_number": True,
                "mark_amendments_as_forwarded": True,
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0] == [
            {
                "id": 18,
                "non_forwarded_amendment_amount": 1,
                "sequential_number": 1,
                "amendment_result_data": [
                    {
                        "id": 19,
                        "non_forwarded_amendment_amount": 0,
                        "sequential_number": 2,
                        "amendment_result_data": [],
                    },
                    {
                        "id": 20,
                        "non_forwarded_amendment_amount": 1,
                        "sequential_number": 3,
                        "amendment_result_data": [
                            {
                                "id": 21,
                                "non_forwarded_amendment_amount": 0,
                                "sequential_number": 4,
                                "amendment_result_data": [],
                            },
                        ],
                    },
                ],
            }
        ]
        self.assert_model_exists(
            "motion/18",
            {
                "number": "MAIN",
                "origin_id": 12,
                "title": "test_foo",
                "meeting_id": 2,
                "text": "test",
                "amendment_ids": [19, 20],
                "additional_submitter": "A man, A hairy woman",
                "sequential_number": 1,
                "state_id": 34,
            },
        )
        self.assert_model_exists(
            "motion/19",
            {
                "number": "AMNDMNT1",
                "lead_motion_id": 18,
                "origin_id": 13,
                "title": "amendment1",
                "meeting_id": 2,
                "amendment_paragraphs": {"0": "texts"},
                "additional_submitter": "A man",
                "sequential_number": 2,
                "state_id": 35,
                "marked_forwarded": True,
            },
        )
        self.assert_model_exists(
            "motion/20",
            {
                "number": "AMNDMNT3",
                "lead_motion_id": 18,
                "origin_id": 15,
                "title": "amendment3",
                "meeting_id": 2,
                "state_id": 35,
                "amendment_paragraphs": {"0": "tests"},
                "additional_submitter": None,
                "amendment_ids": [21],
                "sequential_number": 3,
                "marked_forwarded": True,
            },
        )
        self.assert_model_exists(
            "motion/21",
            {
                "number": "AMNDMNT4",
                "lead_motion_id": 20,
                "origin_id": 16,
                "title": "amendment4",
                "meeting_id": 2,
                "state_id": 35,
                "amendment_paragraphs": {"0": "testssss"},
                "additional_submitter": None,
                "sequential_number": 4,
                "marked_forwarded": True,
            },
        )

    def test_forward_to_2_meetings_1_transaction(self) -> None:
        """Forwarding of 1 motion to 2 meetings in 1 transaction"""
        self.set_models(self.test_model)
        self.set_models(
            {
                "meeting/3": {
                    "name": "meeting3",
                    "motions_default_workflow_id": 13,
                    "committee_id": 52,
                    "is_active_in_organization_id": 1,
                    "default_group_id": 113,
                    "group_ids": [113],
                },
                "motion_workflow/13": {
                    "name": "name_workflow13",
                    "first_state_id": 33,
                    "state_ids": [33],
                    "meeting_id": 3,
                },
                "motion_state/33": {
                    "name": "name_state33",
                    "meeting_id": 3,
                },
                "group/113": {"name": "YZJAwUPK", "meeting_id": 3},
            }
        )
        response = self.request_multi(
            "motion.create_forwarded",
            [
                {
                    "title": "title_12_to_meeting2",
                    "meeting_id": 2,
                    "origin_id": 12,
                    "text": "test2",
                    "reason": "reason_jLvcgAMx2",
                },
                {
                    "title": "title_12_to_meeting3",
                    "meeting_id": 3,
                    "origin_id": 12,
                    "text": "test3",
                    "reason": "reason_jLvcgAMx3",
                },
            ],
        )
        self.assert_status_code(response, 200)

        model = self.assert_model_exists(
            "motion/13",
            {
                "title": "title_12_to_meeting2",
                "meeting_id": 2,
                "origin_id": 12,
                "origin_meeting_id": 1,
                "all_derived_motion_ids": None,
                "all_origin_ids": [12],
                "reason": "reason_jLvcgAMx2",
                "submitter_ids": None,
                "additional_submitter": "committee_forwarder",
                "state_id": 34,
            },
        )
        assert model.get("forwarded")

        model = self.assert_model_exists(
            "motion/14",
            {
                "title": "title_12_to_meeting3",
                "meeting_id": 3,
                "origin_id": 12,
                "origin_meeting_id": 1,
                "all_derived_motion_ids": None,
                "all_origin_ids": [12],
                "reason": "reason_jLvcgAMx3",
                "submitter_ids": None,
                "additional_submitter": "committee_forwarder",
                "state_id": 33,
            },
        )
        assert model.get("forwarded")
        self.assert_model_exists(
            "motion/12",
            {"derived_motion_ids": [13, 14], "all_derived_motion_ids": [13, 14]},
        )
        # test history
        self.assert_history_information(
            "motion/12",
            ["Forwarded to {}", "meeting/2", "Forwarded to {}", "meeting/3"],
        )
        self.assert_history_information("motion/13", ["Motion created (forwarded)"])
        self.assert_history_information("motion/14", ["Motion created (forwarded)"])

    def test_create_forwarded_not_allowed_by_state(self) -> None:
        self.test_model["motion_state/30"]["allow_motion_forwarding"] = False
        self.set_models(self.test_model)
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 2,
                "origin_id": 12,
                "text": "test",
            },
        )
        self.assert_status_code(response, 400)
        assert "State doesn't allow to forward motion." in response.json["message"]

    def test_create_forwarded_with_identical_motion(self) -> None:
        text = "test"
        hash = TextHashMixin.get_hash(text)
        self.set_models(
            {
                "motion/13": {
                    "meeting_id": 2,
                    "text": text,
                    "text_hash": hash,
                },
                **self.test_model,
            }
        )
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 2,
                "origin_id": 12,
                "text": text,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/14", {"text_hash": hash, "identical_motion_ids": [13]}
        )
        self.assert_model_exists("motion/13", {"identical_motion_ids": [14]})

    def test_no_permissions(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_models(self.test_model)
        self.set_models({"group/4": {"meeting_id": 2}})
        self.set_user_groups(self.user_id, [3, 4])
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 2,
                "origin_id": 12,
                "text": "test",
            },
        )
        self.assert_status_code(response, 403)
        assert "Missing permission: motion.can_forward" in response.json["message"]

    def test_permissions(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_models(self.test_model)
        self.set_user_groups(self.user_id, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_MANAGE])
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 2,
                "origin_id": 12,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)

    def test_forward_multiple_to_meeting_with_set_number(self) -> None:
        """Forwarding of 1 motion to 2 meetings in 1 transaction"""
        self.set_models(self.test_model)
        self.set_models(
            {
                "meeting/1": {
                    "motion_ids": [12, 13],
                },
                "motion/13": {
                    "title": "title_FcnPUXJB2",
                    "meeting_id": 1,
                    "state_id": 30,
                },
                "motion_state/30": {"motion_ids": [12, 13]},
                "motion_state/34": {"set_number": True},
            }
        )
        response = self.request_multi(
            "motion.create_forwarded",
            [
                {
                    "title": "title_12",
                    "meeting_id": 2,
                    "origin_id": 12,
                    "text": "test2",
                    "reason": "reason_jLvcgAMx2",
                },
                {
                    "title": "title_13",
                    "meeting_id": 2,
                    "origin_id": 13,
                    "text": "test3",
                    "reason": "reason_jLvcgAMx3",
                },
            ],
        )
        self.assert_status_code(response, 200)
        created = [date["id"] for date in response.json["results"][0]]
        for i in range(2):
            self.assert_model_exists(
                f"motion/{created[i]}", {"number": f"{i+1}", "sequential_number": 1 + i}
            )

    def test_forward_multiple_to_meeting_with_set_number_and_use_original_number(
        self,
    ) -> None:
        """Forwarding of 1 motion to 2 meetings in 1 transaction"""
        self.set_models(self.test_model)
        self.set_models(
            {
                "meeting/1": {
                    "motion_ids": [12, 13],
                },
                "motion/13": {
                    "title": "title_FcnPUXJB2",
                    "meeting_id": 1,
                    "state_id": 30,
                    "number": "1",
                },
                "motion_state/30": {"motion_ids": [12, 13]},
                "motion_state/34": {"set_number": True},
            }
        )
        response = self.request_multi(
            "motion.create_forwarded",
            [
                {
                    "title": "title_12",
                    "meeting_id": 2,
                    "origin_id": 12,
                    "text": "test2",
                    "reason": "reason_jLvcgAMx2",
                },
                {
                    "title": "title_13",
                    "meeting_id": 2,
                    "origin_id": 13,
                    "text": "test3",
                    "reason": "reason_jLvcgAMx3",
                    "use_original_number": True,
                },
            ],
        )
        self.assert_status_code(response, 200)
        created = [date["id"] for date in response.json["results"][0]]
        self.assert_model_exists(f"motion/{created[0]}", {"number": "1"})
        self.assert_model_exists(f"motion/{created[1]}", {"number": "1-1"})

    def test_forward_multiple_to_meeting_with_set_number_and_use_original_number_2(
        self,
    ) -> None:
        """Forwarding of 1 motion to 2 meetings in 1 transaction"""
        self.set_models(self.test_model)
        self.set_models(
            {
                "meeting/1": {
                    "motion_ids": [12, 13],
                },
                "motion/12": {"number": "1"},
                "motion/13": {
                    "title": "title_FcnPUXJB2",
                    "meeting_id": 1,
                    "state_id": 30,
                },
                "motion_state/30": {"motion_ids": [12, 13]},
                "motion_state/34": {"set_number": True},
            }
        )
        response = self.request_multi(
            "motion.create_forwarded",
            [
                {
                    "title": "title_12",
                    "meeting_id": 2,
                    "origin_id": 12,
                    "text": "test2",
                    "reason": "reason_jLvcgAMx2",
                    "use_original_number": True,
                },
                {
                    "title": "title_13",
                    "meeting_id": 2,
                    "origin_id": 13,
                    "text": "test3",
                    "reason": "reason_jLvcgAMx3",
                },
            ],
        )
        self.assert_status_code(response, 200)
        created = [date["id"] for date in response.json["results"][0]]
        self.assert_model_exists(f"motion/{created[0]}", {"number": "1"})
        self.assert_model_exists(f"motion/{created[1]}", {"number": "2"})

    def test_forward_multiple_to_meeting_with_set_number_and_use_original_number_3(
        self,
    ) -> None:
        """Forwarding of 1 motion to 2 meetings in 1 transaction"""
        self.set_models(self.test_model)
        self.set_models(
            {
                "meeting/1": {
                    "motion_ids": [12, 13],
                },
                "meeting/2": {
                    "motion_ids": [14],
                },
                "motion/12": {"number": "1", "submitter_ids": [12]},
                "motion/13": {
                    "title": "title_FcnPUXJB2",
                    "meeting_id": 1,
                    "state_id": 30,
                    "number": "1",
                    "submitter_ids": [13],
                },
                "motion/14": {
                    "title": "title_FcnPUXJB2",
                    "meeting_id": 2,
                    "state_id": 30,
                    "number": "1",
                },
                "motion_state/30": {"motion_ids": [12, 13]},
                "motion_submitter/12": {
                    "meeting_user_id": 1,
                    "motion_id": 12,
                    "meeting_id": 1,
                },
                "motion_submitter/13": {
                    "meeting_user_id": 1,
                    "motion_id": 13,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request_multi(
            "motion.create_forwarded",
            [
                {
                    "title": "title_12",
                    "meeting_id": 2,
                    "origin_id": 12,
                    "text": "test2",
                    "reason": "reason_jLvcgAMx2",
                    "use_original_number": True,
                    "use_original_submitter": True,
                },
                {
                    "title": "title_13",
                    "meeting_id": 2,
                    "origin_id": 13,
                    "text": "test3",
                    "reason": "reason_jLvcgAMx3",
                    "use_original_number": True,
                },
            ],
        )
        self.assert_status_code(response, 200)
        created = [date["id"] for date in response.json["results"][0]]
        self.assert_model_exists(
            f"motion/{created[0]}",
            {
                "number": "1-1",
                "additional_submitter": "Worship the administrator (he · is, very, good)",
            },
        )
        self.assert_model_exists(f"motion/{created[1]}", {"number": "1-2"})

    def test_use_original_submitter_empty(self) -> None:
        self.set_models(self.test_model)
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 2,
                "origin_id": 12,
                "text": "test",
                "reason": "reason_jLvcgAMx",
                "use_original_submitter": True,
            },
        )
        self.assert_status_code(response, 200)
        created_id = response.json["results"][0][0]["id"]
        self.assert_model_exists(
            f"motion/{created_id}", {"number": None, "submitter_ids": None}
        )

    def test_use_original_submitter_multiple(self) -> None:
        self.set_models(self.test_model)
        extra_user_id = self.create_user("user", [111])
        self.set_models(
            {
                "motion/12": {
                    "submitter_ids": [12, 13],
                    "additional_submitter": "Sue B. Mid-Edit",
                },
                "motion_submitter/12": {
                    "meeting_user_id": 1,
                    "motion_id": 12,
                    "meeting_id": 1,
                },
                "motion_submitter/13": {
                    "meeting_user_id": 3,
                    "motion_id": 12,
                    "meeting_id": 1,
                },
                "meeting_user/3": {
                    "motion_submitter_ids": [13],
                },
                "meeting/1": {
                    "meeting_user_ids": [1, 3],
                    "motion_submitter_ids": [12, 13],
                    "user_ids": [1, extra_user_id],
                },
                f"user/{extra_user_id}": {"meeting_user_ids": [3], "meeting_ids": [1]},
            }
        )
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 2,
                "origin_id": 12,
                "text": "test",
                "reason": "reason_jLvcgAMx",
                "use_original_submitter": True,
            },
        )
        self.assert_status_code(response, 200)
        created_id = response.json["results"][0][0]["id"]
        self.assert_model_exists(
            f"motion/{created_id}",
            {
                "additional_submitter": "Worship the administrator (he · is, very, good), User 2, Sue B. Mid-Edit"
            },
        )

    def test_name_generation(self) -> None:
        self.set_models(self.test_model)
        extra_user_data: list[tuple[dict[str, Any], ...]] = [
            ({"title": "He is", "pronoun": "he"}, {"structure_level_ids": [1, 3]}),
            ({"first_name": "King", "pronoun": "Kong"}, {"structure_level_ids": [2]}),
            (
                {
                    "last_name": "Good",
                },
                {"structure_level_ids": [3]},
            ),
            (
                {
                    "title": "He,",
                    "first_name": "she,",
                    "last_name": "it",
                    "pronoun": "ein 's' muss mit",
                },
                {},
            ),
            (
                {
                    "title": "Grandma",
                    "first_name": "not",
                    "last_name": "see",
                },
                {"structure_level_ids": []},
            ),
        ]
        amount = len(extra_user_data)
        extra_user_ids = [self.create_user(f"user{i}", [111]) for i in range(amount)]
        self.set_models(
            {
                "motion/12": {
                    "submitter_ids": list(range(12, 13 + amount)),
                    "additional_submitter": "Sue B. Mid-Edit",
                },
                "motion_submitter/12": {
                    "meeting_user_id": 1,
                    "motion_id": 12,
                    "meeting_id": 1,
                },
                "meeting/1": {
                    "meeting_user_ids": [1, *range(3, 3 + amount)],
                    "motion_submitter_ids": list(range(12, 13 + amount)),
                    "user_ids": [1, *extra_user_ids],
                },
                **{
                    f"user/{extra_user_ids[i]}": {
                        "meeting_user_ids": [i + 3],
                        "meeting_ids": [1],
                        **extra_user_data[i][0],
                    }
                    for i in range(amount)
                },
                **{
                    f"meeting_user/{i + 3}": {
                        "motion_submitter_ids": [13 + i],
                        **extra_user_data[i][1],
                    }
                    for i in range(amount)
                },
                **{
                    f"motion_submitter/{13 + i}": {
                        "meeting_user_id": i + 3,
                        "motion_id": 12,
                        "meeting_id": 1,
                    }
                    for i in range(amount)
                },
            }
        )
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 2,
                "origin_id": 12,
                "text": "test",
                "reason": "reason_jLvcgAMx",
                "use_original_submitter": True,
            },
        )
        self.assert_status_code(response, 200)
        created_id = response.json["results"][0][0]["id"]
        motion = self.assert_model_exists(f"motion/{created_id}")
        for name in [
            "Worship the administrator (he · is, very, good)",
            "He is User 2 (he · is, good)",
            "King (Kong · very)",
            "Good (good)",
            "He, she, it (ein 's' muss mit)",
            "Grandma not see",
            "Sue B. Mid-Edit",
        ]:
            assert name in motion["additional_submitter"]

    def test_with_change_recommendations(self) -> None:
        self.set_models(self.test_model)
        self.set_models(
            {
                "motion/12": {"change_recommendation_ids": [1, 2]},
                "meeting/1": {"motion_change_recommendation_ids": [1, 2]},
                "motion_change_recommendation/1": {
                    "line_from": 11,
                    "line_to": 23,
                    "text": "Hello world",
                    "motion_id": 12,
                    "meeting_id": 1,
                    "rejected": True,
                    "internal": True,
                    "type": "replacement",
                    "other_description": "Iamachangerecommendation",
                    "creation_time": 0,
                },
                "motion_change_recommendation/2": {
                    "line_from": 24,
                    "line_to": 25,
                    "text": "!",
                    "motion_id": 12,
                    "meeting_id": 1,
                    "type": "replacement",
                    "creation_time": 1,
                },
            }
        )
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 2,
                "origin_id": 12,
                "text": "test",
                "reason": "reason_jLvcgAMx",
                "with_change_recommendations": True,
            },
        )
        self.assert_status_code(response, 200)
        created_id = response.json["results"][0][0]["id"]
        self.assert_model_exists(
            f"motion/{created_id}", {"change_recommendation_ids": [3, 4]}
        )
        reco = self.assert_model_exists(
            "motion_change_recommendation/3",
            {
                "line_from": 11,
                "line_to": 23,
                "text": "Hello world",
                "motion_id": created_id,
                "meeting_id": 2,
                "rejected": True,
                "internal": True,
                "type": "replacement",
                "other_description": "Iamachangerecommendation",
            },
        )
        assert reco["creation_time"] > 0
        self.assert_model_exists(
            "motion_change_recommendation/4",
            {
                "line_from": 24,
                "line_to": 25,
                "text": "!",
                "type": "replacement",
                "motion_id": created_id,
                "meeting_id": 2,
            },
        )

    def test_without_change_recommendations(self) -> None:
        self.set_models(self.test_model)
        self.set_models(
            {
                "motion/12": {"change_recommendation_ids": [1, 2]},
                "meeting/1": {"motion_change_recommendation_ids": [1, 2]},
                "motion_change_recommendation/1": {
                    "line_from": 11,
                    "line_to": 23,
                    "text": "Hello world",
                    "motion_id": 12,
                    "meeting_id": 1,
                    "rejected": True,
                    "internal": True,
                    "type": "replacement",
                    "other_description": "Iamachangerecommendation",
                    "creation_time": 0,
                },
                "motion_change_recommendation/2": {
                    "line_from": 24,
                    "line_to": 25,
                    "text": "!",
                    "motion_id": 12,
                    "meeting_id": 1,
                    "type": "replacement",
                    "creation_time": 1,
                },
            }
        )
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 2,
                "origin_id": 12,
                "text": "test",
                "reason": "reason_jLvcgAMx",
            },
        )
        self.assert_status_code(response, 200)
        created_id = response.json["results"][0][0]["id"]
        self.assert_model_exists(
            f"motion/{created_id}", {"change_recommendation_ids": None}
        )
        self.assert_model_not_exists("motion_change_recommendation/3")

    def test_with_no_change_recommendations(self) -> None:
        self.set_models(self.test_model)
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 2,
                "origin_id": 12,
                "text": "test",
                "reason": "reason_jLvcgAMx",
                "with_change_recommendations": True,
            },
        )
        self.assert_status_code(response, 200)

    def test_with_amendment_change_recommendations(self) -> None:
        self.set_models(self.test_model)
        self.set_models(
            {
                "motion/12": {"change_recommendation_ids": [1], "amendment_ids": [13]},
                "meeting/1": {"motion_change_recommendation_ids": [1, 2]},
                "motion/13": {
                    "number": "AMNDMNT1",
                    "title": "amendment1",
                    "meeting_id": 1,
                    "derived_motion_ids": [],
                    "all_origin_ids": [],
                    "all_derived_motion_ids": [],
                    "lead_motion_id": 12,
                    "state_id": 30,
                    "text": "bla",
                    "change_recommendation_ids": [2],
                },
                "motion_change_recommendation/1": {
                    "line_from": 11,
                    "line_to": 23,
                    "text": "Hello world",
                    "motion_id": 12,
                    "meeting_id": 1,
                    "rejected": True,
                    "internal": True,
                    "type": "replacement",
                    "other_description": "Iamachangerecommendation",
                    "creation_time": 0,
                },
                "motion_change_recommendation/2": {
                    "line_from": 24,
                    "line_to": 25,
                    "text": "!",
                    "motion_id": 13,
                    "meeting_id": 1,
                    "type": "replacement",
                    "creation_time": 1,
                },
            }
        )
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 2,
                "origin_id": 12,
                "text": "test",
                "reason": "reason_jLvcgAMx",
                "with_change_recommendations": True,
                "with_amendments": True,
            },
        )
        self.assert_status_code(response, 200)
        created_id = response.json["results"][0][0]["id"]
        self.assert_model_exists(
            f"motion/{created_id}", {"change_recommendation_ids": [3]}
        )
        self.assert_model_exists(
            f"motion/{created_id+1}",
            {"change_recommendation_ids": [4], "lead_motion_id": created_id},
        )
        reco = self.assert_model_exists(
            "motion_change_recommendation/3",
            {
                "line_from": 11,
                "line_to": 23,
                "text": "Hello world",
                "motion_id": created_id,
                "meeting_id": 2,
                "rejected": True,
                "internal": True,
                "type": "replacement",
                "other_description": "Iamachangerecommendation",
            },
        )
        assert reco["creation_time"] > 0
        self.assert_model_exists(
            "motion_change_recommendation/4",
            {
                "line_from": 24,
                "line_to": 25,
                "text": "!",
                "type": "replacement",
                "motion_id": created_id + 1,
                "meeting_id": 2,
            },
        )

    def test_amendment_forwarding_different_states(self) -> None:
        self.create_meeting()
        self.create_meeting(4)
        self.set_models(
            {
                "meeting/1": {
                    "motion_ids": [1],
                    "motion_state_ids": [1, 2],
                },
                "meeting/4": {
                    "motions_default_amendment_workflow_id": 4,
                    "default_group_id": 112,
                    "group_ids": [112],
                    "motion_state_ids": [4, 5],
                },
                "motion_workflow/1": {"state_ids": [1, 2]},
                "motion_state/1": {
                    "allow_motion_forwarding": True,
                    "allow_amendment_forwarding": False,
                },
                "motion_state/2": {
                    "meeting_id": 1,
                    "workflow_id": 1,
                    "allow_motion_forwarding": False,
                    "allow_amendment_forwarding": True,
                },
                "motion_workflow/4": {"state_ids": [4, 5]},
                "motion_state/5": {
                    "meeting_id": 4,
                    "workflow_id": 4,
                },
                "motion/1": {
                    "title": "Motion 1",
                    "meeting_id": 1,
                    "state_id": 1,
                    "derived_motion_ids": [],
                    "all_origin_ids": [],
                    "all_derived_motion_ids": [],
                    "amendment_ids": [2, 3],
                },
                "motion/2": {
                    "title": "Amendment 1",
                    "meeting_id": 1,
                    "state_id": 1,
                    "derived_motion_ids": [],
                    "all_origin_ids": [],
                    "all_derived_motion_ids": [],
                    "lead_motion_id": 1,
                    "amendment_paragraphs": {"0": "texts"},
                },
                "motion/3": {
                    "title": "Amendment 2",
                    "meeting_id": 1,
                    "state_id": 2,
                    "derived_motion_ids": [],
                    "all_origin_ids": [],
                    "all_derived_motion_ids": [],
                    "lead_motion_id": 1,
                    "amendment_paragraphs": {"0": "paragraph"},
                },
                "committee/60": {
                    "name": "committee_forwarder",
                    "forward_to_committee_ids": [63],
                },
                "committee/63": {
                    "name": "committee_receiver",
                    "receive_forwardings_from_committee_ids": [60],
                },
            }
        )
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "Mot 1",
                "meeting_id": 4,
                "origin_id": 1,
                "text": "Wir werden Miss Waikiki",
                "reason": "Weil wir so schön sind, so schlau sind, so schlank und rank",
                "with_change_recommendations": True,
                "with_amendments": True,
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0] == [
            {
                "id": 4,
                "non_forwarded_amendment_amount": 1,
                "sequential_number": 1,
                "amendment_result_data": [
                    {
                        "id": 5,
                        "non_forwarded_amendment_amount": 0,
                        "sequential_number": 2,
                        "amendment_result_data": [],
                    },
                ],
            }
        ]
        self.assert_model_exists(
            "motion/4",
            {
                "title": "Mot 1",
                "meeting_id": 4,
                "origin_id": 1,
                "text": "Wir werden Miss Waikiki",
                "reason": "Weil wir so schön sind, so schlau sind, so schlank und rank",
                "state_id": 4,
                "amendment_ids": [5],
                "all_origin_ids": [1],
                "origin_meeting_id": 1,
                "sequential_number": 1,
                "additional_submitter": "committee_forwarder",
                "identical_motion_ids": [],
            },
        )
        self.assert_model_exists(
            "motion/5",
            {
                "title": "Amendment 2",
                "meeting_id": 4,
                "origin_id": 3,
                "state_id": 4,
                "origin_meeting_id": 1,
                "lead_motion_id": 4,
                "amendment_paragraphs": {"0": "paragraph"},
                "all_origin_ids": [3],
                "additional_submitter": "committee_forwarder",
            },
        )
        self.assert_model_not_exists("motion/6")

    def test_forward_with_meeting_wide_mediafile_with_attachments_false(self) -> None:
        self.base_test_forward_with_attachments_false(origin_mediafile_ids=[1])

    def test_forward_with_orga_wide_mediafile_with_attachments_false(self) -> None:
        self.base_test_forward_with_attachments_false(origin_mediafile_ids=[2])

    def test_forward_with_nested_mediafiles_with_attachments_false(self) -> None:
        self.base_test_forward_with_attachments_false(origin_mediafile_ids=[3, 4, 5, 6])

    def test_forward_with_meeting_wide_mediafile_with_attachments_true(self) -> None:
        self.base_test_forward_with_attachments_true(origin_mediafile_ids=[1])

    def test_forward_with_orga_wide_mediafile_with_attachments_true(self) -> None:
        self.base_test_forward_with_attachments_true(origin_mediafile_ids=[2])

    def test_forward_with_nested_mediafiles_with_attachments_true(self) -> None:
        self.base_test_forward_with_attachments_true(
            origin_mediafile_ids=[1, 2, 3, 4, 5, 6],
            nested_files_ids={3: [1, 4], 2: [5], 5: [6]},
            custom_models_data={
                "mediafile/3": {
                    "child_ids": [1, 4],
                },
                "mediafile/1": {
                    "parent_id": 3,
                },
                "mediafile/4": {
                    "parent_id": 3,
                },
                "mediafile/2": {
                    "is_directory": True,
                    "child_ids": [5],
                },
                "mediafile/5": {
                    "parent_id": 2,
                },
            },
        )

    def test_preserve_meeting_attachments_ids_with_attachments_false(self) -> None:
        self.base_test_preserve_existing_meeting_attachments_ids(with_attachments=False)

    def test_preserve_meeting_attachments_ids_with_attachments_true(self) -> None:
        self.base_test_preserve_existing_meeting_attachments_ids(with_attachments=True)

    def base_test_forward_with_attachments_false(
        self,
        origin_mediafile_ids: list[int],
        custom_models_data: dict[str, dict[str, Any]] = {},
    ) -> None:
        """
        Base test for forwarding a motion without attachments.

        This test verifies that when forwarding a motion with the flag `with_attachments` set to False:
        1. A motion model is created with the correct data but without any attachments.
        2. The target meeting does not include any new ids in the `attachment_meeting_mediafile_ids` field.
        3. New `mediafile` and `meeting_mediafile` models are not created.
        4. Mediafiles are not duplicated.
        """

        (
            response,
            origin_meeting_mediafile_ids,
            target_mediafile_ids,
            target_meeting_mediafile_ids,
        ) = self.set_test_data_for_forwarding_with_attachments(
            False, origin_mediafile_ids, custom_models_data
        )

        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/13",
            {
                "title": "Mot 1",
                "meeting_id": 2,
                "origin_id": 12,
                "state_id": 34,
                "all_origin_ids": [12],
                "origin_meeting_id": 1,
                "sequential_number": 1,
                "attachment_meeting_mediafile_ids": None,
            },
        )
        self.assert_model_exists(
            "meeting/2",
            {
                "meeting_mediafile_ids": None,
            },
        )
        self.media.duplicate_mediafile.assert_not_called()
        for meeting_mediafile_id in target_meeting_mediafile_ids:
            self.assert_model_not_exists(f"meeting_mediafile/{meeting_mediafile_id}")
        for original_id, expected_mediafile_id in zip(
            origin_mediafile_ids, target_mediafile_ids
        ):
            if original_id != expected_mediafile_id:
                self.assert_model_not_exists(f"mediafile/{expected_mediafile_id}")

    def base_test_forward_with_attachments_true(
        self,
        origin_mediafile_ids: list[int],
        nested_files_ids: dict[int, list[int]] = {},
        custom_models_data: dict[str, dict[str, Any]] = {},
    ) -> None:
        """
        Base test for forwarding a motion with attachments.

        This test verifies that when forwarding a motion with the flag `with_attachments` set to True:
        1. A motion model ("motion/13") is created with the correct data.
        2. The target meeting ("meeting/2") includes all the `attachment_meeting_mediafile_ids` used in the origin motion.
        3. For each the meeting-wide mediafiles from the origin motion:
            - A new `mediafile` model is created
            - If the model is not a directory, the corresponding mediafile itself is duplicated
        4. Orga-wide mediafiles and `mediafile` models from the origin motion are not duplicated.
        5. For each forwarded mediafile a new `meeting_mediafile` is created.
        """

        (
            response,
            origin_meeting_mediafile_ids,
            target_mediafile_ids,
            target_meeting_mediafile_ids,
        ) = self.set_test_data_for_forwarding_with_attachments(
            True, origin_mediafile_ids, custom_models_data
        )

        self.assert_status_code(response, 200)

        expected_models: dict[str, dict[str, Any]] = {
            "motion/13": {
                "title": "Mot 1",
                "meeting_id": 2,
                "origin_id": 12,
                "state_id": 34,
                "all_origin_ids": [12],
                "origin_meeting_id": 1,
                "sequential_number": 1,
                "attachment_meeting_mediafile_ids": target_meeting_mediafile_ids,
            },
            "meeting/2": {
                "meeting_mediafile_ids": target_meeting_mediafile_ids,
            },
        }

        for (
            origin_mediafile_id,
            target_mediafile_id,
            origin_meeting_mediafile_id,
            target_meeting_mediafile_id,
        ) in zip(
            origin_mediafile_ids,
            target_mediafile_ids,
            origin_meeting_mediafile_ids,
            target_meeting_mediafile_ids,
        ):
            if origin_mediafile_id != target_mediafile_id:
                m_owner_id = "meeting/2"
                m_meeting_mediafile_ids = [target_meeting_mediafile_id]
            else:
                m_owner_id = ONE_ORGANIZATION_FQID
                m_meeting_mediafile_ids = [
                    origin_meeting_mediafile_id,
                    target_meeting_mediafile_id,
                ]
            expected_models[f"mediafile/{target_mediafile_id}"] = {
                "owner_id": m_owner_id,
                "mimetype": "text/plain",
                "meeting_mediafile_ids": m_meeting_mediafile_ids,
            }
            expected_models[f"meeting_mediafile/{target_meeting_mediafile_id}"] = {
                "meeting_id": 2,
                "mediafile_id": target_mediafile_id,
                "is_public": True,
                "attachment_ids": ["motion/13"],
            }

        mapped_mediafile_ids = {}
        expected_mediaservice_calls = []
        directory_ids = set(nested_files_ids.keys())
        for origin_id, target_id in zip(origin_mediafile_ids, target_mediafile_ids):
            mapped_mediafile_ids[origin_id] = target_id
            if origin_id != target_id and origin_id not in directory_ids:
                expected_mediaservice_calls.append(call(origin_id, target_id))

        if nested_files_ids:
            ORGA_WIDE_MEDIAFILES = {2, 5, 6}
            for origin_parent_id, origin_child_ids in nested_files_ids.items():
                if origin_parent_id not in ORGA_WIDE_MEDIAFILES:
                    target_parent_id = mapped_mediafile_ids[origin_parent_id]
                    target_child_ids = [
                        mapped_mediafile_ids[child_id] for child_id in origin_child_ids
                    ]
                else:
                    target_parent_id = origin_parent_id
                    target_child_ids = origin_child_ids
                expected_models[f"mediafile/{target_parent_id}"][
                    "child_ids"
                ] = target_child_ids
                for child_id in target_child_ids:
                    expected_models[f"mediafile/{child_id}"][
                        "parent_id"
                    ] = target_parent_id

        self.media.duplicate_mediafile.assert_has_calls(
            calls=expected_mediaservice_calls, any_order=True
        )

        for fqid, expected_data in expected_models.items():
            self.assert_model_exists(fqid, expected_data)

    def set_test_data_for_forwarding_with_attachments(
        self,
        with_attachments: bool,
        origin_mediafile_ids: list[int],
        custom_models_data: dict[str, dict[str, Any]],
    ) -> tuple[Response, list[int], list[int], list[int]]:
        """
        Prepares test data and performs a forwarding request, optionally including attachments (based on the with_attachments value).

        Returns a tuple containing:
            - origin_meeting_mediafile_ids (list[int]): The computed meeting mediafile IDs for the given origin mediafiles IDs.
            - target_mediafile_ids (list[int]): The expected IDs of the mediafiles related to the forwarded motion.
            - target_meeting_mediafile_ids (list[int]): The expected meeting mediafiles IDs used as attachments in the forwarded motion.
        """

        ORGA_WIDE_MEDIAFILES = {2, 5, 6}
        origin_meeting_mediafile_ids = [
            mediafile_id + 10 for mediafile_id in origin_mediafile_ids
        ]

        total_mediafiles_count = 6
        target_mediafile_ids = []
        for origin_id in origin_mediafile_ids:
            if origin_id in ORGA_WIDE_MEDIAFILES:
                target_mediafile_ids.append(origin_id)
            else:
                total_mediafiles_count += 1
                target_mediafile_ids.append(total_mediafiles_count)

        target_meeting_mediafile_ids = [
            max(origin_meeting_mediafile_ids) + i
            for i in range(1, len(origin_mediafile_ids) + 1)
        ]

        self.set_models(self.test_model)
        self.set_models(
            {
                "meeting/1": {
                    "admin_group_id": 112,
                    "meeting_mediafile_ids": origin_meeting_mediafile_ids,
                },
                "meeting/2": {
                    "admin_group_id": 112,
                },
                "motion/12": {
                    "attachment_meeting_mediafile_ids": origin_meeting_mediafile_ids
                },
            }
        )

        for mediafile_id, meeting_mediafile_id in zip(
            origin_mediafile_ids, origin_meeting_mediafile_ids
        ):
            self.set_models(
                {
                    f"meeting_mediafile/{meeting_mediafile_id}": {
                        "meeting_id": 1,
                        "mediafile_id": mediafile_id,
                        "is_public": True,
                        "attachment_ids": ["motion/12"],
                    },
                    f"mediafile/{mediafile_id}": {
                        "meeting_mediafile_ids": [meeting_mediafile_id],
                    },
                }
            )

        if custom_models_data:
            self.set_models(custom_models_data)

        self.media.duplicate_mediafile = MagicMock()
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "Mot 1",
                "meeting_id": 2,
                "origin_id": 12,
                "text": "test",
                "with_attachments": with_attachments,
            },
        )

        return (
            response,
            origin_meeting_mediafile_ids,
            target_mediafile_ids,
            target_meeting_mediafile_ids,
        )

    def base_test_preserve_existing_meeting_attachments_ids(
        self, with_attachments: bool
    ) -> None:
        self.set_models(self.test_model)
        self.set_models(
            {
                "meeting_mediafile/11": {
                    "meeting_id": 1,
                    "mediafile_id": 1,
                    "is_public": True,
                },
                "meeting_mediafile/12": {
                    "meeting_id": 2,
                    "mediafile_id": 2,
                    "is_public": True,
                },
                "meeting/1": {
                    "admin_group_id": 112,
                    "meeting_mediafile_ids": [11],
                },
                "meeting/2": {
                    "admin_group_id": 112,
                    "meeting_mediafile_ids": [12],
                },
                "motion/12": {"attachment_meeting_mediafile_ids": [11]},
            }
        )
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "Mot 1",
                "meeting_id": 2,
                "origin_id": 12,
                "text": "test",
                "with_attachments": with_attachments,
            },
        )

        expected_meeting_mediafile_ids = [12]
        if with_attachments:
            expected_meeting_mediafile_ids.append(13)

        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/2",
            {
                "meeting_mediafile_ids": expected_meeting_mediafile_ids,
            },
        )
