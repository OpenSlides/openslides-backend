from typing import Any, cast
from unittest.mock import MagicMock, call

from openslides_backend.action.actions.motion.mixins import TextHashMixin
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.exceptions import DatastoreException
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID, ONE_ORGANIZATION_ID
from tests.system.action.base import BaseActionTestCase


class MotionCreateForwardedTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.test_model: dict[str, dict[str, Any]] = {
            "meeting/4": {"motions_default_amendment_workflow_id": 12},
            "motion_workflow/12": {
                "name": "name_workflow1",
                "first_state_id": 4,
                "state_ids": [4],
                "meeting_id": 4,
            },
            "motion_state/1": {
                "allow_motion_forwarding": True,
                "allow_amendment_forwarding": True,
            },
            "motion/12": {
                "title": "title_FcnPUXJB",
                "meeting_id": 1,
                "state_id": 1,
            },
            "committee/60": {
                "name": "committee_forwarder",
                "forward_to_committee_ids": [63],
            },
            "committee/63": {
                "name": "committee_receiver",
                "receive_forwardings_from_committee_ids": [60],
            },
            "user/1": {
                "first_name": "the",
                "last_name": "administrator",
                "title": "Worship",
                "pronoun": "he",
            },
            "meeting_user/1": {"structure_level_ids": [1, 2, 3]},
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
        }

    def set_test_models(self) -> None:
        self.create_meeting()
        self.create_meeting(4)
        self.set_user_groups(1, [1, 4])
        self.set_models(self.test_model)

    def test_correct_origin_id_set(self) -> None:
        self.set_test_models()
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 4,
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
                "meeting_id": 4,
                "origin_id": 12,
                "origin_meeting_id": 1,
                "all_derived_motion_ids": None,
                "all_origin_ids": [12],
                "reason": "reason_jLvcgAMx",
                "submitter_ids": None,
                "additional_submitter": "committee_forwarder",
                "state_id": 4,
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
        self.assert_history_information("motion/12", ["Forwarded to {}", "meeting/4"])
        self.assert_history_information("motion/13", ["Motion created (forwarded)"])

    def test_no_origin_id(self) -> None:
        self.set_test_models()
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
        self.assertEqual(
            "data must contain ['meeting_id'] properties", response.json["message"]
        )

    def test_no_meeting_id(self) -> None:
        self.set_test_models()
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 4,
                "text": "test",
                "reason": "reason_jLvcgAMx",
            },
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "data must contain ['origin_id'] properties", response.json["message"]
        )

    def test_correct_existing_unregistered_forward_user(self) -> None:
        self.set_test_models()
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
                "meeting_id": 4,
                "origin_id": 12,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        model = self.assert_model_exists(
            "motion/13",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 4,
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
        self.test_model["committee/60"]["forward_to_committee_ids"] = []
        self.set_test_models()
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_Xcdfgee",
                "text": "text",
                "meeting_id": 4,
                "origin_id": 12,
            },
        )
        self.assert_status_code(response, 400)
        self.assertEqual("Committee id 63 not in []", response.json["message"])

    def test_missing_origin(self) -> None:
        self.set_test_models()
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_Xcdfgee",
                "text": "text",
                "meeting_id": 222,
                "origin_id": 13,
            },
        )
        self.assert_status_code(response, 400)
        # TODO: fix whitespace in error message
        self.assertEqual(" Model 'motion/13' does not exist.", response.json["message"])

    def test_all_origin_ids_complex(self) -> None:
        self.set_test_models()
        self.set_models(
            {
                "motion_state/4": {"allow_motion_forwarding": True},
                "motion/6": {
                    "title": "title_FcnPUXJB layer 1",
                    "meeting_id": 1,
                    "state_id": 4,
                    "derived_motion_ids": [11, 12],
                    "all_origin_ids": [],
                    "all_derived_motion_ids": [11, 12, 13],
                },
                "motion/11": {
                    "title": "test11 layer 2",
                    "meeting_id": 1,
                    "state_id": 4,
                    "origin_id": 6,
                    "derived_motion_ids": [13],
                    "all_origin_ids": [6],
                    "all_derived_motion_ids": [13],
                },
                "motion/12": {
                    "title": "test12 layer 2",
                    "meeting_id": 1,
                    "state_id": 4,
                    "origin_id": 6,
                    "derived_motion_ids": [],
                    "all_origin_ids": [6],
                    "all_derived_motion_ids": [],
                },
                "motion/13": {
                    "title": "test13 layer 3",
                    "meeting_id": 1,
                    "state_id": 4,
                    "origin_id": 11,
                    "derived_motion_ids": [],
                    "all_origin_ids": [6, 11],
                    "all_derived_motion_ids": [],
                },
            }
        )
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_XXX_leyer 3",
                "meeting_id": 4,
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
        self.assert_history_information("motion/11", ["Forwarded to {}", "meeting/4"])
        self.assert_history_information("motion/6", None)

    def test_forward_with_deleted_motion_in_all_origin_ids(self) -> None:
        self.set_test_models()
        self.set_models(
            {
                "motion/1": {
                    "title": "deleted",
                    "meeting_id": 1,
                    "state_id": 1,
                    "derived_motion_ids": [2],
                    "all_derived_motion_ids": [2],
                },
                "motion/2": {
                    "title": "motion",
                    "meeting_id": 1,
                    "state_id": 1,
                    "origin_id": 1,
                    "all_origin_ids": [1],
                },
            }
        )
        response = self.request("motion.delete", {"id": 1})
        self.assert_model_exists("motion/2", {"all_origin_ids": []})
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "new",
                "meeting_id": 4,
                "origin_id": 2,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/13",
            {
                "title": "new",
                "meeting_id": 4,
                "state_id": 4,
                "origin_id": 2,
                "all_origin_ids": [2],
                "text": "test",
                "origin_meeting_id": 1,
            },
        )

    def test_not_allowed_to_forward_amendments_directly(self) -> None:
        self.test_model["motion_state/1"]["allow_amendment_forwarding"] = False
        self.set_test_models()
        self.set_models(
            {
                "meeting/1": {"motion_ids": [6, 11, 12]},
                "motion/6": {
                    "title": "title_FcnPUXJB layer 1",
                    "meeting_id": 1,
                    "state_id": 4,
                    "derived_motion_ids": [],
                    "all_origin_ids": [],
                    "all_derived_motion_ids": [],
                    "amendment_ids": [11],
                },
                "motion/11": {
                    "title": "test11 layer 2",
                    "meeting_id": 1,
                    "state_id": 4,
                    "derived_motion_ids": [],
                    "all_origin_ids": [],
                    "all_derived_motion_ids": [],
                    "lead_motion_id": 6,
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
        self.assertEqual("Amendments cannot be forwarded.", response.json["message"])

    def test_allowed_to_forward_amendments_indirectly(self) -> None:
        self.set_test_models()
        self.set_models(
            {
                "meeting/1": {"motion_ids": [12, 13]},
                "motion/12": {
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
                    "state_id": 1,
                    "amendment_paragraphs": {"0": "texts"},
                },
            }
        )
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_foo",
                "meeting_id": 4,
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
                "meeting_id": 4,
                "text": "test",
                "amendment_ids": [15],
                "state_id": 4,
                "additional_submitter": "committee_forwarder",
            },
        )
        self.assert_model_exists(
            "motion/15",
            {
                "lead_motion_id": 14,
                "origin_id": 13,
                "title": "amendment",
                "meeting_id": 4,
                "state_id": 4,
                "amendment_paragraphs": {"0": "texts"},
                "additional_submitter": "committee_forwarder",
                "marked_forwarded": False,
            },
        )

    def test_allowed_to_forward_amendments_indirectly_complex(self) -> None:
        self.set_test_models()
        user1 = self.create_user("first_submitter", [1])
        user2 = self.create_user("second_submitter", [1])
        self.set_models(
            {
                f"user/{user1}": {"first_name": "A", "last_name": "man"},
                f"user/{user2}": {
                    "title": "A",
                    "first_name": "hairy",
                    "last_name": "woman",
                },
                "meeting/1": {"motion_ids": [12, 13, 14, 15]},
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
                    "state_id": 1,
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
                    "state_id": 1,
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
                    "state_id": 1,
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
                "meeting/4": {
                    "motions_default_workflow_id": 4,
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
                    "meeting_id": 4,
                },
                "motion_state/35": {
                    "name": "name_state35",
                    "meeting_id": 4,
                },
            }
        )
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_foo",
                "meeting_id": 4,
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
                "meeting_id": 4,
                "text": "test",
                "amendment_ids": [19, 20],
                "additional_submitter": "A man, A hairy woman",
                "sequential_number": 1,
                "state_id": 4,
            },
        )
        self.assert_model_exists(
            "motion/19",
            {
                "number": "AMNDMNT1",
                "lead_motion_id": 18,
                "origin_id": 13,
                "title": "amendment1",
                "meeting_id": 4,
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
                "meeting_id": 4,
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
                "meeting_id": 4,
                "state_id": 35,
                "amendment_paragraphs": {"0": "testssss"},
                "additional_submitter": None,
                "sequential_number": 4,
                "marked_forwarded": True,
            },
        )

    def test_forward_to_2_meetings_1_transaction(self) -> None:
        """Forwarding of 1 motion to 2 meetings in 1 transaction"""
        self.set_test_models()
        self.create_meeting(7)
        self.set_models(
            {
                "meeting/7": {"committee_id": 63},
                "committee/63": {"meeting_ids": [4, 7]},
            }
        )
        response = self.request_multi(
            "motion.create_forwarded",
            [
                {
                    "title": "title_12_to_meeting2",
                    "meeting_id": 4,
                    "origin_id": 12,
                    "text": "test2",
                    "reason": "reason_jLvcgAMx2",
                },
                {
                    "title": "title_12_to_meeting3",
                    "meeting_id": 7,
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
                "meeting_id": 4,
                "origin_id": 12,
                "origin_meeting_id": 1,
                "all_derived_motion_ids": None,
                "all_origin_ids": [12],
                "reason": "reason_jLvcgAMx2",
                "submitter_ids": None,
                "additional_submitter": "committee_forwarder",
                "state_id": 4,
            },
        )
        assert model.get("forwarded")

        model = self.assert_model_exists(
            "motion/14",
            {
                "title": "title_12_to_meeting3",
                "meeting_id": 7,
                "origin_id": 12,
                "origin_meeting_id": 1,
                "all_derived_motion_ids": None,
                "all_origin_ids": [12],
                "reason": "reason_jLvcgAMx3",
                "submitter_ids": None,
                "additional_submitter": "committee_forwarder",
                "state_id": 7,
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
            ["Forwarded to {}", "meeting/4", "Forwarded to {}", "meeting/7"],
        )
        self.assert_history_information("motion/13", ["Motion created (forwarded)"])
        self.assert_history_information("motion/14", ["Motion created (forwarded)"])

    def test_create_forwarded_not_allowed_by_state(self) -> None:
        self.test_model["motion_state/1"]["allow_motion_forwarding"] = False
        self.set_test_models()
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 4,
                "origin_id": 12,
                "text": "test",
            },
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "State doesn't allow to forward motion.", response.json["message"]
        )

    def test_create_forwarded_with_identical_motion(self) -> None:
        self.create_meeting()
        self.create_meeting(4)
        text = "test"
        hash = TextHashMixin.get_hash(text)
        self.set_models(
            {
                "motion/13": {
                    "meeting_id": 4,
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
                "meeting_id": 4,
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
        self.set_test_models()
        self.user_id = self.create_user("user", [4])
        self.login(self.user_id)
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 4,
                "origin_id": 12,
                "text": "test",
            },
        )
        self.assert_status_code(response, 403)
        self.assertEqual(
            "You are not allowed to perform action motion.create_forwarded. Missing permission: motion.can_forward",
            response.json["message"],
        )

    def test_permissions(self) -> None:
        self.set_test_models()
        self.user_id = self.create_user("user", [3])
        self.login(self.user_id)
        self.set_group_permissions(3, [Permissions.Motion.CAN_MANAGE])
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 4,
                "origin_id": 12,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)

    def test_forward_multiple_to_meeting_with_set_number(self) -> None:
        """Forwarding of 1 motion to 2 meetings in 1 transaction"""
        self.set_test_models()
        self.set_models(
            {
                "meeting/1": {"motion_ids": [12, 13]},
                "motion/13": {
                    "title": "title_FcnPUXJB2",
                    "meeting_id": 1,
                    "state_id": 1,
                },
                "motion_state/1": {"motion_ids": [12, 13]},
                "motion_state/4": {"set_number": True},
            }
        )
        response = self.request_multi(
            "motion.create_forwarded",
            [
                {
                    "title": "title_12",
                    "meeting_id": 4,
                    "origin_id": 12,
                    "text": "test2",
                    "reason": "reason_jLvcgAMx2",
                },
                {
                    "title": "title_13",
                    "meeting_id": 4,
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
        self.set_test_models()
        self.set_models(
            {
                "meeting/1": {"motion_ids": [12, 13]},
                "motion/13": {
                    "title": "title_FcnPUXJB2",
                    "meeting_id": 1,
                    "state_id": 1,
                    "number": "1",
                },
                "motion_state/1": {"motion_ids": [12, 13]},
                "motion_state/4": {"set_number": True},
            }
        )
        response = self.request_multi(
            "motion.create_forwarded",
            [
                {
                    "title": "title_12",
                    "meeting_id": 4,
                    "origin_id": 12,
                    "text": "test2",
                    "reason": "reason_jLvcgAMx2",
                },
                {
                    "title": "title_13",
                    "meeting_id": 4,
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
        self.set_test_models()
        self.set_models(
            {
                "meeting/1": {"motion_ids": [12, 13]},
                "motion/12": {"number": "1"},
                "motion/13": {
                    "title": "title_FcnPUXJB2",
                    "meeting_id": 1,
                    "state_id": 1,
                },
                "motion_state/1": {"motion_ids": [12, 13]},
                "motion_state/4": {"set_number": True},
            }
        )
        response = self.request_multi(
            "motion.create_forwarded",
            [
                {
                    "title": "title_12",
                    "meeting_id": 4,
                    "origin_id": 12,
                    "text": "test2",
                    "reason": "reason_jLvcgAMx2",
                    "use_original_number": True,
                },
                {
                    "title": "title_13",
                    "meeting_id": 4,
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
        self.set_test_models()
        self.set_models(
            {
                "meeting/1": {"motion_ids": [12, 13]},
                "meeting/4": {"motion_ids": [14]},
                "motion/12": {"number": "1", "submitter_ids": [12]},
                "motion/13": {
                    "title": "title_FcnPUXJB2",
                    "meeting_id": 1,
                    "state_id": 1,
                    "number": "1",
                    "submitter_ids": [13],
                },
                "motion/14": {
                    "title": "title_FcnPUXJB2",
                    "meeting_id": 4,
                    "state_id": 1,
                    "number": "1",
                },
                "motion_state/1": {"motion_ids": [12, 13]},
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
                    "meeting_id": 4,
                    "origin_id": 12,
                    "text": "test2",
                    "reason": "reason_jLvcgAMx2",
                    "use_original_number": True,
                    "use_original_submitter": True,
                },
                {
                    "title": "title_13",
                    "meeting_id": 4,
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
        self.set_test_models()
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 4,
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
        self.set_test_models()
        extra_user_id = self.create_user("user", [1])
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
                "meeting_user/3": {"motion_submitter_ids": [13]},
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
                "meeting_id": 4,
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
        self.set_test_models()
        extra_user_data: list[tuple[dict[str, Any], ...]] = [
            ({"title": "He is", "pronoun": "he"}, {"structure_level_ids": [1, 3]}),
            ({"first_name": "King", "pronoun": "Kong"}, {"structure_level_ids": [2]}),
            (
                {"last_name": "Good"},
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
        extra_user_ids = [self.create_user(f"user{i}", [1]) for i in range(amount)]
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
                "meeting_id": 4,
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
        self.set_test_models()
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
                "meeting_id": 4,
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
                "meeting_id": 4,
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
                "meeting_id": 4,
            },
        )

    def test_without_change_recommendations(self) -> None:
        self.set_test_models()
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
                "meeting_id": 4,
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
        self.set_test_models()
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 4,
                "origin_id": 12,
                "text": "test",
                "reason": "reason_jLvcgAMx",
                "with_change_recommendations": True,
            },
        )
        self.assert_status_code(response, 200)

    def test_with_amendment_change_recommendations(self) -> None:
        self.set_test_models()
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
                    "state_id": 1,
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
                "meeting_id": 4,
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
                "meeting_id": 4,
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
                "meeting_id": 4,
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
                    "default_group_id": 4,
                    "group_ids": [4],
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

    def _update_list_field(
        self,
        models_data: dict[str, dict[str, Any]],
        fqid: str,
        field: str,
        new_value: int,
    ) -> dict[str, dict[str, Any]]:
        """
        For the models defined by fqid retrieves the value of the given field.
        If its type is list, appends it with the new_value.
        """
        existing = self.get_model(fqid).get(field, [])
        if isinstance(existing, list):
            models_data.setdefault(fqid, {})[field] = existing + [new_value]
        return models_data

    def create_mediafiles_from_dict(
        self, meeting_mediafiles: list[dict[str, int | list[int] | bool]]
    ) -> None:
        """
        Accepts data for creating mediafile and meeting mediafile and creates
        them with all the relations.
        Skips mediafiles creation for instances that already exist.
        """
        for mediafile in meeting_mediafiles:
            meeting_mediafile_id = cast(int, mediafile.get("meeting_mediafile_id", 0))
            mediafile_id = cast(int, mediafile.get("mediafile_id", 0))
            meeting_id = cast(int, mediafile.get("meeting_id", 0))
            is_directory = bool(mediafile.get("is_directory", False))

            raw_motion_ids = mediafile.get("motion_ids", [])
            motion_ids = raw_motion_ids if isinstance(raw_motion_ids, list) else []

            is_orga_wide = bool(mediafile.get("is_orga_wide", False))
            owner_meeting_id: int = 0 if is_orga_wide else meeting_id

            try:
                fqid = f"mediafile/{mediafile_id}"
                self.assert_model_exists(fqid)
                self.set_models(
                    self._update_list_field(
                        {}, fqid, "meeting_mediafile_ids", meeting_mediafile_id
                    )
                )
            except DatastoreException:
                self.create_mediafile(mediafile_id, owner_meeting_id, is_directory)
            self.create_meeting_mediafile(
                meeting_mediafile_id, mediafile_id, meeting_id, motion_ids
            )

    def create_mediafile(
        self,
        mediafile_id: int,
        owner_meeting_id: int = 0,
        is_directory: bool = False,
    ) -> None:
        fqid = f"mediafile/{mediafile_id}"
        model_data: dict[str, str | int | bool] = {
            "is_directory": is_directory,
            "title": (
                f"folder_{mediafile_id}" if is_directory else f"title_{mediafile_id}"
            ),
        }
        models_data = {fqid: model_data}

        if owner_meeting_id:
            owner_fqid = f"meeting/{owner_meeting_id}"
            model_data["owner_id"] = owner_fqid
            self._update_list_field(
                models_data,
                owner_fqid,
                "mediafile_ids",
                mediafile_id,
            )
        else:
            model_data.update(
                {
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                }
            )
            self._update_list_field(
                models_data, ONE_ORGANIZATION_FQID, "mediafile_ids", mediafile_id
            )

        if not is_directory:
            model_data["mimetype"] = "text/plain"
        self.set_models(models_data)

    def create_meeting_mediafile(
        self,
        meeting_mediafile_id: int,
        mediafile_id: int,
        meeting_id: int,
        motion_ids: list[int] = [],
    ) -> None:
        mm_fqid = f"meeting_mediafile/{meeting_mediafile_id}"
        model_data: dict[str, int | bool | list[str]] = {
            "meeting_id": meeting_id,
            "mediafile_id": mediafile_id,
            "is_public": True,
        }
        models_data = {mm_fqid: model_data}

        for fqid in [f"meeting/{meeting_id}", f"mediafile/{mediafile_id}"]:
            self._update_list_field(
                models_data, fqid, "meeting_mediafile_ids", meeting_mediafile_id
            )

        if motion_ids:
            model_data["attachment_ids"] = [
                f"motion/{motion_id}" for motion_id in motion_ids
            ]
            for motion_id in motion_ids:
                self._update_list_field(
                    models_data,
                    f"motion/{motion_id}",
                    "attachment_meeting_mediafile_ids",
                    meeting_mediafile_id,
                )
        self.set_models(models_data)

    def base_test_forward_with_attachments_false(self, is_orga_wide: bool) -> None:
        """
        Base test for forwarding a motion without attachments.

        This test verifies that when forwarding a motion with the flag
        `with_attachments` set to False:
        1. A motion model is created with the correct data but without any
           attachments.
        2. The target meeting does not include any new ids in the
           `attachment_meeting_mediafile_ids` field.
        3. New `mediafile` and `meeting_mediafile` models are not created.
        4. Mediafiles are not duplicated.
        """
        self.set_test_models()
        if is_orga_wide:
            self.create_mediafile(1)
        else:
            self.create_mediafile(1, 1)
        self.create_meeting_mediafile(10, 1, 1, [12])
        self.media.duplicate_mediafile = MagicMock()

        response = self.request(
            "motion.create_forwarded",
            {
                "title": "Mot 1",
                "meeting_id": 4,
                "origin_id": 12,
                "text": "test",
                "with_attachments": False,
            },
        )

        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/13",
            {
                "title": "Mot 1",
                "meeting_id": 4,
                "origin_id": 12,
                "state_id": 4,
                "all_origin_ids": [12],
                "origin_meeting_id": 1,
                "sequential_number": 1,
                "attachment_meeting_mediafile_ids": None,
            },
        )
        self.assert_model_exists("meeting/4", {"meeting_mediafile_ids": None})
        self.media.duplicate_mediafile.assert_not_called()
        self.assert_model_not_exists("mediafile/2")
        self.assert_model_not_exists("meeting_mediafile/2")

    def test_forward_with_attachments_false_meeting_wide_mediafile(self) -> None:
        self.base_test_forward_with_attachments_false(is_orga_wide=False)

    def test_forward_with_attachments_false_orga_wide_mediafile(self) -> None:
        self.base_test_forward_with_attachments_false(is_orga_wide=True)

    def test_forward_with_attachments_true_meeting_wide_mediafile(self) -> None:
        """
        Ensure that:
        1. Meeting-wide mediafile is duplicated in the database and media-service;
        2. meeting_mediafile is created in the new meeting, points to the new mediafile
            and is attached to the new motion.
        """
        self.set_test_models()
        self.create_mediafile(1, 1)
        self.create_meeting_mediafile(11, 1, 1, motion_ids=[12])
        self.media.duplicate_mediafile = MagicMock()
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "Mot 1",
                "meeting_id": 4,
                "origin_id": 12,
                "text": "test",
                "with_attachments": True,
            },
        )
        self.assert_status_code(response, 200)
        self.media.duplicate_mediafile.assert_called_once_with(1, 2)

        self.assert_model_exists(
            "motion/13", {"attachment_meeting_mediafile_ids": [12]}
        )
        self.assert_model_exists(
            "meeting/4", {"meeting_mediafile_ids": [12], "mediafile_ids": [2]}
        )
        self.assert_model_exists(
            "mediafile/2",
            {"owner_id": "meeting/4", "meeting_mediafile_ids": [12]},
        )
        self.assert_model_exists(
            "meeting_mediafile/12",
            {"meeting_id": 4, "mediafile_id": 2, "attachment_ids": ["motion/13"]},
        )

    def test_forward_with_attachments_true_orga_wide_mediafile(self) -> None:
        """
        Ensure that:
        1. Orga-wide mediafile is not duplicated in the database and media-service;
        2. meeting_mediafile is created in the new meeting, points to the origin
            mediafile and is attached to the new motion.
        """
        self.set_test_models()
        self.create_mediafile(1)
        self.create_meeting_mediafile(11, 1, 1, motion_ids=[12])
        self.media.duplicate_mediafile = MagicMock()
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "Mot 1",
                "meeting_id": 4,
                "origin_id": 12,
                "text": "test",
                "with_attachments": True,
            },
        )
        self.assert_status_code(response, 200)
        self.media.duplicate_mediafile.assert_not_called()

        self.assert_model_exists(
            "motion/13", {"attachment_meeting_mediafile_ids": [12]}
        )
        self.assert_model_exists(
            "meeting/4", {"meeting_mediafile_ids": [12], "mediafile_ids": None}
        )
        self.assert_model_exists(
            "mediafile/1",
            {"owner_id": "organization/1", "meeting_mediafile_ids": [11, 12]},
        )
        self.assert_model_exists(
            "meeting_mediafile/12",
            {"meeting_id": 4, "mediafile_id": 1, "attachment_ids": ["motion/13"]},
        )

    def test_forward_with_attachments_true_nested_mediafiles(self) -> None:
        """
        Ensures that if origin motion has nested mediafiles with both owner types:
        1. Only meeting-wide mediafiles are duplicated in database and media-service.
        2. New meeting_mediafiles are created for all the mediafiles used as
            attachments and pointing at the correct mediafiles: new instances if owner
            is meeting and origin mediafiles if owner is organization.
        3. Meeting-wide directories are not duplicated in the media-service.
        4. Parent-child relations are preserved for the duplicated meeting-wide mediafiles.
        """
        self.set_test_models()
        self.create_mediafile(1, 1, is_directory=True)
        self.create_mediafile(3, 1)
        self.create_mediafile(4, 1)

        self.create_mediafile(2, is_directory=True)
        self.create_mediafile(5, is_directory=True)
        self.create_mediafile(6)

        # TODO: move parent-child relations to the new method
        self.set_models(
            {
                "mediafile/1": {"child_ids": [3, 4]},
                "mediafile/3": {"parent_id": 1},
                "mediafile/4": {"parent_id": 1},
                "mediafile/2": {"child_ids": [5]},
                "mediafile/5": {"parent_id": 2, "child_ids": [6]},
                "mediafile/6": {"parent_id": 5},
            }
        )

        for i in range(1, 7):
            self.create_meeting_mediafile(i + 10, i, 1, motion_ids=[12])

        self.media.duplicate_mediafile = MagicMock()
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "Mot 1",
                "meeting_id": 4,
                "origin_id": 12,
                "text": "test",
                "with_attachments": True,
            },
        )
        self.assert_status_code(response, 200)
        self.assertEqual(self.media.duplicate_mediafile.call_count, 2)
        self.media.duplicate_mediafile.assert_has_calls(
            calls=[call(3, 8), call(4, 9)], any_order=True
        )

        self.assert_model_exists(
            "meeting/4",
            {
                "meeting_mediafile_ids": [17, 18, 19, 20, 21, 22],
                "mediafile_ids": [7, 8, 9],
            },
        )
        self.assert_model_exists(
            "motion/13", {"attachment_meeting_mediafile_ids": [17, 18, 19, 20, 21, 22]}
        )
        self.assert_model_exists(
            "mediafile/7",
            {
                "owner_id": "meeting/4",
                "meeting_mediafile_ids": [17],
                "child_ids": [8, 9],
            },
        )
        self.assert_model_exists(
            "mediafile/2",
            {
                "owner_id": "organization/1",
                "meeting_mediafile_ids": [12, 18],
                "child_ids": [5],
            },
        )
        self.assert_model_exists(
            "mediafile/8",
            {
                "owner_id": "meeting/4",
                "meeting_mediafile_ids": [19],
                "parent_id": 7,
            },
        )
        self.assert_model_exists(
            "mediafile/9",
            {
                "owner_id": "meeting/4",
                "meeting_mediafile_ids": [20],
                "parent_id": 7,
            },
        )
        self.assert_model_exists(
            "mediafile/5",
            {
                "owner_id": "organization/1",
                "meeting_mediafile_ids": [15, 21],
                "parent_id": 2,
                "child_ids": [6],
            },
        )
        self.assert_model_exists(
            "mediafile/6",
            {
                "owner_id": "organization/1",
                "meeting_mediafile_ids": [16, 22],
                "parent_id": 5,
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/17",
            {
                "meeting_id": 4,
                "mediafile_id": 7,
                "attachment_ids": ["motion/13"],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/18",
            {
                "meeting_id": 4,
                "mediafile_id": 2,
                "attachment_ids": ["motion/13"],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/19",
            {
                "meeting_id": 4,
                "mediafile_id": 8,
                "attachment_ids": ["motion/13"],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/20",
            {
                "meeting_id": 4,
                "mediafile_id": 9,
                "attachment_ids": ["motion/13"],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/21",
            {
                "meeting_id": 4,
                "mediafile_id": 5,
                "attachment_ids": ["motion/13"],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/22",
            {
                "meeting_id": 4,
                "mediafile_id": 6,
                "attachment_ids": ["motion/13"],
            },
        )

    def test_forward_to_the_same_meeting_with_orga_wide_mediafile(self) -> None:
        """
        Verify orga-wide mediafile is reused correctly when motion is forwarded
        to the same meeting.
        """
        self.set_test_models()
        self.set_models(
            {
                "committee/60": {
                    "forward_to_committee_ids": [63, 60],
                    "receive_forwardings_from_committee_ids": [60],
                    "meeting_ids": [1, 2],
                },
                "motion_workflow/33": {
                    "name": "name_workflow1",
                    "first_state_id": 1,
                    "state_ids": [1],
                    "meeting_id": 1,
                },
                "meeting/1": {
                    "motions_default_workflow_id": 33,
                    "motions_default_amendment_workflow_id": 33,
                },
            }
        )
        self.create_mediafiles_from_dict(
            [
                {
                    "meeting_mediafile_id": 1,
                    "mediafile_id": 1,
                    "meeting_id": 1,
                    "motion_ids": [12],
                    "is_orga_wide": True,
                },
            ]
        )
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "Mot 1",
                "meeting_id": 1,
                "origin_id": 12,
                "text": "test",
                "with_attachments": True,
            },
        )
        self.assert_status_code(response, 200)
        self.media.duplicate_mediafile.assert_not_called()
        self.assert_model_exists("meeting/1", {"meeting_mediafile_ids": [1]})
        self.assert_model_exists("motion/13", {"attachment_meeting_mediafile_ids": [1]})
        self.assert_model_exists(
            "mediafile/1",
            {"meeting_mediafile_ids": [1], "owner_id": ONE_ORGANIZATION_FQID},
        )
        self.assert_model_exists(
            "meeting_mediafile/1",
            {
                "meeting_id": 1,
                "mediafile_id": 1,
                "attachment_ids": ["motion/12", "motion/13"],
            },
        )

    def base_test_preserve_existing_meeting_attachments_ids(
        self, with_attachments: bool
    ) -> None:
        """
        Verify that forwarding new mediafiles doesn't impact existing mediafiles
        in the target meeting.
        """
        self.set_test_models()
        self.create_mediafiles_from_dict(
            [
                {
                    "meeting_mediafile_id": 11,
                    "mediafile_id": 1,
                    "meeting_id": 1,
                    "motion_ids": [12],
                    "is_orga_wide": False,
                },
                {
                    "meeting_mediafile_id": 12,
                    "mediafile_id": 2,
                    "meeting_id": 4,
                    "is_orga_wide": False,
                },
            ]
        )
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "Mot 1",
                "meeting_id": 4,
                "origin_id": 12,
                "text": "test",
                "with_attachments": with_attachments,
            },
        )

        expected_mediafile_ids = [2]
        expected_meeting_mediafile_ids = [12]
        if with_attachments:
            expected_mediafile_ids.append(3)
            expected_meeting_mediafile_ids.append(13)

        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/4",
            {
                "meeting_mediafile_ids": expected_meeting_mediafile_ids,
                "mediafile_ids": expected_mediafile_ids,
            },
        )

    def test_preserve_meeting_attachments_ids_with_attachments_false(self) -> None:
        self.base_test_preserve_existing_meeting_attachments_ids(with_attachments=False)

    def test_preserve_meeting_attachments_ids_with_attachments_true(self) -> None:
        self.base_test_preserve_existing_meeting_attachments_ids(with_attachments=True)

    def set_2_motions_with_same_attachment(self, is_orga_wide: bool) -> None:
        self.set_test_models()
        self.set_models(
            {
                "motion/13": {
                    "title": "Motion 13",
                    "meeting_id": 1,
                    "state_id": 1,
                },
                "motion_state/1": {"motion_ids": [12, 13]},
            }
        )
        self.create_mediafiles_from_dict(
            [
                {
                    "meeting_mediafile_id": 11,
                    "mediafile_id": 1,
                    "meeting_id": 1,
                    "motion_ids": [12, 13],
                    "is_orga_wide": is_orga_wide,
                },
            ]
        )
        self.media.duplicate_mediafile = MagicMock()

    def test_forward_to_1_meeting_together_with_shared_meeting_wide_mediafile(
        self,
    ) -> None:
        """
        Verify forwarding two motions with the same meeting-wide mediafile in one
        transaction creates only 1 new mediafile and 1 new meeting_mediafile.
        """
        self.set_2_motions_with_same_attachment(is_orga_wide=False)
        response = self.request_multi(
            "motion.create_forwarded",
            [
                {
                    "title": "Mot 1",
                    "meeting_id": 4,
                    "origin_id": 12,
                    "text": "test",
                    "with_attachments": True,
                },
                {
                    "title": "Mot 2",
                    "meeting_id": 4,
                    "origin_id": 13,
                    "text": "test",
                    "with_attachments": True,
                },
            ],
        )
        self.assert_status_code(response, 200)
        self.media.duplicate_mediafile.assert_called_once_with(1, 2)
        self.assert_model_not_exists("mediafile/3")
        self.assert_model_not_exists("meeting_mediafile/13")
        self.assert_model_exists(
            "meeting/4",
            {"meeting_mediafile_ids": [12], "mediafile_ids": [2]},
        )
        self.assert_model_exists(
            "mediafile/2", {"owner_id": "meeting/4", "meeting_mediafile_ids": [12]}
        )
        self.assert_model_exists(
            "meeting_mediafile/12",
            {
                "meeting_id": 4,
                "mediafile_id": 2,
                "attachment_ids": ["motion/14", "motion/15"],
            },
        )
        self.assert_model_exists(
            "motion/14", {"attachment_meeting_mediafile_ids": [12]}
        )
        self.assert_model_exists(
            "motion/15", {"attachment_meeting_mediafile_ids": [12]}
        )

    def test_correct_suffixes_forward_separately_shared_meeting_wide_mediafile(
        self,
    ) -> None:
        """
        Verify separately forwarded motions with the same attachment get mediafiles
        with correct title suffixes.
        """
        self.set_2_motions_with_same_attachment(is_orga_wide=False)
        self.set_models(
            {
                "motion/14": {
                    "title": "Motion 14",
                    "meeting_id": 1,
                    "state_id": 1,
                    "attachment_meeting_mediafile_ids": [11],
                },
                "motion_state/1": {"motion_ids": [12, 13, 14]},
                "meeting_mediafile/11": {
                    "attachment_ids": ["motion/12", "motion/13", "motion/14"]
                },
                "mediafile/1": {"title": "title_1 (12)"},
            }
        )
        response1 = self.request(
            "motion.create_forwarded",
            {
                "title": "Mot 1",
                "meeting_id": 4,
                "origin_id": 12,
                "text": "test",
                "with_attachments": True,
            },
        )
        response2 = self.request(
            "motion.create_forwarded",
            {
                "title": "Mot 2",
                "meeting_id": 4,
                "origin_id": 13,
                "text": "test",
                "with_attachments": True,
            },
        )
        response3 = self.request(
            "motion.create_forwarded",
            {
                "title": "Mot 3",
                "meeting_id": 4,
                "origin_id": 14,
                "text": "test",
                "with_attachments": True,
            },
        )
        self.assert_status_code(response1, 200)
        self.assert_status_code(response2, 200)
        self.assert_status_code(response3, 200)
        self.assertEqual(self.media.duplicate_mediafile.call_count, 3)
        self.media.duplicate_mediafile.assert_has_calls(
            calls=[call(1, 2), call(1, 3), call(1, 4)], any_order=True
        )
        self.assert_model_exists(
            "meeting/4",
            {
                "meeting_mediafile_ids": [12, 13, 14],
                "mediafile_ids": [2, 3, 4],
            },
        )
        self.assert_model_exists(
            "mediafile/2",
            {
                "meeting_mediafile_ids": [12],
                "owner_id": "meeting/4",
                "title": "title_1 (12)",
            },
        )
        self.assert_model_exists(
            "mediafile/3",
            {
                "meeting_mediafile_ids": [13],
                "owner_id": "meeting/4",
                "title": "title_1 (12) (1)",
            },
        )
        self.assert_model_exists(
            "mediafile/4",
            {
                "meeting_mediafile_ids": [14],
                "owner_id": "meeting/4",
                "title": "title_1 (12) (2)",
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/12",
            {"meeting_id": 4, "mediafile_id": 2, "attachment_ids": ["motion/15"]},
        )
        self.assert_model_exists(
            "meeting_mediafile/13",
            {"meeting_id": 4, "mediafile_id": 3, "attachment_ids": ["motion/16"]},
        )
        self.assert_model_exists(
            "meeting_mediafile/14",
            {"meeting_id": 4, "mediafile_id": 4, "attachment_ids": ["motion/17"]},
        )
        self.assert_model_exists(
            "motion/15", {"attachment_meeting_mediafile_ids": [12]}
        )
        self.assert_model_exists(
            "motion/16", {"attachment_meeting_mediafile_ids": [13]}
        )
        self.assert_model_exists(
            "motion/17", {"attachment_meeting_mediafile_ids": [14]}
        )

    def test_correct_suffixes_same_title_different_parents(
        self,
    ) -> None:
        """Verify identical titles in other directories don't trigger suffix addition."""
        self.set_2_motions_with_same_attachment(is_orga_wide=False)
        self.create_mediafiles_from_dict(
            [
                {
                    "meeting_mediafile_id": 12,
                    "mediafile_id": 2,
                    "meeting_id": 1,
                    "motion_ids": [13],
                    "is_orga_wide": False,
                    "is_directory": True,
                },
                {
                    "meeting_mediafile_id": 13,
                    "mediafile_id": 3,
                    "meeting_id": 1,
                    "motion_ids": [13],
                    "is_orga_wide": False,
                },
            ]
        )
        self.set_models(
            {
                "motion/13": {"attachment_meeting_mediafile_ids": [12, 13]},
                "meeting_mediafile/11": {"attachment_ids": ["motion/12"]},
                "mediafile/2": {"child_ids": [3]},
                "mediafile/3": {"parent_id": 2, "title": "title_1"},
            }
        )
        response1 = self.request(
            "motion.create_forwarded",
            {
                "title": "Mot 1",
                "meeting_id": 4,
                "origin_id": 12,
                "text": "test",
                "with_attachments": True,
            },
        )
        response2 = self.request(
            "motion.create_forwarded",
            {
                "title": "Mot 2",
                "meeting_id": 4,
                "origin_id": 13,
                "text": "test",
                "with_attachments": True,
            },
        )
        self.assert_status_code(response1, 200)
        self.assert_status_code(response2, 200)

        self.assertEqual(self.media.duplicate_mediafile.call_count, 2)
        self.media.duplicate_mediafile.assert_has_calls(
            calls=[call(1, 4), call(3, 6)], any_order=True
        )
        self.assert_model_exists(
            "mediafile/4",
            {
                "meeting_mediafile_ids": [14],
                "owner_id": "meeting/4",
                "title": "title_1",
            },
        )
        self.assert_model_exists(
            "mediafile/5",
            {
                "meeting_mediafile_ids": [15],
                "owner_id": "meeting/4",
                "title": "folder_2",
            },
        )
        self.assert_model_exists(
            "mediafile/6",
            {
                "meeting_mediafile_ids": [16],
                "owner_id": "meeting/4",
                "title": "title_1",
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/14",
            {"meeting_id": 4, "mediafile_id": 4, "attachment_ids": ["motion/14"]},
        )
        self.assert_model_exists(
            "meeting_mediafile/15",
            {"meeting_id": 4, "mediafile_id": 5, "attachment_ids": ["motion/15"]},
        )
        self.assert_model_exists(
            "meeting_mediafile/16",
            {"meeting_id": 4, "mediafile_id": 6, "attachment_ids": ["motion/15"]},
        )
        self.assert_model_exists(
            "motion/14", {"attachment_meeting_mediafile_ids": [14]}
        )
        self.assert_model_exists(
            "motion/15", {"attachment_meeting_mediafile_ids": [15, 16]}
        )

    def base_forward_to_1_meeting_with_shared_orga_wide_mediafile(
        self, forward_in_one_transaction: bool
    ) -> None:
        """Verify orga-wide mediafile is reused across separate forwardings correctly."""
        self.set_2_motions_with_same_attachment(is_orga_wide=True)
        if forward_in_one_transaction:
            response = self.request_multi(
                "motion.create_forwarded",
                [
                    {
                        "title": "Mot 1",
                        "meeting_id": 4,
                        "origin_id": 12,
                        "text": "test",
                        "with_attachments": True,
                    },
                    {
                        "title": "Mot 2",
                        "meeting_id": 4,
                        "origin_id": 13,
                        "text": "test",
                        "with_attachments": True,
                    },
                ],
            )
            self.assert_status_code(response, 200)
        else:
            response1 = self.request(
                "motion.create_forwarded",
                {
                    "title": "Mot 1",
                    "meeting_id": 4,
                    "origin_id": 12,
                    "text": "test",
                    "with_attachments": True,
                },
            )
            response2 = self.request(
                "motion.create_forwarded",
                {
                    "title": "Mot 2",
                    "meeting_id": 4,
                    "origin_id": 13,
                    "text": "test",
                    "with_attachments": True,
                },
            )
            self.assert_status_code(response1, 200)
            self.assert_status_code(response2, 200)

        self.media.duplicate_mediafile.assert_not_called()
        self.assert_model_not_exists("mediafile/2")
        self.assert_model_not_exists("meeting_mediafile/13")
        self.assert_model_exists(
            "meeting/4",
            {"meeting_mediafile_ids": [12], "mediafile_ids": None},
        )
        self.assert_model_exists("mediafile/1", {"meeting_mediafile_ids": [11, 12]})
        self.assert_model_exists(
            "meeting_mediafile/12",
            {
                "meeting_id": 4,
                "mediafile_id": 1,
                "attachment_ids": ["motion/14", "motion/15"],
            },
        )
        self.assert_model_exists(
            "motion/14", {"attachment_meeting_mediafile_ids": [12]}
        )
        self.assert_model_exists(
            "motion/15", {"attachment_meeting_mediafile_ids": [12]}
        )

    def test_forward_to_1_meeting_with_shared_orga_wide_mediafile_together(
        self,
    ) -> None:
        self.base_forward_to_1_meeting_with_shared_orga_wide_mediafile(True)

    def test_forward_to_1_meeting_with_shared_orga_wide_mediafile_separately(
        self,
    ) -> None:
        self.base_forward_to_1_meeting_with_shared_orga_wide_mediafile(False)

    def test_forward_to_2_meetings_1_transaction_orga_wide_mediafiles(
        self,
    ) -> None:
        self.set_test_models()
        self.create_meeting(7)
        self.create_mediafiles_from_dict(
            [
                {
                    "meeting_mediafile_id": 11,
                    "mediafile_id": 1,
                    "meeting_id": 1,
                    "motion_ids": [12],
                    "is_orga_wide": False,
                },
            ]
        )
        self.set_models(
            {
                "meeting/7": {"committee_id": 63},
                "committee/63": {"meeting_ids": [4, 7]},
            }
        )
        self.media.duplicate_mediafile = MagicMock()
        response = self.request_multi(
            "motion.create_forwarded",
            [
                {
                    "title": "Forward to meeting 4",
                    "meeting_id": 4,
                    "origin_id": 12,
                    "text": "test",
                    "with_attachments": True,
                },
                {
                    "title": "Forward to meeting 7",
                    "meeting_id": 7,
                    "origin_id": 12,
                    "text": "test",
                    "with_attachments": True,
                },
            ],
        )
        self.assert_status_code(response, 200)
        self.assertEqual(self.media.duplicate_mediafile.call_count, 2)
        self.media.duplicate_mediafile.assert_has_calls(
            calls=[call(1, 2), call(1, 3)], any_order=True
        )
        self.assert_model_exists(
            "meeting/4", {"meeting_mediafile_ids": [12], "mediafile_ids": [2]}
        )
        self.assert_model_exists(
            "meeting/7", {"meeting_mediafile_ids": [13], "mediafile_ids": [3]}
        )
        self.assert_model_exists(
            "mediafile/2", {"meeting_mediafile_ids": [12], "owner_id": "meeting/4"}
        )
        self.assert_model_exists(
            "mediafile/3", {"meeting_mediafile_ids": [13], "owner_id": "meeting/7"}
        )
        self.assert_model_exists(
            "meeting_mediafile/12",
            {"meeting_id": 4, "mediafile_id": 2, "attachment_ids": ["motion/13"]},
        )
        self.assert_model_exists(
            "meeting_mediafile/13",
            {"meeting_id": 7, "mediafile_id": 3, "attachment_ids": ["motion/14"]},
        )
        self.assert_model_exists(
            "motion/13", {"attachment_meeting_mediafile_ids": [12]}
        )
        self.assert_model_exists(
            "motion/14", {"attachment_meeting_mediafile_ids": [13]}
        )

    def set_motion_with_amendment(self) -> None:
        self.set_test_models()
        self.set_models(
            {
                "motion/12": {"amendment_ids": [13]},
                "motion/13": {
                    "title": "Amendment 13",
                    "meeting_id": 1,
                    "state_id": 1,
                    "lead_motion_id": 12,
                },
                "motion_state/1": {"motion_ids": [12, 13]},
            }
        )
        self.create_mediafiles_from_dict(
            [
                {
                    "meeting_mediafile_id": 11,
                    "mediafile_id": 1,
                    "meeting_id": 1,
                    "motion_ids": [13],
                    "is_orga_wide": False,
                },
                {
                    "meeting_mediafile_id": 14,
                    "mediafile_id": 6,
                    "meeting_id": 1,
                    "motion_ids": [12, 13],
                    "is_orga_wide": False,
                },
                {
                    "meeting_mediafile_id": 17,
                    "mediafile_id": 8,
                    "meeting_id": 1,
                    "motion_ids": [12],
                    "is_orga_wide": True,
                },
                {
                    "meeting_mediafile_id": 24,
                    "mediafile_id": 19,
                    "meeting_id": 1,
                    "motion_ids": [13],
                    "is_orga_wide": False,
                },
            ]
        )

    def test_forward_with_attachments_true_with_amendments_true_with_nested_amendments(
        self,
    ) -> None:
        self.set_motion_with_amendment()
        self.set_models(
            {
                "motion/13": {"amendment_ids": [14]},
                "motion/14": {
                    "title": "Amendment 14",
                    "meeting_id": 1,
                    "state_id": 1,
                    "lead_motion_id": 13,
                },
            }
        )
        self.create_mediafiles_from_dict(
            [
                {
                    "meeting_mediafile_id": 20,
                    "mediafile_id": 20,
                    "meeting_id": 1,
                    "motion_ids": [14],
                    "is_orga_wide": False,
                },
            ]
        )
        self.set_models(
            {
                "meeting_mediafile/11": {"attachment_ids": ["motion/13", "motion/14"]},
                "motion/14": {"attachment_meeting_mediafile_ids": [20, 11]},
            }
        )
        self.media.duplicate_mediafile = MagicMock()
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "Forward to meeting 2",
                "meeting_id": 4,
                "origin_id": 12,
                "text": "test",
                "with_attachments": True,
                "with_amendments": True,
            },
        )
        self.assert_status_code(response, 200)
        self.assertEqual(self.media.duplicate_mediafile.call_count, 4)
        self.media.duplicate_mediafile.assert_has_calls(
            calls=[call(6, 21), call(1, 22), call(19, 23), call(20, 24)], any_order=True
        )
        self.assert_model_exists(
            "meeting/4",
            {
                "meeting_mediafile_ids": [25, 26, 27, 28, 29],
                "mediafile_ids": [21, 22, 23, 24],
            },
        )
        self.assert_model_exists("mediafile/8", {"meeting_mediafile_ids": [17, 26]})
        self.assert_model_exists(
            "mediafile/21", {"meeting_mediafile_ids": [25], "owner_id": "meeting/4"}
        )
        self.assert_model_exists(
            "mediafile/22", {"meeting_mediafile_ids": [27], "owner_id": "meeting/4"}
        )
        self.assert_model_exists(
            "mediafile/23", {"meeting_mediafile_ids": [28], "owner_id": "meeting/4"}
        )
        self.assert_model_exists(
            "mediafile/24", {"meeting_mediafile_ids": [29], "owner_id": "meeting/4"}
        )
        self.assert_model_exists(
            "meeting_mediafile/25",
            {
                "meeting_id": 4,
                "mediafile_id": 21,
                "attachment_ids": ["motion/16", "motion/15"],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/26",
            {"meeting_id": 4, "mediafile_id": 8, "attachment_ids": ["motion/15"]},
        )
        self.assert_model_exists(
            "meeting_mediafile/27",
            {
                "meeting_id": 4,
                "mediafile_id": 22,
                "attachment_ids": ["motion/17", "motion/16"],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/28",
            {"meeting_id": 4, "mediafile_id": 23, "attachment_ids": ["motion/16"]},
        )
        self.assert_model_exists(
            "meeting_mediafile/29",
            {"meeting_id": 4, "mediafile_id": 24, "attachment_ids": ["motion/17"]},
        )
        self.assert_model_exists(
            "motion/15", {"attachment_meeting_mediafile_ids": [25, 26]}
        )
        self.assert_model_exists(
            "motion/16", {"attachment_meeting_mediafile_ids": [27, 25, 28]}
        )
        self.assert_model_exists(
            "motion/17", {"attachment_meeting_mediafile_ids": [29, 27]}
        )

    def base_forward_with_attachments_true_without_amendments(
        self, with_amendments: bool, allow_amendment_forwarding: bool
    ) -> None:
        """
        Verify that only mediafiles from the lead motion are forwarded.

        Check 2 cases:
        - with_amendments=False
        - with_amendments=True, amendment motion_state has allow_motion_forwarding=False
        """
        self.set_motion_with_amendment()
        if not allow_amendment_forwarding:
            self.set_models(
                {
                    "motion_state/4": {
                        "motion_ids": [13],
                        "allow_motion_forwarding": True,
                    },
                    "motion/13": {"state_id": 4},
                }
            )
        self.media.duplicate_mediafile = MagicMock()
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "Forward to meeting 2",
                "meeting_id": 4,
                "origin_id": 12,
                "text": "test",
                "with_attachments": True,
                "with_amendments": with_amendments,
            },
        )
        self.assert_status_code(response, 200)
        self.media.duplicate_mediafile.assert_called_once_with(6, 20)

        self.assert_model_not_exists("motion/15")
        self.assert_model_not_exists("mediafile/21")
        self.assert_model_not_exists("meeting_mediafile/27")

        self.assert_model_exists(
            "meeting/4", {"meeting_mediafile_ids": [25, 26], "mediafile_ids": [20]}
        )
        self.assert_model_exists("mediafile/8", {"meeting_mediafile_ids": [17, 26]})
        self.assert_model_exists(
            "mediafile/20", {"meeting_mediafile_ids": [25], "owner_id": "meeting/4"}
        )
        self.assert_model_exists(
            "meeting_mediafile/25",
            {"meeting_id": 4, "mediafile_id": 20, "attachment_ids": ["motion/14"]},
        )
        self.assert_model_exists(
            "meeting_mediafile/26",
            {"meeting_id": 4, "mediafile_id": 8, "attachment_ids": ["motion/14"]},
        )

    def test_forward_with_attachments_true_with_amendments_false(self) -> None:
        self.base_forward_with_attachments_true_without_amendments(
            with_amendments=False, allow_amendment_forwarding=True
        )

    def test_forward_with_attachments_true_allow_amendment_forwarding_false(
        self,
    ) -> None:
        self.base_forward_with_attachments_true_without_amendments(
            with_amendments=True, allow_amendment_forwarding=False
        )

    def base_forward_with_attachments_false(self, with_amendments: bool) -> None:
        self.set_motion_with_amendment()
        self.media.duplicate_mediafile = MagicMock()

        response = self.request(
            "motion.create_forwarded",
            {
                "title": "Forward to meeting 2",
                "meeting_id": 4,
                "origin_id": 12,
                "text": "test",
                "with_attachments": False,
                "with_amendments": with_amendments,
            },
        )
        self.assert_status_code(response, 200)
        self.media.duplicate_mediafile.assert_not_called()
        self.assert_model_not_exists("mediafile/20")
        self.assert_model_not_exists("meeting_mediafile/25")
        self.assert_model_exists(
            "meeting/4",
            {"meeting_mediafile_ids": None, "mediafile_ids": None},
        )
        self.assert_model_exists(
            "mediafile/8",
            {"meeting_mediafile_ids": [17]},
        )
        self.assert_model_exists(
            "motion/14", {"attachment_meeting_mediafile_ids": None}
        )

        if with_amendments:
            self.assert_model_exists(
                "motion/15", {"attachment_meeting_mediafile_ids": None}
            )
        else:
            self.assert_model_not_exists("motion/15")

    def test_forward_with_attachments_false_with_amendments_true(self) -> None:
        self.base_forward_with_attachments_false(with_amendments=True)

    def test_forward_with_attachments_false_with_amendments_false(self) -> None:
        self.base_forward_with_attachments_false(with_amendments=False)

    def test_forward_multiple_motions_with_mediafiles_and_amendments_in_1_transaction(
        self,
    ) -> None:
        self.set_test_models()
        self.set_models(
            {
                "motion/12": {"amendment_ids": [13]},
                "motion/13": {
                    "title": "Amendment 13",
                    "meeting_id": 1,
                    "state_id": 1,
                    "lead_motion_id": 12,
                },
                "motion/16": {
                    "title": "Motion 16",
                    "meeting_id": 1,
                    "state_id": 1,
                },
                "motion/17": {
                    "title": "Motion 17",
                    "meeting_id": 1,
                    "state_id": 1,
                },
            }
        )
        self.create_mediafiles_from_dict(
            [
                {
                    "meeting_mediafile_id": 8,
                    "mediafile_id": 1,
                    "meeting_id": 1,
                    "motion_ids": [16],
                    "is_orga_wide": False,
                },
                {
                    "meeting_mediafile_id": 14,
                    "mediafile_id": 6,
                    "meeting_id": 1,
                    "motion_ids": [13],
                    "is_orga_wide": False,
                },
                {
                    "meeting_mediafile_id": 17,
                    "mediafile_id": 9,
                    "meeting_id": 1,
                    "motion_ids": [12],
                    "is_orga_wide": True,
                },
                {
                    "meeting_mediafile_id": 31,
                    "mediafile_id": 16,
                    "meeting_id": 1,
                    "motion_ids": [13, 17],
                    "is_orga_wide": False,
                },
                {
                    "meeting_mediafile_id": 30,
                    "mediafile_id": 19,
                    "meeting_id": 1,
                    "motion_ids": [16],
                    "is_orga_wide": True,
                },
            ]
        )
        self.set_models({"motion_state/1": {"motion_ids": [12, 13, 16, 17]}})
        self.media.duplicate_mediafile = MagicMock()
        response = self.request_multi(
            "motion.create_forwarded",
            [
                {
                    "title": "Mot 17",
                    "meeting_id": 4,
                    "origin_id": 12,
                    "text": "test",
                    "with_attachments": True,
                    "with_amendments": True,
                },
                {
                    "title": "Mot 18",
                    "meeting_id": 4,
                    "origin_id": 16,
                    "text": "test",
                    "with_attachments": True,
                },
                {
                    "title": "Mot 19",
                    "meeting_id": 4,
                    "origin_id": 17,
                    "text": "test",
                    "with_attachments": True,
                },
            ],
        )
        self.assert_status_code(response, 200)
        self.assertEqual(self.media.duplicate_mediafile.call_count, 3)
        self.media.duplicate_mediafile.assert_has_calls(
            calls=[call(1, 20), call(16, 21), call(6, 22)], any_order=True
        )
        self.assert_model_exists(
            "meeting/4",
            {
                "meeting_mediafile_ids": [32, 33, 34, 35, 36],
                "mediafile_ids": [20, 21, 22],
            },
        )
        self.assert_model_exists(
            "motion/18", {"attachment_meeting_mediafile_ids": [33]}
        )
        self.assert_model_exists(
            "motion/19", {"attachment_meeting_mediafile_ids": [32, 34]}
        )
        self.assert_model_exists(
            "motion/20", {"attachment_meeting_mediafile_ids": [35]}
        )
        self.assert_model_exists(
            "motion/21", {"attachment_meeting_mediafile_ids": [36, 35]}
        )
        self.assert_model_exists(
            "mediafile/20", {"meeting_mediafile_ids": [32], "owner_id": "meeting/4"}
        )
        self.assert_model_exists(
            "mediafile/21", {"meeting_mediafile_ids": [35], "owner_id": "meeting/4"}
        )
        self.assert_model_exists(
            "mediafile/22", {"meeting_mediafile_ids": [36], "owner_id": "meeting/4"}
        )
        self.assert_model_exists(
            "mediafile/9",
            {"meeting_mediafile_ids": [17, 33], "owner_id": ONE_ORGANIZATION_FQID},
        )
        self.assert_model_exists(
            "mediafile/19",
            {"meeting_mediafile_ids": [30, 34], "owner_id": ONE_ORGANIZATION_FQID},
        )
        self.assert_model_exists(
            "meeting_mediafile/32",
            {"meeting_id": 4, "mediafile_id": 20, "attachment_ids": ["motion/19"]},
        )
        self.assert_model_exists(
            "meeting_mediafile/36",
            {"meeting_id": 4, "mediafile_id": 22, "attachment_ids": ["motion/21"]},
        )
        self.assert_model_exists(
            "meeting_mediafile/33",
            {"meeting_id": 4, "mediafile_id": 9, "attachment_ids": ["motion/18"]},
        )
        self.assert_model_exists(
            "meeting_mediafile/34",
            {"meeting_id": 4, "mediafile_id": 19, "attachment_ids": ["motion/19"]},
        )
        self.assert_model_exists(
            "meeting_mediafile/35",
            {
                "meeting_id": 4,
                "mediafile_id": 21,
                "attachment_ids": ["motion/21", "motion/20"],
            },
        )
