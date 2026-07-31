from typing import Any

from openslides_backend.action.util.actions_map import actions_map
from openslides_backend.action.util.typing import ActionResults

from .base import BaseActionTestCase


class TestMultiActionInterplay(BaseActionTestCase):
    """
    Tests the interaction between old-style and new-style actions,
    specifically when they are requested together.
    """

    # list of action_name, payloads, return_object, expected_results tuples
    # to be tested together in that order.
    case_actions: list[
        list[
            tuple[
                str,
                list[dict[str, Any]],
                ActionResults | None,
                dict[str, dict[str, Any] | None],
            ]
        ]
    ] = [
        [
            (
                "organization_tag.create",
                [
                    {"name": "Never", "color": "#123456", "organization_id": 1},
                    {"name": "gonna", "color": "#789abc", "organization_id": 1},
                ],
                [{"id": id_} for id_ in [1, 2]],
                {
                    "organization_tag/1": {
                        "name": "Never",
                        "color": "#123456",
                        "organization_id": 1,
                    },
                    "organization_tag/2": {
                        "name": "gonna",
                        "color": "#789abc",
                        "organization_id": 1,
                    },
                },
            ),  # legacy for now
            (
                "motion_workflow.create",
                [
                    {"name": "give", "meeting_id": 1},
                    {"name": "you", "meeting_id": 1},
                    {"name": "up.", "meeting_id": 1},
                ],
                [{"id": id_, "sequential_number": id_} for id_ in [2, 3, 4]],
                {
                    "motion_workflow/2": {"name": "give", "meeting_id": 1},
                    "motion_workflow/3": {"name": "you", "meeting_id": 1},
                    "motion_workflow/4": {"name": "up.", "meeting_id": 1},
                },
            ),
            (
                "user.update",
                [{"id": 1, "meeting_id": 1, "group_ids": [2]}],
                [None],
                {"meeting_user/1": {"user_id": 1, "meeting_id": 1, "group_ids": [2]}},
            ),  # legacy for now
            (
                "theme.create",
                [
                    {
                        "name": "Never",
                        "primary_500": "#aaaaaa",
                        "accent_500": "#bbbbbb",
                        "warn_500": "#cccccc",
                    },
                    {
                        "name": "gonna",
                        "primary_500": "#dddddd",
                        "accent_500": "#eeeeee",
                        "warn_500": "#ffffff",
                    },
                ],
                [{"id": id_} for id_ in [2, 3]],
                {
                    "theme/2": {
                        "name": "Never",
                        "primary_500": "#aaaaaa",
                        "accent_500": "#bbbbbb",
                        "warn_500": "#cccccc",
                    },
                    "theme/3": {
                        "name": "gonna",
                        "primary_500": "#dddddd",
                        "accent_500": "#eeeeee",
                        "warn_500": "#ffffff",
                    },
                },
            ),
            (
                "meeting.create",
                [
                    {
                        "name": "let you down.",
                        "committee_id": 60,
                        "language": "en",
                        "location": "Never gonna run around and desert you.",
                        "description": "Never gonna make you cry.",
                        "admin_ids": [1],
                    }
                ],
                [{"id": 2}],
                {
                    "meeting/2": {
                        "name": "let you down.",
                        "committee_id": 60,
                        "language": "en",
                        "location": "Never gonna run around and desert you.",
                        "description": "Never gonna make you cry.",
                    },
                    "meeting_user/2": {"user_id": 1, "meeting_id": 2},
                },
            ),  # legacy for now
        ],
        [
            (
                "organization_tag.delete",
                [{"id": id_} for id_ in [1, 2]],
                None,
                {"organization_tag/2": None},
            ),
            (
                "motion.create",
                [
                    {
                        "meeting_id": 1,
                        "title": "Never gonna",
                        "text": "SAYYYYYYY goodbye.",
                    }
                ],
                [{"id": 2, "sequential_number": 2}],
                {
                    "motion/2": {
                        "meeting_id": 1,
                        "title": "Never gonna",
                        "text": "SAYYYYYYY goodbye.",
                    },
                    "list_of_speakers/2": {"content_object_id": "motion/2"},
                },
            ),  # legacy for now
            (
                "motion_workflow.update",
                [{"id": 2, "name": "Never"}],
                [None],
                {"motion_workflow/2": {"name": "Never"}},
            ),
            (
                "topic.create",
                [
                    {"title": "gonna", "meeting_id": 1},
                ],
                [{"id": 1, "sequential_number": 1}],
                {
                    "topic/1": {"title": "gonna", "meeting_id": 1},
                    "agenda_item/1": {"content_object_id": "topic/1", "meeting_id": 1},
                },
            ),  # legacy for now
            (
                "theme.update",
                [
                    {"id": 2, "name": "tell"},
                    {"id": 3, "name": "a"},
                ],
                [None, None],
                {"theme/2": {"name": "tell"}, "theme/3": {"name": "a"}},
            ),
            (
                "user.create",
                [{"username": "lie", "email": "and.hurt@you.de"}],
                [{"id": 2}],
                {"user/2": {"username": "lie", "email": "and.hurt@you.de"}},
            ),  # legacy for now
        ],
        [
            ("motion.delete", [{"id": 2}], None, {"motion/2": None}),  # legacy for now
            (
                "organization.delete_history_information",
                [{"id": 1}],
                None,
                {f"history_position/{id_}": None for id_ in [1, 2, 3, 4, 5]},
            ),
            (
                "meeting.update",
                [{"id": id_, "time_zone": "Europe/Berlin"} for id_ in [1, 2]],
                [None, None],
                {f"meeting/{id_}": {"time_zone": "Europe/Berlin"} for id_ in [1, 2]},
            ),
        ],
    ]

    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.create_motion(1)

    def test_test_validity(self) -> None:
        count_dda = 0
        count_legacy = 0
        has_mixed_tests = False
        for case_iteration in self.case_actions:
            count_iter_dda = 0
            count_iter_legacy = 0
            action_names = {action_name for action_name, _, _, _ in case_iteration}
            for action_name in action_names:
                if actions_map[action_name].legacy:
                    count_legacy += 1
                    count_iter_legacy += 1
                else:
                    count_dda += 1
                    count_iter_dda += 1
            if count_iter_legacy and count_iter_dda:
                has_mixed_tests = True
        assert (
            has_mixed_tests
        ), "This test order needs to be switched up or this testclass is pointless"
        assert count_legacy > 0, "No legacy actions left."
        assert count_dda > 0, "Where did all the DDActions go?"

    def test_parse_actions_normal(self) -> None:
        for case_iteration in self.case_actions:
            response = self.request_json(
                [
                    {
                        "action": action_name,
                        "data": payloads,
                    }
                    for action_name, payloads, _, _ in case_iteration
                ],
            )
            self.assert_status_code(response, 200)
            all_results: list[ActionResults | None] = []
            for _, _, results, expected in case_iteration:
                all_results.append(results)
                for fqid, expected_data in expected.items():
                    if expected_data:
                        self.assert_model_exists(fqid, expected_data)
                    else:
                        self.assert_model_not_exists(fqid)
            assert response.json["results"] == all_results

    def test_parse_actions_non_atomic(self) -> None:
        for i, case_iteration in enumerate(self.case_actions):
            response = self.request_json(
                [
                    {
                        "action": action_name,
                        "data": payloads,
                    }
                    for action_name, payloads, _, _ in case_iteration
                ],
                atomic=False,
            )
            try:
                self.assert_status_code(response, 200)
                all_results: list[ActionResults | None] = []
                for _, _, results, expected in case_iteration:
                    all_results.append(results)
                    for fqid, expected_data in expected.items():
                        if expected_data:
                            self.assert_model_exists(fqid, expected_data)
                        else:
                            self.assert_model_not_exists(fqid)
                assert response.json["results"] == all_results
            except Exception as e:
                raise e

    def test_parse_actions_internal(self) -> None:
        for case_iteration in self.case_actions:
            response = self.request_json(
                [
                    {
                        "action": action_name,
                        "data": payloads,
                    }
                    for action_name, payloads, _, _ in case_iteration
                ],
                internal=True,
            )
            self.assert_status_code(response, 200)
            all_results: list[ActionResults | None] = []
            for _, _, results, expected in case_iteration:
                all_results.append(results)
                for fqid, expected_data in expected.items():
                    if expected_data:
                        self.assert_model_exists(fqid, expected_data)
                    else:
                        self.assert_model_not_exists(fqid)
            assert response.json["results"] == all_results
