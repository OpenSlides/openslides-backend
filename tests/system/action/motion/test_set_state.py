import threading
import time

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionSetStateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                "motion_state/76": {
                    "meeting_id": 1,
                    "name": "test0",
                    "motion_ids": [],
                    "next_state_ids": [77],
                    "previous_state_ids": [],
                    "allow_submitter_edit": True,
                },
                "motion_state/77": {
                    "meeting_id": 1,
                    "name": "test1",
                    "motion_ids": [22],
                    "first_state_of_workflow_id": 76,
                    "next_state_ids": [],
                    "previous_state_ids": [76],
                    "allow_submitter_edit": True,
                },
                "motion/22": {
                    "meeting_id": 1,
                    "title": "test1",
                    "state_id": 77,
                    "number_value": 23,
                    "submitter_ids": [12],
                    "created": 1687339000,
                },
                "motion_submitter/12": {
                    "meeting_id": 1,
                    "motion_id": 22,
                    "meeting_user_id": 5,
                },
                "meeting_user/5": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "motion_submitter_ids": [12],
                },
                "meeting/1": {
                    "id": 1,
                    "meeting_user_ids": [5],
                },
                "user/1": {"id": 1, "meeting_user_ids": [5]},
            }
        )

    def test_set_state_correct_previous_state(self) -> None:
        check_time = round(time.time())
        self.update_model("motion_state/76", {"set_workflow_timestamp": True})
        response = self.request("motion.set_state", {"id": 22, "state_id": 76})
        self.assert_status_code(response, 200)
        model = self.get_model("motion/22")
        assert model.get("state_id") == 76
        assert model.get("number_value") == 23
        assert model.get("last_modified", 0) >= check_time
        assert model.get("workflow_timestamp", 0) >= check_time
        assert model.get("created") == 1687339000
        self.assert_history_information(
            "motion/22", ["State set to {}", "motion_state/76"]
        )

    def test_set_state_correct_next_state(self) -> None:
        self.set_models(
            {
                "motion_state/76": {
                    "motion_ids": [22],
                },
                "motion_state/77": {
                    "motion_ids": [],
                },
                "motion/22": {
                    "state_id": 76,
                    "number": "A021",
                },
            }
        )
        response = self.request("motion.set_state", {"id": 22, "state_id": 77})
        self.assert_status_code(response, 200)
        model = self.get_model("motion/22")
        assert model.get("state_id") == 77
        assert model.get("number") == "A021"

    def test_set_state_wrong_not_in_next_or_previous(self) -> None:
        self.set_models(
            {
                "motion_state/76": {
                    "next_state_ids": [],
                },
                "motion_state/77": {
                    "previous_state_ids": [],
                },
                "user/1": {
                    "organization_management_level": None,
                },
            }
        )
        response = self.request("motion.set_state", {"id": 22, "state_id": 76})
        self.assert_status_code(response, 400)
        self.assertIn(
            "State '76' is not in next or previous states of the state '77'.",
            response.json["message"],
        )

    def test_set_state_perm_ignore_graph_with_can_manage_metadata(self) -> None:
        self.set_models(
            {
                "motion_state/76": {
                    "next_state_ids": [],
                },
                "motion_state/77": {
                    "previous_state_ids": [],
                },
                "user/1": {
                    "organization_management_level": None,
                },
                "group/1": {
                    "meeting_id": 1,
                    "permissions": [Permissions.Motion.CAN_MANAGE_METADATA],
                },
            }
        )
        self.set_user_groups(1, [1])
        response = self.request("motion.set_state", {"id": 22, "state_id": 76})
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/22", {"state_id": 76})

    def test_set_state_set_number_multiple_motions(self) -> None:
        self.set_models(
            {
                "motion_state/76": {
                    "set_number": True,
                },
                "motion_state/77": {
                    "motion_ids": [22, 23, 24],
                },
                "motion/22": {
                    "number_value": None,
                },
                "motion/23": {
                    "meeting_id": 1,
                    "state_id": 77,
                },
                "motion/24": {
                    "meeting_id": 1,
                    "state_id": 77,
                },
            }
        )
        response = self.request_multi(
            "motion.set_state",
            [
                {"id": 22, "state_id": 76},
                {"id": 23, "state_id": 76},
                {"id": 24, "state_id": 76},
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/22")
        assert model.get("state_id") == 76
        assert model.get("number") == "1"
        model = self.get_model("motion/23")
        assert model.get("state_id") == 76
        assert model.get("number") == "2"
        model = self.get_model("motion/24")
        assert model.get("state_id") == 76
        assert model.get("number") == "3"

    def test_history_multiple_actions(self) -> None:
        self.set_models(
            {
                "motion/23": {
                    "meeting_id": 1,
                    "state_id": 77,
                },
            }
        )
        response = self.request_multi(
            "motion.set_state", [{"id": 22, "state_id": 76}, {"id": 23, "state_id": 76}]
        )
        self.assert_status_code(response, 200)
        self.assert_history_information(
            "motion/22", ["State set to {}", "motion_state/76"]
        )
        self.assert_history_information(
            "motion/23", ["State set to {}", "motion_state/76"]
        )

    def test_history_multiple_actions_different_states(self) -> None:
        self.set_models(
            {
                "motion/23": {
                    "meeting_id": 1,
                    "state_id": 76,
                },
            }
        )
        response = self.request_multi(
            "motion.set_state", [{"id": 22, "state_id": 76}, {"id": 23, "state_id": 77}]
        )
        self.assert_status_code(response, 200)
        self.assert_history_information(
            "motion/22", ["State set to {}", "motion_state/76"]
        )
        self.assert_history_information(
            "motion/23", ["State set to {}", "motion_state/77"]
        )

    def test_set_state_no_permission(self) -> None:
        self.base_permission_test(
            {},
            "motion.set_state",
            {"id": 22, "state_id": 76},
        )

    def test_set_state_permission(self) -> None:
        self.base_permission_test(
            {},
            "motion.set_state",
            {"id": 22, "state_id": 76},
            Permissions.Motion.CAN_MANAGE_METADATA,
        )

    def test_set_state_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "motion.set_state",
            {"id": 22, "state_id": 76},
        )

    def test_set_state_permission_submitter(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "organization_management_level": None,
                },
            }
        )
        response = self.request("motion.set_state", {"id": 22, "state_id": 76})
        self.assert_status_code(response, 200)

    def test_set_state_permission_submitter_and_withdraw(self) -> None:
        self.set_models(
            {
                "motion_state/76": {
                    "allow_submitter_edit": False,
                    "submitter_withdraw_back_ids": [77],
                },
                "motion_state/77": {
                    "allow_submitter_edit": False,
                    "submitter_withdraw_state_id": 76,
                },
                "user/1": {
                    "organization_management_level": None,
                },
                "meeting_user/5": {
                    "user_id": 1,
                    "meeting_id": 1,
                    "group_ids": [1],
                },
                "group/1": {
                    "meeting_id": 1,
                    "meeting_user_ids": [5],
                    "permissions": [Permissions.Motion.CAN_MANAGE_METADATA],
                },
            }
        )
        response = self.request("motion.set_state", {"id": 22, "state_id": 76})
        self.assert_status_code(response, 200)

    def test_set_state_parallel(self) -> None:
        count: int = 5
        self.sync_event = threading.Event()
        self.sync_event.clear()

        self.set_models(
            {
                "motion_state/77": {
                    "motion_ids": [22 + i for i in range(count)],
                },
                **{
                    f"motion/{22+i}": {
                        "meeting_id": 1,
                        "state_id": 77,
                        "number_value": 23 + i,
                    }
                    for i in range(count)
                },
            }
        )

        threads = []
        for i in range(count):
            thread = threading.Thread(target=self.thread_method, kwargs={"i": i})
            thread.start()
            threads.append(thread)

        exceptions = []
        check_time = time.time()
        self.sync_event.set()
        for thread in threads:
            thread.join()
            if exc := getattr(thread, "exception", None):
                exceptions.append(exc)
        duration = round(time.time() - check_time, 2)
        print(duration)
        for exception in exceptions:
            raise exception

    def thread_method(self, i: int) -> None:
        self.sync_event.wait()
        try:
            response = self.request("motion.set_state", {"id": 22 + i, "state_id": 76})
            self.assert_status_code(response, 200)
            self.assert_model_exists(f"motion/{22+i}", {"state_id": 76})
        except Exception as e:
            self.exception = e
