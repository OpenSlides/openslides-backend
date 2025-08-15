import threading
from datetime import datetime
from zoneinfo import ZoneInfo

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionSetStateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.create_motion(1, 22)
        self.set_user_groups(1, [1])
        self.set_models(
            {
                "motion_state/76": {
                    "name": "test0",
                    "weight": 76,
                    "meeting_id": 1,
                    "next_state_ids": [22],
                    "workflow_id": 22,
                    "allow_submitter_edit": True,
                },
                "motion_state/22": {
                    "previous_state_ids": [76],
                    "allow_submitter_edit": True,
                },
                "motion/22": {
                    "number_value": 23,
                    "created": datetime.fromtimestamp(1687339000),
                },
                "motion_submitter/12": {
                    "meeting_id": 1,
                    "motion_id": 22,
                    "meeting_user_id": 1,
                },
            }
        )

    def test_set_state_correct_previous_state(self) -> None:
        check_time = datetime.now(ZoneInfo("UTC"))
        self.update_model("motion_state/76", {"set_workflow_timestamp": True})
        response = self.request("motion.set_state", {"id": 22, "state_id": 76})
        self.assert_status_code(response, 200)
        model = self.assert_model_exists(
            "motion/22",
            {
                "state_id": 76,
                "number_value": 23,
                "created": datetime.fromtimestamp(1687339000, ZoneInfo("UTC")),
            },
        )
        assert (
            model.get("last_modified", datetime.fromtimestamp(0, ZoneInfo("UTC")))
            >= check_time
        )
        assert (
            model.get("workflow_timestamp", datetime.fromtimestamp(0, ZoneInfo("UTC")))
            >= check_time
        )
        self.assert_history_information(
            "motion/22", ["State set to {}", "motion_state/76"]
        )

    def test_set_state_correct_next_state(self) -> None:
        self.set_models(
            {
                "motion/22": {"state_id": 76, "number": "A021"},
            }
        )
        response = self.request("motion.set_state", {"id": 22, "state_id": 22})
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/22", {"state_id": 22, "number": "A021"})

    def test_set_state_wrong_not_in_next_or_previous(self) -> None:
        self.set_models(
            {
                "motion_state/76": {"next_state_ids": None},
                "motion_state/22": {"previous_state_ids": None},
                "user/1": {"organization_management_level": None},
            }
        )
        response = self.request("motion.set_state", {"id": 22, "state_id": 76})
        self.assert_status_code(response, 400)
        self.assertIn(
            "State '76' is not in next or previous states of the state '22'.",
            response.json["message"],
        )

    def test_set_state_perm_ignore_graph_with_can_manage_metadata(self) -> None:
        self.set_models(
            {
                "motion_state/76": {"next_state_ids": None},
                "motion_state/22": {"previous_state_ids": None},
                "user/1": {"organization_management_level": None},
                "group/1": {"permissions": [Permissions.Motion.CAN_MANAGE_METADATA]},
            }
        )
        response = self.request("motion.set_state", {"id": 22, "state_id": 76})
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/22", {"state_id": 76})

    def test_set_state_set_number_multiple_motions(self) -> None:
        self.create_motion(1, 23)
        self.create_motion(1, 24)
        self.set_models(
            {
                "meeting/1": {"motions_number_min_digits": 1},
                "motion_state/76": {"set_number": True},
                "motion/22": {"number_value": None},
                "motion/23": {"state_id": 22},
                "motion/24": {"state_id": 22},
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
        self.assert_model_exists("motion/22", {"state_id": 76, "number": "1"})
        self.assert_model_exists("motion/23", {"state_id": 76, "number": "2"})
        self.assert_model_exists("motion/24", {"state_id": 76, "number": "3"})

    def test_history_multiple_actions(self) -> None:
        self.create_motion(1, 23)
        self.set_models({"motion/23": {"state_id": 22}})
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
        self.create_motion(1, 23)
        self.set_models({"motion/23": {"state_id": 76}})
        response = self.request_multi(
            "motion.set_state", [{"id": 22, "state_id": 76}, {"id": 23, "state_id": 22}]
        )
        self.assert_status_code(response, 200)
        self.assert_history_information(
            "motion/22", ["State set to {}", "motion_state/76"]
        )
        self.assert_history_information(
            "motion/23", ["State set to {}", "motion_state/22"]
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
                    "submitter_withdraw_back_ids": [22],
                },
                "motion_state/22": {
                    "allow_submitter_edit": False,
                    "submitter_withdraw_state_id": 76,
                },
                "user/1": {"organization_management_level": None},
                "group/1": {"permissions": [Permissions.Motion.CAN_MANAGE_METADATA]},
            }
        )
        response = self.request("motion.set_state", {"id": 22, "state_id": 76})
        self.assert_status_code(response, 200)

    def test_set_state_parallel(self) -> None:
        count: int = 5
        self.sync_event = threading.Event()
        self.sync_event.clear()
        for i in range(count):
            self.create_motion(1, 22 + i)
        self.set_models(
            {
                f"motion/{22+i}": {
                    "state_id": 22,
                    "number_value": 23 + i,
                }
                for i in range(count)
            }
        )

        threads = []
        for i in range(count):
            thread = threading.Thread(target=self.thread_method, kwargs={"i": i})
            thread.start()
            threads.append(thread)

        exceptions = []
        check_time = datetime.now()
        self.sync_event.set()
        for thread in threads:
            thread.join()
            if exc := getattr(thread, "exception", None):
                exceptions.append(exc)
        duration = datetime.now() - check_time
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
